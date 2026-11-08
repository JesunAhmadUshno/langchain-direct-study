"""LangChain arm: the shared executor inside a chain of runnables.

Durability design (frozen in PREREGISTRATION.md):

- Sequencing and composition: LCEL. One step of the task is one
  invocation of a RunnableSequence of RunnableLambda stages: load
  state, run one executor step, persist state. The driver invokes
  the chain until the run status is no longer running.
- Cross-step state: the executor state dict travels as the runnable
  input and output value, LangChain's data-flow convention.
- Durable state: langchain-core ships no checkpointer for arbitrary
  runnable state (checkpointing lives in LangGraph, the graph layer,
  out of scope here). The persist stage writes the full state dict
  to the arm's own SQLite store after every step, the same
  durability discipline as the native arm, and the load stage reads
  it back on the next invocation or on resume after a kill.
- Effect idempotency: the executor asks the ledger (was_applied)
  before applying an effect and treats a hit as recovered. The
  commit hook applies through the shared append_record. This is the
  discipline both arms of the sibling study applied.

The graph framework is never imported by this module. langchain
1.4.9 installs langgraph as a dependency of its agent surface, but
no code path here touches it; tests/test_arms_smoke.py asserts
langgraph stays out of sys.modules after an arm run.
"""

import json
import os
import sqlite3
import time

from langchain_core.runnables import RunnableLambda

from . import executor
from .tools import Tools

DB_NAME = "langchain_state.sqlite"


def _connect(run_dir):
    conn = sqlite3.connect(os.path.join(run_dir, DB_NAME))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS run_state ("
        "id INTEGER PRIMARY KEY CHECK (id = 1), body TEXT NOT NULL)"
    )
    conn.commit()
    return conn


def _load_state(conn):
    row = conn.execute("SELECT body FROM run_state WHERE id = 1").fetchone()
    if row is None:
        return None
    return json.loads(row[0])


def _save_state(conn, state):
    conn.execute(
        "INSERT INTO run_state (id, body) VALUES (1, ?) "
        "ON CONFLICT(id) DO UPDATE SET body = excluded.body",
        (json.dumps(state),),
    )
    conn.commit()


def run(task, trial_seed, run_dir):
    """Run or resume one trial. Returns the result dict."""
    os.makedirs(run_dir, exist_ok=True)
    tools = Tools(run_dir, task, trial_seed)
    trace = executor.Trace(run_dir)
    conn = _connect(run_dir)

    def reconcile(key):
        return tools.was_applied(key)

    def commit(action):
        return tools.append_record(
            action["collection"], action["payload"], action["key"], action["step"]
        )

    ctx = executor.Context(task, tools, trace, reconcile, commit)

    def load_stage(_value):
        state = _load_state(conn)
        if state is None:
            state = executor.new_state()
        return state

    def step_stage(state):
        return executor.execute_one(state, ctx)

    def persist_stage(state):
        _save_state(conn, state)
        return state

    chain = (
        RunnableLambda(load_stage)
        | RunnableLambda(step_stage)
        | RunnableLambda(persist_stage)
    )

    state = _load_state(conn)
    if state is None:
        state = executor.new_state()
        _save_state(conn, state)
    started = time.perf_counter()
    while state["status"] == "running":
        state = chain.invoke(None)
    wall = time.perf_counter() - started
    conn.close()
    return {
        "status": state["status"],
        "failure": state["failure"],
        "invocations": state["invocations"],
        "wall_seconds": wall,
        "state_bytes": os.path.getsize(os.path.join(run_dir, DB_NAME)),
    }

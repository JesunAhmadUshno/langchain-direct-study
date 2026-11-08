"""Native arm: a hand-written loop with its own SQLite event log.

Durability design (the write-ahead pattern):
- After every step, the full executor state is committed to SQLite.
- Before an effect is applied, an intent row is committed. After the
  effect returns, the row is marked done.
- On restart the state is loaded back and the loop continues at the
  first unfinished step. An intent row without a done mark means the
  process died around the effect; the ledger itself is then asked
  (was_applied) whether the effect landed, and the answer decides
  whether the step is recovered or re-applied.
"""

import json
import os
import sqlite3
import time

from . import executor
from .tools import Tools

DB_NAME = "native_state.sqlite"


def _connect(run_dir):
    conn = sqlite3.connect(os.path.join(run_dir, DB_NAME))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS run_state ("
        "id INTEGER PRIMARY KEY CHECK (id = 1), body TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS effects ("
        "key TEXT PRIMARY KEY, status TEXT NOT NULL)"
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
        row = conn.execute(
            "SELECT status FROM effects WHERE key = ?", (key,)
        ).fetchone()
        entry = tools.was_applied(key)
        if entry is not None:
            if row is None or row[0] != "done":
                conn.execute(
                    "INSERT INTO effects (key, status) VALUES (?, 'done') "
                    "ON CONFLICT(key) DO UPDATE SET status = 'done'",
                    (key,),
                )
                conn.commit()
            return entry
        return None

    def commit(action):
        conn.execute(
            "INSERT INTO effects (key, status) VALUES (?, 'intent') "
            "ON CONFLICT(key) DO NOTHING",
            (action["key"],),
        )
        conn.commit()
        entry = tools.append_record(
            action["collection"], action["payload"], action["key"], action["step"]
        )
        conn.execute(
            "UPDATE effects SET status = 'done' WHERE key = ?", (action["key"],)
        )
        conn.commit()
        return entry

    ctx = executor.Context(task, tools, trace, reconcile, commit)
    state = _load_state(conn)
    if state is None:
        state = executor.new_state()
        _save_state(conn, state)
    started = time.perf_counter()
    while state["status"] == "running":
        state = executor.execute_one(state, ctx)
        _save_state(conn, state)
    wall = time.perf_counter() - started
    conn.close()
    return {
        "status": state["status"],
        "failure": state["failure"],
        "invocations": state["invocations"],
        "wall_seconds": wall,
        "state_bytes": os.path.getsize(os.path.join(run_dir, DB_NAME)),
    }

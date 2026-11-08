"""The shared per-step executor.

One call runs one step: ask the policy for the action, run it against the
tools with the shared retry budget, record the observation. Both arms use
this function unchanged. The arms differ only in the context they pass:

- ctx.tools: the shared tool implementations.
- ctx.reconcile(key): arm durability hook. Returns the ledger entry for
  an effect that is already applied, or None.
- ctx.commit(action): arm durability hook. Applies the effect through
  tools.append_record and records the arm's own completion mark.

State is a plain dict: next_step (0-based), observations (string step
index to result dict), invocations, status, failure.

Fault hook F1: when STUDY_KILL_MODE=before_step and STUDY_KILL_STEP is
the 1-based number of the step about to start, the process is killed
before that step does anything. The previous step is already durable in
both arms at that point (checkpoint written, event log committed).
"""

import json
import os
import signal

from . import policy
from .tasks import RETRY_BUDGET, STEP_BUDGET
from .tools import TransientToolError


def new_state():
    return {
        "next_step": 0,
        "observations": {},
        "invocations": 0,
        "status": "running",
        "failure": None,
    }


class Trace:
    """Append-only run trace. Each line is flushed and synced so the
    trace survives a SIGKILL and can be scored across attempts."""

    def __init__(self, run_dir):
        self.path = os.path.join(run_dir, "trace.jsonl")

    def write(self, event):
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())


class Context:
    def __init__(self, task, tools, trace, reconcile, commit):
        self.task = task
        self.tools = tools
        self.trace = trace
        self.reconcile = reconcile
        self.commit = commit


def _fault_hook_before_step(state):
    mode = os.environ.get("STUDY_KILL_MODE", "")
    if mode != "before_step":
        return
    kill_step = int(os.environ.get("STUDY_KILL_STEP", "0"))
    if state["next_step"] + 1 == kill_step:
        os.kill(os.getpid(), signal.SIGKILL)


def execute_one(state, ctx):
    """Run exactly one step of the task. Mutates and returns state."""
    _fault_hook_before_step(state)
    task = ctx.task
    step_index = state["next_step"]
    if step_index >= len(task.steps):
        state["status"] = "completed"
        return state
    if state["invocations"] >= STEP_BUDGET:
        state["status"] = "failed"
        state["failure"] = "step budget exhausted"
        return state
    step_spec = task.steps[step_index]
    ctx.trace.write({"event": "step_start", "step": step_index})
    action = policy.decide(task, step_index, state["observations"])
    state["invocations"] += 1
    attempt = 0
    while True:
        try:
            if action["tool"] == "lookup":
                ctx.tools.maybe_fail(step_index, step_spec, attempt)
                value = ctx.tools.lookup(action["store_key"])
                state["observations"][str(step_index)] = {"value": value}
            elif action["tool"] == "append_record":
                existing = ctx.reconcile(action["key"])
                if existing is not None:
                    state["observations"][str(step_index)] = {
                        "entry": existing,
                        "recovered": True,
                    }
                else:
                    ctx.tools.maybe_fail(step_index, step_spec, attempt)
                    entry = ctx.commit(action)
                    state["observations"][str(step_index)] = {"entry": entry}
            else:  # pragma: no cover, the policy emits two tools only
                raise ValueError("unknown tool %r" % (action["tool"],))
            break
        except TransientToolError:
            attempt += 1
            if attempt > RETRY_BUDGET:
                state["status"] = "failed"
                state["failure"] = (
                    "tool retries exhausted at step %d" % step_index
                )
                ctx.trace.write(
                    {"event": "step_failed", "step": step_index}
                )
                return state
    state["next_step"] = step_index + 1
    if state["next_step"] >= len(task.steps):
        state["status"] = "completed"
    ctx.trace.write({"event": "step_done", "step": step_index})
    return state

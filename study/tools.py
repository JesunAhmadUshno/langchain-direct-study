"""Tool implementations, shared by both arms.

Tools are bound to one run directory. The side-effecting tool,
append_record, appends one JSON line to the run ledger on every call and
does not deduplicate: exactly-once is the orchestrator's problem.

Flakiness: a step spec may carry a failure probability. The draw is a
hash of (task_id, trial_seed, step_index, attempt), so both arms face the
identical sequence. A flaky failure raises TransientToolError before any
effect is applied.

Fault injection: when the environment carries STUDY_KILL_MODE=mid_step
and STUDY_KILL_STEP, append_record kills the process with SIGKILL after
the ledger write is durable and before the call returns. That is the F2
fault of SPEC.md: the effect exists, the orchestrator does not know.
"""

import hashlib
import json
import os
import signal


class TransientToolError(Exception):
    """A tool call failed transiently, before applying any effect."""


def failure_draw(task_id, trial_seed, step_index, attempt, probability):
    """Deterministic draw: True when this attempt fails."""
    material = "%s|%s|%s|%s" % (task_id, trial_seed, step_index, attempt)
    digest = hashlib.sha256(material.encode("utf-8")).digest()
    value = int.from_bytes(digest[:8], "big") / float(1 << 64)
    return value < probability


class Tools:
    def __init__(self, run_dir, task, trial_seed):
        self.run_dir = run_dir
        self.task = task
        self.trial_seed = trial_seed
        self.ledger_path = os.path.join(run_dir, "ledger.jsonl")
        self.kill_mode = os.environ.get("STUDY_KILL_MODE", "")
        self.kill_step = int(os.environ.get("STUDY_KILL_STEP", "0"))

    # -- ledger helpers -------------------------------------------------
    def _ledger_entries(self):
        entries = []
        if os.path.exists(self.ledger_path):
            with open(self.ledger_path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
        return entries

    def was_applied(self, key):
        """Read-only reconciliation: the ledger entry for key, or None."""
        for entry in self._ledger_entries():
            if entry["key"] == key:
                return entry
        return None

    def ledger_keys(self):
        return [entry["key"] for entry in self._ledger_entries()]

    # -- the tool surface ------------------------------------------------
    def lookup(self, store_key):
        return self.task.store[store_key]

    def maybe_fail(self, step_index, step_spec, attempt):
        probability = step_spec.get("flaky")
        if probability is None:
            return
        if failure_draw(self.task.task_id, self.trial_seed, step_index, attempt, probability):
            raise TransientToolError(
                "transient failure at step %d attempt %d" % (step_index, attempt)
            )

    def append_record(self, collection, payload, key, step_index):
        entry = {"collection": collection, "payload": payload, "key": key}
        with open(self.ledger_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        if self.kill_mode == "mid_step" and self.kill_step == step_index + 1:
            # F2: effect durable, result never recorded. Die now.
            os.kill(os.getpid(), signal.SIGKILL)
        return entry

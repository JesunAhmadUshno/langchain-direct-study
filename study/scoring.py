"""Scoring of one finished run directory against its task fixture.

A run succeeds when the arm reports completion and the ledger holds
each intended effect exactly once and nothing else. Recomputed steps
are traced step starts beyond the first start of the same step, summed
over the run (a step re-entered after a resume counts once per extra
entry).
"""

import json
import os
from collections import Counter


def _read_jsonl(path):
    rows = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


def score_run(task, run_dir, result):
    ledger = _read_jsonl(os.path.join(run_dir, "ledger.jsonl"))
    got = Counter(entry["key"] for entry in ledger)
    intended = Counter(task.intended_keys())
    duplicates = sorted(key for key, count in got.items() if count > 1)
    missing = sorted((intended - got).elements())
    extra = sorted((got - intended).elements())
    exactly_once = got == intended
    completed = bool(result) and result.get("status") == "completed"
    trace = _read_jsonl(os.path.join(run_dir, "trace.jsonl"))
    starts = Counter(
        event["step"] for event in trace if event.get("event") == "step_start"
    )
    recomputed = sum(count - 1 for count in starts.values())
    return {
        "completed": completed,
        "exactly_once": exactly_once,
        "success": completed and exactly_once,
        "duplicates": duplicates,
        "missing": missing,
        "extra": extra,
        "recomputed_steps": recomputed,
        "failure": (result or {}).get("failure"),
    }

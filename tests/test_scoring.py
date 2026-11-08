import json

from study import scoring
from study.tasks import TASKS_BY_ID


def _write(run_dir, name, rows):
    with open(run_dir / name, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def _ledger(keys):
    return [{"collection": "c", "payload": "p", "key": k} for k in keys]


def test_exact_ledger_succeeds(tmp_path):
    task = TASKS_BY_ID["T01"]
    _write(tmp_path, "ledger.jsonl", _ledger(task.intended_keys()))
    scored = scoring.score_run(task, str(tmp_path), {"status": "completed"})
    assert scored["success"] and scored["exactly_once"]
    assert scored["duplicates"] == scored["missing"] == scored["extra"] == []


def test_duplicate_missing_and_extra_are_detected(tmp_path):
    task = TASKS_BY_ID["T01"]  # intended: t01-fx1, t01-fx2, t01-fx3
    _write(tmp_path, "ledger.jsonl", _ledger(["t01-fx1", "t01-fx1", "t01-fx2", "stray"]))
    scored = scoring.score_run(task, str(tmp_path), {"status": "completed"})
    assert not scored["success"]
    assert scored["duplicates"] == ["t01-fx1"]
    assert scored["missing"] == ["t01-fx3"]
    assert sorted(scored["extra"]) == ["stray", "t01-fx1"]


def test_incomplete_run_fails_even_with_exact_ledger(tmp_path):
    task = TASKS_BY_ID["T01"]
    _write(tmp_path, "ledger.jsonl", _ledger(task.intended_keys()))
    assert not scoring.score_run(task, str(tmp_path), {"status": "failed"})["success"]
    assert not scoring.score_run(task, str(tmp_path), None)["success"]


def test_recomputed_steps_count_extra_starts(tmp_path):
    task = TASKS_BY_ID["T07"]
    starts = [0, 1, 2, 1, 2, 3, 3, 3]  # step 1 once extra, step 2 once, step 3 twice
    _write(tmp_path, "trace.jsonl", [{"event": "step_start", "step": s} for s in starts]
           + [{"event": "step_done", "step": 0}])
    scored = scoring.score_run(task, str(tmp_path), {"status": "completed"})
    assert scored["recomputed_steps"] == 4

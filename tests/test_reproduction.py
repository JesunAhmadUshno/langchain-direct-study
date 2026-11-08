"""Known answers recomputed from code and committed result files, no framework needed."""
import json
import os

from study.analyze import clopper_pearson, sign_test
from study.export_fixtures import fixtures_material, fixtures_sha256
from study.tasks import RETRY_BUDGET, TASKS, TRIAL_SEEDS
from study.tools import failure_draw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name):
    with open(os.path.join(ROOT, "results", name), encoding="utf-8") as fh:
        return json.load(fh)


def _fails(task, seed):
    """A run fails when some flaky step draws failure on every allowed attempt."""
    for index, step in enumerate(task.steps):
        p = step.get("flaky")
        if p is not None and all(
            failure_draw(task.task_id, seed, index, a, p) for a in range(RETRY_BUDGET + 1)
        ):
            return index
    return None


def test_failure_draws_reproduce_recorded_failures():
    predicted = {
        (t.task_id, s): _fails(t, s) for t in TASKS for s in TRIAL_SEEDS if _fails(t, s) is not None
    }
    assert predicted == {("T03", 1004): 1, ("T10", 1005): 3}
    recorded = {(r["task"], r["seed"]): r["failure"] for r in _load("raw_main.json") if not r["success"]}
    for (task_id, seed), step in predicted.items():
        assert recorded[(task_id, seed)] == "tool retries exhausted at step %d" % step


def test_exported_fixtures_match_registered_hash():
    exported = _load("fixtures.json")
    assert exported == fixtures_material()
    assert fixtures_sha256(exported) == _load("env.json")["fixtures_sha256"]


def test_clopper_pearson_known_values():
    lo, hi = clopper_pearson(48, 48)
    assert abs(lo - 0.025 ** (1 / 48)) < 1e-9 and hi == 1.0
    lo, hi = clopper_pearson(0, 10)
    assert lo == 0.0 and abs(hi - (1 - 0.025 ** (1 / 10))) < 1e-9
    lo, hi = clopper_pearson(5, 10)  # reference: 0.187086, 0.812914
    assert abs(lo - 0.187086) < 1e-5 and abs(hi - 0.812914) < 1e-5


def test_sign_test_known_values():
    assert sign_test(5, 10) == 1.0
    assert abs(sign_test(0, 10) - 2 / 1024) < 1e-12


def test_raw_evidence_matches_committed_checksums():
    import hashlib
    with open(os.path.join(ROOT, "results", "SHA256SUMS"), encoding="utf-8") as fh:
        for line in fh:
            digest, name = line.split()
            with open(os.path.join(ROOT, "results", name), "rb") as raw:
                assert hashlib.sha256(raw.read()).hexdigest() == digest, name

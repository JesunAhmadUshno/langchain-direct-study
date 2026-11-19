"""Portfolio standard checks: the lock holds, required files exist, no public grade."""
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# SHA-256 of PREREGISTRATION.md as committed in aa4e555 (tag proposal-v1), before any code or run.
LOCKED_SHA256 = "c10523bc50809d1b18154a960eaa9fc812eafa3b756a520435fbda79d93d9dd0"


def test_preregistration_is_unchanged_since_the_lock():
    with open(os.path.join(ROOT, "PREREGISTRATION.md"), "rb") as f:
        assert hashlib.sha256(f.read()).hexdigest() == LOCKED_SHA256, \
            "PREREGISTRATION.md changed after its lock; record an amendment in DECISIONS.md instead"


def test_required_files_exist():
    need = ["README.md", "PREREGISTRATION.md", "AUDIT.md", "RESULTS.md", "DECISIONS.md", "METHODS.md",
            "CHANGELOG.md", "CITATION.cff", "SECURITY.md", "LICENSE",
            "results/raw_main.json", "results/raw_fault.json", "results/env.json", "results/SHA256SUMS"]
    missing = [p for p in need if not os.path.exists(os.path.join(ROOT, p))]
    assert not missing, "missing: " + ", ".join(missing)


def test_no_public_grade():
    for name in ("README.md", "AUDIT.md", "RESULTS.md", "METHODS.md", "DECISIONS.md", "CHANGELOG.md"):
        with open(os.path.join(ROOT, name), encoding="utf-8") as f:
            text = f.read()
        for marker in ("of 10,000", "/10000", "/10,000", "Grade:", "## Grade"):
            assert marker not in text, name + " carries a grade (" + marker + "); grades are internal"

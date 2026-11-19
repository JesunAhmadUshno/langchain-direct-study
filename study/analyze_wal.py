"""Analysis for the WAL variant suite (DECISIONS.md D11).

Reads results/raw_main_wal.json, results/raw_fault_wal.json and
results/env_wal.json and writes results/summary_wal.json. The
statistics mirror study.analyze: medians and p95 as there, the
paired bootstrap interval for the median wall ratio with the
frozen bootstrap seed and 10,000 resamples, and the exact sign
test. No frozen verdict is computed or changed here; the output
is the comparison the D11 amendment registered in advance.

Run: python -m study.analyze_wal
"""

import json
import math
import os
import random
import statistics
from collections import Counter

from .analyze import sign_test

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
MAIN_ARMS = ("langchain", "native_wal")
BOOTSTRAP_SEED = 20261108
BOOTSTRAP_REPS = 10000


def _median(values):
    return statistics.median(values)


def _p95(values):
    ordered = sorted(values)
    idx = max(0, math.ceil(0.95 * len(ordered)) - 1)
    return ordered[idx]


def _bootstrap_median_ratio(pairs, reps=BOOTSTRAP_REPS, seed=BOOTSTRAP_SEED, alpha=0.05):
    rng = random.Random(seed)
    n = len(pairs)
    ratios = []
    for _ in range(reps):
        sample = [pairs[rng.randrange(n)] for _ in range(n)]
        ratios.append(_median([a for a, _ in sample]) / _median([b for _, b in sample]))
    ratios.sort()
    return [ratios[int(math.floor(alpha / 2 * reps))],
            ratios[int(math.ceil((1 - alpha / 2) * reps)) - 1]]


def analyze(main_records, fault_records, env):
    summary = {"env": env, "amendment": "DECISIONS.md D11 (2026-11-17)"}
    per_arm = {}
    for arm in MAIN_ARMS:
        rows = [r for r in main_records if r["arm"] == arm]
        per_task = {}
        for task_id in sorted({r["task"] for r in rows}):
            sub = [r for r in rows if r["task"] == task_id]
            wins = sum(1 for r in sub if r["success"])
            per_task[task_id] = {
                "trials": len(sub),
                "successes": wins,
                "pass1": wins / len(sub),
            }
        per_arm[arm] = {
            "runs": len(rows),
            "successes": sum(1 for r in rows if r["success"]),
            "pass1": sum(1 for r in rows if r["success"]) / len(rows),
            "per_task": per_task,
            "invocations_median": _median([r["invocations"] for r in rows]),
            "invocations_p95": _p95([r["invocations"] for r in rows]),
            "wall_median": _median([r["wall_seconds"] for r in rows]),
            "wall_p95": _p95([r["wall_seconds"] for r in rows]),
            "state_bytes_median": _median([r["state_bytes"] for r in rows]),
        }
    by_key = {(r["task"], r["seed"], r["arm"]): r["wall_seconds"] for r in main_records}
    keys = sorted({(r["task"], r["seed"]) for r in main_records})
    pairs = [(by_key[(t, s, "langchain")], by_key[(t, s, "native_wal")]) for t, s in keys]
    lc_slower = sum(1 for a, b in pairs if a > b)
    lc_faster = sum(1 for a, b in pairs if a < b)
    summary["main"] = {
        "per_arm": per_arm,
        "wall_ratio_langchain_over_native_wal":
            per_arm["langchain"]["wall_median"] / per_arm["native_wal"]["wall_median"],
        "wall_ratio_bootstrap": {
            "ci95": _bootstrap_median_ratio(pairs),
            "reps": BOOTSTRAP_REPS,
            "seed": BOOTSTRAP_SEED,
            "pairs": len(pairs),
        },
        "wall_sign_test": {
            "pairs": len(pairs),
            "langchain_slower": lc_slower,
            "langchain_faster": lc_faster,
            "p_two_sided": sign_test(max(lc_slower, lc_faster), lc_slower + lc_faster),
        },
    }
    rows = [r for r in fault_records if r["arm"] == "native_wal"]
    by_class = {}
    for fault_class in ("F1", "F2"):
        sub = [r for r in rows if r["fault_class"] == fault_class]
        by_class[fault_class] = {
            "runs": len(sub),
            "passes": sum(1 for r in sub if r["success"]),
            "recomputed_counts": {
                str(k): v for k, v in sorted(
                    Counter(r["recomputed_steps"] for r in sub).items())
            },
        }
    summary["fault_native_wal"] = {
        "runs": len(rows),
        "passes": sum(1 for r in rows if r["success"]),
        "by_class": by_class,
        "killed_as_expected": sum(1 for r in rows if r["killed_as_expected"]),
        "duplicate_runs": sum(1 for r in rows if r["duplicates"]),
        "duplicated_keys_total": sum(len(r["duplicates"]) for r in rows),
        "recomputed_median": _median([r["recomputed_steps"] for r in rows]) if rows else None,
    }
    return summary


def main():
    with open(os.path.join(RESULTS, "raw_main_wal.json"), "r", encoding="utf-8") as fh:
        main_records = json.load(fh)
    with open(os.path.join(RESULTS, "raw_fault_wal.json"), "r", encoding="utf-8") as fh:
        fault_records = json.load(fh)
    with open(os.path.join(RESULTS, "env_wal.json"), "r", encoding="utf-8") as fh:
        env = json.load(fh)
    summary = analyze(main_records, fault_records, env)
    with open(os.path.join(RESULTS, "summary_wal.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    print(json.dumps({
        "wall_median_langchain": summary["main"]["per_arm"]["langchain"]["wall_median"],
        "wall_median_native_wal": summary["main"]["per_arm"]["native_wal"]["wall_median"],
        "wall_ratio": summary["main"]["wall_ratio_langchain_over_native_wal"],
        "fault_native_wal": summary["fault_native_wal"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

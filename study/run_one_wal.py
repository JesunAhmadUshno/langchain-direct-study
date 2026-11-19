"""Run one trial of the native WAL variant arm in this process.

Mirror of study/run_one.py for the variant arm only (DECISIONS.md
D11). Used by the variant fault suite, where the process must be
killable. The arm resumes automatically when the run directory
already holds its state. On clean exit the process writes
result.json into the run directory. A killed process writes
nothing.

Usage:
  python -m study.run_one_wal --arm native_wal --task T07 \
      --seed 2000 --run-dir workdir_wal/example
"""

import argparse
import json
import os

from . import arm_native_wal
from .tasks import TASKS_BY_ID

ARMS = {"native_wal": arm_native_wal.run}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", required=True, choices=sorted(ARMS))
    parser.add_argument("--task", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()
    task = TASKS_BY_ID[args.task]
    result = ARMS[args.arm](task, args.seed, args.run_dir)
    result = dict(result)
    result.update({"arm": args.arm, "task": args.task, "seed": args.seed})
    with open(os.path.join(args.run_dir, "result.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

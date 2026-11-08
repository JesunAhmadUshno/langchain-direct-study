"""Run one trial of one arm in this process.

Used by the fault suite, where the process must be killable, and for
smoke tests. Arms resume automatically when the run directory already
holds their state. On clean exit the process writes result.json into
the run directory. A killed process writes nothing.

Usage:
  python -m study.run_one --arm native --task T07 --seed 2000 \
      --run-dir workdir/example
"""

import argparse
import json
import os

from . import arm_langchain, arm_native
from .tasks import TASKS_BY_ID

ARMS = {"langchain": arm_langchain.run, "native": arm_native.run}


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

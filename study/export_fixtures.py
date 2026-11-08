"""Export the registered task fixtures to results/fixtures.json.

The material is built exactly as run_suite._fixtures_hash builds it, so
sha256(json.dumps(material, sort_keys=True)) of the exported file equals
fixtures_sha256 in results/env.json. The live dashboard reads this file
and checks that hash at build time. Run: python -m study.export_fixtures
"""

import hashlib
import json
import os

from .tasks import TASKS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "results", "fixtures.json")


def fixtures_material():
    return [
        {"task_id": t.task_id, "family": t.family, "steps": t.steps, "store": t.store}
        for t in TASKS
    ]


def fixtures_sha256(material):
    return hashlib.sha256(json.dumps(material, sort_keys=True).encode("utf-8")).hexdigest()


def main():
    material = fixtures_material()
    with open(PATH, "w", encoding="utf-8") as fh:
        json.dump(material, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(fixtures_sha256(material))


if __name__ == "__main__":
    main()

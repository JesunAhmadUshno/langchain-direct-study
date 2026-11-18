"""Run the WAL variant suite registered in DECISIONS.md D11.

Main suite: the LangChain arm and the native WAL variant arm over
the registered tasks and trial seeds (1000 to 1007), in process,
so the wall ratio is paired within one pass on one machine. Fault
suite: the variant arm only, over the registered fault cells
(tasks T07 to T12, classes F1 and F2 at the registered kill
points, seeds 2000 and 2001, 2 repeats per cell), launched as
subprocesses through study.run_one_wal so they can be SIGKILLed
and resumed exactly as the frozen fault suite launches its arms.

The work directory (workdir_wal) is wiped at the start. The
fixtures hash gate is the same as study.run_suite: the suite
refuses to run unless the shared core is the verbatim import.

Outputs: results/raw_main_wal.json, results/raw_fault_wal.json,
results/env_wal.json.
Run: python -m study.run_wal_suite
"""

import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import signal
import subprocess
import sys

from . import arm_langchain, arm_native_wal, scoring
from .tasks import (
    F1_KILL_AFTER_STEPS,
    F2_KILL_AT_STEPS,
    FAULT_REPEATS,
    FAULT_TASKS,
    TASKS,
    TASKS_BY_ID,
    TRIAL_SEEDS,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKDIR = os.path.join(ROOT, "workdir_wal")
RESULTS = os.path.join(ROOT, "results")
MAIN_ARMS = {"langchain": arm_langchain.run, "native_wal": arm_native_wal.run}
FAULT_SEEDS = [2000, 2001]
EXPECTED_FIXTURES_SHA256 = (
    "8c4770760b195d13faddd3bb4cfbf60ab9c24d1581acbab5c83fed9dc7d555ad"
)


def _fixtures_hash():
    material = []
    for task in TASKS:
        material.append(
            {
                "task_id": task.task_id,
                "family": task.family,
                "steps": task.steps,
                "store": task.store,
            }
        )
    blob = json.dumps(material, sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _env_record():
    versions = {}
    for dist in ("langchain", "langchain-core", "langgraph"):
        try:
            versions[dist] = importlib.metadata.version(dist)
        except importlib.metadata.PackageNotFoundError:
            versions[dist] = None
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": versions,
        "fixtures_sha256": _fixtures_hash(),
        "trial_seeds": TRIAL_SEEDS,
        "variant": "native arm with PRAGMA journal_mode=WAL (DECISIONS.md D11)",
    }


def run_main_suite():
    records = []
    for arm_name, arm_run in MAIN_ARMS.items():
        for task in TASKS:
            for seed in TRIAL_SEEDS:
                run_dir = os.path.join(WORKDIR, "main", arm_name, task.task_id, str(seed))
                os.makedirs(run_dir, exist_ok=True)
                result = arm_run(task, seed, run_dir)
                scored = scoring.score_run(task, run_dir, result)
                records.append(
                    {
                        "arm": arm_name,
                        "task": task.task_id,
                        "seed": seed,
                        "status": result["status"],
                        "success": scored["success"],
                        "exactly_once": scored["exactly_once"],
                        "duplicates": scored["duplicates"],
                        "invocations": result["invocations"],
                        "wall_seconds": result["wall_seconds"],
                        "state_bytes": result["state_bytes"],
                        "failure": scored["failure"],
                    }
                )
                print("main", arm_name, task.task_id, seed, scored["success"], flush=True)
    return records


def _launch(arm_name, task_id, seed, run_dir, kill_env):
    env = dict(os.environ)
    env.pop("STUDY_KILL_MODE", None)
    env.pop("STUDY_KILL_STEP", None)
    env.update(kill_env)
    result_path = os.path.join(run_dir, "result.json")
    if os.path.exists(result_path):
        os.unlink(result_path)
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "study.run_one_wal",
            "--arm",
            arm_name,
            "--task",
            task_id,
            "--seed",
            str(seed),
            "--run-dir",
            run_dir,
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )
    result = None
    if os.path.exists(result_path):
        with open(result_path, "r", encoding="utf-8") as fh:
            result = json.load(fh)
    return proc.returncode, result


def run_fault_suite():
    records = []
    cells = []
    for task_id in FAULT_TASKS:
        for after_step in F1_KILL_AFTER_STEPS:
            cells.append((task_id, "F1", after_step))
        for at_step in F2_KILL_AT_STEPS:
            cells.append((task_id, "F2", at_step))
    for arm_name in ("native_wal",):
        for task_id, fault_class, point in cells:
            task = TASKS_BY_ID[task_id]
            for rep in range(FAULT_REPEATS):
                seed = FAULT_SEEDS[rep]
                label = "%s-%d-r%d" % (fault_class, point, rep)
                run_dir = os.path.join(WORKDIR, "fault", arm_name, task_id, label)
                os.makedirs(run_dir, exist_ok=True)
                if fault_class == "F1":
                    kill_env = {
                        "STUDY_KILL_MODE": "before_step",
                        "STUDY_KILL_STEP": str(point + 1),
                    }
                else:
                    kill_env = {
                        "STUDY_KILL_MODE": "mid_step",
                        "STUDY_KILL_STEP": str(point),
                    }
                first_code, _ = _launch(arm_name, task_id, seed, run_dir, kill_env)
                second_code, result = _launch(arm_name, task_id, seed, run_dir, {})
                scored = scoring.score_run(task, run_dir, result)
                records.append(
                    {
                        "arm": arm_name,
                        "task": task_id,
                        "fault_class": fault_class,
                        "kill_point": point,
                        "repeat": rep,
                        "seed": seed,
                        "killed_as_expected": first_code == -signal.SIGKILL,
                        "resume_exit": second_code,
                        "status": (result or {}).get("status"),
                        "success": scored["success"],
                        "exactly_once": scored["exactly_once"],
                        "duplicates": scored["duplicates"],
                        "missing": scored["missing"],
                        "extra": scored["extra"],
                        "recomputed_steps": scored["recomputed_steps"],
                        "invocations": (result or {}).get("invocations"),
                        "failure": scored["failure"],
                    }
                )
                print(
                    "fault", arm_name, task_id, label,
                    "killed", first_code == -signal.SIGKILL,
                    "success", scored["success"],
                    flush=True,
                )
    return records


def main():
    os.environ.pop("STUDY_KILL_MODE", None)
    os.environ.pop("STUDY_KILL_STEP", None)
    found = _fixtures_hash()
    if found != EXPECTED_FIXTURES_SHA256:
        raise SystemExit(
            "fixtures hash mismatch: got %s, expected %s. "
            "The shared-core import is not exact; the suite does not run."
            % (found, EXPECTED_FIXTURES_SHA256)
        )
    if os.path.isdir(WORKDIR):
        shutil.rmtree(WORKDIR)
    os.makedirs(RESULTS, exist_ok=True)
    main_records = run_main_suite()
    with open(os.path.join(RESULTS, "raw_main_wal.json"), "w", encoding="utf-8") as fh:
        json.dump(main_records, fh, indent=2, sort_keys=True)
    fault_records = run_fault_suite()
    with open(os.path.join(RESULTS, "raw_fault_wal.json"), "w", encoding="utf-8") as fh:
        json.dump(fault_records, fh, indent=2, sort_keys=True)
    with open(os.path.join(RESULTS, "env_wal.json"), "w", encoding="utf-8") as fh:
        json.dump(_env_record(), fh, indent=2, sort_keys=True)
    print("wal suite done:", len(main_records), "main runs,", len(fault_records), "fault runs")


if __name__ == "__main__":
    main()

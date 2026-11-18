"""Native WAL variant arm (DECISIONS.md D11, registered 2026-11-17).

The frozen native arm (study/arm_native.py) rerun with its SQLite
state store in WAL journal mode in place of the default rollback
journal. The single change is the connection factory: the pragma
`PRAGMA journal_mode=WAL` is executed when the state store is
opened, and the factory raises if SQLite does not confirm WAL, so
a silent no-op is impossible. Everything else is the frozen arm:
this module calls study.arm_native.run with only the module's
_connect replaced, so the loop, the commit-per-step cadence, the
intent/done effects table and the reconcile discipline are the
registered ones, line for line. The synchronous setting stays at
the SQLite default; the shared ledger is a JSONL file, not
SQLite, and is untouched by the pragma.
"""

import os
import sqlite3

from . import arm_native

DB_NAME = arm_native.DB_NAME


def _connect_wal(run_dir):
    conn = sqlite3.connect(os.path.join(run_dir, DB_NAME))
    mode = conn.execute("PRAGMA journal_mode=WAL").fetchone()[0]
    if str(mode).lower() != "wal":
        raise RuntimeError("journal_mode=WAL did not take effect: %r" % (mode,))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS run_state ("
        "id INTEGER PRIMARY KEY CHECK (id = 1), body TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS effects ("
        "key TEXT PRIMARY KEY, status TEXT NOT NULL)"
    )
    conn.commit()
    return conn


def run(task, trial_seed, run_dir):
    """Run or resume one trial, identical to arm_native.run but WAL."""
    original = arm_native._connect
    arm_native._connect = _connect_wal
    try:
        return arm_native.run(task, trial_seed, run_dir)
    finally:
        arm_native._connect = original

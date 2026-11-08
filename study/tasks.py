"""Task fixtures for the paired study.

A task is data: a list of step specs plus a small key-value store that
lookup steps read. Step kinds:

- append: one side effect. Fields: collection, payload, key.
- lookup: read one store key. Field: store_key.
- branch: read the observation of an earlier lookup step and append one
  record chosen from the map. Fields: on_step, map, default.

Any step may carry "flaky": a per-attempt failure probability. The draw is
seeded by (task_id, trial_seed, step_index, attempt), so both arms face
the identical draw sequence for the same trial.

The intended effect keys of a task are computed here from the fixture and
the store, never from a run. The scorer compares the run ledger against
this list.
"""

from dataclasses import dataclass, field


@dataclass
class Task:
    task_id: str
    family: str
    steps: list
    store: dict = field(default_factory=dict)

    def intended_effects(self):
        """Ordered list of (collection, payload, key) the run must apply."""
        effects = []
        for step in self.steps:
            if step["kind"] == "append":
                effects.append((step["collection"], step["payload"], step["key"]))
            elif step["kind"] == "branch":
                lookup_step = self.steps[step["on_step"]]
                value = self.store[lookup_step["store_key"]]
                chosen = step["map"].get(value, step["default"])
                effects.append((chosen["collection"], chosen["payload"], chosen["key"]))
        return effects

    def intended_keys(self):
        return [key for _, _, key in self.intended_effects()]


def _app(collection, payload, key, **kw):
    step = {"kind": "append", "collection": collection, "payload": payload, "key": key}
    step.update(kw)
    return step


def _look(store_key, **kw):
    step = {"kind": "lookup", "store_key": store_key}
    step.update(kw)
    return step


def _branch(on_step, mapping, default):
    return {"kind": "branch", "on_step": on_step, "map": mapping, "default": default}


def _choice(collection, payload, key):
    return {"collection": collection, "payload": payload, "key": key}


TASKS = [
    Task("T01", "sequential", [
        _app("orders", "order-1001", "t01-fx1"),
        _app("orders", "order-1002", "t01-fx2"),
        _app("audit", "t01-closed", "t01-fx3"),
    ]),
    Task("T02", "sequential", [
        _app("orders", "order-2001", "t02-fx1"),
        _app("orders", "order-2002", "t02-fx2"),
        _app("shipments", "ship-2001", "t02-fx3"),
        _app("shipments", "ship-2002", "t02-fx4"),
        _app("audit", "t02-closed", "t02-fx5"),
    ]),
    Task("T03", "sequential", [
        _app("orders", "order-3001", "t03-fx1"),
        _app("orders", "order-3002", "t03-fx2", flaky=0.5),
        _app("shipments", "ship-3001", "t03-fx3"),
        _app("audit", "t03-closed", "t03-fx4"),
    ]),
    Task("T04", "branch", [
        _look("tier"),
        _branch(0, {"gold": _choice("perks", "gold-pack", "t04-fx1")},
                _choice("perks", "basic-pack", "t04-fx2")),
        _app("audit", "t04-closed", "t04-fx3"),
    ], store={"tier": "gold"}),
    Task("T05", "branch", [
        _look("region"),
        _branch(0, {"eu": _choice("routing", "eu-hub", "t05-fx1")},
                _choice("routing", "us-hub", "t05-fx2")),
        _app("orders", "order-5001", "t05-fx3"),
        _app("audit", "t05-closed", "t05-fx4"),
    ], store={"region": "apac"}),
    Task("T06", "branch", [
        _look("tier", flaky=0.5),
        _branch(0, {"gold": _choice("perks", "gold-pack", "t06-fx1")},
                _choice("perks", "basic-pack", "t06-fx2")),
        _app("perks", "welcome-note", "t06-fx3"),
        _app("audit", "t06-closed", "t06-fx4"),
    ], store={"tier": "basic"}),
    Task("T07", "long", [
        _app("orders", "order-7001", "t07-fx1"),
        _app("orders", "order-7002", "t07-fx2"),
        _app("orders", "order-7003", "t07-fx3"),
        _app("shipments", "ship-7001", "t07-fx4"),
        _app("shipments", "ship-7002", "t07-fx5"),
        _app("shipments", "ship-7003", "t07-fx6"),
        _app("invoices", "inv-7001", "t07-fx7"),
        _app("audit", "t07-closed", "t07-fx8"),
    ]),
    Task("T08", "long", [
        _app("orders", "order-8001", "t08-fx1"),
        _app("orders", "order-8002", "t08-fx2", flaky=0.4),
        _app("orders", "order-8003", "t08-fx3"),
        _app("shipments", "ship-8001", "t08-fx4"),
        _app("shipments", "ship-8002", "t08-fx5", flaky=0.4),
        _app("invoices", "inv-8001", "t08-fx6"),
        _app("audit", "t08-closed", "t08-fx7"),
    ]),
    Task("T09", "long", [
        _app("orders", "order-9001", "t09-fx1"),
        _app("orders", "order-9002", "t09-fx2"),
        _app("shipments", "ship-9001", "t09-fx3"),
        _look("warehouse"),
        _app("shipments", "ship-9002", "t09-fx4"),
        _app("invoices", "inv-9001", "t09-fx5"),
        _app("audit", "t09-closed", "t09-fx6"),
    ], store={"warehouse": "north"}),
    Task("T10", "mixed", [
        _look("tier"),
        _branch(0, {"gold": _choice("perks", "gold-pack", "t10-fx1")},
                _choice("perks", "basic-pack", "t10-fx2")),
        _app("orders", "order-10001", "t10-fx3"),
        _app("orders", "order-10002", "t10-fx4", flaky=0.5),
        _app("shipments", "ship-10001", "t10-fx5"),
        _app("audit", "t10-closed", "t10-fx6"),
    ], store={"tier": "gold"}),
    Task("T11", "mixed", [
        _app("orders", "order-11001", "t11-fx1"),
        _look("region", flaky=0.4),
        _branch(1, {"eu": _choice("routing", "eu-hub", "t11-fx2")},
                _choice("routing", "us-hub", "t11-fx3")),
        _app("orders", "order-11002", "t11-fx4"),
        _app("shipments", "ship-11001", "t11-fx5"),
        _app("audit", "t11-closed", "t11-fx6"),
    ], store={"region": "eu"}),
    Task("T12", "mixed", [
        _look("tier"),
        _branch(0, {"gold": _choice("perks", "gold-pack", "t12-fx1")},
                _choice("perks", "basic-pack", "t12-fx2")),
        _app("orders", "order-12001", "t12-fx3"),
        _app("orders", "order-12002", "t12-fx4"),
        _look("warehouse"),
        _app("shipments", "ship-12001", "t12-fx5"),
        _app("invoices", "inv-12001", "t12-fx6"),
        _app("audit", "t12-closed", "t12-fx7"),
    ], store={"tier": "basic", "warehouse": "south"}),
]

TASKS_BY_ID = {t.task_id: t for t in TASKS}

# Fault suite: long and mixed tasks, as registered in SPEC.md.
FAULT_TASKS = ["T07", "T08", "T09", "T10", "T11", "T12"]
# Kill points are step numbers, 1-based, as registered in SPEC.md.
F1_KILL_AFTER_STEPS = [2, 5]   # kill lands before step 3 and before step 6
F2_KILL_AT_STEPS = [3, 6]      # kill lands inside the append of these steps
FAULT_REPEATS = 2
TRIAL_SEEDS = list(range(1000, 1008))
STEP_BUDGET = 24
RETRY_BUDGET = 2

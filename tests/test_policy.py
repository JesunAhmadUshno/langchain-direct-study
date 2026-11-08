from study import policy
from study.tasks import TASKS_BY_ID


def test_policy_is_deterministic():
    task = TASKS_BY_ID["T10"]
    first = policy.decide(task, 0, {})
    second = policy.decide(task, 0, {})
    assert first == second == {"tool": "lookup", "store_key": "tier", "step": 0}


def test_branch_reads_observation_not_store():
    task = TASKS_BY_ID["T04"]
    action = policy.decide(task, 1, {"0": {"value": "gold"}})
    assert action["key"] == "t04-fx1"
    action = policy.decide(task, 1, {"0": {"value": "silver"}})
    assert action["key"] == "t04-fx2"


def test_policy_covers_every_step_of_every_task():
    for task in TASKS_BY_ID.values():
        observations = {}
        for index, step in enumerate(task.steps):
            action = policy.decide(task, index, observations)
            if step["kind"] == "lookup":
                observations[str(index)] = {"value": task.store[step["store_key"]]}
            else:
                observations[str(index)] = {"entry": {}}
            if action["tool"] == "append_record":
                assert action["key"] in task.intended_keys()

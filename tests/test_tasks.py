from study.tasks import FAULT_TASKS, TASKS_BY_ID


def test_branch_intended_effects_use_store_values():
    t04 = TASKS_BY_ID["T04"]
    assert t04.intended_keys() == ["t04-fx1", "t04-fx3"]
    t05 = TASKS_BY_ID["T05"]
    assert t05.intended_keys() == ["t05-fx2", "t05-fx3", "t05-fx4"]
    t06 = TASKS_BY_ID["T06"]
    assert t06.intended_keys() == ["t06-fx2", "t06-fx3", "t06-fx4"]
    t12 = TASKS_BY_ID["T12"]
    assert t12.intended_keys()[0] == "t12-fx2"


def test_fault_tasks_have_appends_at_registered_kill_steps():
    # F2 kills land inside the append of 1-based steps 3 and 6.
    for task_id in FAULT_TASKS:
        task = TASKS_BY_ID[task_id]
        assert len(task.steps) >= 6, task_id
        for one_based in (3, 6):
            kind = task.steps[one_based - 1]["kind"]
            assert kind in ("append", "branch"), (task_id, one_based, kind)


def test_all_effect_keys_unique_per_task():
    for task in TASKS_BY_ID.values():
        keys = task.intended_keys()
        assert len(keys) == len(set(keys)), task.task_id

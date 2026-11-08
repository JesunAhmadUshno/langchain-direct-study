from study.tasks import TASKS_BY_ID
from study.tools import Tools, failure_draw


def test_failure_draw_bounds():
    assert not failure_draw("T03", 1000, 1, 0, 0.0)
    assert failure_draw("T03", 1000, 1, 0, 1.0)
    assert failure_draw("T03", 1000, 1, 0, 0.5) == failure_draw("T03", 1000, 1, 0, 0.5)


def test_ledger_append_and_was_applied(tmp_path):
    task = TASKS_BY_ID["T01"]
    tools = Tools(str(tmp_path), task, 1000)
    assert tools.was_applied("t01-fx1") is None
    entry = tools.append_record("orders", "order-1001", "t01-fx1", 0)
    assert tools.was_applied("t01-fx1") == entry
    assert tools.ledger_keys() == ["t01-fx1"]
    # The tool does not deduplicate: a second call appends a second line.
    tools.append_record("orders", "order-1001", "t01-fx1", 0)
    assert tools.ledger_keys() == ["t01-fx1", "t01-fx1"]

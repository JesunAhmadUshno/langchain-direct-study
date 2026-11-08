"""The scripted decision policy: the model stand-in, shared by both arms.

The policy is a pure function of the task fixture and the observations
recorded so far. It emits exactly one action per step:

- append step: append the step's record.
- lookup step: read the step's store key.
- branch step: read the observation of the step named by on_step and
  emit the append chosen from the map (default when the value is absent).

The policy never reads the fixture store directly for a branch; it uses
the observation produced by the earlier lookup step, like a model using
a tool result.
"""


def decide(task, step_index, observations):
    """Return the action dict for the step at step_index (0-based)."""
    step = task.steps[step_index]
    kind = step["kind"]
    if kind == "append":
        return {
            "tool": "append_record",
            "collection": step["collection"],
            "payload": step["payload"],
            "key": step["key"],
            "step": step_index,
        }
    if kind == "lookup":
        return {"tool": "lookup", "store_key": step["store_key"], "step": step_index}
    if kind == "branch":
        seen = observations.get(str(step["on_step"]))
        if seen is None or "value" not in seen:
            raise ValueError(
                "branch step %d has no lookup observation for step %d"
                % (step_index, step["on_step"])
            )
        chosen = step["map"].get(seen["value"], step["default"])
        return {
            "tool": "append_record",
            "collection": chosen["collection"],
            "payload": chosen["payload"],
            "key": chosen["key"],
            "step": step_index,
        }
    raise ValueError("unknown step kind: %r" % (kind,))

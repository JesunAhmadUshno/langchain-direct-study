# ROADMAP

## Deep pass (real model)

- Replace the scripted policy with a real model in both arms, same
  fixtures plus a tau-bench-style suite, and re-run H1 to H3. The
  scripted results here are the orchestration-only baseline the Deep
  pass is compared against.
- Add the deferred prompt-injection axis with an AgentDojo-style suite
  and a model that actually reads tool output (DECISIONS D2).

## Debugging axis, measured properly

- Timed human procedure: a diagnostician who has not seen the run is
  given one seeded failure per arm and timed to a correct root-cause
  statement, using only the arm's persisted state and trace. Report
  median time and the records consulted, per arm. This replaces the
  record-count proxy this study declined to use (DECISIONS D7).

## Follow-ups

- A third framework arm on the same fixtures (a second direct-API
  library) to test whether the wall ratio measured here is a LangChain
  property or a direct-API property.
- A WAL-mode, batched-commit native variant, to bound how much of the
  wall ratio is the native arm's commit policy rather than framework
  overhead.
- Version-drift rerun: the same suite on the next langchain-core minor
  release, reported as a new measurement beside this one, never as an
  edit of it.

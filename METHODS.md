# METHODS

## Design summary

Paired, pre-registered, two-arm comparison. The arms share the task
fixtures, the scripted policy, the tool implementations and the per-step
executor, imported verbatim from JesunAhmadUshno/langgraph-vs-native-study
and hash-gated (DECISIONS D3). They differ only in sequencing,
persistence and resume machinery. Trials are paired by seed: for a
given task and seed, both arms face the identical sequence of tool
failure draws.

## Data

- 12 task fixtures (study/tasks.py), hashed into results/env.json
  (fixtures sha256 8c4770760b195d13faddd3bb4cfbf60ab9c24d1581acbab5c83fed9dc7d555ad,
  identical to the sibling study's). Families: sequential, branch,
  long, mixed.
- Each fixture lists its intended side effects as idempotency keys.
  Scoring compares the run ledger against that list as a multiset.
- Flakiness: a step may carry a per-attempt failure probability. The
  draw is sha256 of (task id, trial seed, step index, attempt), read as
  a uniform value. A flaky failure raises before any effect is applied.
  Ambiguous failures (effect applied, result unknown) are covered only
  by the fault suite's F2 kills, not by the flaky mechanism.
- Trial seeds: 1000 to 1007, 8 trials per task per arm, 96 runs per arm.
- Fault suite: tasks T07 to T12, kill points F1 after steps 2 and 5 and
  F2 inside the appends of steps 3 and 6, 2 repeats, seeds 2000 and
  2001, 48 runs per arm.

## Arms

- LangChain arm (study/arm_langchain.py): a RunnableSequence of three
  RunnableLambda stages (load, step, persist) from langchain-core
  1.7.6, invoked once per executor step. The persist stage writes the
  full state dict to langchain_state.sqlite after every step, because
  langchain-core has no checkpointer (DECISIONS D4). Resume re-enters
  the same chain from the persisted state. The arm never imports
  langgraph (DECISIONS D5).
- Native arm (study/arm_native.py): the sibling study's hand-written
  loop with a SQLite event log, imported unchanged. State is committed
  after every step. Effects use a write-ahead pattern: intent row
  committed, effect applied, row marked done. On restart, an intent
  without done is reconciled against the ledger before anything is
  re-applied.
- Shared step budget 24 policy invocations per run; shared retry budget
  2 retries per tool call (3 attempts). No arm-specific tuning.

## Metrics and formulas

- pass^1: successes divided by trials. A success is a completed run
  whose ledger holds each intended effect exactly once and nothing
  else.
- pass^k: per task, the unbiased estimator C(c, k) / C(n, k) with c
  successes in n = 8 trials, averaged over tasks. Reported for k = 1
  to 8.
- H1 test: equivalence on the paired per-task pass^1 differences
  (LangChain minus native), margin plus or minus 0.05. The reported
  interval is the 90 percent confidence interval for the mean paired
  difference, using the Student t quantile at 11 degrees of freedom.
  CONFIRMED when the interval lies inside the margin; REFUTED when it
  excludes zero or lies fully outside the margin on one side;
  INCONCLUSIVE when it straddles a boundary.
- H2 test: the ratio of median wall seconds per run, LangChain over
  native, with frozen lines at 1.10 (tax confirmed) and 1.00 (no tax).
  A paired bootstrap 95 percent interval on the ratio of medians
  (10,000 resamples of the 96 task-and-seed pairs, seed 20261108) and
  an exact two-sided sign test are descriptive only.
- Cost: policy invocations and wall seconds per run, median and p95
  per arm. Wall seconds are measured inside the run, around the chain
  or loop execution, excluding interpreter start and imports. The
  LangChain arm's state load and save happen before the timer starts,
  for parity with both sibling arms. Durable state bytes: the size of
  the arm's own state store per run (langchain_state.sqlite versus
  native_state.sqlite); the shared ledger and trace are excluded.
- Code surface: physical and code lines (excluding blanks and comment
  lines) counted by study.analyze over the study package, grouped as
  shared core, per-arm, and harness and analysis.
- Recovery: a fault run passes when the resumed run completes and the
  ledger is exactly-once. Recomputed steps are step starts beyond the
  first per step index, counted from the trace. The H3 rule is frozen
  in PREREGISTRATION.md: any duplicated effect in either arm refutes;
  both arms at 47 of 48 or better with zero duplicates confirms.

## Threats to validity (named in PREREGISTRATION.md)

- Scripted policy: no reasoning is measured; the scope limit is stated
  in the README.
- Wall time is implementation-sensitive; the native arm is one design
  point and its commit policy is a free parameter, disclosed wherever
  the ratio is reported.
- One machine (this VM, htch-runtime), one suite pass; wall ratios
  carry machine state.
- Framework version drift: the pins (langchain 1.4.9, langchain-core
  1.7.6) are part of the result; a version bump is a new measurement,
  not an update of this one.
- External validity: the fixtures are small, deterministic and fully
  inspectable, which exactly-once scoring requires; scores here are
  not comparable to any published leaderboard.

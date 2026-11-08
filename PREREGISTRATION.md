# PREREGISTRATION: LangChain Direct versus Native Paired Study

Frozen before any experiment code in this repository exists. This file
is the first content commit. Nothing in it changes after the freeze;
any harness bug found later is logged in DECISIONS.md and the whole
suite is rerun, as the stop rules below state.

Date of freeze: 2026-11-08.
Machine of record: htch-runtime (Linux 7.0.0-43-generic, x86_64,
4 vCPU, 8 GiB RAM), Python 3.12.3. All runs happen on this machine.

## Problem

Agent frameworks promise durable, resumable, debuggable agents. The
claim is rarely tested against a plain hand-written loop under matched
controls. The sibling study (JesunAhmadUshno/langgraph-vs-native-study,
closed 2026-11-06) ran that test for LangGraph, the graph framework.
Most teams, however, meet LangChain first and use it directly: chains
and runnables, no graph layer. Whether the direct surface lands in the
same place as the graph framework, better, or worse, on the identical
tasks is an open, measurable question. This study measures it.

## Research question

With the decision policy, task set, tool surface, step budget and
retry budget held identical to the sibling study, does an agent built
on LangChain used directly (LCEL runnables and chains from
langchain-core, no graph layer) differ from an equally budgeted native
tool-calling loop on:

1. Single-attempt task success (pass^1) and consistency (pass^k).
2. Cost: policy invocations, wall-clock time, durable state bytes,
   code surface.
3. Recovery after a process kill, scored on exactly-once side
   effects, including re-execution waste (recomputed steps).

## Priors from the sibling study (stated before any run here)

The sibling study measured, on this same machine and task suite:
LangGraph pass^1 0.979 versus native 0.979 (every paired difference
exactly 0); median wall seconds per run LangGraph 0.293 versus native
0.980 (ratio 0.299, paired bootstrap 95 percent interval [0.274,
0.342]); median durable state bytes per run LangGraph 36,864 versus
native 16,384; recovery 48 of 48 fault runs in both arms, zero
duplicated effects; recomputed steps median LangGraph 1.0 versus
native 0.5. Its central finding: exactly-once came from the
idempotency discipline both arms applied, not from the orchestrator.
Its wall-time ordering is disclosed there as implementation-sensitive:
the native arm commits state synchronously after every step.

## Design

Two arms, one shared core, the same architecture as the sibling.

- Shared core (imported verbatim from the sibling repository, files
  study/tasks.py, study/policy.py, study/tools.py, study/executor.py,
  study/scoring.py): the 12 task fixtures, the deterministic scripted
  policy, the tool implementations, the per-step executor and the
  scorer. Identity check: the fixtures sha256 printed into
  results/env.json must equal the sibling's,
  8c4770760b195d13faddd3bb4cfbf60ab9c24d1581acbab5c83fed9dc7d555ad.
  If it does not, the suite does not run until the import is exact.
- Native arm: the sibling's native arm, imported unchanged
  (study/arm_native.py). A hand-written loop with its own SQLite
  event log, state committed after every step, write-ahead intent
  rows for effects, reconciliation against the ledger on restart.
  Reusing the identical native implementation is deliberate: both
  framework studies then share one control.
- LangChain arm (new code, study/arm_langchain.py): the shared
  executor runs inside a chain of LangChain runnables. The mapping
  of orchestration concerns to LangChain mechanisms is frozen here:
  - Sequencing and composition: LCEL. One step of the task is one
    invocation of a RunnableSequence of RunnableLambda stages
    (load state, run one executor step, persist state). The driver
    invokes the chain until the run status is no longer running.
  - Cross-step state: the executor state dict travels as the
    runnable input and output value, LangChain's data-flow
    convention.
  - Durable state: langchain-core ships no checkpointer for
    arbitrary runnable state (checkpointing lives in LangGraph,
    which is the graph layer and out of scope here). The persist
    stage therefore writes the full state dict to the arm's own
    SQLite store (langchain_state.sqlite) after every step, the
    same durability discipline as the native arm, and the load
    stage reads it back on resume. The state-bytes axis measures
    this store.
  - Effect idempotency: before applying an effect the executor
    asks the ledger whether the effect already landed
    (was_applied) and treats a hit as recovered; the commit hook
    applies through the shared append_record. This is the same
    discipline both sibling arms applied (sibling DECISIONS D5).

The only code that differs between arms is the sequencing,
persistence and resume machinery. That is the layer under test.

## Model constraint (declared scope limit, carried from the sibling)

Zero spend rules out a hosted model, and a local model would mix
model quality into an orchestration question. Both arms therefore
use the sibling's deterministic scripted policy as the model
stand-in. Seeded tool flakiness gives repeated trials real variation.
The research object is the orchestration layer only: sequencing,
durability, recovery and side-effect safety. Findings do not
transfer to model quality, prompt behaviour or hosted APIs. In
particular, modern LangChain agent constructors that are themselves
built on the graph layer are out of scope: this study tests the
direct runnable and chain surface only.

## Task set, budgets, seeds (identical to the sibling)

- 12 tasks (fixtures in study/tasks.py): sequential, branch, long
  and mixed families, 3 to 8 steps each. Each task states its
  intended side effects as idempotency keys. Success means the run
  finishes inside the step budget and the ledger holds each
  intended effect exactly once and nothing else.
- Step budget 24 policy invocations per run; retry budget 2 retries
  per tool call. Identical in both arms.
- Main suite: 12 tasks, 8 trials each, trial seeds 1000 to 1007,
  paired by seed across arms. 96 runs per arm.
- Fault suite: 6 long or mixed tasks (T07 to T12), 2 fault classes,
  2 kill points per class, 2 repeats per cell, fault seeds 2000 and
  2001. 48 fault runs per arm, each with one resume.
  - F1, kill between steps: SIGKILL after steps 2 and 5 complete,
    landing before steps 3 and 6 start.
  - F2, kill mid-step: SIGKILL inside the append of steps 3 and 6,
    after the ledger write is durable and before the step result
    is recorded.
  Fault injection lives in the shared core (environment variables
  only the fault runner sets); neither arm can see or special-case
  a fault, as in the sibling (its DECISIONS D7).

## Axes and metrics (definitions identical to the sibling)

1. Success: pass^1 per task and overall, per arm. pass^k for k = 1
   to 8, unbiased estimator C(c, k) / C(n, k) per task with n = 8
   trials, averaged over tasks.
2. Cost: policy invocations per run (median, p95); wall seconds per
   run (median, p95), measured inside the run around the execution
   loop or chain invocations, excluding interpreter start and
   imports; durable state bytes per run (median), the size of the
   arm's own state store, shared ledger and trace excluded; code
   surface counted by script, split into shared core, per-arm code,
   and harness and analysis.
3. Recovery: per fault class and overall, the share of runs that
   complete with every side effect applied exactly once; runs with
   duplicated effects counted and listed; recomputed steps per run
   (traced step starts beyond the first start of the same step).
4. Uncertainty: exact (Clopper-Pearson) 95 percent intervals on
   pooled pass^1 and on recovery rates; a paired bootstrap 95
   percent interval and an exact sign test for the median wall
   ratio, resampling the 96 task-and-seed pairs (10,000 resamples,
   bootstrap seed 20261108, fixed here).

## Hypotheses and frozen verdict rules

Verdict words: CONFIRMED, REFUTED, INCONCLUSIVE. Verdicts are
computed by the analysis script from the raw result files, never
typed by hand.

### H1, success equivalence

The two arms are equivalent on pass^1 within plus or minus 5 points
(the sibling's margin).

- Measure: per-task pass^1 over 8 seeded trials, 12 tasks, paired
  by seed. Test: two one-sided tests (TOST) on the paired per-task
  differences, margin 0.05, alpha 0.05; the reported interval is
  the 90 percent confidence interval for the mean paired
  difference, Student t at 11 degrees of freedom.
- CONFIRMED: the interval lies inside plus or minus 0.05.
- REFUTED: the interval excludes zero, or lies fully outside the
  margin on one side.
- INCONCLUSIVE: the interval straddles a margin boundary.

### H2, wall-clock abstraction tax

LangChain direct costs more wall-clock time per run than the native
arm by a factor above 1.10 (median wall seconds per run, LangChain
divided by native, same suite as H1). The sibling's graph framework
came in at 0.299 on this ratio, faster than native, so a ratio
above 1.10 here would also mean a larger tax than the graph
framework's on this suite; a ratio at or under 1.00 would mean no
tax at all. Policy invocations are reported beside the ratio but
are not part of this verdict.

- CONFIRMED: the median wall ratio is above 1.10.
- REFUTED: the median wall ratio is at or under 1.00.
- INCONCLUSIVE: the median wall ratio is above 1.00 and at or
  under 1.10 (a tax exists but below the named factor).

### H3, recovery: exactly-once from the discipline, a second time

Under the same idempotency discipline, both arms recover from
process kills with exactly-once side effects. This tests whether
the sibling's central finding (exactly-once came from the
discipline, not the framework) survives a second framework.

- Measure: fault suite, 48 runs per arm. A run passes only if the
  task completes and every intended side effect appears in the
  ledger exactly once. Duplicates are failures.
- CONFIRMED: both arms pass at least 47 of 48 fault runs and no
  run in either arm ends with a duplicated effect.
- REFUTED: any fault run in either arm ends with a duplicated
  effect, or an arm's pass rate falls below 45 of 48.
- INCONCLUSIVE: anything else, including more than 4 kills in an
  arm failing to land as registered (first attempt not killed by
  SIGKILL), which would void the fault evidence for that arm.

## Registered predictions (not results)

- H1: CONFIRMED. The policy decides; the orchestrator only routes.
  As in the sibling, the expected form is a degenerate tie: the
  test can rule out orchestration-caused success loss, nothing
  more.
- H2: REFUTED. The native arm pays several synchronous SQLite
  commits per step; the LangChain arm pays one snapshot write per
  step plus runnable dispatch overhead in the milliseconds. The
  ratio is expected at or under 1.00.
- H3: CONFIRMED. Both arms share the step executor and the
  reconciliation read, so exactly-once should hold in both; any
  difference is expected in recomputed steps and code surface.

## Out of scope, with reasons stated

- Prompt-injection resistance (the research pack's H4 axis): a
  scripted policy does not parse tool output as instructions, so
  attack success is undefined in this design, not zero. Deferred,
  exactly as the sibling deferred it (its DECISIONS D2), to a pass
  with a real model.
- Debugging surface (the sibling's H4): not measured here. The
  sibling's registered procedure counted trace records read by a
  scripted diagnostician and was reported Not yet measured there
  because the arms persist traces in incommensurable units; the
  same problem applies to this pair (SQLite snapshot rows versus
  event records). No proxy number will be presented as diagnosis
  time.
- Real model quality, prompt design, hosted APIs, production
  deployment, multi-process checkpoint stores, human-in-the-loop
  interrupts.

## Versions

Pinned for this study: langchain 1.4.9 and langchain-core 1.7.6 on
Python 3.12.3. The full dependency lock is written to
requirements-lock.txt at the harness commit, and the installed
versions are printed into results/env.json by the suite. Framework
version drift is a named threat to this evidence: results hold for
the pinned versions only, and the pins are part of the result.

## Stop rules

- The suite runs once as registered: 12 tasks, 8 trials, seeds
  1000 to 1007 per task; fault suite as registered above.
- No task, seed, threshold or verdict rule changes after the first
  suite run. Any fix to a harness bug after a run is logged in
  DECISIONS.md and the whole suite is rerun; partial reruns are
  not reported.
- Failures, duplicates and killed runs are published, not
  filtered.
- One command reruns the whole study: python -m study.run_suite,
  then python -m study.analyze regenerates RESULTS.md.

## Societal impact

Framework choice is a recurring, expensive decision for small AI
teams, and it is usually made on fashion, tutorial counts or vendor
claims. Paired measurements on identical tasks, with the failure
modes published, are how that decision becomes an engineering
decision instead. The stakes are not abstract: agents that act for
people move money, send messages and change records, and an agent
that repeats a side effect after a crash can charge twice or book
twice. Evidence about which orchestration choices prevent that, and
what they cost, is safety evidence for every team shipping agents.

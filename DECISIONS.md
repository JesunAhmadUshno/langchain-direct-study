# DECISIONS

## D1. Scripted policy instead of a model (carried from the sibling study)

Zero spend rules out hosted models, and a small local model would mix
model quality and a user simulator into an orchestration question. This
study uses the same deterministic scripted policy as
JesunAhmadUshno/langgraph-vs-native-study, in both arms. Consequence:
the research object is the orchestration layer only, and every claim in
this repository is limited to that layer. The real-model run is the Deep
pass (ROADMAP.md).

## D2. Prompt injection stays deferred (sibling study DECISIONS D2)

A scripted policy does not read tool output as instructions, so attack
success is undefined, not zero. Rather than report a meaningless tie,
the prompt-injection axis is deferred to the Deep pass with a real
model and an AgentDojo-style suite, exactly as the sibling study
deferred it. This study registers no injection hypothesis.

## D3. Shared core and native arm imported verbatim, hash-gated

The task fixtures, policy, tools, executor and scoring module are
imported byte for byte from the sibling repository, and so is the
native arm. The suite refuses to run unless the fixtures sha256 equals
the sibling's published hash,
8c4770760b195d13faddd3bb4cfbf60ab9c24d1581acbab5c83fed9dc7d555ad.
Any drift in the shared core would silently change the research object;
the hash turns that drift into a loud failure. The sibling repository
itself is never modified.

## D4. LangChain persistence mapping: runnables for sequencing, SQLite for durability

langchain-core 1.7.6 ships no checkpointer of its own; checkpointing in
the LangChain ecosystem lives in the graph layer, which this study
excludes by design. The honest mapping of "LangChain's own mechanisms
where they exist, the same SQLite discipline where they do not" is:

- Sequencing: one task step is one invocation of a RunnableSequence of
  three RunnableLambda stages (load state, run one executor step,
  persist state), composed with the pipe operator. The executor state
  dict is the runnable input and output value.
- Durability: the persist stage writes the full state dict to the arm's
  own SQLite store after every step, the same commit-per-step cadence
  as the native arm's event log and the sibling LangGraph arm's
  checkpointer.
- Exactly-once: reconcile is the shared tools.was_applied check and
  commit is the shared tools.append_record, the sibling study's D5
  discipline, unchanged. The framework arm is not run without its
  discipline; that would test a strawman.

## D5. LangGraph is present only as a transitive dependency, never imported

langchain 1.4.9 depends on langgraph 1.2.20, so the package is
installed in the environment. The LangChain arm imports only
langchain_core.runnables. A test asserts that running the arm leaves
langgraph out of sys.modules, and results/env.json records the
installed langgraph version so the fact is visible rather than hidden.
Any accidental import fails CI, not just code review.

## D6. Verdict words and the H2 reframing

The sibling study reported Supported, Refuted and Inconclusive. This
study uses CONFIRMED, REFUTED and INCONCLUSIVE, computed by
study.analyze from the frozen rules in PREREGISTRATION.md. The sibling
H2 was a bound check (invocations and wall ratios under fixed bounds).
Here H2 is a tax test on the wall ratio alone: CONFIRMED above 1.10,
REFUTED at or under 1.00, INCONCLUSIVE between, because the research
question asks whether the direct-API tax exists and how it compares to
the graph framework's measured ratio, not whether it stays under a
budget. Invocation counts are still measured and published; they are
identical by construction under the shared executor and carry no
verdict.

## D7. Debugging axis not measured (sibling study DECISIONS D8)

The two arms persist traces in incommensurable units (a single-row
state store versus an event log), so a record count would measure the
storage format, not diagnosis effort. No proxy number is presented as
diagnosis time. ROADMAP.md carries the timed human procedure for the
Deep pass.

## D8. Fault injection lives in the harness, not in either arm

The F1 hook sits at the executor's step boundary and the F2 hook inside
the shared append_record, both driven by environment variables that
only the fault runner sets. Neither arm can see or special-case a
fault. Resume attempts run with no kill variables set. (Sibling study
DECISIONS D7, unchanged.)

## D9. Native arm code budget: measured, not capped

The native arm is imported unchanged from the sibling study, so its
code surface is whatever it was (counted by script and published).
This study does not cap either arm; the code surface of both arms is
counted and published so a reader can judge whether the comparison was
fair. The native arm is one competent implementation, not "the" native
approach. (Sibling study DECISIONS D6, unchanged.)

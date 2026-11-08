# AUDIT

Self-audit of this repository against the standing project standard:
one real research question, hypotheses frozen before any measured run,
measured results only, verdicts published either way, receipts on every
claim.

## Claim audit

Every headline figure in README.md and RESULTS.md is computed by
study.analyze from results/raw_main.json and results/raw_fault.json,
and was independently recounted from those raw files by a separate
script before publication. The recount matched on every figure:
pass^1 0.979 in both arms (94 of 96), all 12 paired differences exactly
0.000, wall medians 0.398 s (LangChain) and 0.869 s (native), ratio
0.459, invocation medians 5.0 in both arms, state bytes medians 8,192
and 16,384, fault passes 48 of 48 in both arms, zero duplicated-effect
runs, 96 of 96 kills landed as SIGKILL, recomputed-step medians 0.5 in
both arms. Sibling figures quoted for the cross-study table were read
from the sibling repository's published RESULTS.md and are labelled as
published sibling numbers wherever they appear.

Jev claim_check (gate record): model jev-1.13.0, noul 0.55, route
REVIEW (bands: clear at 0.85 or above, block at 0.10 or below, review
between), usage 1,417 input and 20 output tokens. Spec and raw result:
~/workspace/tools/jev/langchain-direct-study-claim-spec-2026-11-08.json
and langchain-direct-study-claim-results-2026-11-08.json; the record is
also committed at results/jev-claim-check.json. On REVIEW the figures
were hand-verified against the tables, as described above, and the
verdicts stand on that verification.

Protocol integrity: PREREGISTRATION.md is the first content commit
(aa4e555), before the harness commit and before any run. The suite ran
once, as registered; no harness fix was needed after the run, and no
partial rerun is reported. The shared core and native arm are verbatim
imports from the sibling repository, enforced at run time by the
fixtures hash gate (8c4770760b195d13faddd3bb4cfbf60ab9c24d1581acbab5c83fed9dc7d555ad).

## Security

No credentials, no network calls, no model APIs. The only external
inputs are the pinned packages in requirements.txt. Fault injection is
SIGKILL of the study's own subprocesses on its own work directory.
The LangChain arm's never-imports-langgraph property is enforced by a
test, not by convention.

## Cost

Zero spend. Compute is this VM's shared capacity; the suite pass took
about 6.4 minutes of wall time. Jev usage for the claim check is
recorded above.

## Licence and data

Apache-2.0 (LICENSE). All fixtures are synthetic and defined in code;
no external dataset, no personal data. The sibling repository is
Apache-2.0 as well; imported files keep their original form.

## Maintenance

The study is a frozen measurement. A langchain-core version bump is a
new measurement under ROADMAP.md, never an edit of this one. The
reproduction tests (tests/test_reproduction.py) recompute known answers
from the committed raw files and verify their SHA-256 checksums, so
evidence drift fails CI.

## Grade: 6,400 of 10,000

| Item | Deduction |
|---|---|
| No model in the loop: the scripted policy measures orchestration only, so the verdicts cannot speak to framework behaviour under real reasoning load (declared scope limit, Deep pass pending) | -1,400 |
| One machine, one suite pass, on a shared VM: wall-time figures carry machine state and have no replication | -700 |
| H1 test is degenerate (paired standard deviation 0): the equivalence verdict rules out orchestration-caused success loss but carries no further information | -500 |
| Debugging axis not measured (trace units incommensurable across arms); carried as a deferral, not closed | -400 |
| Cross-framework wall comparison (LangChain 0.459 versus LangGraph 0.299) rests on two separate native runs; descriptive only | -300 |
| Fixtures are small, deterministic and synthetic by design; no comparability to any published benchmark | -300 |
| **Total** | **-3,600** |

What was not deducted, and why: the pre-registration was frozen before
any run and the verdict rules were applied as written, including an
H2 REFUTED against the registered prediction's framing of a tax; the
exactly-once discipline was replicated into a third arm without
weakening it; raw evidence, checksums and reproduction tests are
committed; the Jev REVIEW was closed by hand verification, not by
rounding the noul up.

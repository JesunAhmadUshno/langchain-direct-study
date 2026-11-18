# Suite re-execution, 2026-11-17: committed record versus rerun

Gap-closure run. The registered suite (`python -m study.run_suite`,
then `python -m study.analyze`) was re-executed in full in a scratch
copy of this repository, on the workspace block device (btrfs), with
the pinned environment (langchain 1.4.9, langchain-core 1.7.6,
Python 3.12.3, fixtures sha256 verified by the suite's own gate).
No committed file was modified. Rerun raw output is saved beside
this file as `raw_main_rerun.json`, `raw_fault_rerun.json` and
`summary_rerun.json`.

Environment difference, stated once: the rerun machine is this
shared VM under CPU throttling (about 1.5 effective cores against
the machine of record's 4 vCPU), so absolute wall times are not
expected to match; the protocol's medians and the ratio are the
comparison quantities, exactly as PREREGISTRATION.md frames them.

## Aggregates that match exactly

| Aggregate | Committed | Rerun | Match |
|---|---|---|---|
| H1 verdict | CONFIRMED | CONFIRMED | yes |
| H2 verdict (frozen rule: median ratio at or under 1.00) | REFUTED | REFUTED | yes |
| H3 verdict | CONFIRMED | CONFIRMED | yes |
| pass^1 pooled, native | 94 of 96 (0.979) | 94 of 96 (0.979) | yes |
| pass^1 pooled, LangChain | 94 of 96 (0.979) | 94 of 96 (0.979) | yes |
| Per-task pass^1, all 24 arm-task cells | as RESULTS.md | identical | yes |
| pass^k, k = 1 to 8, both arms | as RESULTS.md | identical | yes |
| H1 90 percent CI for the paired difference | [0.000, 0.000] | [0.000, 0.000] | yes |
| Policy invocations per run, median / p95, both arms | 5.0 / 8 | 5.0 / 8 | yes |
| Durable state bytes per run, median, native | 16,384 | 16,384 | yes |
| Durable state bytes per run, median, LangChain | 8,192 | 8,192 | yes |
| Fault runs passed, native | 48 of 48 | 48 of 48 | yes |
| Fault runs passed, LangChain | 48 of 48 | 48 of 48 | yes |
| Fault passes by class, both arms | F1 24 of 24, F2 24 of 24 | F1 24 of 24, F2 24 of 24 | yes |
| Runs with duplicated effects, both arms | 0 | 0 | yes |
| Kills landed as registered, both arms | 48 of 48 | 48 of 48 | yes |
| Recomputed steps, median, both arms | 0.5 | 0.5 | yes |
| Recomputed counts by class, both arms | F1 {0: 24}, F2 {1: 24} | F1 {0: 24}, F2 {1: 24} | yes |
| Fault raw file | raw_fault.json | byte-identical (md5 399cfd1256b959f0baa858b09100d6f8) | yes |

## Wall-time aggregates (environment-bound; differences expected)

| Aggregate | Committed | Rerun | Note |
|---|---|---|---|
| Native wall per run, median | 0.869 s | 1.073 s | rerun slower under CPU throttle |
| Native wall per run, p95 | 1.488 s | 1.484 s | essentially unchanged |
| LangChain wall per run, median | 0.398 s | 0.919 s | rerun much slower: the LangChain arm is CPU-bound Python, so throttling taxes it proportionally more than the fsync-bound native arm |
| LangChain wall per run, p95 | 0.649 s | 2.260 s | same effect, tail |
| Median wall ratio, LangChain / native | 0.459 | 0.856 | still under the frozen 1.00 no-tax line, so H2 REFUTED reproduces |
| Paired bootstrap 95 percent CI for the ratio | [0.414, 0.497] | [0.766, 1.026] | rerun interval crosses 1.00 |
| Paired sign test | LangChain faster in 96 of 96, p = 2.5e-29 | LangChain faster in 43, slower in 53, p = 0.358 | not decisive on this throttled VM |

Reading: every success, cost-count and recovery aggregate
reproduces exactly, and the frozen H2 verdict reproduces because
the verdict rule turns on the median ratio, which stayed under
1.00. The strength of the wall evidence did not reproduce: on the
machine of record LangChain was faster in every pair, while under
this VM's CPU throttle the paired differences are a coin flip
around a still-favourable median. That is the implementation- and
machine-sensitivity the paper already discloses, now measured a
second time from the other side.

## Discarded first attempt (disclosed)

A first rerun attempt was executed in a scratch copy under /tmp.
On this machine /tmp is a tmpfs (RAM disk), where fsync is nearly
free; the native arm's median wall fell to 0.0018 s and the ratio
inverted to 2.937. Those wall figures are not a re-execution of
the registered measurement, whose cost model is fsync latency on
a block device, so the attempt was discarded for the wall axis
and the suite was rerun on the workspace block device (above).
Its deterministic aggregates (success, invocations, state bytes,
fault counts, duplicates) matched the committed record as well;
they are filesystem-independent.

# WAL-mode native variant, 2026-11-17 (DECISIONS.md D11)

Gap-closure variant run, registered in DECISIONS.md D11 before
any variant run and executed exactly as registered: the native
arm with its SQLite state store in WAL journal mode
(`PRAGMA journal_mode=WAL` at open; study/arm_native_wal.py runs
the frozen arm with only its connection factory replaced), the
same 12 tasks, trial seeds 1000 to 1007, 96 main runs, with the
LangChain arm rerun in the same pass so the wall ratio is paired
within one pass on one machine; fault suite for the variant arm,
same cells as registered, 48 runs. Raw output: raw_main_wal.json,
raw_fault_wal.json, env_wal.json, summary_wal.json beside this
file. No frozen verdict changes: H2 belongs to the frozen arms.

Environment: this shared, CPU-throttled VM (about 1.5 effective
cores), workspace block device (btrfs). Absolute wall times are
not comparable across passes or machines; the within-pass ratio
is the load-controlled figure, and cross-pass median differences
are reported as indicative only.

## Wall time: the registered comparison

| Measure | Committed, synchronous native (machine of record) | Re-execution, synchronous native (this VM) | WAL pass (this VM, one pass) |
|---|---|---|---|
| Native wall per run, median | 0.869 s | 1.073 s | 0.455 s (native-WAL) |
| Native wall per run, p95 | 1.488 s | 1.484 s | 0.891 s |
| LangChain wall per run, median | 0.398 s | 0.919 s | 0.518 s |
| LangChain wall per run, p95 | 0.649 s | 2.260 s | 1.030 s |
| Median wall ratio, LangChain / native | 0.459 | 0.856 | 1.141 (against native-WAL) |
| Paired bootstrap 95 percent CI for the ratio | [0.414, 0.497] | [0.766, 1.026] | [0.998, 1.282] |
| Paired sign test | LangChain faster in 96 of 96, p = 2.5e-29 | faster in 43, slower in 53, p = 0.358 | faster in 47, slower in 49, p = 0.919 |

## Does the H2 reading survive WAL? No.

The frozen H2 reading is that LangChain direct is faster than
the native arm (median ratio 0.459 on the machine of record,
REFUTED tax). With the native state store in WAL mode, the
native median in this pass is 0.455 s against LangChain's
0.518 s in the same pass: the ratio is 1.141, above the 1.00
no-tax line and above even the frozen 1.10 tax factor. The
paired sign test is a coin flip (LangChain faster in 47 pairs,
slower in 49, p = 0.919) and the bootstrap interval [0.998,
1.282] sits at or above 1.00 throughout. So the ordering does
not survive: at the median it inverts, and at pair level the
two arms are indistinguishable.

What moved: the native arm itself. Against the same-day
synchronous re-execution median of 1.073 s, WAL cut the native
median to 0.455 s (about 2.4 times faster; a cross-pass
comparison on a variably loaded VM, so indicative, not paired).
That swing is larger than the entire LangChain-versus-native
gap the frozen study measured. The conclusion the variant
supports is the one the paper already states as a caveat, now
with a number on it: the frozen wall ratio is a property of
the native arm's rollback-journal commit policy, not a
measured framework tax. Under WAL there is no tax to refund;
if anything the sign flips, within noise.

## Native-WAL on the other axes (same pass)

| Aggregate | Native-WAL | Frozen native (committed) |
|---|---|---|
| pass^1 pooled | 94 of 96 (0.979) | 94 of 96 (0.979) |
| Per-task pass^1 | identical pattern (T03 and T10 at 0.875, rest 1.000) | as RESULTS.md |
| Policy invocations per run, median / p95 | 5.0 / 8 | 5.0 / 8 |
| Durable state bytes per run, median | 16,384 | 16,384 |

## Fault behaviour under WAL (variant arm, 48 runs)

| Aggregate | Native-WAL | Frozen native (committed) |
|---|---|---|
| Fault runs passed | 48 of 48 | 48 of 48 |
| By class | F1 24 of 24, F2 24 of 24 | F1 24 of 24, F2 24 of 24 |
| Kills landed as registered | 48 of 48 | 48 of 48 |
| Runs with duplicated effects | 0 | 0 |
| Duplicated effect keys, total | 0 | 0 |
| Recomputed steps, median | 0.5 | 0.5 |
| Recomputed counts by class | F1 {0: 24}, F2 {1: 24} | F1 {0: 24}, F2 {1: 24} |

WAL changed the native arm's speed and nothing else: success,
invocations, state size and exactly-once recovery are the
frozen arm's numbers, cell for cell.

<!-- AUTO-GENERATED. DO NOT EDIT. -->
# Paper II major-revision tables

## Same-candidate-pool sequence ablation

Evidence tier: **Published manual transcription Gold**. All variants use identical documents, positioned candidate pools, matcher, and tolerance; the bootstrap unit is the document.

| Variant | v004 P / R / F1 (95% CI) | v004 FCR | v005 P / R / F1 (95% CI) | v005 FCR |
|---|---:|---:|---:|---:|
| Raw parser | 0.883 / 0.282 / 0.428 [0.339, 0.515] | -- | 0.737 / 0.264 / 0.389 [0.305, 0.466] | -- |
| Eligible pool, no sequence | 0.815 / 0.419 / 0.554 [0.475, 0.625] | 0.324 | 0.718 / 0.402 / 0.516 [0.438, 0.588] | 0.322 |
| + monotonic sequence | 0.942 / 0.418 / 0.579 [0.495, 0.655] | 0.111 | 0.911 / 0.394 / 0.550 [0.471, 0.619] | 0.062 |
| + continuity / zero-origin | 0.950 / 0.403 / 0.566 [0.480, 0.644] | 0.126 | 0.914 / 0.374 / 0.530 [0.450, 0.603] | 0.086 |
| + column stability, no term bonus | 0.951 / 0.400 / 0.563 [0.476, 0.641] | 0.126 | 0.909 / 0.363 / 0.519 [0.437, 0.593] | 0.124 |
| Complete archived score | 0.953 / 0.403 / 0.566 [0.480, 0.645] | 0.121 | 0.914 / 0.374 / 0.530 [0.450, 0.603] | 0.084 |

## Document-level risk and net utility

Evidence tier: **Published manual transcription Gold**. The primary safety unit is the document; the iid-action bound is retained only as a secondary diagnostic.

| Cohort | Policy | Net additional matches / 100 documents | Net change in incorrect predictions | Worsened documents (document F1) | Accepted documents | Review/abstain documents |
|---|---|---:|---:|---:|---:|---:|
| v004 | Unselective sequence | 234.0 | -34 | 6 | 79 | 0 |
| v004 | Addition-only risk policy | 43.0 | 0 | 0 | 8 | 71 |
| v005 | Unselective sequence | 227.0 | -122 | 10 | 85 | 0 |
| v005 | Addition-only risk policy | 39.0 | 0 | 0 | 11 | 74 |

Across 200 documents, the addition-only policy accepted 82 actions in 19 documents, observed 0 worsened documents, and retained 145 changed-sequence documents for review or abstention. The one-sided 95% zero-event upper bound is 0.1459 per accepted document; the secondary iid-action bound is 0.0359.

## Post-hoc shallow-start prior sensitivity

Evidence tier: **Published manual transcription Gold**. The candidate pool, references, matcher, and tolerance are fixed; this is explanatory sensitivity, not threshold selection.

| Start penalty per foot | v004 predicted / F1 | v005 predicted / F1 |
|---:|---:|---:|
| 0.0000 | 822 / 0.5662 | 846 / 0.5310 |
| 0.0005 | 822 / 0.5662 | 846 / 0.5304 |
| 0.0010 | 822 / 0.5662 | 846 / 0.5297 |
| 0.0025 | 822 / 0.5662 | 846 / 0.5297 |
| 0.0050 | 822 / 0.5662 | 846 / 0.5297 |

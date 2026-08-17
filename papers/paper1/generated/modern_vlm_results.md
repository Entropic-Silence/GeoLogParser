# Modern VLM Results

This table is generated only from runs whose artifact directory records `status=completed`. Metrics with different evidence tiers are never pooled.

| Group | Model | Interface | Cohort | Evidence | Docs | Pages | P | R | F1 (document 95% CI) | Boundary-exact | Zero output | JSON-valid | Numeric invalidity | s/page |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Open | Qwen3.8-27B-FP8 | generalist_direct_json | California v001 | GOLD_PUBLISHED_MANUAL_TRANSCRIPTION | 50 | 77 | 0.908 | 0.958 | 0.932 [0.888, 0.973] | 0.740 | 0.000 | 0.987 | 0.009 | 9.99 |
| Open | Qwen3.8-27B-FP8 | generalist_direct_json | California v002 | GOLD_PUBLISHED_MANUAL_TRANSCRIPTION | 100 | 154 | 0.854 | 0.942 | 0.896 [0.841, 0.943] | 0.700 | 0.000 | 1.000 | 0.007 | 10.83 |
| Open | Qwen3.8-27B-FP8 | generalist_direct_json | California v003 | GOLD_PUBLISHED_MANUAL_TRANSCRIPTION | 100 | 154 | 0.907 | 0.930 | 0.918 [0.878, 0.953] | 0.720 | 0.000 | 1.000 | 0.004 | 10.40 |
| Open | Qwen3.8-27B-FP8 | generalist_direct_json | California v004 | GOLD_PUBLISHED_MANUAL_TRANSCRIPTION | 100 | 147 | 0.919 | 0.915 | 0.917 [0.876, 0.952] | 0.740 | 0.050 | 0.959 | 0.017 | 11.35 |
| Open | Qwen3.8-27B-FP8 | generalist_direct_json | California v005 | GOLD_PUBLISHED_MANUAL_TRANSCRIPTION | 100 | 141 | 0.909 | 0.896 | 0.903 [0.864, 0.939] | 0.690 | 0.010 | 1.000 | 0.011 | 12.60 |
| Open | Qwen3.8-27B-FP8 | generalist_direct_json | Swissgeol held-out | SOURCE_AGREEMENT_REFERENCE | 35 | 35 | 0.592 | 0.562 | 0.577 [0.535, 0.619] | 0.000 | 0.000 | 1.000 | 0.050 | 4.54 |

## Paired California Comparison

The following deltas resample whole reports while retaining the paired Qwen and frozen RapidOCR predictions. They apply only to the published-manual-transcription California cohorts; they are not pooled with the Swissgeol source-agreement panel.

| Cohort | Qwen F1 | RapidOCR F1 | Delta F1 (Qwen - RapidOCR), document 95% CI | Bootstrap Pr(delta > 0) |
| --- | ---: | ---: | ---: | ---: |
| California v001 | 0.932 | 0.390 | 0.542 [0.436, 0.649] | 1.000 |
| California v002 | 0.896 | 0.450 | 0.445 [0.345, 0.543] | 1.000 |
| California v003 | 0.918 | 0.383 | 0.535 [0.457, 0.614] | 1.000 |
| California v004 | 0.917 | 0.428 | 0.489 [0.405, 0.578] | 1.000 |
| California v005 | 0.903 | 0.389 | 0.514 [0.434, 0.595] | 1.000 |

## Registered But Not Yet Comparable

| Group | Model | Cohort | Status |
| --- | --- | --- | --- |
| Open | MinerU2.5-Pro-2604-1.2B | California v001 | NO_GO_BOUNDED_SMOKE_ZERO_INTERVALS |
| Open | PaddleOCR-VL-1.6 | California v001 | NO_GO_PAGE_LEVEL_TABLE_TASK_ZERO_INTERVALS |
| Closed | requested chatgpt5.6-sol-high / served gpt-5.6-sol | California v001-v005 | NO_GO_SYNTHETIC_VISUAL_PREFLIGHT_UPSTREAM_502_NO_GOLD_REQUEST |
| Closed | Claude Opus 4.6 | California v001-v005 | NOT_RUN_REQUIRES_VALID_OFFICIAL_API_CREDENTIAL |

## Retained Operational Records

The interrupted v004 attempts are retained for transport auditing only. They have no score and were superseded by the completed frozen v004 run above; no page was selectively retried.

| Model | Cohort | Status |
| --- | --- | --- |
| Qwen3.8-27B-FP8 | California v004 | TRANSPORT_INTERRUPTED_BEFORE_PAGE_REQUEST |
| Qwen3.8-27B-FP8 | California v004 | TRANSPORT_INTERRUPTED_AFTER_98_PAGE_REQUESTS |

## Interpretation Boundary

Direct extraction quality is distinct from assurance capability. The comparison may attribute an assurance property to GeoLogParser only when the corresponding run records field-level source geometry, deterministic numeric checks, constraint outcomes, an explicit acceptance or abstention decision, and database provenance. A registered or unavailable closed model contributes no score and no comparative conclusion.

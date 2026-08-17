# Modern VLM Results

This table is generated only from runs whose artifact directory records `status=completed`. Metrics with different evidence tiers are never pooled.

| Group | Model | Interface | Cohort | Evidence | Docs | Pages | P | R | F1 | Boundary-exact | Zero output | JSON-valid | Numeric invalidity | s/page |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Open | Qwen3.8-27B-FP8 | generalist_direct_json | California v001 | GOLD_PUBLISHED_MANUAL_TRANSCRIPTION | 50 | 77 | 0.908 | 0.958 | 0.932 | 0.740 | 0.000 | 0.987 | 0.009 | 9.99 |
| Open | Qwen3.8-27B-FP8 | generalist_direct_json | California v002 | GOLD_PUBLISHED_MANUAL_TRANSCRIPTION | 100 | 154 | 0.854 | 0.942 | 0.896 | 0.700 | 0.000 | 1.000 | 0.007 | 10.83 |

## Registered But Not Yet Comparable

| Group | Model | Cohort | Status |
| --- | --- | --- | --- |
| Open | Qwen3.8-27B-FP8 | California v003 | RUNNING |
| Open | Qwen3.8-27B-FP8 | California v004 | PLANNED |
| Open | Qwen3.8-27B-FP8 | California v005 | PLANNED |
| Open | Qwen3.8-27B-FP8 | Swissgeol held-out | PLANNED |
| Open | MinerU2.5-Pro-2604-1.2B | California v001 | RUNNING |
| Open | PaddleOCR-VL-1.6 | California v001 | READY_FOR_SMOKE |
| Closed | GPT-5.6 Sol | California v001-v005 | NOT_RUN_REQUIRES_VALID_OFFICIAL_API_CREDENTIAL |
| Closed | Claude Opus 4.6 | California v001-v005 | NOT_RUN_REQUIRES_VALID_OFFICIAL_API_CREDENTIAL |

## Interpretation Boundary

Direct extraction quality is distinct from assurance capability. The comparison may attribute an assurance property to GeoLogParser only when the corresponding run records field-level source geometry, deterministic numeric checks, constraint outcomes, an explicit acceptance or abstention decision, and database provenance. A registered or unavailable closed model contributes no score and no comparative conclusion.

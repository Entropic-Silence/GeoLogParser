# VLM Proposal Assurance

Evidence tier: **Published manual transcription Gold**. The direct VLM and positioned reader are frozen independently; Gold is used only after decisions. Confidence intervals use document-cluster bootstrap.

| Cohort | Role | Raw P | Numeric-anchor coverage | Owned/accepted coverage | Accepted actions | Selective P (95% CI) | False acceptance | Docs with actions | Error docs |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| California v001 | development | 0.908 | 0.817 | 0.236 | 174 | 1.000 [1.000, 1.000] | 0.000 | 33 | 0 |
| California v002 | validation | 0.854 | 0.849 | 0.287 | 561 | 0.979 [0.951, 0.997] | 0.021 | 72 | 5 |
| California v003 | held-out replication | 0.907 | 0.845 | 0.244 | 447 | 0.993 [0.984, 1.000] | 0.007 | 63 | 3 |

Numeric-anchor coverage means that the exact source-unit value occurs in a positioned bbox on the same page; it does not establish column ownership. Owned/accepted coverage requires complete top-bottom agreement with the independently parsed positioned interval and retained source regions. Partial acceptance does not establish document completeness, so all non-complete documents remain in the review queue.

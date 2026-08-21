# Evidence tiers for the GeoLogParser paper series

The three manuscripts use the same evidence vocabulary. A tier describes the
independence and provenance of the reference, not the apparent quality of a
prediction. Results from different tiers are kept in separate table panels and
figures.

| Evidence type | Operational meaning | Claims supported |
|---|---|---|
| Published manual transcription Gold | An external institution transcribed the source images manually and reports quality control. This project did not recreate that review. | Formal extraction precision, recall, F1, numerical error, and document-level exactness within the published reference scope. |
| Source-agreement reference | An explicit PDF table can be aligned to an authoritative database record for the same object. Selection may condition on agreement. | Source-specific image/database agreement and method diagnostics; not a representative human image-GT estimate. |
| Authoritative metadata | Official database fields without an independently transcribed image reference. | Field coverage, conditional page/database agreement, and disagreement counts; not recognition accuracy when the page/database truth is unresolved. |
| Machine Silver | A reference produced by multiple models, deterministic rules, or machine adjudication. | Agreement, coverage, candidate yield, and training-corpus diagnostics; not Gold accuracy. |
| Audit / no GT | No independent reference for the target field. | Coverage, candidate count, runtime, schema validity, and failure taxonomy only. |

Synthetic fixtures are reported as a separate controlled-evidence class. Their
ground truth is exact by construction, but they support only controlled
mechanism and robustness claims, not performance on real historical logs.

The ownership boundary across the related manuscripts is:

- Paper I: task definition, evidence tiers, representative baselines, multi-cohort stability, and source-shift findings.
- Paper II: candidate-sequence reconstruction, correction harm, risk acceptance, and abstention.
- Paper III: propagation of upstream errors and spatial-support loss into surface and volume diagnostics.

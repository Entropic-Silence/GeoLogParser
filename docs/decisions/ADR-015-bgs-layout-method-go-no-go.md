# ADR-015: Development Gate Before BGS v002 External Evaluation

Date: 2026-08-15

## Context

BGS offshore v001 is now a development source because its baseline failures
have been inspected. A source-title- and record-disjoint v002 freeze contains
3 documents, 4 evaluation pages, 49 official intervals, and 3 new source
groups. Running v002 before the method is technically credible would consume a
small external confirmation set without answering the scientific question.

The v001 failure-attribution sequence found that semantic layout was detected
on 33/34 pages, whereas exact full-page OCR visibility covered only 75/367
reference boundaries. General semantic-panel tiling increased joint visibility
to 96/367. A field-specific, line-removed 4x reread contributed a different
error channel; the union reached 110/367 (29.97%). Thus layout localization is
mostly available, but visual candidate recall remains a hard ceiling.

The v018 development model corrected a plural ``DESCRIPTIONS`` anchor failure,
recomputed multiscale/field ROI evidence, calibrated depth columns in both
directions, and used mixed-page semantic-role experts with nested OOF
calibration. On the same source-disjoint folds it achieved boundary
precision/recall/F1 0.4940/0.2262/0.3103 and interval F1 0.1116 at ±0.05 m.
The calibrated candidate ECE was 0.0352. A sequence-level selective operating
point accepted 43 boundaries (coverage 0.1172), with precision 0.9302 and CNER
0.0698. The method still fails the interval-F1 gate and the full-coverage
boundary-precision gate. The v018 artifact SHA256 is
``cd2f60e2b5de8db4816d25753e983e03dd239177f007e53587d2ce4362af54aa``.

## Decision

Do not run BGS v002 yet. The external freeze remains unopened for extraction
evaluation until a replacement development method satisfies all predeclared
conditions on BGS v001 source-disjoint folds:

1. interval F1 at ±0.05 m >= 0.15;
2. boundary precision at ±0.10 m >= 0.70 with recall >= 0.20;
3. a selective operating point with critical numerical error rate <= 0.10 and
   accepted-boundary coverage >= 0.10;
4. every accepted boundary has page and bbox provenance;
5. thresholds and model serialization are committed before v002 execution.

These are release gates, not paper success criteria and not claims about
population performance. If v002 is evaluated and its errors are used for any
method change, v002 becomes validation and a new v003 external freeze is
required.

## Consequences

- The current v007 artifact is retained as development failure evidence.
- The v018 artifact is retained as the strongest development candidate, but is
  not an external result and does not authorize v002 execution.
- The v019 agreement-feature test is rejected: boundary F1 fell to 0.2873,
  interval F1 to 0.1004, and selective precision to 0.8627. Correlated
  cross-reader agreement is not accepted as independent evidence.
- Further work targets candidate recall and structured sequence inference, not
  OCR/VLM model-count expansion.
- The next method revision must explicitly model template family, depth-scale
  geometry, terminal-depth evidence, and mutually exclusive numeric roles.
- BGS v002 rights remain `PENDING_MANUAL_PRE_SUBMISSION_REVIEW` and its small
  three-source denominator must be disclosed when eventually used.

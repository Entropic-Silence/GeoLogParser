# ADR-017: Multi-column structural events and interval-pair decoding

Date: 2026-08-16

Status: `PARTIAL_ACCEPT` for multi-column candidate generation;
`REJECT` for the pairwise interval ranker.

## Context

NativeMM ablations showed that official BGS boundaries are often expressed in
narrow recovery, lithology, formation or contact columns. The v018 parser
searched one inferred graphic column, imposing a structural-evidence ceiling.

## Decision

Add reference-blind multi-column detection around the calibrated depth field.
Each column contributes horizontal-line and texture-transition candidates with
column position, activity, rank and cross-column support features. Continue to
use source-disjoint candidate ranking and monotonic geological decoding.

Separately test a learned pair ranker that predicts whether two boundary
candidates form one adjacent interval. The pair model must be rejected unless
it improves source-disjoint interval F1.

## Evidence

The v021 multi-column route increased source-disjoint BGS v001 interval F1 from
0.1116 to 0.1213. Boundary precision/recall/F1 were 0.5659/0.1989/0.2944, so
boundary F1 fell from v018's 0.3103. Its selective point accepted 41 boundaries
with precision 0.9268, reference-relative coverage 0.1117 and CNER 0.0732.

The pairwise model evaluated 77,637 candidate pairs under outer source folds and
reduced interval F1 to 0.0445 and boundary F1 to 0.2066. It is rejected.

A subsequent source-disjoint column gate retained six learned high-scoring
graphic columns per page before the existing monotonic decoder. It reached
boundary precision/recall/F1 0.6610/0.2125/0.3216 and interval F1 0.1475 at
±0.05 m, the strongest current development result. CNER remained 0.3390, so
the interval gate was not met and the variant is not eligible for external
release.

Its coverage-risk audit identifies a deployable selective point at threshold
0.65: 40 accepted boundaries, precision 0.9500, reference-relative coverage
0.1090 and CNER 0.0500. This passes the selective reliability criteria but does
not override the failed full-sequence interval gate.

## Consequence

The column-gated v022 candidate is retained as the next development baseline,
not as the frozen external model. It remains below the interval-F1 >= 0.15
release gate and has unacceptable critical numerical error for automatic
acceptance, so BGS v002 is not opened. Further work should reduce false graphic
events and improve endpoint coverage rather than enumerate more candidate pairs.

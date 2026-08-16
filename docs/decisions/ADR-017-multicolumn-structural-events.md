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

## Consequence

v021 is retained as an interval-focused development ablation, not as the frozen
external model. It remains below the interval-F1 >= 0.15 release gate, so BGS
v002 is not opened. Further work should suppress semantically irrelevant
columns before candidate generation and improve event coverage, rather than
enumerating more boundary pairs.

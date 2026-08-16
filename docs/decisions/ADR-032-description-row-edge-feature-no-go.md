# ADR-032: Description-row edge alignment is not a primary structural expert

Date: 2026-08-16  
Status: `NO_GO_PRIMARY_RETAIN_FEATURE`

## Question

Can reference-blind alignment between graphical contact candidates and OCR
description-row edges distinguish geological boundaries from scale grids,
sampling lines, and table rules on BGS long pages?

## Evidence

The candidate generator now measures a soft distance from every graphical
transition to the top or bottom edge of adjacent OCR text rows. On BGS v001
development, this feature had weak candidate-level discrimination: the mean
support was `0.5855` for candidates within 0.10 m of a reference boundary and
`0.4574` for other candidates; the rank-based single-feature AUC was `0.5912`.

Against the otherwise identical v026 role-fallback run, the row-edge feature
changed source-disjoint monotonic Boundary/Interval F1 from
`0.3094/0.1179` to `0.3099/0.1190`. At the selective operating point,
Boundary F1 increased from `0.1773` to `0.1902`, but CNER worsened from
`0.0769` to `0.0930`. Nested routing with the fixed v024 expert reached
Boundary/Interval F1 `0.3333/0.1786`, below routed v028
(`0.3475/0.1978`).

The result is consistent with the raster-contact failure in ADR-030. OCR text
boxes encode line wrapping, stamps, labels, and sampling annotations as well as
geological descriptions. A nearby row edge is evidence of a structural event,
but not evidence of that event's semantic owner.

## Decision

Do not promote description-row alignment as a new expert or continue tuning
its distance threshold. Retain the feature in candidate provenance and future
joint event representations. Keep v028 as the BGS development method. Do not
open BGS v003.

A successor must jointly infer event ownership and sequence role rather than
add more independent local scores. The minimum development gate remains a
clear improvement over v028 in both Interval F1 and critical numerical risk,
followed by an independent source-disjoint evaluation.

## Reproducibility

- Feature implementation: `src/geologparser/layout/depth_semantics.py`
- Ranker integration: `scripts/run_bgs_layout_method_development.py`
- Development output:
  `experiments/paper2/analysis/bgs_layout_method_development_v026_row_edges.json`
- Nested routed output:
  `experiments/paper2/analysis/bgs_routed_moe_v029_row_edges_nested.json`
- Model artifact:
  `experiments/paper2/models/bgs_layout_field_aware_moe_v026_row_edges.json`
- Frozen external status: BGS v003 remained unopened.

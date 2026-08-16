# ADR-033: Joint event-owner sequence decoding is not yet viable

Date: 2026-08-16  
Status: `NO_GO_PRIMARY`

## Question

Can a sequence decoder that explicitly penalizes switches between printed,
graphical, and terminal-metadata event owners overcome the long-page structural
recall bottleneck while keeping candidate probabilities fixed?

## Evidence

The diagnostic used the v026 row-edge candidate report and performed nested
source-disjoint selection of both the sequence threshold and owner-switch
penalty. The target fold was never used for parameter selection. The resulting
overall Boundary/Interval F1 was `0.2934/0.1132`, with Boundary CNER
`0.6517`. This is below routed v028 (`0.3475/0.1978`, CNER `0.3281`) and
below the v026 candidate report's monotonic sequence (`0.3099/0.1190`).

The decoder emitted 267 boundaries, of which 93 matched the reference at
±0.05 m. The additional sequence-level preference for owner continuity did not
recover the missing evidence and instead admitted incompatible graphical and
printed candidates into longer sequences.

## Decision

Do not promote owner-switch penalties or continue tuning this decoder family.
The failure indicates that semantic ownership must be inferred before
candidate generation or represented jointly with visual regions, not imposed
after independent candidate probabilities have already collapsed the evidence.
Keep v028 as the current BGS development method and do not open BGS v003.

## Reproducibility

- Implementation: `scripts/run_bgs_joint_event_sequence_v030.py`
- Candidate input:
  `experiments/paper2/analysis/bgs_layout_method_development_v026_row_edges.json`
- Output:
  `experiments/paper2/analysis/bgs_joint_event_sequence_v030_nested.json`
- Frozen external status: BGS v003 remained unopened.

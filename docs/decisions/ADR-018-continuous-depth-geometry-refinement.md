# ADR-018: Continuous-depth geometry refinement before external evaluation

Date: 2026-08-16

Status: `ACCEPT`; development release gates passed.

## Context

The v022 semantic-column gate raised BGS v001 interval F1 to 0.1475 but still
treated every calibrated graphical event as an integer whenever the decoder's
coarse snap policy selected a one-metre grid. Error inspection showed real
half- and tenth-metre boundaries being converted, for example, from calibrated
depths near 5.50 and 10.48 m to 5 and 11 m. The graphical location was useful;
the final quantisation destroyed its numerical evidence.

A source-disjoint post-sequence logistic pruner was tested first. It reduced
boundary F1 to 0.2960 and interval F1 to 0.1137, so it is rejected. The failure
shows that deleting selected events after decoding removes true adjacent
boundaries and cannot repair biased depth quantisation.

## Decision

Retain deterministic depth-scale geometry after structural event selection.
For graphical events on sufficiently well-calibrated pages, preserve the raw
y-to-depth projection. Values close to an integer remain snapped; other values
retain calibrated decimal precision. Integer radius, decimal precision, and
maximum scale residual are selected using only the other outer source folds.
The final external model is trained on all v001 development groups and frozen
before any BGS v002 extraction evaluation.

## Evidence

Five-fold source-disjoint development reached boundary precision/recall/F1
0.6949/0.2234/0.3381 and interval F1 0.1797 at ±0.05 m. At ±0.10 m, boundary
precision/recall/F1 were 0.7203/0.2316/0.3505. The selective threshold 0.60
accepted 46 boundaries at precision 0.9565, reference-relative coverage
0.1253, and CNER 0.0435. Page and bbox provenance was present for 118/118
selected boundaries.

These results pass all five ADR-015 release conditions. The final all-v001
geometry parameters are an integer snap radius of 0.10 m, two retained decimal
places, and maximum page-scale RMSE of 0.08. The development artifact SHA256 is
`81a962a8211d2b1a4de60d0b420d8100d8dbe07039f3e05693428d78a57f5e11`.
The serialized external model is
`experiments/paper2/models/bgs_layout_column_geometry_v023.json` with SHA256
`1aa0389ae520c62115e6c6e737727d694937b6e9c0cdb36971137b95af169db4`.

## Consequences

- v023 replaces v022 as the frozen development candidate.
- BGS v002 becomes eligible for its single predeclared external evaluation only
  after the serialized model and this ADR are committed.
- No threshold, feature, prompt, or geometry change may follow inspection of
  v002 without demoting it to validation and freezing a new external source.
- The method claim is continuous geometry recovery after structural grounding,
  not generative guessing of critical depths.

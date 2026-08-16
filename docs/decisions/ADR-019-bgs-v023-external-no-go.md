# ADR-019: BGS v023 external result is a no-go

Date: 2026-08-16

Status: `NO_GO`; BGS v002 consumed and closed.

## Context

ADR-018 froze v023 after it passed every predeclared BGS v001 development gate.
Commit `9ce6fd6` fixed the candidate model, semantic-column gate, full and
selective thresholds, continuous-depth parameters, and provenance policy before
the first BGS v002 extraction evaluation.

The external set contains three unseen source titles, four evaluation pages,
49 official intervals, and 52 unique boundaries. Prediction generation was
completed before references were accessed for scoring. No v002 result was used
for feature, threshold, or model selection.

## Result

At ±0.05 m, boundary precision/recall/F1 were
0.0227/0.0385/0.0286, interval F1 was 0, and CNER was 0.9773. The frozen
selective threshold accepted 50 boundaries but achieved precision 0.0400 and
CNER 0.9600. Provenance remained complete for 88/88 full-sequence outputs.
Inference after source OCR took 1.600 s/page and peaked at 206,792 KiB RSS.

The result artifact SHA256 is
`6e01d60b2be0328652658169276c4606fbfb7abd6297a58d4bf727eaf9258ee1`.

## Decision

Reject the claim that v023 restores unseen-source structural generalization.
The source-disjoint development gain is retained as development evidence only.
BGS v002 is now consumed and must not be reused as an external test. Its
document-level errors cannot drive a revised method unless v002 is explicitly
demoted to validation and a new v003 external set is frozen first.

## Consequences

- Paper II must report this failed confirmation, not only v001 development.
- The next method route requires independent development sources with stronger
  column-role/event supervision and a newly frozen external source.
- Selective confidence from v001 is not transportable under this source shift;
  calibration and abstention require explicit out-of-domain safeguards.
- Complete provenance does not compensate for incorrect structural inference.

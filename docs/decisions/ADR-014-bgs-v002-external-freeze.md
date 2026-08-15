# ADR-014: BGS v001 Development Role and v002 External Freeze

Date: 2026-08-15

## Decision

The 26-source-group BGS Offshore v001 benchmark is now development and failure-
attribution evidence for the long-page/layout-aware method. Its aggregate and
document-level failures have already been inspected, so it cannot serve as a
new unseen-source confirmation for that method.

A separate v002 freeze contains only source titles and record IDs absent from
v001. Page location uses a reference-blind low-DPI OCR semantic locator when a
PDF has no native `BH_COMP_LOG` marker. The source interval rows are not read by
the locator or extraction method. v002 is frozen before the new layout-aware
parser is evaluated and must be run once without threshold or prompt changes.

## Consequences

- BGS v001 results remain valid Paper I evidence of existing-method failure.
- New Paper II development may use v001 images, OCR, and reference intervals.
- BGS v002 is the external generalization check; any post-v002 tuning requires
  a v003 source-disjoint freeze.
- The v002 sample is small because only three of the four remaining eligible
  source groups exposed locatable composite-log pages. Its result must be
  reported with the exact 3-document/49-interval denominator.

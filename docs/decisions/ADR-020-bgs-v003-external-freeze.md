# ADR-020: BGS v003 replacement external freeze

Date: 2026-08-16

Status: `FROZEN_UNOPENED`.

## Context

BGS v002 was consumed by the failed v023 confirmation. The BGS eligibility
query contains 30 source-title groups under the current interval and licence
criteria: 26 entered v001 development and three entered v002. The final unused
group uses legacy `BH_LOG` page identifiers rather than `BH_COMP_LOG`, so the
generic composite-page locator did not retain it.

The remaining PDF was inspected only to identify which pages are geological
log tables. Pages 2--6 contain the continuous geological log with explicit
`Thickness` and `Depth from Surface` columns; pages 7--8 are drilling daily
reports and page 1 is a cover sheet. No interval values were used to select the
five evaluation pages.

## Decision

Freeze `BGS_OFFSHORE_1951578` as BGS v003 before any post-v002 method change.
The set contains one unseen source title, one eight-page PDF, five evaluation
pages, and seven official intervals. It excludes every v001/v002 record and
source title.

Manifest SHA256:
`12f683ca0312740dbeb68ee3bebcd92b0a0644dce22de92115c46c8faf2236d4`.
Split SHA256:
`d6a2160ea74a65c70b3a0df3d8ad2da10629e88bf12ddea46e6dceaa805be56e`.
Source PDF SHA256:
`6872000cca59c7d528479901f9401214d2cadb94b2d5cc6a6dba039d788ab3e3`.

## Consequences

- v003 must remain unopened until a revised method is frozen on sources other
  than v002/v003.
- v003 is a very small one-source confirmation and cannot by itself establish
  population-level generalization.
- The explicit page override is acquisition metadata, not a learned layout
  parameter, and must be disclosed with the five-page denominator.
- Original pages remain internal pending the pre-submission rights review.

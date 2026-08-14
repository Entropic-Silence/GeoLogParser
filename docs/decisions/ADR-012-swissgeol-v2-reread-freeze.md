# ADR-012: Freeze the Swissgeol v2 reread policy before v003 held-out evaluation

Date: 2026-08-14

Status: Accepted

## Context

The v1 policy missed all three incorrect documents in the incremental v002
held-out test. A new v003 source freeze was therefore divided by salted PDF
content hash before further development. Only its 37-document/85-interval
development partition was evaluated while designing the successor policy; the
35-document/80-interval held-out partition remained unrun.

Development errors exposed three recurring evidence patterns: OCR table borders
between a boundary and material text, `O` read instead of zero in a leading
range, and complementary interval rows across PSM-3, PSM-4, and high-resolution
views. The old acceptance rule also preserved spurious first-pass splits even
when the peer reader and repeated high-resolution views agreed on a complete
sequence.

## Decision

Freeze policy `v2` with the following changes:

- parse leading boundary values followed by OCR table-border underscores or
  vertical bars;
- normalize a leading `O` to zero only in an explicit numeric range pattern;
- retain the v1 empty-section, suspicious-range, and reader-disagreement
  triggers, with an additional non-zero-top trigger;
- accept a changed sequence only when the PSM-4 peer sequence is contiguous
  from zero and either has at least two identical high-resolution readings or
  is completely covered by complementary first-pass and repeated high-
  resolution interval evidence;
- otherwise preserve the first pass and emit `NEEDS_REVIEW` when triggered.

The v003 development run produced first-pass F1 `0.9467455621` and final F1
`0.9880952381`. Three accepted rereads corrected three development documents;
development FCR was `0/3`. These values are development evidence only and must
not appear as held-out method performance.

## Consequences

The code, parser normalization, trigger set, acceptance rules, tests, and this
ADR must be committed before the v003 held-out manifest is passed to any model
runner. No further policy change may be evaluated on that held-out partition and
reported as an independent estimate. If v2 fails, the result remains reportable
and another untouched dataset or preregistered split is required for v3.

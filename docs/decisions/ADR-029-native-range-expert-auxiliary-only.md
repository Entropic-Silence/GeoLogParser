# ADR-029: Native range expert remains auxiliary

Date: 2026-08-16  
Status: `ACCEPT_AUXILIARY_ONLY`

## Evidence

The native PDF branch was extended to parse explicit range tokens such as
`0-40m` and `40-250m`. On the Thurgau layout development split it selected
16/37 documents (coverage `0.4324`) and reached Boundary/Interval F1
`0.4000/0.3590`. On the corresponding 35-document held-out split it selected
19/35 documents (coverage `0.5429`) and reached `0.4943/0.3833`.

The already-frozen OCR plus constraint-rereading run on the same held-out
split reached Boundary/Interval F1 `0.9502/0.9211` and 29/35 exact final
documents. The native branch therefore supplies useful independent structural
evidence and abstention behavior, but it is not a replacement for the current
primary extraction path.

On the BGS v001 development manifest, all 26 native predictions abstained
(coverage `0.0`). This is expected for raster/scanned pages and confirms that
the native branch cannot be presented as a universal cross-source solution.

## Decision

Retain explicit-range and positioned-text extraction as a routed auxiliary
expert for native PDFs. Do not merge its predictions unconditionally into the
OCR+constraint output and do not promote it as the Paper II primary method.
Its evidence may trigger review, explain a numeric field, or provide a safe
candidate when the primary path lacks a structural column.

The next Paper II method work must target raster/scanned pages through
reference-blind graphical boundary grounding, scale reconstruction, and
field-role evidence. BGS v003 remains frozen and unopened.

## Evaluation caveat

The Thurgau held-out artifacts were already used by earlier frozen constraint
experiments; this comparison is a descriptive validation of the new branch,
not an untouched external claim. The manifest is authoritative source-table
agreement, not project human annotation.

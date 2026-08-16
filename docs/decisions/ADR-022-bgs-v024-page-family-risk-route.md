# ADR-022: Route heterogeneous BGS pages by structural family and risk

Date: 2026-08-16

Status: `ACCEPT`

## Context

The frozen v023 geometry method reached boundary F1 0.3381 and interval F1
0.1797 on source-disjoint BGS v001 development, but failed on the consumed
BGS v002 external set. Corrected-page validation confirmed that the failure was
structural: a long scaled log produced 2,021 candidates and 87 false boundary
outputs, a graphical contact log produced no candidates, and an explicit
thickness/depth table was not recognized.

## Decision

Paper II v024 introduces a reference-blind page-family router with four routes:

1. `explicit_depth_range_table`: high-resolution, table-column range parsing;
2. `scaled_composite_log`: existing geometry route subject to structural-risk
   gates;
3. `graphical_contact_log`: existing geometry route subject to the same gates;
4. `unsupported`: document-level abstention.

Candidate explosion is not sufficient by itself to reject a development page.
The document is rejected only when candidates exceed 1,000 per page and the
baseline output is either at least 40 boundaries or at least 3% of candidates.
This preserves source-disjoint development coverage while rejecting the BGS
v002 long-log failure pattern. Explicit parsing is accepted only when a
zero-starting contiguous sequence of at least three ranges is recovered.

## Evidence

- BGS v001 development v024: boundary precision/recall/F1
  `0.6897/0.2180/0.3313`, interval F1 `0.1801`, CNER `0.3103`.
  v023 comparison was boundary F1 `0.3381`, interval F1 `0.1797`.
- Corrected BGS v002r2 validation: four true boundaries recovered from the
  explicit range table with no false positives; the long-log page and the
  zero-evidence page were rejected. Overall boundary precision/recall/F1 was
  `1.0000/0.0769/0.1429`, interval F1 `0.1154`, and CNER `0.0000`.

## Consequence

The route is a reliability and abstention improvement, not a demonstrated
replacement for v023 on the development source. It must not be promoted to the
Paper II primary method without a new independent development source showing a
material structural-recall gain. BGS v003 remains frozen and unopened.

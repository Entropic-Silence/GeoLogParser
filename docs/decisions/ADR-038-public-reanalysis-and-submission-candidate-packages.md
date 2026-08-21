# ADR-038: Public reanalysis inputs and submission-candidate package semantics

Date: 2026-08-17

## Context

The major-revision audit identified three reproducibility gaps:

1. Paper II's core same-candidate-pool ablation could not be recomputed from public inputs.
2. Paper III's spatial diagnostics could be redrawn from frozen JSON but not recomputed without controlled coordinates.
3. Packages labelled SUBMISSION_READY could be mistaken for manuscripts that had passed rights, author, and journal-specific checks.

The Paper III public-coordinate transform also exposed numerical origin dependence in the original convex-hull grid construction. With only three deep-boundary support points, floating cancellation at projected coordinates of order one million metres changed edge inclusion after deidentification.

## Decision

- Release a pseudonymized Paper II candidate pool containing normalized geometry, sequence scores, reference intervals, and stable salted keys, but no OCR text, raw bbox, source ID, or path. Exact depth sequences remain linkable to public tables, so anonymity is not claimed.
- Release a Paper III input obtained by centroid subtraction, rigid rotation, and vertical-origin subtraction, with no source ID or absolute origin.
- Evaluate polygon area and hull-clipped grids in a local coordinate frame, use scale-aware edge tolerance, and treat sub-micrometre coordinate differences as identical IDW support.
- Regenerate Paper III sensitivity values from the stabilized implementation. The reanalysis, rather than the earlier origin-sensitive point estimate, supplies the manuscript headline.
- Use SUBMISSION_READY_CANDIDATE only when scientific/evidence audits pass. Keep submission_ready=false until rights, authorship, disclosures, journal format, and final human review are complete.
- Render unavailable or inapplicable table cells as N/A, not TBD. TBD remains reserved for genuinely unrun manuscript work.

## Consequences

- Paper II's 200 documents and 2,225 candidates can be reanalysed without source PDFs.
- Paper III's 35 transformed records reproduce the main support, volume, LOO, and jackknife diagnostics without revealing an absolute origin.
- Stabilized Paper III full-support raw/reread/risk volume errors are 0.1387/0.1213/0.0821; matched-subset values remain 0.0326/0.0754/0.0754.
- Existing immutable formal run files remain unchanged; the versioned post-hoc sensitivity analysis is explicitly the source of the revised manuscript values.
- Scientific completeness is distinct from legal and editorial readiness.

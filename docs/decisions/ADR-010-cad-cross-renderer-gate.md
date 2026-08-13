# ADR-010: Keep CAD candidates quarantined after renderer disagreement

- Status: accepted
- Date: 2026-08-13

## Context

Three automatically prioritized Chinese DWGs have exact source-DWG versus
derivative-DXF graphical-entity and ordered-text inventory agreement. That
structural result does not verify pixels. The installed LibreCAD 2.1.3 help
exposes only file opening/debug options, and isolated offscreen probes stay in
the GUI event loop until terminated without creating an export.

Two available raster chains were audited independently. For
`MENDELEY_DWG_009` and `MENDELEY_DWG_010`, the LibreDWG-SVG chain produced an
explicit invalid-geometry placeholder, so no comparison is valid. For
`MENDELEY_DWG_011`, both rasters are nonblank, but normalized foreground IoU is
0.0005905677887454653 and the two-pixel-tolerance bidirectional F1 is
0.003955665965985095. These are technical occupancy diagnostics, not fidelity
metrics or model results.

## Decision

Keep all three drawings quarantined and `benchmark_eligible: false`. Do not
extend the LibreCAD 2.1.3 GUI route with brittle menu automation. Require a
renderer/exporter with an explicit batch interface or a documented human CAD
export, followed by human visual, font, privacy, location-sensitivity, and
third-party-content review. Do not count any DWG or derivative as a Paper I
page before those gates and human annotation are complete.

The canonical technical artifact is `priority_renderer_audit_v003`, manifest
SHA256 `51173c63c25dbe3f47a339a6f4a3429faed1e622bf63339cd2cd770ff4dca4d9`.
It records the audit-script hash and verifies the upstream DXF hashes. The
immutable v001 artifact is retained under a `superseded` name because its
nearest-neighbour downsampling could erase one-pixel CAD lines; v002 is retained
as the corrected-algorithm predecessor to v003.

## Consequences

The project has stronger negative evidence about this conversion route but no
new Chinese Benchmark pages, Ground Truth, or formal Paper I results. Effort
returns to rights-clear PDF/JPG/PNG discovery and human annotation of already
prepared public international pages unless a better CAD renderer becomes
available.

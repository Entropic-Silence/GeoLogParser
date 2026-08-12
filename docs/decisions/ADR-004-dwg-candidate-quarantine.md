# ADR-004: Quarantine licensed DWG candidates before page-image inclusion

- Status: accepted
- Date: 2026-08-12

## Context

The Mendeley Data item `10.17632/vcpz47r3sv.2` is CC BY 4.0 and contains 33
DWG files. GeoLogParser phase 1, however, accepts PDF/JPG/PNG, and repository
licensing alone does not establish that every embedded title block, location,
or third-party element is safe to redistribute.

A single-file audit used LibreDWG 0.14 source release SHA256
`62ebb73b984f865960f20ed26619ea5f8789d5e3fd088fa40a2598384da81275`.
The selected DWG SHA256 was
`061e30744086a5eda84ca8f88dacc6fbff254ca54290d9be907886f9eaf084e3`.
DWG-to-SVG confirmed Chinese geological descriptions and a borehole column,
while the converter warned `MTEXT ignored`. JSON inspection also found a named
company and named mining-area/project title. No claim is made about the other
32 drawings.

## Decision

Keep the archive and derived audit artifacts under `/data/GeoLogParser` and
set `benchmark_eligible: false`. Do not count DWG files as phase-1 pages. A
future inclusion decision requires all of the following:

1. deterministic conversion with converter version and hashes recorded;
2. visual and extracted-text review of every candidate drawing;
3. anonymization or exclusion rules for companies, projects, coordinates, and
   sensitive locations;
4. third-party-content screening and attribution plan;
5. validation that ignored/unsupported CAD entities do not remove ground-truth
   evidence; and
6. explicit creation of a versioned PDF/PNG derivative dataset.

## Consequences

The collection can inform schema and acquisition planning now, but cannot
support Paper I accuracy, scale, template-diversity, or Chinese benchmark
claims. Any future derivatives must retain source hashes and conversion
provenance.

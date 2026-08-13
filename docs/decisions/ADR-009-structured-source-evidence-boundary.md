# ADR-009: Keep structured source data separate from extraction evidence

- Status: Accepted
- Date: 2026-08-13

## Context

Some licensed public repositories release XLSX/CSV borehole records rather
than legacy PDF/JPG/PNG logs. These records can support Paper III protocol
development, but they do not show that GeoLogParser extracted a document
correctly. They also may contain coordinates whose reference system, privacy,
or sensitivity has not been reviewed.

The public coal-borehole workbook further demonstrates why generic vertical
interval rules cannot be applied blindly to directional drilling fields. A
reported final drilled length, roof intersection depth, and seam thickness do
not necessarily share the interval semantics assumed by C1-C5.

## Decision

Every structured-data audit declares exactly one source role. Current public
workbooks use `source_structured_data`. This role is distinct from:

- `ai_extraction_output`;
- `human_ground_truth`;
- `constraint_validated_ai_output`.

Structured source data may be used to design database, geometry, perturbation,
and export protocols. It may enter a formal downstream experiment only after
its experiment-specific gates pass. Those gates include field semantics, CRS,
units, privacy/sensitive-location review, and a frozen protocol.

No structured-source row may be counted as a document page, annotation, Ground
Truth page, or successful extraction. A comparison between structured source
data and synthetic perturbations cannot establish OCR/VLM accuracy or the
benefit of constraint validation.

Source-field checks whose semantics are uncertain are reported as observations,
not violations. In particular, no automatic correction is authorized from a
cross-field relation until the fields' physical reference definitions are
documented.

Constraint results use three explicit states: `passed`, `violated`, and
`not_evaluated`. A not-evaluated result retains `passed=true` only for backward
compatibility, but its score is null and its evaluated count is zero. It must
not contribute a successful check to consistency metrics.

## Consequences

- Paper III can develop against real, licensed tabular records without leaking
  those rows into Paper I or Paper II claims.
- Formal Paper III `Raw AI vs QC vs Human GT` results remain blocked until an
  image-derived, human-verified extraction cohort exists.
- Audit manifests bind conclusions to exact acquired-file hashes and preserve
  superseded audits rather than overwriting them.
- Dataset suitability may become narrower after content inspection; repository
  abstracts are not treated as file inventories.

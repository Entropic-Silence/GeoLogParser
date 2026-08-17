# ADR-040: Modern VLM Assurance-Gap Research Direction

Date: 2026-08-17

## Context

Under the frozen direct page-to-JSON protocol, Qwen3.8-27B-FP8 obtained
California Gold interval F1 of 0.932 (v001), 0.896 (v002), and 0.918 (v003),
with document-boundary exact rates of 0.740, 0.700, and 0.720. A broad claim
that end-to-end VLMs cannot read borehole intervals is therefore false for this
standardized source family.

The same runs also expose an operational distinction. They provide direct
interval text and page-level response provenance, but the frozen direct JSON
interface has no field-level bbox, no calibrated field confidence, no
accept/review decision, and no retained constraint trace. It emitted malformed
numeric ranges at rates 0.0094, 0.0071, and 0.0043 before deterministic range
rejection. These are interface observations, not claims that the base model
cannot produce grounding or confidence under a different prompt.

## Decision

Reframe the system-level research gap as **assured conversion of strong VLM
proposals into reviewable geological database records**, rather than as a
claim that a routed OCR parser must beat every modern VLM on raw interval F1.

The prospective extension, if pursued, must be a VLM-proposal assurance layer:

1. retain the direct VLM proposal unchanged;
2. attach field-specific visual evidence only through an independently
   reproducible positioned-text or visual anchor;
3. apply deterministic numeric, sequence and geological constraints;
4. accept only a documented subset, otherwise emit `NEEDS_REVIEW` without
   silently repairing the VLM proposal;
5. measure evidence coverage, critical numerical error, selective precision,
   coverage, review burden and document-level harm separately from raw F1.

No Gold cohort beyond v001 may be used to tune this layer. v002 is validation
only; v003-v005 must remain unread for development until a fixed implementation
and operating policy are registered. BGS v003 remains permanently excluded.

## Go/No-Go Gate

The extension is eligible for a held-out California evaluation only when a
synthetic-plus-v001 development study demonstrates all of the following:

- source-field evidence coverage of at least 0.70 among proposed critical
  depth fields;
- no increase in deterministic critical-numeric invalidity after acceptance;
- a predeclared, non-zero coverage operating point with higher selective
  precision than the unfiltered VLM proposal; and
- page-level provenance, field geometry, constraint outcomes and decision
  reasons serialized per output record.

Failure of any gate closes the extension. The completed direct-VLM benchmark
remains valid and is reported without using this proposed layer.

## Consequences

Paper I becomes stronger as a provenance-aware evaluation: high direct-VLM F1
on one source family does not establish auditable or risk-controlled database
delivery. Paper II retains ownership of the decision and correction-safety
problem. Any new VLM-assurance result is reported as a separately versioned
extension, never retroactively as a property of the frozen direct baseline.

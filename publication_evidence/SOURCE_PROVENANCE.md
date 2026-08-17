# Source provenance requiring final author verification

Date frozen: 2026-08-17

The publication bundle includes privacy-minimized assertion projections derived
from the sources below. It does not include source inventories, source PDFs,
page images, model inputs, coordinates, or full structured databases. Before
public release or manuscript submission, the
author must verify the exact item-level licence, attribution, redistribution,
privacy, and sensitive-location scope recorded in
`datasets/source_verification_ledger.yaml` and `docs/submission_blockers.md`.

The document-level and reanalysis projections are pseudonymized or transformed,
not anonymous. Exact depth-sequence lookup links 198/200 Paper II records
uniquely within the released cohort manifests, and rigid distance fingerprints
link all 35 Paper III points to the matching original point set. Aggregate
diagnostics are recorded in `analysis_inputs/linkage/`; no record mapping is
released. Rights and sensitive-location review must explicitly account for
this linkability.

Included summary families:

- BGS metadata robustness inventory.
- Mendeley borehole-log CAD conversion/fidelity inventories.
- Padova panel, annotation-assignment, degradation, and spatial inventories.
- Mendeley SedLog, subsurface-slope, and Tiber content summaries.
- International and SedLog source-review status summaries.
- Mendeley coal-borehole structured-content audit.
- Sanming quarantine database aggregate row counts only; database records are
  not redistributed.

Each projection retains the SHA-256 of its original local evidence file in
`papers/claim_registry.json` (`origin_source_sha256`) and in
`publication_evidence/manifest.json`. It exposes only the values used by
registered manuscript assertions and is not a substitute for the controlled
source evidence.

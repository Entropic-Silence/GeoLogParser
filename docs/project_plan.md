# Project plan

## Current objective

Convert the completed research foundation into a rights-cleared, manually
verified Chinese benchmark and execute Paper I B1–B6. In parallel, mature the
already implemented Paper II/III method and workflow components without making
empirical claims before suitable labels and spatial data exist.

## What existed at start

No `/root/GeoLogParser` repository existed on 2026-08-12. The host had active
AI/mining services and model assets for other projects, but no identified
GeoLogParser code, document OCR stack, or suitable benchmark model weights.

## What was missing

All project-specific schemas, adapters, tests, manifests, data-license records,
experiment metadata, prompts, baselines, and paper planning were missing.

## Phased execution

1. **Foundation:** environment, scope, schema, constraints, baseline interfaces,
   evaluation primitives, and registry.
2. **Public-data smoke test:** legally usable samples, real document runs, error
   logging, and schema stabilization.
3. **Paper I data and benchmark:** annotation tool, QC, leakage-resistant splits,
   baselines, robustness, and error analysis.
4. **Paper II method:** C1–C10, re-reading, ranking, calibration, abstention, and
   ablations.
5. **Paper III workflow:** spatial database, exports, 3D workflow, error
   propagation, and human-efficiency study.

## Storage and compute

- `/root/GeoLogParser`: source, tests, docs, small schemas/manifests, active
  experiment configs, and small logs requiring low-latency access.
- `/data/GeoLogParser`: downloaded/restricted source documents, model weights,
  caches, preprocessed pages, crops, and large experiment artifacts.
- GPU mining is paused only for a scheduled model run and restored after the
  run. No GPU workload is needed for the foundation phase.

## Reproducibility gates

- A schema change requires a version bump or backward-compatibility decision.
- Every constraint/numeric metric requires tests.
- Every experiment gets a unique ID and immutable result directory.
- Every paper number is generated from saved outputs; absent results are `TBD`.
- Dataset access, license, redistribution, citation, and access date are logged
  before ingestion.

## Status audit — 2026-08-12

- Phase 0 environment/repository/experiment framework: **COMPLETED**.
- Phase 1 v001 Schema and synthetic examples/tests: **COMPLETED**.
- Phase 2 public data validation: BGS and Padova audit samples **COMPLETED**;
  one CC BY Chinese DWG collection acquired and automatically pre-screened,
  but its priority derivatives show unresolved cross-renderer disagreement and
  remain quarantined/incomplete; a diverse
  rights-cleared Chinese page-image benchmark is **NOT COMPLETED**.
- Phase 3 baselines: Tesseract+regex, RapidOCR+regex, B2 text-only local LLM,
  B3 positioned-text layout, B4/B5 VLM, and conservative B6 engineering audits
  **COMPLETED** on public/quarantined audit inputs; GT-based formal comparison
  **NOT COMPLETED**.
- Phase 4 evaluation API, boundary matching, coverage and calibration metrics:
  **COMPLETED v001**; configurable critical-numerical-error, normalized text
  similarity, hierarchical auxiliary, and auto-accept-risk metrics are now
  implemented, subject to dataset-driven threshold/ontology validation.
- Phase 5 annotation backend/UI and auto proposals: **COMPLETED v001**; a
  separate revisioned CAD privacy/content-review UI and eligibility gate are
  **COMPLETED v001**. The primary UI reports exact GT-gate/progress status,
  labels per-page exports as draft until eligible, and refuses incomplete GT
  collection export. Record-hash attestations now prevent unsupported double/
  expert status. A two-track, full-overlap Padova assignment has been frozen
  with service-level reviewer allowlists and pre-adjudication comparison gates;
  both tracks remain unassigned `auto` seeds. Actual manual/double/expert
  geological annotations are **NOT COMPLETED**.
- Phase 6 Paper I benchmark/splits/degradation/failure analysis: infrastructure
  **PARTIAL**; publishable data and experiments **NOT COMPLETED**.
- Phase 7 C1–C10: **COMPLETED v001** with tests.
- Phase 8 constraint-guided ROI rereading/ranking: **COMPLETED v001** with
  controlled tests and annotation-UI numeric OCR re-reading. Every UI run is
  hash-traceable and non-mutating until explicit human confirmation. A VLM ROI
  adapter and human-GT multimodal field trial are **NOT COMPLETED**.
- Phase 9 Paper II experiments/ablations/calibration/FCR: **NOT COMPLETED**.
- Phase 10 database/export: SQLite/CSV/JSON/XLSX/Parquet/GeoJSON/GeoParquet/
  GeoPackage **COMPLETED v001**; a validated interval-bearing spatial case is
  **NOT COMPLETED**. A source-coordinate-only Padova snapshot exists with all
  coordinate fields marked unverified/needs-review.
- Phase 11 3D/error propagation: IDW synthetic single- and 30-seed protocol
  runs and a hash-indexed PyVista/VTP interoperability run are **COMPLETED**;
  GemPy integration and a real human-verified 3D workflow are **NOT COMPLETED**.
- Phase 12 Paper III downstream/human study: **NOT COMPLETED**.
- Paper manuscripts: complete sectioned research drafts with generated audit
  tables and honest `TBD`; final publishable papers **NOT COMPLETED**.

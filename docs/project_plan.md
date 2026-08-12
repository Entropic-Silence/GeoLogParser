# Project plan

## Current objective

Establish a tested, traceable research foundation without model training:
environment snapshot, repository, schema, constraints, data registry, minimal
baseline, evaluation API, and paper boundaries.

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


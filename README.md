# GeoLogParser

GeoLogParser is a research-grade, modular pipeline for converting heterogeneous
legacy borehole logs into traceable structured geological data.

The current milestone is deliberately narrow:

```text
single borehole-log PDF/JPG/PNG -> JSON/CSV
```

This repository contains executable engineering baselines and immutable audit
runs. It does **not** yet contain a rights-cleared Chinese benchmark, a trained
project model, or publishable headline results. Unrun experiments and unknown
quantities are reported as `TBD`.

## First-round capabilities

- Borehole JSON Schema v001 with source/display bboxes and field provenance.
- Ten non-mutating geological constraints (C1–C10).
- Tesseract and RapidOCR adapters, mixed/native/scanned PDF routing, panel-aware
  native text extraction, and conservative layout/regex extraction.
- Boundary-aware interval matching, constraint coverage, ECE/Brier, review
  queue, confidence fusion, and temperature calibration primitives.
- Constraint-guided ROI rereading and abstaining candidate ranker.
- Revisioned local annotation UI with evidence highlighting and timing events.
- Revisioned CAD privacy/content-review gate and traceable DWG→DXF→PNG audit
  derivatives, kept outside the phase-1 input contract.
- SQLite/CSV/JSON/XLSX/Parquet/GeoJSON/GeoParquet export and a transparent
  multi-seed synthetic IDW propagation protocol.
- Immutable experiment indexes and generated three-paper result tables.

## Storage policy

Code, tests, schemas, prompts, small manifests, and experiment metadata live in
this repository on SSD. Large datasets, weights, caches, and generated
artifacts live under `/data/GeoLogParser` on the mechanical RAID array. No
dataset is redistributed merely because it appears in the registry.

## Development

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
```

Optional document backends are installed separately:

```bash
python -m pip install -e '.[pdf,ocr]'
python -m pip install -r requirements-ocr-rapidocr.txt
python -m pip install -r requirements-annotation.txt
python -m pip install -r requirements-export.txt
python -m pip install -r requirements-cad-audit.txt  # acquisition audit only
```

See `docs/environment_report.md`, `docs/research_scope.md`, and
`docs/project_plan.md` before adding a model or dataset.

Current limitations are explicit: rights-cleared Chinese benchmark pages and
manual/expert Ground Truth are `NOT COMPLETED`; B2–B6 have engineering audits
but no GT-based formal comparison; Paper II empirical ablations and Paper III
real-site/human studies are also `NOT COMPLETED`.

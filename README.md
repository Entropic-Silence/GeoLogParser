# GeoLogParser

GeoLogParser is a research-grade, modular pipeline for converting heterogeneous
legacy borehole logs into traceable structured geological data.

The current milestone is deliberately narrow:

```text
single borehole-log PDF/JPG/PNG -> JSON/CSV
```

This repository contains executable baselines, immutable audit runs, three
evidence-linked manuscript candidates, and generated review packages. The
current papers use published manual-transcription references and authoritative
source-agreement references; no project-created human Ground Truth is claimed.
Source licence, privacy, and redistribution checks remain a separate
pre-submission gate.

The machine-derived scientific-content gate is
[docs/generated/publication_readiness.md](docs/generated/publication_readiness.md).
It excludes audit-only, failure-analysis, and protocol-only runs from formal
paper evidence. The top-level package manifest deliberately keeps
`all_submission_ready=false` until [docs/submission_blockers.md](docs/submission_blockers.md)
is signed off.

The closure evidence trail is summarized in
[docs/claim_evidence_matrix.md](docs/claim_evidence_matrix.md) and
[docs/manuscript_closure_audit.md](docs/manuscript_closure_audit.md).
The compact, clone-verifiable evidence subset is documented in
[publication_evidence/README.md](publication_evidence/README.md). It contains
exact run metadata, aggregate metrics, and selected pseudonymized document-level
predictions/errors, but not restricted source pages, raw OCR regions, or model
weights. Distinctive depth sequences and rigidly transformed coordinates remain
linkable to public records; the bundle does not claim anonymity.

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
artifacts live under `/data/GeoLogParser` on the mechanical RAID array. The
formal source inputs needed for the principal paper experiments are published
as the portable data companion release `data-v002`; see
[`datasets/public/dataset_bundle_v002/README.md`](datasets/public/dataset_bundle_v002/README.md).
The historical `data-v001` prerelease is superseded and is not DOI-ready.
Duplicate freezes, failed branches, model weights, and quarantine-only sources
remain outside the release. The release manifest and source ledger preserve
the evidence tier, attribution, and final-author rights-review status for every
file. The complete Paper 4 code, manuscript, figures, evidence, and audits are
fixed by `paper4-cageo-v1.0.6`; the data companion does not replace that tag.

## Development

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
pytest
python scripts/build_publication_evidence.py
python scripts/regenerate_publication_artifacts.py --publication-core
python scripts/build_paper_packages.py
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

Current limitations are explicit: there is no project-created human annotation
study, the Chinese/DWG candidates are benchmark-ineligible, BGS v003 is a
consumed zero-coverage external failure, and Paper III reports a downstream IDW
diagnostic rather than validated production geology or human time savings.

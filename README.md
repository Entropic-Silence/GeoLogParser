# GeoLogParser

GeoLogParser is a research-grade, modular pipeline for converting heterogeneous
legacy borehole logs into traceable structured geological data.

The current milestone is deliberately narrow:

```text
single borehole-log PDF/JPG/PNG -> JSON/CSV
```

This repository does **not** contain a trained model or a benchmark result yet.
Unrun experiments and unknown quantities are reported as `TBD`.

## First-round capabilities

- Borehole JSON Schema v0.0.1 with field-level provenance.
- Five non-corrective geological constraints.
- Adapter-based OCR/direct-PDF-text baseline and conservative regex extractor.
- Model-independent evaluation primitives.
- Dataset licensing registry and three-paper research roadmap.

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
```

See `docs/environment_report.md`, `docs/research_scope.md`, and
`docs/project_plan.md` before adding a model or dataset.


# Annotation/review application

Current status: backend primitives for panel rendering and revisioned annotation
storage are implemented and tested. A manifest can split a multi-borehole PDF
page into independent visual panels while retaining page, normalized crop,
source SHA256, rendered SHA256, and rights status.

Run panel rendering with:

```bash
.venv/bin/python scripts/render_annotation_panels.py \
  configs/datasets/sanming_quarantine_panels_v001.jsonl \
  /data/GeoLogParser/artifacts/annotation/sanming_quarantine_v001
```

The Sanming manifest is internal quarantine material and cannot be released or
counted in the benchmark. Build proposals and start the local UI with:

```bash
.venv/bin/python scripts/build_annotation_proposals.py \
  /data/GeoLogParser/artifacts/annotation/sanming_quarantine_v001/panel_manifest.jsonl \
  /data/GeoLogParser/artifacts/annotation/sanming_quarantine_v001/annotations
.venv/bin/uvicorn app.server:app --host 127.0.0.1 --port 8000
```

The rights-cleared Padova public annotation pack can be generated and opened
without mixing it with quarantined Chinese material:

```bash
.venv/bin/python scripts/build_unipd_annotation_pack.py \
  --source-manifest /data/GeoLogParser/datasets/public/unipd_levee_geotech_v001/metadata/manifest.jsonl \
  --output-root /data/GeoLogParser/artifacts/annotation/unipd_levee_geotech_v001
GEOLOGPARSER_ANNOTATION_ROOT=/data/GeoLogParser/artifacts/annotation/unipd_levee_geotech_v001/annotations \
  .venv/bin/uvicorn app.server:app --host 127.0.0.1 --port 8000
```

The UI provides panel switching, header/interval editing, evidence inspection,
Schema + C1–C10 validation, review queue, append-only timing events, and
conflict-safe revisioned saves. Native-PDF proposal builders store both source
PDF points and transformed rendered-pixel bboxes, so eligible evidence is
highlighted in the displayed panel. Standalone CSV/XLSX/Parquet exporters are
implemented in the library; UI export buttons and interactive field re-reading
remain `NOT COMPLETED`.

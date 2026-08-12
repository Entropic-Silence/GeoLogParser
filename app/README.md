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

The UI provides panel switching, header/interval editing, evidence inspection,
Schema + C1–C10 validation, workflow status, and conflict-safe revisioned saves.
For original native-PDF evidence, bbox is in unrotated PDF points while the UI
image is rendered pixels; until explicit transform metadata is added, clicking
such evidence shows page/source text and intentionally does not draw a false
rectangle. Pixel-space OCR bbox highlighting is implemented. Review queue,
field re-reading, and CSV/XLSX export remain `NOT COMPLETED`.

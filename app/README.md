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
counted in the benchmark. The interactive left-image/right-fields browser,
bbox click highlighting, review queue, field re-reading, and export controls
remain `NOT COMPLETED`.

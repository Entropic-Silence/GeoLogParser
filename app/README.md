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
conflict-safe revisioned saves. It now displays collection-level GT progress
and exact per-page GT-gate failures. Per-page JSON/CSV/XLSX exports are always
labelled `DRAFT_NOT_GT` until that annotation passes the human gate; the
collection JSONL endpoint refuses download unless every page passes. Native-PDF proposal builders store both source
PDF points and transformed rendered-pixel bboxes, so eligible evidence is
highlighted in the displayed panel. Standalone CSV/XLSX/Parquet exporters are
implemented in the library and exposed as review-time downloads. Interactive
field re-reading remains `NOT COMPLETED`.

After real review, create a frozen GT snapshot with:

```bash
.venv/bin/python scripts/export_verified_annotations.py \
  /data/GeoLogParser/artifacts/annotation/unipd_levee_geotech_v001/annotations \
  /data/GeoLogParser/datasets/derived/unipd_gt_v001/annotations.jsonl
```

The command deliberately fails if even one item remains `auto`; it never
promotes auto proposals to Ground Truth.

## Quarantined CAD content review

CAD derivatives use a separate UI and storage root so a privacy/content review
cannot be mistaken for geological Ground Truth annotation:

```bash
.venv/bin/uvicorn app.cad_review_server:app --host 127.0.0.1 --port 8001
```

The service verifies derivative hashes, stores revisioned human decisions, and
rejects `eligible_for_annotation` when the derivative manifest reports an
incomplete conversion. All current Mendeley priority derivatives have that
warning, so they may only be excluded, kept internal, or sent for repair and
re-review. Content review never sets `benchmark_eligible` directly.

For a non-human structural/text reconciliation of the three priority
derivatives, run:

```bash
.venv/bin/python scripts/audit_cad_conversion_fidelity.py \
  /data/GeoLogParser/datasets/public/mendeley_borehole_logs_v002/audit/priority_derivatives_v001/derivative_manifest.jsonl \
  /data/GeoLogParser/datasets/public/mendeley_borehole_logs_v002/audit/priority_derivatives_v001 \
  /data/GeoLogParser/datasets/public/mendeley_borehole_logs_v002/audit/priority_fidelity_v003 \
  /data/GeoLogParser/tools/prefix/libredwg-0.14/bin/dwgread \
  --library-dir /data/GeoLogParser/tools/prefix/libredwg-0.14/lib
```

This audit deliberately leaves human review, privacy review, and benchmark
eligibility false. A successful inventory match must not be presented as a
human visual-completeness decision.

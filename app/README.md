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
collection JSONL endpoint refuses download unless every page passes.
Native-PDF proposal builders store both source PDF points and transformed
rendered-pixel bboxes, so eligible evidence is highlighted in the displayed
panel. A reviewer may draw a tighter field bbox, use it temporarily for a
numeric ROI re-read, or bind it locally to the field. Bound boxes are marked
`human_drawn` with the saving annotator ID; they do not replace `source_bbox`,
confirm the value, or persist until the ordinary revisioned save succeeds.
SQLite/XLSX/Parquet exports preserve that display-bbox provenance.
Standalone CSV/XLSX/Parquet exporters are
implemented in the library and exposed as review-time downloads. Numeric fields
with rendered-pixel evidence can now trigger high-resolution ROI readers. The
default web process remains CPU-only Tesseract; an optional local VLM reader is
available to versioned experiment scripts and must be injected explicitly into
the API process. VLM numeric tokens carry no model confidence or token bbox
unless a later calibration/grounding experiment establishes them. Each run
freezes its crop, reader output/audit, ranking decision, source-panel hash, and
result hash under the annotation artifact root. Re-reading is
non-mutating: even an accepted candidate is applied locally as `needs_review`
and requires explicit human confirmation plus the ordinary revisioned save.
The default UI does not expose a VLM toggle; VLM use remains an explicitly
configured experiment path.

Human verification statuses are evidence-gated. A `single_verified` save adds
an attestation bound to the exact canonical record SHA256. `double_verified`
requires two distinct anonymized annotator IDs to attest the same final record;
if the second reviewer edits any field, the earlier hash no longer matches and
the edited record must be reviewed again. `expert_verified` is accepted only
for IDs explicitly configured on the server:

```bash
GEOLOGPARSER_EXPERT_ANNOTATOR_IDS=expert-anon-01 \
GEOLOGPARSER_ANNOTATION_ROOT=/data/GeoLogParser/artifacts/annotation/unipd_levee_geotech_v001/annotations \
  .venv/bin/uvicorn app.server:app --host 127.0.0.1 --port 8000
```

The UI displays the effective attestation count/IDs for the current record.
Use stable anonymized IDs; never put names, email addresses, or other personal
data into annotation metadata. With no expert allowlist configured, nobody can
self-declare `expert_verified`.

For independent duplicate annotation, generate separate tracks before either
reviewer starts. The existing Padova v001 task pack was created with:

```bash
.venv/bin/python scripts/build_blinded_annotation_pack.py \
  /data/GeoLogParser/artifacts/annotation/unipd_levee_geotech_v001/annotations \
  /data/GeoLogParser/artifacts/annotation/unipd_blinded_duplicate_v001 \
  --track track_a=padova-reviewer-a \
  --track track_b=padova-reviewer-b
```

Its assignment-manifest SHA256 is
`e4c18c84cd06c4ba599cca4e881fbc21bd5d4e6b976964462cee0438ae7508f2`.
Those IDs currently identify unassigned review tracks, not people, and create
no verification attestation. Give each actual reviewer exactly one stable
anonymous track ID and serve only that directory, for example:

```bash
GEOLOGPARSER_ANNOTATION_ROOT=/data/GeoLogParser/artifacts/annotation/unipd_blinded_duplicate_v001/tracks/track_a/annotations \
GEOLOGPARSER_ALLOWED_ANNOTATOR_IDS=padova-reviewer-a \
  .venv/bin/uvicorn app.server:app --host 127.0.0.1 --port 8011
```

Run track B from its own annotation root and a different port/process. The
allowlist prevents cross-track saves through the service interface. Both roots
still reside on a shared host filesystem, so this is not an OS security
boundary; use separate Unix accounts/permissions or supervised reviewer
sessions when adversarial access is a concern. Reviewers must not inspect peer
files before agreement is frozen.

After every page in both tracks independently passes the single-review GT gate,
freeze pre-adjudication agreement with:

```bash
.venv/bin/python scripts/compare_annotation_tracks.py \
  /data/GeoLogParser/artifacts/annotation/unipd_blinded_duplicate_v001/tracks/track_a/annotations \
  /data/GeoLogParser/artifacts/annotation/unipd_blinded_duplicate_v001/tracks/track_b/annotations \
  /data/GeoLogParser/artifacts/annotation/unipd_blinded_duplicate_v001/agreement/pre_adjudication_v001.json
```

The command refuses incomplete tracks, reused annotator IDs, and an existing
output. Agreement is measured before adjudication and is not final GT. Any
disagreement must be adjudicated separately; the exact adjudicated record must
then receive the required final attestations.

The agreement artifact includes every differing v001 field value, interval
count/ID difference, per-document record hashes, and aggregate metrics. Only
after that immutable artifact exists may the non-GT adjudication pack be built:

```bash
.venv/bin/python scripts/build_adjudication_pack.py \
  /data/GeoLogParser/artifacts/annotation/unipd_blinded_duplicate_v001/agreement/pre_adjudication_v001.json \
  /data/GeoLogParser/artifacts/annotation/unipd_blinded_duplicate_v001/tracks/track_a/annotations \
  /data/GeoLogParser/artifacts/annotation/unipd_blinded_duplicate_v001/tracks/track_b/annotations \
  /data/GeoLogParser/artifacts/annotation/unipd_blinded_duplicate_v001/adjudication/v001
```

The builder rechecks every frozen track file hash. It writes both reviewer
records and a case-level discrepancy list, but deliberately writes no
`final.json`. Differing cases are `adjudication_pending`; byte-identical records
are still `confirmation_pending`. A human adjudicator must inspect source
evidence, create the final record through the annotation service, and obtain
the configured record-bound attestations. Agreement and adjudication artifacts
are evidence about annotation quality, not automatic Ground Truth.

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
incomplete conversion. Its default root is the 33-item SVG audit
`full_svg_derivatives_v002`: 20 items contain a trimmed review raster, 11 are
empty-render placeholders, and two have invalid-geometry placeholders. Every
item has a conversion warning, so none may be promoted by this UI. Entity-ID
coverage is displayed as a structural diagnostic, never as visual fidelity.
Content review never sets `benchmark_eligible` directly.

Reproduce that immutable, review-only audit with:

```bash
.venv/bin/python scripts/render_mendeley_dwg_svg_derivatives.py \
  /data/GeoLogParser/datasets/public/mendeley_borehole_logs_v002/raw/Borehole.logs.collection.zip \
  /data/GeoLogParser/datasets/public/mendeley_borehole_logs_v002/metadata/manifest.jsonl \
  /data/GeoLogParser/datasets/public/mendeley_borehole_logs_v002/audit/full_svg_derivatives_v002 \
  /data/GeoLogParser/tools/prefix/libredwg-0.14/bin/dwg2SVG \
  /data/GeoLogParser/tools/prefix/libredwg-0.14/bin/dwgread \
  --library-dir /data/GeoLogParser/tools/prefix/libredwg-0.14/lib \
  --output-width 2000
```

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

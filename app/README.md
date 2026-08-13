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
GEOLOGPARSER_FIXED_ANNOTATOR_ID=padova-reviewer-a \
  .venv/bin/uvicorn app.server:app --host 127.0.0.1 --port 8011
```

Run track B from its own annotation root and a different port/process. The
server-fixed actor is used for saves, bbox bindings, and timing events; the
browser cannot select the peer actor. This binds a service instance to a track,
but does not authenticate the human operating the browser. Both roots still
reside on a shared host filesystem, so this is not an OS security boundary; use
separate authenticated accounts/permissions or supervised reviewer sessions.
Reviewers must not inspect peer files before agreement is frozen.

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

Regenerate the current assignment-progress snapshot at any time with:

```bash
.venv/bin/python scripts/audit_annotation_assignment.py \
  /data/GeoLogParser/artifacts/annotation/unipd_blinded_duplicate_v001 \
  /data/GeoLogParser/artifacts/annotation/unipd_blinded_duplicate_v001/status/current.json
```

This live audit checks track ID completeness and reports status, revision,
record/file hashes, effective attestations, GT-gate progress, agreement files,
and adjudication manifests. It is separate from publication readiness so the
same 15 pages are not double-counted merely because they appear in two reviewer
tracks.

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

## PDF/image source content review

Candidate PDF pages and standalone images use a separate source-review service
before geological annotation. Build an immutable rendered pack from one or more
hash-bound page-content manifests:

```bash
.venv/bin/python scripts/build_page_review_pack.py \
  /data/GeoLogParser/datasets/public/mendeley_subsurface_slopes_logs_v001/metadata/content_manifest.jsonl \
  /data/GeoLogParser/datasets/public/mendeley_tiber_borehole_pdf_v001/metadata/content_manifest.jsonl \
  --output-root /data/GeoLogParser/artifacts/source_review/international_candidates_v001 \
  --phase1-scope international_candidate \
  --dpi 180
```

Start the review UI:

```bash
GEOLOGPARSER_PAGE_REVIEWER_ID=reviewer-anon-01 \
.venv/bin/uvicorn app.page_review_server:app --host 0.0.0.0 --port 8002
```

The reviewer records whether the page is phase-1 borehole content, whether the
render is complete, and the status/action for organization, person/signature,
contact, coordinates/location, stamp/watermark, and third-party content.
`eligible_for_annotation` requires a readable borehole page with every present
item explicitly cleared and no pending redaction. The stored reviewer identity
is self-attested by the local operator; the service does not authenticate a
person or establish expert status.

The queue defaults to unreviewed pages and supports reviewed/eligible/restricted
filters, previous/next navigation, and 50%--200% image zoom. `Set all absent`
only fills the disclosure form; it does not save a review or decide eligibility.
After a successful save, the UI advances to the next unreviewed page and
refreshes counts from `GET /api/status`. Set
`GEOLOGPARSER_PAGE_REVIEWER_ID` to bind one service process to a stable
anonymous reviewer ID. Without it, the human operator must enter an ID, which
is retained only in browser local storage. Neither mode authenticates a person.
The live `review_status.json` is written under the mutable review directory by
default so the immutable rendered pack is not modified.

Audit current status without exporting:

```bash
.venv/bin/python scripts/audit_page_reviews.py \
  /data/GeoLogParser/artifacts/source_review/international_candidates_v001 \
  /data/GeoLogParser/artifacts/source_review/international_candidates_v001/reviews \
  --output /data/GeoLogParser/artifacts/source_review/international_candidates_v001/reviews/review_status.json
```

After every item has a valid human decision, add `--eligible-manifest PATH` to
freeze the subset that may enter geological annotation. Partial export is
rejected while any item remains unreviewed. Source review never creates
geological Ground Truth and always leaves `benchmark_eligible=false`.

Only after the complete queue audit has produced a frozen eligible manifest may
automatic extraction proposals be generated:

```bash
.venv/bin/python scripts/audit_page_reviews.py \
  /data/GeoLogParser/artifacts/source_review/international_candidates_v001 \
  /data/GeoLogParser/artifacts/source_review/international_candidates_v001/reviews \
  --eligible-manifest /data/GeoLogParser/artifacts/source_review/international_candidates_v001/reviews/eligible_v001.jsonl
.venv/bin/python scripts/build_eligible_annotation_pack.py \
  /data/GeoLogParser/artifacts/source_review/international_candidates_v001 \
  /data/GeoLogParser/artifacts/source_review/international_candidates_v001/reviews \
  /data/GeoLogParser/artifacts/source_review/international_candidates_v001/reviews/eligible_v001.jsonl \
  /data/GeoLogParser/artifacts/annotation/international_candidates_auto_v001
```

The builder re-audits every page, requires the eligible manifest byte hash to
match that canonical audit, and rechecks source PDF, rendered PNG, and review
JSON hashes. Native PDFs retain PDF-point `source_bbox` evidence and add a
transform-derived display bbox. Scanned PDFs and images run OCR against the
frozen review PNG and store only rendered-pixel display bboxes; their
`source_bbox` remains null. The output is immutable, labelled `auto`, has zero
human-verified annotations, null accuracy metrics, and `benchmark_eligible=false`.
It is an extraction proposal pack, never a Ground Truth export.

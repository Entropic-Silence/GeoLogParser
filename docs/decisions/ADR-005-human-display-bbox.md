# ADR-005: Human-drawn display bbox provenance

- Status: accepted
- Date: 2026-08-13

## Context

Some extracted fields inherit a native-PDF text-block bbox that spans several
table cells. Constraint-guided rereading can then see unrelated numbers and
prefer a geologically plausible value from the wrong column.

## Decision

Keep `source_bbox` in its original source coordinate space. Store review-time
pixel geometry separately as `display_bbox`, with optional
`display_bbox_source` and `display_bbox_annotator_id`. A human-drawn bbox must be
validated against the exact rendered image dimensions and attributed to the
annotator who saves it. Drawing or binding a bbox never confirms the field
value and never changes `extraction_method` or `validation_status`.

Temporary bboxes may be used for a non-mutating reread without being bound to
the record. PDF-derived display bboxes use `pdf_transform_v001`; model-grounded
boxes use `model_grounded`; review boxes use `human_drawn`.

## Consequences

Source evidence remains intact, display/highlight geometry is auditable, and a
reviewer can tighten a reread ROI without fabricating PDF coordinates. SQLite,
XLSX, and Parquet provenance projections retain the display-bbox source and
annotator. Existing v001 records remain valid because the new keys are
optional.

# CAD derivative and privacy-review protocol

This protocol applies only to quarantined acquisition candidates. It does not
expand the phase-1 model input contract beyond PDF/JPG/PNG and does not make a
DWG or its derivative benchmark-eligible.

## Immutable source evidence

For every archive member, preserve archive index, raw and decoded member name,
CRC32, byte size, DWG signature, source SHA256, dataset DOI, licence, and the
archive/source-manifest hashes. Never use a decoded filename as Ground Truth.

## Versioned derivative chain

1. Extract one member to an isolated audit directory and verify its SHA256.
2. Convert DWG to DXF with pinned LibreDWG; capture stdout/stderr and hash the
   DXF. Warnings about unsupported classes, HATCH, MTEXT, buffer overflow, or
   invalid paper space set `conversion_may_be_incomplete: true`.
3. Render DXF model/paper layouts separately with pinned ezdxf/matplotlib.
   Record renderer versions, layout name, DPI, background, font substitutions,
   repair/audit messages, pixel dimensions, and output SHA256.
4. Keep source, DXF, images, logs, and review records under `/data/GeoLogParser`.
   Only code, schemas, aggregate counts, and non-sensitive hashes enter Git.

An optional entity-inventory reconciliation compares source DWG graphical
entities with derivative DXF modelspace by type, handle, text count, and ordered
text hash. Database objects such as layers, styles, and dictionaries are not
modelspace entities and must be excluded from both populations. A full match
narrows structural/text-loss risk but does not override converter warnings or
prove pixel fidelity, correct font substitution, privacy, rights, or geological
correctness. Human visual/content review remains mandatory.

## Technical raster comparison

Independent raster paths may be compared only as a diagnostic. For each image,
estimate the border background, threshold a foreground mask, record the content
bbox and foreground fraction, and normalize the content to a fixed occupancy
grid. Use area aggregation before thresholding: nearest-neighbour downsampling
can erase one-pixel CAD lines. Record raw IoU and a symmetric, tolerance-aware
coverage F1 together with all thresholds.

A placeholder, blank image, or invalid renderer geometry makes a pair
`not_comparable`. Known missing entities do not prevent an occupancy diagnostic,
but they must set conversion-incomplete evidence and prevent a fidelity claim.
Low cross-renderer overlap is evidence of disagreement, not evidence identifying
which rendering is correct. High overlap is also insufficient to prove accurate
text, fonts, geometry, privacy, or rights. Therefore this diagnostic must retain
`visual_fidelity_status: not_assessed` until a real reviewer completes the
separate checklist.

LibreCAD 2.1.3 may be used as an isolated offscreen startup probe, but its
documented/help command line exposes no PDF/PNG/print/export option. A process
that stays open without a fatal Qt error shows only that the GUI event loop
started; it does not prove complete parsing and creates no review derivative.
Do not automate GUI menus or infer export success from a timeout.

The installed fallback for Chinese glyphs is `DroidSansFallbackFull.ttf`.
Replacing a missing CAD font is a visible derivative transform; it must be
recorded and never treated as original pixel evidence.

## Human privacy/content review

Automatic keyword screening only prioritizes review. A human reviewer records
one decision per rendered drawing:

- `exclude`: unsafe, irrelevant, or technically incomplete;
- `internal_only`: research use may continue but no public derivative;
- `anonymize_then_review`: candidate masks/crops must be produced and reviewed;
- `eligible_for_annotation`: only after rights, third-party content, privacy,
  location sensitivity, and conversion completeness all pass.

The checklist explicitly covers project/organization names, person names and
approval signatures, phone/email/address, coordinates and exact engineering
location, stamps/watermarks, third-party logos/content, missing CAD entities,
and whether the drawing is genuinely a single-borehole log. Review records use
anonymous reviewer IDs and timestamps. Absence of a detected keyword is never
interpreted as clearance.

## Anonymization and provenance

Masks/crops are separate derivatives. Each redaction records source item,
layout, normalized bbox/polygon, reason category, reviewer ID, timestamp, and
pre/post image hashes. Geological fields and interval evidence must not be
masked unless the item is excluded. Coordinates may be withheld from the
public release while retained under controlled access; this policy must be
explicit at dataset-version level.

## Release gate

A versioned PDF/PNG dataset can enter annotation only when every item has a
completed human review and no unresolved conversion or disclosure flag. The GT
exporter remains independent: `auto` annotations still cannot become Ground
Truth. Release counts and licences are computed from the gated manifest, never
from archive inventory or automatic screening.

# Research log

## 2026-08-12 — Foundation initialization

- Experiment: none; this is an engineering/setup activity.
- Observation: no prior GeoLogParser repository existed. The host has ample CPU,
  RAM, disk, and five NVIDIA GPUs, but all GPUs are mining and the system Python
  lacks the intended OCR/ML packages.
- Failure: document baseline had not yet been run at log creation time.
- Decision: use a standard-library domain core with optional OCR/PDF adapters;
  keep large assets on `/data/GeoLogParser`; do not interrupt mining for this
  phase.
- Next step: validate schemas and constraints, install a small isolated test
  environment, and execute a provenance-preserving OCR smoke test.

## 2026-08-12 — Tesseract adapter smoke test

- Experiment: engineering smoke test; not a benchmark result.
- Observation: Tesseract 4.1.1 executed through the CLI adapter and preserved
  line bounding boxes/confidence. On a synthetic 300 dpi Courier fixture it
  read `ZK-01` as `ZK-Ol` while reading `4.50` correctly.
- Failure: exact borehole-ID OCR failed through a known `0/O` and `1/I/l`
  confusion mode. This result must not be generalized to dataset performance.
- Decision: keep OCR text unchanged, preserve its evidence, and let future C8/
  cross-model review flag candidates; do not silently rewrite the identifier.
- Next step: execute the full OCR→text→JSON path, add a versioned error code,
  and compare real OCR backends only after obtaining rights-cleared samples.

## 2026-08-12 — Foundation test run

- Experiment: `P0_SYNTHETIC_OCR_SMOKE_001` (pre-commit connectivity run) and
  reserved traceable rerun `P0_SYNTHETIC_OCR_SMOKE_002`; both use the same
  synthetic engineering fixture and neither is a benchmark.
- Observation: image→Tesseract TSV→text regions→regex→schema-shaped JSON/CSV
  completed on CPU. The run produced two intervals and retained bbox/confidence.
- Failure: this is not a real borehole log and cannot support an accuracy claim.
  Native PDF was exercised with generated PostScript/PDF text, not field data.
- Decision: report only pipeline connectivity and test status. Real baseline
  metrics remain `TBD` until a rights-cleared, annotated dataset exists.
- Next step: acquire and legally audit a small public sample set, then run a
  dataset versioned smoke benchmark before changing the schema.

## 2026-08-12 — Fixed-ID BGS B1 audit

- Experiment: `P1_B1_BGS_AUDIT_001`; immutable result directory
  `results/2026-08-12/P1_B1_BGS_AUDIT_001`; source dataset is the frozen BGS
  IDs 4, 5, 6, and 10 manifest with SHA256
  `7847e402293971684919626bea3555276dcd386433ed1634fadad4b955cb3ce5`.
- Observation: the CPU Tesseract 4.1.1 + conservative regex baseline processed
  four documents (20 pages) in 127.375155 seconds. Borehole-ID exact match was
  3/4. Coordinate extraction covered 4/4 references for both axes with zero
  paired-value MAE. These statements apply only to this fixed audit sample.
- Failure: final-depth coverage was 0/4, so its MAE is undefined (`null`), not
  zero. Only one interval was emitted; it was a false parse of OCR text
  `4 0 50 Sand rE` and C1/C2 correctly flagged the invalid depths/thickness.
  The other three documents emitted no interval. The run contains eight
  field/interval error rows.
- Decision: retain this run as a connectivity and failure-mode audit, not a
  representative BGS result and not a Paper I headline table. Always report
  numeric extraction coverage beside MAE. Never count an unevaluated
  constraint as evidence of geological consistency.
- Next step: add an independently packaged OCR backend, rerun the identical
  fixed-ID audit under a new experiment ID, and freeze a backend-neutral
  prediction/evaluation protocol before expanding the sample.

## 2026-08-12 — Fixed-ID BGS RapidOCR audit

- Experiment: `P1_B1_RAPIDOCR_BGS_AUDIT_001`; identical four-document,
  20-page input and 300 dpi rendering as the Tesseract audit. Runtime was
  RapidOCR ONNX Runtime 1.4.4/1.23.2 on CPU; model files and SHA256 values are
  recorded in `run.json` and the model registry.
- Observation: borehole-ID exact match was 4/4. Runtime was 70.504828 seconds
  (3.525241 seconds/page), with peak process RSS 892,068 KiB. These values are
  measurements from this process and this fixed audit sample only.
- Failure: coordinate coverage, final-depth coverage, and interval emission
  were all zero. Consequently all paired MAEs are undefined (`null`) and all
  C1–C10 results had `evaluated_count=0`. The OCR detector returned many small
  regions (154–457 per document), while the conservative extractor expects
  coherent lines; this is a region-aggregation/interface failure rather than
  evidence that the underlying page lacks text.
- Decision: freeze this failed run unchanged. Do not interpret 4/4 ID match as
  overall extraction success, and do not interpret unevaluated constraints as
  consistency. Add an explicit, tested spatial line-aggregation stage and use
  a new experiment ID for any rerun.
- Next step: inspect region geometry on a frozen page, implement backend-neutral
  aggregation with provenance-preserving union bboxes, and compare both raw and
  aggregated extraction without overwriting either audit.

## 2026-08-12 — RapidOCR BGS header-spacing repair audit

- Experiment: `P1_B1_RAPIDOCR_BGS_AUDIT_002`; new immutable run after one
  tested extractor change allowing OCR-deleted spaces in the literal
  `British National Grid` header. No model, input, DPI, or metadata-GT change.
- Observation: borehole-ID exact match and coordinate coverage were both 4/4;
  coordinate paired-value MAE was zero for both axes. Total runtime was
  70.116934 seconds (3.505847 seconds/page) and peak process RSS was 968,728
  KiB. These are audit-sample measurements, not representative estimates.
- Failure: final-depth coverage remained 0/4 and no intervals were emitted.
  C8 evaluated two coordinate fields per document; other constraints remained
  unevaluated. Thus the repair resolves one extraction-interface error only.
- Decision: freeze both pre-fix and post-fix experiments, so the effect is
  traceable rather than overwritten. Do not expand the regex to join distant
  columns using y proximity: the historical BGS tables place geological text
  and depth columns far apart and require explicit layout reasoning.
- Next step: formalize interval matching and constraint-coverage summaries,
  then implement column-aware layout evidence before claiming interval metrics.

## 2026-08-12 — Quarantined Chinese panel-rendering validation

- Experiment: engineering validation only; no benchmark ID and no accuracy
  metric. Source is the rights-unverified Sanming public-web candidate PDF,
  SHA256 `a227f24191cee7613d313c75dbc103ce6f36c3b7144b0d9626c07bfcb7f767ef`.
- Observation: pages 44–45 are A3 pages containing two boreholes each. A
  normalized half-page panel manifest produced four independent 150 dpi PNGs
  (ZK2, ZK9, ZK11, ZK14), each about 1241×1755 pixels. The generated manifest
  stores source/render hashes, page, crop, DPI, project/template quarantine IDs,
  and a prohibition-pending-rights-review flag. Visual inspection confirmed the
  primary panel header and table are retained.
- Failure/risk: pages visibly contain exact coordinates, project information,
  stamps, signatures, and company details; narrow neighboring border remnants
  occur at the half-page seam. Rights, privacy, and sensitive-location review
  are incomplete. These four panels are not counted as released or
  rights-cleared benchmark pages.
- Decision: keep rendered images and generated manifest under `/data` only.
  Treat a panel, not a physical PDF page, as the one-borehole annotation unit.
  Annotation saves are revisioned and preserve prior JSON in history.
- Next step: exploit the candidate's native Unicode text layer through a
  panel-aware adapter for internal schema validation, while continuing the
  independent rights-clearance process.

## 2026-08-12 — Local annotation UI and auto-proposal validation

- Experiment: engineering validation only; no accuracy metric. A panel-aware
  PyMuPDF adapter, conservative native-text extractor, revisioned FastAPI API,
  and browser editor were exercised on the four quarantined panels.
- Observation: v002 produced four revision-1 `auto` proposals with 2, 3, 4,
  and 3 extracted intervals for ZK2, ZK9, ZK11, and ZK14. The API listed all
  four records, returned the image and page, and ran Schema+C1–C10 validation.
  HTTP smoke responses were 200. Original PDF-point evidence is preserved; a
  tested rotation/clip/scale transform adds separate rendered-pixel bboxes for
  UI highlighting.
- Failure: the first v002 render attempt failed because page rotation metadata
  was read after the PDF context closed. The single generated intermediate PNG
  was deleted, a real-PDF lifecycle regression test was added, and v002 was
  rebuilt from an empty destination. FastAPI's TestClient emits one upstream
  warning about future `httpx2`; dependency checks otherwise pass.
- Decision: all proposals remain status `auto`; none is Ground Truth. Save uses
  optimistic revision checks and archives prior JSON. Quarantined images and
  annotations remain under `/data` and are not committed or redistributed.
- Next step: implement review-queue scoring and human timing instrumentation,
  then obtain an actual manual verification pass before computing any Chinese
  extraction metric.

## 2026-08-12 — Conservative native layout-to-description binding

- Experiment: internal engineering comparison of v002 versus v003 auto
  proposals on the same four quarantined panels; no human Ground Truth and no
  accuracy claim.
- Observation: a conservative binder searches native text blocks for ordered
  geological headings ending in `土` or `岩` followed by a colon. It binds text
  only when heading count exactly equals extracted interval count. In v003 all
  12 intervals received raw lithology and description evidence. Deterministic
  review items decreased from 28 in v002 to 4 in v003; the four remaining items
  are weak C9 sequence warnings for source codes ①→④ or ②→④.
- Failure/risk: equal cardinality and order are template assumptions, not a
  general layout solution. Description correctness has not been manually
  verified. The public-source web search performed in parallel returned noisy
  results and no new Chinese record with auditable redistribution permission.
- Decision: if heading/interval counts differ, bind nothing and send missing
  fields to review. Preserve source text and union bbox. Never synthesize
  missing stratum codes from C9. Keep all v003 records status `auto`.
- Next step: implement field-level ROI rereading candidates and ranking with
  explicit evidence/constraint terms, then validate correction safety using
  controlled fixtures before any automatic acceptance experiment.

## 2026-08-12 — Synthetic IDW error-propagation protocol smoke

- Experiment: `P3_SYNTHETIC_ERROR_PROPAGATION_SMOKE_001`; four synthetic
  boreholes, first internal boundary, IDW power 2, 6×6 query grid, perturbation
  magnitudes 0.01/0.05/0.10/0.50/1.00 m, and one recorded seed per condition.
- Observation: the experiment produced five prediction rows and metrics for 36
  grid points per condition. For example, recorded surface MAE values were
  0.006136, 0.024720, 0.061361, 0.306805, and 1.000000 m in magnitude order.
  These numbers validate the implementation protocol only.
- Failure/limitation: this fixture uses four artificial points, one internal
  boundary, one seed per magnitude, and no human-validated extraction. At the
  1.00 m condition all sampled signs happened to align, yielding MAE≈1.00 m;
  this illustrates high sampling variance and is not a geological conclusion.
- Decision: index the run as `protocol_only`, not paper evidence. Formal Paper
  III experiments require spatially coherent, rights-cleared, human-validated
  boreholes, multiple seeds, mean/std/confidence intervals, and comparison of
  raw AI, constraint-validated, and human GT surfaces.
- Next step: add multi-seed experiment aggregation and automatic table/figure
  generation, while continuing acquisition of eligible spatial data.

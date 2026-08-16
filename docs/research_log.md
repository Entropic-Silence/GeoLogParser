# Research log

## 2026-08-13 — Human-gated page source-review queue

- Experiment: source-review workflow construction, not a human review or
  extraction experiment. Two international content manifests contributed 29
  candidate pages; a third manifest contributed no in-scope rows.
- Observation: 180-DPI rendering produced 29 hash-bound PNGs (28 engineering
  borelogs and one stratigraphic column). The pack manifest SHA256 is
  `b3211ad6ea46a0d7a1925be47df24e593312ec1096529738b92db6427b83186b`.
  Full-resolution technical inspection confirmed that one page from each source
  is legible, but this model inspection is not logged as human content/privacy
  review.
- Decision: separate page-source review from geological annotation. A page can
  become `annotation_eligible` only after a self-attested human reviewer records
  phase-1 fit, render completeness, and an action for each disclosure class.
  The review can never set `benchmark_eligible` or create Ground Truth. Reject
  partial eligible-manifest export until every pack item is reviewed.
- Current status: 29 unreviewed, zero annotation-eligible, zero
  Benchmark-eligible, and zero Ground Truth pages.
- Next step: obtain real human content/privacy decisions, then create auto
  extraction proposals only for the frozen eligible subset.

## 2026-08-13 — Focused open-metadata survey and page-content manifests

- Experiment: read-only metadata survey plus selected public acquisition and
  automated content triage; not a benchmark experiment or human source review.
- Observation: v005 issued 15 requests (12 successful), froze 28 unique
  DataCite records, and retained three HTTP 403 Figshare failures. Complete
  Mendeley dataset inventories fixed the nested-file blind spot in the older
  root-folder API. Three CC BY sources passed frozen acquisition verification.
- Observation: hash-bound manifests classified 28 English engineering-borelog
  pages and one English stratigraphic-column page as international candidates;
  18 resistivity images, 20 laboratory-report pages, and 38 analytical pages
  were explicitly excluded from phase 1. These counts come from generated
  manifests rather than prose inspection totals.
- Limitation: classification provenance is
  `automated_project_agent_content_triage_20260813`; human content review,
  privacy review, Ground Truth, and benchmark eligibility are all zero. The
  newly acquired Chinese PDF/JPG/PNG candidate count is also zero. The Figshare
  Chinese core-photo/lithology candidate remains inaccessible from this host.
- Decision: keep download evidence (`acquisition.json`) immutable in meaning and
  write page classifications to separate `content_manifest.jsonl` and
  `content_summary.json` files. Require exactly one rule per page and reject
  source hash drift, gaps, overlaps, or claimed human review in the automated
  builder.
- Next step: prioritize rights-cleared Chinese page images and real two-track
  human annotation. Do not run formal Paper I/II/III comparisons without GT.

## 2026-08-12 — Traceable paper-figure generation

- Experiment: generated five figures from hashed result indexes/manifests:
  Paper I audit coverage and degradation-input distribution; Paper II method
  schematic; Paper III Padova source locations and synthetic error propagation.
- Observation: the source-coordinate plot separates Grizzaga, Panaro, and
  Tagliamento into distant site groups. Treating all 11 points as one local
  interpolated surface would be geologically and spatially unjustified.
- Decision: encode `audit`, `protocol-only`, `unverified`, or `design` limits in
  plot titles/captions. Store output SHA256 values and source manifest hashes in
  `papers/figure_manifest.json`. Do not generate absent Paper II performance or
  real Paper III model figures.
- Next step: once formal experiments exist, add accuracy/generalization,
  calibration, FCR, review-efficiency, and real-site downstream figures through
  the same generated-only path.

## 2026-08-12 — Padova source-coordinate GIS export

- Experiment: exported one point per source borehole (not one per page) from the
  audited Padova KMZ link into SQLite, GeoJSON, GeoParquet, and GeoPackage.
- Observation: all four outputs contain 11 located boreholes; SQLite contains
  zero intervals. GeoPackage layer `boreholes` reports `EPSG:4326`, and all 11
  coordinate statuses are `needs_review`. Output SHA256 values are recorded in
  `/data/GeoLogParser/artifacts/spatial/unipd_source_catalog_v001/summary.json`;
  Paper III real-model metrics are null.
- Failure: the first GeoPackage write exposed an OGR incompatibility with
  Arrow null-only inferred fields because collar elevation/final depth are
  absent. The incomplete output directory was quarantined then deleted after
  identifying its four generated files. Explicit nullable field types fixed
  the export; the clean version was rebuilt from scratch.
- Decision: add fixed `pyogrio`/`pyproj` export dependencies and a GeoPackage
  writer preserving coordinate status/warnings. A separate readiness gate now
  requires at least three eligible points, one CRS, and human-verified collar
  elevations and target boundaries before surface modelling. Source coordinate
  presence does not certify survey accuracy.
- Next step: derive collar elevation and intervals only through human review;
  then run the readiness gate before any real IDW/GemPy/PyVista workflow.

## 2026-08-12 — Paper II ablation protocol gate

- Experiment: implemented the immutable Paper II ablation runner and paper-table
  renderer; no empirical Paper II run was created because no human-verified
  correction case set exists.
- Observation: the evaluator now verifies identical case IDs, references,
  originals, review labels, partitions, and GT statuses across variants. Named
  ablations may disable exactly one declared module; the full variant disables
  none. The expected matrix contains full plus seven single-module removals.
- Decision: reject case-set drift and multi-module removals before calculating
  FCR, correction success, review recall/rate, Brier score, or ECE. Create
  `experiments/paper2/result_index.jsonl` and generate Paper II tables from
  hashes using the same mechanism as Papers I/III.
- Next step: build real field-level cases from reviewed GT, freeze disjoint
  calibration/test partitions, then run the complete eight-variant matrix.

## 2026-08-12 — Parameterized Padova degradation inputs

- Experiment: generated deterministic synthetic degradations for all 15 Padova
  rendered pages using 18 profiles spanning resolution, blur, noise, skew, JPEG
  compression, contrast, broken lines, watermark, stamp, and partial occlusion.
- Observation: 270 derived images occupy approximately 285 MB on the mechanical
  data volume. Degradation manifest SHA256 is
  `ca6bc6d6f2eff3df6916b3a87d43f24df6dacb13f4e924048b79120a339c5ba9`;
  source panel manifest SHA256 is
  `2ee38b8da430075df80a4b3c16a4739838b4320ecbc73ce18dcfcbcb1ac79e2a`.
- Limitation: this is a robustness input set, not a robustness result. Accuracy
  is null because the source pages still lack human GT.
- Decision: record exact operation order, parameters, seeds, and source/output
  hashes. Replace the preprocessing and split-builder placeholders with
  executable CLIs; keep the generated images outside Git under `/data`.
- Next step: after GT is frozen, run identical extraction adapters on clean and
  degraded images and report performance by profile/severity rather than only
  an overall mean.

## 2026-08-12 — Result-derived annotation pack and GT evaluator

- Experiment: transformed the immutable Padova B6 audit predictions into a new
  review-only annotation pack. The source predictions SHA256 is
  `bf44f8c06acde38f3cf97b2dc3db2efe20d617dd59d6c92b82f79f1278fbb226`.
- Observation: the pack contains 15 auto annotations and 87 proposed
  intervals, compared with zero intervals in the initial direct-text proposals.
  Human-verified annotation count is still zero and accuracy remains null.
- Failure: the earlier verified-annotation exporter trusted a human document
  status without checking interval completeness or field-level human
  confirmation. That could have admitted a status-only zero-interval record.
- Decision: enforce a GT content/provenance gate and replace the dataset-level
  evaluation placeholder with an ID-aligned, schema-validating runner that
  preserves metric denominators and traceable errors. An identity synthetic
  smoke test passed but is not indexed or used as paper evidence. The gate
  treats a human-confirmed `null` as a legitimate absent source field, distinct
  from an unreviewed abstention; the UI now supports explicit field/row/batch
  confirmation.
- Next step: use the new B6 pack for actual human review; export GT only after
  the gate passes, then evaluate the frozen B1–B6 predictions.

## 2026-08-12 — Padova annotation-to-spatial catalog gate

- Experiment: linked the 15 existing page-level annotation proposals to 11
  source borehole locations without changing annotation status or values.
- Observation: the generated catalog contains 11 borehole documents and 15
  page annotations; zero pages are human verified and zero boreholes are
  eligible for spatial modelling. Catalog SHA256 is
  `dd116b81d6b9740b349434f553dad8e82352a37b06fba117f14cc3c35164fd71`.
- Failure: all current Padova page proposals contain zero intervals. The prior
  annotation UI could not add the first interval because it attempted to clone
  a nonexistent last interval.
- Decision: add schema-ready empty human interval creation, deletion, and
  one-based page provenance; implement an explicit human-only multi-page merge
  and attach source coordinates only as `needs_review` with
  `SOURCE_COORDINATE_UNVERIFIED`. No accuracy metric was created.
- Next step: improve conservative native-PDF interval proposals, then conduct
  real human verification before any GT export or spatial experiment.

## 2026-08-12 — Padova source-location linkage audit

- Experiment: source metadata linkage, not extraction accuracy or Ground
  Truth. The repository KMZ SHA256 is
  `daa59ddcdf9033733eab0d738d4078fa9b8caf38c66e85efe3c21ab624f1e730`.
- Observation: all 11 borehole PDFs linked to source-provided WGS84 points by a
  canonicalized borehole identifier. The frozen location manifest SHA256 is
  `106e7daaf45a6692bbd2a57e2557114cc190a99f1c21897a289dc7c934eba137`.
  The locations form three river/site groups described by the source README,
  creating a plausible real spatial case candidate for Paper III.
- Limitation: locations are source-provided and not independently surveyed or
  human verified. The KMZ lists `TS5`, while the corresponding `TS5.pdf` page
  header is known to read `TS2`; the link is therefore flagged rather than
  silently resolved. The archive's XLS/XLSX files contain CPT/laboratory data,
  not interval Ground Truth for the PDF logs.
- Decision: store coordinates as `EPSG:4326` with validation status
  `source_provided_unverified` and retain the ID-conflict warning. Do not use
  the location manifest to score header extraction or create GT.
- Next step: manually verify borehole identities/intervals and decide whether a
  spatially coherent subset can support Paper III raw/QC/GT comparison.

## 2026-08-12 — Public-repository metadata search extension

- Experiment: read-only DataCite discovery; not data acquisition or a
  benchmark experiment.
- Observation: exact `borehole log` title search returned 27 DataCite records
  and recovered the already acquired Mendeley collection. Chinese keyword
  searches additionally surfaced CGS records already in the registry and a
  Zenodo CC BY 4.0 record (`10.5281/zenodo.15400683`) whose abstract reports
  shear-wave measurements from 9,715 Chinese boreholes.
- Failure/limitation: DataCite exposes no file list, format, size, or content URL
  for the Zenodo record, and the Zenodo API was unreachable from this host. The
  9,715 value is a source abstract statement, not an acquired dataset count.
  Broad Chinese searches also returned many irrelevant records.
- Decision: register the record as metadata-only and potentially relevant to
  Paper III. Do not claim it contains logs, coordinates, stratigraphy, or usable
  individual profiles until files and rights are inspected.
- Next step: retry an official file inventory later or through a browser/manual
  route; continue seeking directly inspectable, licensed PDF/PNG sources.

## 2026-08-12 — Mendeley Chinese DWG single-file rights/content audit

- Experiment: acquisition/content audit, not a benchmark experiment. Dataset
  DOI `10.17632/vcpz47r3sv.2`; archive SHA256
  `c262d83a255a64e5d8e285fe327204f430022856fe66b9ac3b61b9e67ebc1a16`.
- Observation: the archive contains 33 valid DWG files in eight source folders.
  Legacy ZIP names can be reversibly decoded from CP437 bytes as GB18030. A
  single fixed sample converted with LibreDWG 0.14 and contained Chinese
  lithological descriptions and a comprehensive borehole column.
- Failure/risk: LibreDWG emitted `MTEXT ignored`; the resulting SVG is therefore
  incomplete. Extracted CAD text contained a named company and named mining
  area/project. The remaining 32 drawings were not inspected, and DWG lies
  outside the phase-1 PDF/JPG/PNG input contract.
- Decision: keep the entire collection quarantined and `benchmark_eligible:
  false`; do not count it toward Chinese page, template, or Ground Truth totals.
  Record the gating requirements in ADR-004.
- Next step: build a deterministic conversion/content-audit manifest for all
  files, then review and anonymize eligible PDF/PNG derivatives before human
  annotation. Accuracy experiments remain blocked until verified GT exists.

## 2026-08-12 — Mendeley DWG full automatic content pre-screen

- Experiment: automatic acquisition audit `full_prescreen_v001`; not human
  review, annotation, or benchmark evidence. Source manifest SHA256 is
  `431ea76ee9534316c181c8df53ed0474b932ef907fe166a2537c70cb130ff58a`.
- Observation: pinned `dwgread 0.14` converted all 33 drawings to transient
  minJSON without a process failure. All 33 contained Chinese text and 30/33
  triggered at least one conservative disclosure-risk category. Aggregate
  string-level signals included 203 borehole/log matches and 5,569 geological
  description matches. These are keyword occurrence counts, not document
  labels or accuracy metrics.
- Limitation: lack of a keyword hit does not prove a drawing is safe. The JSON
  diagnostic did not reproduce the SVG converter's `MTEXT ignored` warning;
  converter-specific completeness therefore remains unresolved. No drawing in
  this full pass received human visual review.
- Decision: retain all 33 as `benchmark_eligible: false`. Prioritize the three
  automatically low-risk drawings for visual review, while treating them as
  equally quarantined until a human decision is recorded. Store only hashes and
  category counts in the audit manifest; do not place raw extracted text in Git.
- Next step: produce reviewable, versioned derivatives with a renderer that
  preserves CAD text, then complete privacy/location and third-party-content
  review before annotation.

## 2026-08-12 — Priority CAD review derivatives

- Experiment: review-only derivative build `priority_derivatives_v001`; not a
  benchmark experiment. Inputs were the three drawings with no automatic risk
  keyword hit (`MENDELEY_DWG_009`–`011`).
- Observation: pinned LibreDWG 0.14 generated DXF and ezdxf 1.4.3 plus
  matplotlib 3.10.5 generated 1025×4025 model-space PNGs for all three. The
  derivative manifest SHA256 is
  `1189e00d7e36b73d58a16a632ef730c3eb4050ec89ec38949f8ce9b79b7dfda0`.
  An explicit Droid Sans Fallback substitution made Chinese labels renderable.
- Failure/risk: all three conversions emitted warnings or errors, including
  unsupported classes and skipped entities, so
  `conversion_may_be_incomplete=true` for every item. The very tall CAD aspect
  ratio also limits whole-image visual inspection. Automatic low risk did not
  become content clearance; human review count remains zero.
- Decision: preserve the source/DXF/PNG/log/hash chain under `/data`; keep all
  derivatives quarantined and ineligible. Introduce a mandatory content-review
  schema before any item can proceed to annotation.
- Next step: add tiled/zoomable reviewer presentation and obtain real human
  decisions; exclude or repair technically incomplete derivatives before GT.

## 2026-08-12 — Reproducible B2 text-only LLM rerun

- Experiment: `P1_B2_QWEN3VL4B_TEXT_UNIPD_AUDIT_003`, recorded code commit
  `d67a2e248353c44a9555bc7c93ed737f5b21cbbf`.
- Observation: the 15-page rerun produced 13 Schema-valid responses, 74
  unverified intervals, eight violations among 538 constraint evaluations, and
  11,973 input tokens. Mean latency was 50.102257 s/page; peak allocated GPU
  memory was 9,296,219,648 bytes. Excluding runtime fields, every prediction
  row was byte-identical after canonical JSON sorting to development audit
  `_002`.
- Limitation: all annotations remain `auto`; accuracy metrics are null. The
  identical content demonstrates repeatability for this greedy run only, not
  correctness or general model determinism.
- Decision: index `_003` as `audit_only`, preserve both latency measurements,
  and use `_003` as the code-at-recorded-commit reference. The RTX 5090 mining
  job was restored immediately after inference.
- Next step: obtain human-verified annotations before computing B2 accuracy or
  comparing B2 against other baselines.

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

## 2026-08-12 — Local Qwen3-VL B4 engineering audits

- Experiments: three immutable single-panel smoke runs followed by
  `P1_B4_QWEN3VL4B_SANMING_AUDIT_001` and
  `P1_B4_QWEN3VL4B_BGS_AUDIT_001`. Model revision is
  `ebb281ec70b05090aa6165b016eac8ec08e71b17`; prompts and manifests are hashed.
- Observation: prompt v001 reached the 1,536-token limit and emitted truncated
  JSON. Prompt v002 reduced repetition, but the next smoke exposed a missing
  `jsonschema` dependency in the isolated runtime. After locking that dependency,
  a one-panel response became Schema-valid and C1/C2/C4 detected four numerical
  violations. Every failed run remains frozen rather than overwritten.
- Chinese audit: 3/4 valid responses, eight intervals, 20 violations among 82
  constraint evaluations, 50.637324 s/image mean, and 9,291,707,392 bytes peak
  allocated GPU memory. One response hit 1,024 tokens. These four panels are
  quarantined and have no human GT, so accuracy is null.
- BGS audit: 4/4 valid but empty responses on the first page of each fixed
  document, 6.397402 s/image mean. This is abstention/coverage behavior, not
  accuracy. Full multi-page VLM evaluation remains unrun.
- Operational failure: `docker stop Pearl` was automatically reversed by the
  fleet guardian. The supported control-socket `miner_stop`/`miner_start`
  commands were then used. The 5090 was verified idle before bounded runs and
  restored to 100% utilization afterward; other miners remained active.
- Decision: keep Qwen3-VL-4B as the first Apache-2.0 B4 adapter, mark all
  whole-image fields ungrounded, and require constraints/review rather than
  treating syntactic JSON success as acceptance.
- Next step: acquire/verify real GT, run B5 and B6 on eligible splits, and add
  a constrained rereading audit against human-corrected numerical fields.

## 2026-08-12 — Qwen3-VL B5 few-shot engineering audit

- Experiment: `P1_B5_QWEN3VL4B_SANMING_AUDIT_001`; same four quarantine
  panels/model/runtime as B4, versioned prompt `vlm_extract_fewshot_v001`.
- Observation: 1/4 responses were Schema-valid; three hit the 1,024-token cap.
  Mean inference latency was 59.300853 s/image and peak allocated memory was
  9,293,797,376 bytes. The one valid record emitted three intervals with three
  constraint violations.
- Decision: record B5 as a negative audit result. Do not claim few-shot
  improvement or accuracy without human GT. Future prompt changes get a new
  version and experiment ID; B5 v001 remains immutable.

## 2026-08-12 — Multi-seed Paper III protocol validation

- Experiment: `P3_SYNTHETIC_ERROR_PROPAGATION_MULTISEED_001`; 30 deterministic
  seeds for each of five boundary perturbation magnitudes on the same synthetic
  four-borehole IDW fixture.
- Observation: the pipeline reports mean, sample standard deviation, and an
  explicitly named normal-approximation 95% CI. At 1.00 m, synthetic surface
  MAE mean/std were 0.662470/0.110565 m.
- Limitation: random-sign seeds are repeats of an artificial fixture, not
  independent sites. These values remain `protocol_only` and cannot support a
  geological conclusion.
- Next step: replace the fixture with a rights-cleared spatially coherent site
  and compare human GT, raw AI, and constraint-validated surfaces.

## 2026-08-12 — CC BY 4.0 Padova borehole-log source acquisition

- Dataset: University of Padova DOI
  `10.25430/researchdata.cab.unipd.it.00001663`. Repository JSON records public
  file 14335 under CC BY 4.0, size 15,986,769 bytes, and MD5
  `030f545f07da0abcb06ca4ead715bf9c`.
- Observation: the download matched MD5; local archive SHA256 is
  `f07bdd15f7bef34bd2697274c1f472b85a9a359b21ea7fece52012e27cf60163`.
  The borehole subset has 11 PDFs/15 native-PDF pages. A fixed manifest stores
  per-document SHA256, page type, DOI, licence, and unannotated status.
- Engineering finding: direct text extraction after international-header and
  decimal-comma support covers all 11 borehole IDs but no final depths or
  intervals. Geological descriptions survive in the text layer while most
  depth boundaries are graphical/layout evidence. This is not an accuracy
  result because no project human GT exists.
- Source-quality warning: file `TS5.pdf` visibly reports `BOREHOLE: TS2` in its
  header. The project does not decide whether filename or header is correct
  without source clarification/human annotation.
- Failure/fix: real headers exposed over-greedy ID capture and C8 matching the
  `i/l` in the word `Elevation`. Each repair received tests and a new audit ID;
  prior runs remain unchanged.
- Decision: this source is eligible for international/public validation and
  annotation with attribution, but cannot satisfy the Chinese Paper I core.

## 2026-08-12 — Padova annotation pack, CGS rights audit, and B6 contract

- Annotation artifact: rendered all 15 Padova pages at 150 dpi and created 15
  revisioned `auto` proposals under
  `/data/GeoLogParser/artifacts/annotation/unipd_levee_geotech_v001`.
  `panel_manifest.jsonl` SHA256 is
  `2ee38b8da430075df80a4b3c16a4739838b43228bf1a9e7ff9ff7b835f77d4b3`.
  Every page retains source/render hashes, page number, visual crop, licence,
  and PDF-to-rendered bbox transformation. None is Ground Truth yet.
- CGS audit: DataCite metadata for four DOI candidates was recorded in the data
  registry. Three `rightsList` entries point only to an institutional URL and
  one is empty; this is not a licence grant. DOI targets timed out from this
  host. No files were downloaded and eligible Chinese benchmark size remains
  zero.
- Implementation: added conservative B6 field fusion. Agreement retains
  grounded provenance; conflicts retain the grounded value but set
  `needs_review`; unaligned VLM-only intervals remain explicit review items.
  Added a human-GT-gated Paper II evaluator requiring disjoint calibration and
  test partitions. It rejects `auto` annotations before computing FCR, review
  recall, Brier score, or ECE.
- Runtime failure: the first Padova B4 invocation failed before model loading
  because the isolated AI environment lacked the repository import path. No
  experiment directory was created. The rerun explicitly used `PYTHONPATH=src`.
- Next step: complete and index Padova B4/B6 audits, then manually validate the
  public annotations. B4/B6 audits without human GT remain coverage/failure
  evidence only.

## 2026-08-12 — B3 positioned-text layout audit

- Experiment: `P1_B3_LAYOUT_UNIPD_AUDIT_001` over all 15 public Padova pages.
- Observation: PS1/PS2 pages contain repeated, positioned textual depth ranges,
  while GS/TS/TPS boundaries are primarily vector graphics. A conservative
  dominant-x-column rule emitted 46 unverified intervals on 5/15 pages and
  abstained on the remaining ten. It triggered three constraint violations
  across 367 evaluations and required 0.039417 s/page mean CPU time.
- Limitation: all references remain `auto`; interval correctness is unknown.
  The rule cannot parse vector-only scales and positional description binding
  is template-sensitive. These counts are coverage evidence, not accuracy.
- Decision: retain abstention as an explicit cross-template failure rather than
  weaken the minimum-column evidence rule. Formal B3 metrics await human GT.

## 2026-08-12 — Ground-Truth export gate and GeoParquet interoperability

- Annotation gate: a new export rejects any collection containing `auto`
  status and records human status, annotator IDs, and snapshot SHA256. The real
  Padova pack was passed through this command and correctly failed on
  `UNIPD_GS1_P001`; no GT file was created. This is a safety test, not an
  annotation result.
- Agreement API: two independently supplied annotation collections can now be
  compared for categorical header exact agreement and boundary numeric MAE;
  documents with different interval counts are explicitly counted/excluded
  from pairwise boundary MAE.
- Interoperability: QGIS-readable GeoParquet point export now includes WKB and
  GeoParquet 1.1 metadata. Export requires one explicit EPSG identifier and
  rejects mixed/unknown CRSs. No coordinate transformation is inferred.
- Limitation: GeoPackage and real spatial case-study export remain unrun; the
  current records do not provide a rights-cleared, human-validated coherent
  site.

## 2026-08-12 — B2 text-only local LLM audit

- Failed run: `P1_B2_QWEN3VL4B_TEXT_UNIPD_AUDIT_001` created its immutable
  directory and then failed before model loading because PyMuPDF was absent
  from the isolated AI environment. The failure was frozen and indexed; the
  runtime dependency was then installed without altering `_001`.
- Completed run: `P1_B2_QWEN3VL4B_TEXT_UNIPD_AUDIT_002`; 15 Padova pages,
  Qwen3-VL-4B language stack at revision `ebb281ec...`, no image input,
  deterministic decoding, prompt `llm_extract_v001`, and 1,536 output-token
  cap. Native positioned text hashes were stored per page.
- Observation: 13/15 responses were Schema-valid; two hit the token cap. Valid
  responses emitted 74 unverified intervals, with eight violations across 538
  constraint evaluations. Mean inference time was 35.331825 s/page; peak
  allocated GPU memory was 9,296,219,648 bytes. Total input was 11,973 tokens.
- Limitation: no human GT exists. Some vector-only depth templates produced no
  intervals, while others produced interval candidates from textual ranges;
  neither behavior is scored as correct. Results are structured-output and
  coverage evidence only.
## 2026-08-12 — CAD fidelity reconciliation and reliability metrics

- Objective: narrow the conversion uncertainty for the three automatically
  low-risk Mendeley DWG candidates without treating an automatic check as
  human review or Ground Truth.
- First failed audit: `priority_fidelity_v001` compared LibreDWG database
  objects (layers/styles/dictionaries) with DXF modelspace entities and
  therefore produced a population mismatch. The directory was preserved as
  `priority_fidelity_v001_superseded_object_scope_error`; it is not a research
  result and is not entered in a paper result index.
- Corrected audit: `priority_fidelity_v002` restricts the source population to
  graphical entities. MENDELEY_DWG_009, 010, and 011 matched 1,244/1,244,
  1,905/1,905, and 7,173/7,173 source/derivative handles. Their 363, 537, and
  611 ordered text entities also matched by SHA256. Manifest SHA256:
  `0a5af970a16bbec9bd5dc8cdb849d529eeec4e67e817cce85c9a74454b4371cb`.
- Limitation: inventory equivalence does not establish pixel fidelity, correct
  fonts, privacy clearance, third-party rights, human visual completeness,
  benchmark eligibility, or geological correctness. Human reviews and
  eligible items remain zero.
- Evaluation implementation: added configurable Critical Numerical Error Rate
  (missing prediction or absolute error above a supplied threshold), macro
  normalized edit similarity, auxiliary hierarchy-path precision/recall/F1,
  auto-accept rate, and auto-accept error rate. Domain thresholds and the
  observed-term ontology remain `TBD`; no empirical Paper I/II result was
  created.
- Source triage: registered SAGE/Figshare China site-classification metadata,
  Dryad Gonghe core-stress data, and two distinct Xiong'an DOI records. None
  supplies a newly verified phase-1 image source. No file or claimed headline
  borehole count was added to project inventory.
- Next step: human-review the public Padova annotations and Mendeley content,
  then freeze GT, split manifests, critical-error thresholds, and ontology
  version before formal experiments.

## 2026-08-12 — Full Mendeley DWG rendering audit and renderer failure taxonomy

- Objective: generate review-only rasters for all 33 rights-recorded Mendeley
  DWGs without equating a converter return code, emitted SVG IDs, or a
  machine-readable drawing inventory with visual completeness.
- Preserved failure 1: `full_derivatives_v001_failed_strict_reader` contains
  LibreDWG DXFs rejected by ezdxf's strict reader because of invalid
  `SORTENTSTABLE` handle ordering.
- Preserved failure 2: `full_derivatives_v002_failed_mixed_sortents_repair`
  records an unsuccessful repair attempt; observed sequences mixed `(331,5)`,
  `(5,331)`, `(331,331)`, and odd tails, so a hand-written DXF rewrite was
  abandoned rather than silently discard source semantics.
- Preserved failure 3: `full_derivatives_v003` is the unrepaired strict-reader
  route. `full_svg_derivatives_v001_superseded_status_label_error` produced the
  correct artifact classes but used an ambiguous technical-status label; it is
  retained and explicitly superseded, not treated as a result.
- Final audit: `full_svg_derivatives_v002` converts source DWG directly with
  LibreDWG `dwg2SVG`, reconciles renderer IDs against source `minJSON`, checks
  finite positive viewBox geometry, verifies non-transparent raster content,
  and trims excess transparent space. Unsupported entities are not repaired or
  overlaid using inferred coordinates.
- Observation: 20/33 files yielded a non-empty review raster; 11/33 yielded an
  empty raster; 2/33 emitted invalid sentinel geometry. None achieved complete
  entity-ID coverage. Across 789,244 source graphical entities, 538,740 source
  IDs appeared in SVG. These counts measure structural renderer coverage, not
  geometric or semantic correctness. The manifest SHA256 is
  `10b618f35a9ca322379e07a9924f849f72ce1436311f037e258af843b69fdc74`.
- Safety state: all 33 records retain `conversion_may_be_incomplete=true`,
  `visual_fidelity_status=not_assessed`, `human_visual_review_status=not_reviewed`,
  and `benchmark_eligible=false`. Human review count and Ground Truth count are
  both zero. The 33 CAD files are not counted as Phase-1 benchmark pages.
- Decision: use the 20 non-empty derivatives only to triage content/privacy and
  renderer failure. A source-faithful CAD conversion route or source-side PDF
  export remains necessary before any can enter annotation.

## 2026-08-12 — Annotation-integrated numeric ROI re-reading

- Objective: connect the tested constraint-guided re-reading primitives to the
  human annotation workflow without allowing a model proposal to become Ground
  Truth automatically.
- Implementation: numeric MVP fields with a rendered-pixel bbox can trigger a
  high-resolution ROI crop and Tesseract re-read from the UI. The API accepts
  the current unsaved record together with the stored annotation revision, so
  ranking reflects the editor's visible state while optimistic concurrency
  still rejects stale server revisions.
- Evidence: each run stores the source-panel SHA256, ROI bbox/scale, crop and
  crop SHA256, adapter identity, raw OCR regions/confidences, all candidate
  component scores, constraint counts before/after, decision, and immutable
  result SHA256. The ROI can be fetched only through an identity- and
  hash-checked endpoint for visual inspection.
- Safety: the endpoint never saves or edits an annotation. An accepted proposal
  remains `extraction_method=fusion`, `validation_status=needs_review`, and
  carries `CONSTRAINT_GUIDED_REREAD_PROPOSAL`; the reviewer must apply it
  locally, inspect the ROI, explicitly confirm it, and save a new revision.
- Verification: unit/API tests cover non-mutation, stale revisions, preservation
  of unsaved edits, hash-checked ROI retrieval, refusal to mix PDF-point and
  pixel bboxes, and refusal to use the numeric path for text fields.
- Limitation: default UI re-reading is OCR-only. VLM ROI grounding, manually
  drawn bbox selection, real human-corrected case accuracy, false correction
  rate, and Paper II effect sizes remain `TBD`.

## 2026-08-12 — Synthetic PyVista interoperability protocol

- Objective: establish a stable Paper III surface exchange path without
  coupling extraction/evaluation code to a rapidly changing geological-model
  API or claiming that a synthetic interpolated surface is a real 3D model.
- Implementation: a dependency-neutral `SurfaceGrid` converts IDW elevations on
  a strictly ordered regular grid to deterministic triangle topology. The
  optional PyVista adapter writes VTK PolyData (`.vtp`) with `elevation_m` point
  data and an off-screen PNG. PyVista 0.48.4 and VTK 9.6.2 are pinned in the
  `paper3-3d` optional dependency group.
- Real run: `P3_SYNTHETIC_PYVISTA_INTEROP_001` used the four-borehole synthetic
  fixture, boundary index 0, IDW power 2, and an 11×11 grid. It wrote 121 points
  and 200 triangle cells with elevation bounds 96.8–100.8 m. The VTP SHA256 is
  `283830930242804c7fa378972153c93a0da317c10a099739b8e13604fa62478b` and the
  PNG SHA256 is
  `ade2507596b32db5ab15e9898c8007b948f9536d68ce226eea640c6b249c98b5`.
- Evidence boundary: the run is indexed as `protocol_only`; its screenshot is
  an interoperability artifact, not real geology, model accuracy, QC benefit,
  or Paper III empirical evidence. It used CPU/off-screen rendering and did not
  pause mining.
- Decision: retain GemPy as a separate future adapter after a coherent,
  human-verified interval-bearing site passes the existing readiness gate.
  Real raw-vs-QC-vs-GT 3D comparison remains `TBD`.

## 2026-08-12 — Ground-Truth progress and draft-export UI gate

- Objective: reduce manual-review friction without weakening the human Ground
  Truth boundary.
- Implementation: the annotation API/UI now reports per-annotation GT gate
  failures, collection status counts, exportable progress, and aggregate gate
  failure counts. Reviewers can download the current page as JSON, CSV, or
  XLSX; response headers and filenames mark every non-gated export
  `DRAFT_NOT_GT`.
- Safety: the verified-collection JSONL endpoint returns HTTP 409 with exact
  per-page failure reasons unless every annotation passes the existing field-
  level human-authorship/provenance gate. It never promotes or partially
  exports `auto` records as GT.
- Verification: API/export regression tests cover JSON/CSV/XLSX draft labels,
  status counts, and verified-collection rejection. Real Padova GT count
  remains zero because no human review was performed by the automated agent.
- GT semantic repair: MVP borehole-level `null` values now require the same
  human-authored, human-verified, page-traceable evidence as interval nulls;
  unreviewed model abstention can no longer silently become “confirmed absent.”
- Formal-index gate: `formal_benchmark`, `formal_method`, and
  `formal_downstream` labels now require a frozen GT SHA256 plus paper-specific
  protocol evidence. Both index creation and later hash verification reject
  unsupported formal labels.

## 2026-08-13 — Evidence-gated manuscript review packages

- Objective: make the three evolving manuscripts independently auditable while
  preventing structurally complete drafts, audit runs, or synthetic protocols
  from being presented as submission-ready research evidence.
- Implementation: `scripts/build_paper_packages.py` checks required sections,
  BibTeX keys, local links, result-index hashes, unresolved `TBD`/citation
  markers, formal experiment counts, manuscript hashes, and versioned claim
  tags. It emits per-paper evidence audits and explicitly labelled review
  bundles plus a top-level package manifest.
- Claim trace: manuscript numeric claims now point through
  `papers/claim_registry.json` to immutable source files. In addition to source
  SHA256 verification, registry assertions check exact JSON-pointer values and
  read-only SQLite table counts. The Padova catalog claim is bound to 11
  source-provided unverified coordinate records and zero intervals. The
  quarantined Sanming connectivity claim is bound to four auto boreholes, 12
  intervals, and 224 field-provenance rows. Neither is Ground Truth or formal
  downstream evidence.
- Verification: negative tests prove that changed source bytes, unregistered
  manuscript tags, unused registry claims, mismatched indexed metric hashes,
  and incorrect JSON/SQLite numeric assertions fail the structural audit.
  Current package audits report no missing tags, unused tags, or claim-source
  errors.
- Evidence boundary: Paper I, II, and III each pass the structural package
  audit but have zero formal experiment runs and unresolved `TBD` markers. All
  three packages are therefore labelled `DRAFT_NOT_SUBMISSION_READY`.
- Next step: a human reviewer must verify the public Padova annotation pack and
  produce a frozen Ground Truth snapshot before any formal benchmark, Paper II
  ablation, or Paper III raw-vs-QC-vs-GT result can be generated.

## 2026-08-13 — Public OCR+VLM field-ROI engineering audit

- Experiment: `P2_QWEN3VL4B_TESSERACT_UNIPD_ROI_AUDIT_001`; two numeric fields
  from the public Padova `UNIPD_GS1_P001` auto proposal, Tesseract 4.1.1 plus
  Qwen3-VL-4B-Instruct revision
  `ebb281ec70b05090aa6165b016eac8ec08e71b17`, strict prompt
  `constraint_reread_numeric_v001`, greedy decoding, and no human Ground Truth.
- Resource control: the guardian paused only `rtx5090`; the run used physical
  GPU 0 while the other four miners continued. The worker was restored
  immediately afterward, its container returned healthy, and GPU 0 returned to
  100% mining utilization. The initial CLI attempt failed before artifact
  creation because the isolated AI venv needed `PYTHONPATH=src`; the successful
  rerun used the same unused experiment ID.
- Observation: both VLM responses passed the strict numeric-token JSON parser,
  neither declared uncertainty, and both cases shared at least one numeric
  value with OCR. Both decisions remained `NEEDS_REVIEW`, so no proposal was
  accepted. Mean VLM generation time was 3.509931 s/ROI and peak allocated GPU
  memory was 9,032,973,312 bytes. These are engineering diagnostics, not
  accuracy or correction-safety estimates.
- Failure analysis: the narrow collar-elevation crop showed only `35,22` and
  correctly remained under review because no target violation was reduced. The
  source-provided groundwater bbox spanned multiple header cells, so both
  readers emitted total depth `15.00` as well as water table `-5.80`. C6 favored
  the wrong-column `15.0` candidate because it removed the negative-depth
  warning; the run abstained because candidate scores lacked margin.
- Safety revision: after preserving the run unchanged, candidate policy was
  tightened so any reader that emits multiple distinct numbers from one field
  ROI forces `NEEDS_REVIEW`. This prevents geological plausibility from
  automatically selecting among a visibly multi-field crop.
- Scoring repair: audit inspection also found that the then-current target
  violation counter treated any warning in the same borehole container as if
  it affected the selected field. This did not change either recorded decision
  but polluted the collar-elevation before/after count. The counter now accepts
  only an exact affected-field path or an explicitly interval-wide path, with a
  regression test proving that groundwater warnings cannot change a collar-
  elevation candidate's constraint score. The immutable run retains the
  original recorded scores; future runs use the repaired implementation.
- Trace: the run freezes source annotation/image hashes, crop parameters,
  model/prompt/runtime metadata, raw generations, OCR regions, scores, and
  decisions. A recursive artifact manifest additionally hashes both ROI PNGs,
  both field-level result JSON files, and the resolved input manifest; result
  index verification rejects nested artifact tampering or path escape.
- Evidence boundary: source annotations are `auto`, therefore accuracy, FCR,
  method benefit, calibration, and statistical significance remain `TBD`.

## 2026-08-13 — Human-drawn field evidence for annotation and re-reading

- Objective: let a reviewer replace an overly broad display ROI without
  overwriting the immutable source PDF bbox or silently confirming a value.
- Implementation: the annotation UI records a drawn rectangle in rendered
  image pixels, supports non-persistent numeric re-reading from the draft ROI,
  and can bind the rectangle locally as `human_drawn`. The API validates finite,
  ordered coordinates against the rendered image dimensions and requires the
  saving annotator to match the bbox annotator. Binding preserves the field
  value, extraction method, validation status, and original `source_bbox`.
- Provenance: v001 field envelopes now optionally retain
  `display_bbox_source` and `display_bbox_annotator_id`. Native-PDF conversions
  are marked `pdf_transform_v001`; SQLite initialization migrates legacy
  `field_provenance` tables in place, and tabular exports retain both columns.
- Verification: API regression tests cover invalid bounds, non-finite values,
  non-persistence, annotator mismatch, revision history, and temporary reread
  behavior. The full suite passed with 244 tests and 15 upstream deprecation
  warnings; JavaScript syntax and whitespace checks passed.
- Research boundary: no human values were entered and no auto proposal was
  promoted. Padova Ground Truth remains 0 pages; Paper I/II/III empirical
  claims and submission readiness remain `TBD`.

## 2026-08-13 — Record-bound human verification attestations

- Objective: prevent `double_verified` and `expert_verified` from being
  unsupported self-reported labels.
- Implementation: each human verification now records an anonymized actor ID,
  role, revision, timestamp, and canonical record SHA256. Double verification
  requires two distinct IDs on the identical final hash. Any edit invalidates
  earlier attestations for GT gating. Expert verification additionally requires
  a server-side allowlisted ID; the default expert allowlist is empty.
- Export/agreement audit: GT snapshot summaries count all effective attestors,
  not only the last saver. Agreement evaluation rejects overlapping annotator
  ID sets. These checks establish technical identity separation; study-level
  professional qualifications and independence still require real protocol
  records.
- Compatibility: legacy auto proposals without attestation metadata remain
  readable. Pre-existing human-status records are deliberately not
  grandfathered into GT without a hash-bound re-attestation.
- Verification: the full pre-documentation suite passed with 254 tests and 15
  upstream deprecation warnings. No public annotation was modified and Padova
  Ground Truth remains 0 pages.

## 2026-08-13 — Blinded duplicate Padova annotation assignment

- Objective: obtain future agreement evidence from independent answers rather
  than a second reviewer editing a visible first answer.
- Implementation: an immutable builder copies only hash-verified `auto` seeds
  into separate full-overlap tracks, freezes source annotation/record/image
  hashes, and refuses existing outputs. Track services can restrict writes to a
  single anonymized ID. A comparison command requires both complete human-GT
  tracks, disjoint IDs, and a new output path before freezing input hashes and
  pre-adjudication agreement.
- Real task pack: 15 Padova pages were copied byte-identically to track A and
  track B under `/data/GeoLogParser/artifacts/annotation/`; assignment manifest
  SHA256 is `e4c18c84cd06c4ba599cca4e881fbc21bd5d4e6b976964462cee0438ae7508f2`.
  Both track IDs are unassigned placeholders, every page remains `auto`, and
  effective attestation count is zero.
- Negative run: the real comparison command failed at the first `auto` page as
  required and created no agreement artifact. Thus identical model seeds are
  not counted as human agreement.
- Limitation: separate directories/services on one shared Unix account are not
  an adversarial filesystem boundary. Reviewer protocol or separate OS
  permissions are still required. Actual human assignment, agreement,
  adjudication, and Ground Truth remain `NOT COMPLETED`.

## 2026-08-13 — Pre-adjudication field-difference protocol

- Objective: preserve reviewer disagreement at field level before any answer is
  reconciled into final Ground Truth.
- Implementation: agreement output now lists every v001 borehole/interval value
  difference, interval count/ID mismatch, affected document, and both record
  hashes. A separate immutable adjudication-pack builder rechecks every frozen
  annotation file hash and copies both reviewer records plus the discrepancy
  list into case directories.
- Safety: the builder creates zero final records. Disagreements are marked
  `adjudication_pending`; equal records remain `confirmation_pending` because
  agreement alone is not evidence that either answer matches the source.
- Verification: tests cover differing/equal tracks, immutable outputs, and
  mutation after agreement. Actual Padova agreement and adjudication remain
  `NOT COMPLETED` because both real tracks still contain only `auto` seeds.

## 2026-08-13 — Traceable duplicate-annotation status audit

- Objective: report task preparation separately from actual human progress and
  prevent the two copies of each page from being counted as two GT pages.
- Implementation: a live status audit validates each track's annotation-ID set
  against the assignment manifest and records per-file/revision/status/record
  hashes, effective attestations, GT gate counts, and agreement/adjudication
  artifact counts.
- Real snapshot: the Padova task has 15 source pages, two tracks, and 30 task
  files; all remain `auto`. Effective attestations, GT-exportable track items,
  agreement artifacts, and adjudication manifests are all zero. Snapshot SHA256
  is `3906f8297d8a70b01e2b4af4ae1956a4d1b58eddbaa2ef16521192d663864d3e`.
- Publication boundary: Paper I cites these as workflow-readiness counts only.
  The publication-readiness GT count continues to use a final GT root, so
  duplicate tracks cannot inflate dataset or human annotation counts.

## 2026-08-13 — Server-fixed annotation-track actor

- Objective: stop treating a browser-supplied reviewer string as the identity
  control for blinded tracks.
- Implementation: a track service may now fix its actor ID server-side. Saves,
  bbox bindings, and timing sessions reject any conflicting client ID and use
  the fixed actor for attestations. The UI reads the fixed ID from status and
  makes the annotator field read-only.
- Real negative smoke: Track A exposed `padova-reviewer-a` as fixed and rejected
  a Track B save with HTTP 422. The target annotation SHA256 remained
  `76376c6c0277580eaeebf41991885dd1bebf7a1172bc49f6787c9d5322407f0c`,
  revision 1, status `auto`, with zero attestations.
- Limitation: a fixed service actor binds a process to a task track; it does not
  authenticate the human at the keyboard. Authenticated accounts, consent,
  qualifications, and supervision remain deployment/study requirements.
- Verification: full suite passed with 267 tests and 15 upstream deprecation
  warnings; all three paper packages remain `DRAFT_NOT_SUBMISSION_READY`.

## 2026-08-13 — Frozen Chinese borehole open-metadata survey

- Objective: replace ad hoc discovery notes with a rerunnable chain from frozen
  query to raw response, request status, candidate disposition, and file
  inventory, without turning repository search hits into dataset counts.
- Implementation: `survey_open_metadata.py` freezes request parameters,
  explicit User-Agent, UTC timestamps, HTTP status, response bytes/SHA256,
  normalized DataCite records, manually declared dispositions, anonymous
  Mendeley file inventories, and a recursive artifact manifest. Existing output
  directories are immutable; a verifier rejects changed/missing/extra files and
  broken request-to-response hashes.
- Preserved failure: v001 used Python's default browser signature and received
  Cloudflare 1010 for all seven Mendeley file probes. v002 fixed access with a
  stable User-Agent but did not record that effective header in request
  evidence. v003 then used an ambiguous `manually_reviewed` count for automated
  metadata triage. All three artifacts remain unchanged as superseded history.
- Canonical run: v004 issued 32 read-only requests; 27 succeeded and five
  repository probes failed. The five DataCite queries returned 226 unique DOI
  records after overlap deduplication. Fifteen candidates were curated by the
  automated project agent, not a human source reviewer, and
  seven anonymous Mendeley inventories were frozen. Manifest SHA256 is
  `48a4b19577d8e1e61040cbe78caba99ffa187f862c4254692fa108c443d6b540`.
- Evidence boundary: source-reported query totals and abstract quantities are
  not project data scale. The survey can create a content-review candidate but
  is hard-coded to create zero Benchmark-eligible candidates.
- Outcome: one open PDF content-review candidate was identified, but it is an
  English international SedLog source. No new Chinese PDF/JPG/PNG item passed
  both licence and file-inventory gates. Chinese Benchmark GT remains zero.

## 2026-08-13 — Public SedLog PDF acquisition and content audit

- Source: Mendeley DOI `10.17632/v6k9s36pbm.1`, CC BY 4.0. Anonymous inventory
  listed one 10,549,922-byte PDF with SHA256
  `007d26b081677478bd0534b26309c696871c6735237eac7669c53ac7e8e6dd02`;
  the acquired file matched exactly.
- Observation: the PDF has 18 unusually tall native-text pages. Programmatic
  ID checks and a rendered-page review confirmed 18 SedLog lithology columns
  with depth axes, lithology patterns, and structure/fossil symbols. It is
  English, not Chinese, and most MVP borehole header/description fields are
  absent.
- Decision: retain it for Paper I international transfer and layout stress
  testing only. The manifest explicitly sets every page `unannotated` and
  `benchmark_eligible=false`; human GT and eligible-page counts are zero.
- Trace: local PDF manifest SHA256 is
  `f6b0deb3b94e09286eb3c94dd356b8f90ca72fa7d5820b46a0e291c710a88d49`.
  No GPU was used and mining was not interrupted.

## 2026-08-13 — Source-survey verification

- Verification: the full Python suite passed with 275 tests and 15 upstream
  deprecation warnings. Python compilation, all three immutable result indexes,
  the publication-readiness audit, and all three paper-package audits passed.
- JavaScript compatibility note: `app/static/app.js` passed `node --check` with
  the host's Node 12.22.9. The pre-existing CAD review UI uses optional chaining
  and nullish coalescing; Node 12's parser rejected that syntax even though it
  is supported by the target modern browser runtime. No JavaScript files were
  changed in this survey work.
- Publication state: the readiness audit still reports zero exportable Ground
  Truth pages and zero formal runs for Paper I, II, and III. All manuscript
  packages remain `DRAFT_NOT_SUBMISSION_READY` with unresolved `TBD` evidence.

## 2026-08-13 — Licensed structured-data acquisition and content audit

- Acquisition: downloaded and SHA256-verified the frozen Mendeley inventories
  for Binhai BH-CPTU/10-44 (`44` XLSX, `5,923,040` bytes) and the coal-borehole
  minimum release (`4` files, `70,490` bytes). The acquisition evidence SHA256
  values are `a689d0cd41f5c1a94fae6c4e5bfeda0c10f114fb342ab390cae62557e94ea0cf`
  and `1a808d2f89050e5cad4d6bf315a0bc1e6ffe17de8012eb6e8600f7b94b62d9ad`.
- Binhai observation: all 44 files are seven-column CPTU sheets with 3,750 rows
  each, for 165,000 measurement rows. X/Y are redacted as `*`; units, CRS,
  lithology, intervals, borehole records, and laboratory tables are absent. The
  source is ineligible for current formal Paper I-III experiments. Audit v002
  SHA256 is `31628e74ec28aa7d7da0c8cdfd82060bd9abcd4116027339358f9808add13be0`.
- Coal observation: the workbook has 602 unique and complete records. It exposes
  numeric local X/Y/Z and directional borehole/coal-seam fields, but no CRS.
  The README exposes a contact email and precise locations await human review.
  The entrypoint references four absent scripts, so the released workflow is
  not runnable as published. Audit v002 SHA256 is
  `261bee6cdd7b400476aa34c19046034303c2114cf4f26c5cb1c5e0151f852b21`.
- Constraint lesson: `roof_depth + seam_thickness > final_depth` occurs in 594
  coal records, but those fields describe directional drilled/geometric
  quantities with incompletely documented reference semantics. It is retained
  as an observation and must not trigger correction. Audit v001 encoded the
  angle relation incorrectly; it remains immutable as failed history and was
  superseded by v002, where `zenith - inclination = 90 degrees` is verified.
- Evidence boundary: both releases are `source_structured_data`, not document
  images, AI extractions, constraint-validated predictions, or human Ground
  Truth. Formal experiment counts and manuscript status therefore remain
  unchanged. No GPU was used and mining was not interrupted.

## 2026-08-13 — Coal-602 source-field propagation protocol

- Objective: exercise Paper III's multi-seed spatial perturbation mechanics on
  a licensed, non-synthetic record pattern without misrepresenting structured
  source rows as AI output or human Ground Truth.
- Privacy boundary: source Y/X were translated to zero-origin local `u/v`.
  Neither the translation origin, original borehole IDs, absolute coordinates,
  nor gridded proxy values were persisted in experiment outputs. The protocol
  preserves source/audit hashes and aggregate extents only; this is not a human
  privacy or sensitive-location clearance.
- Run: `P3_COAL602_SOURCE_ROOF_PROXY_PROTOCOL_001` used 602 source records, a
  41 by 41 grid clipped to 80 convex-hull points, five perturbation magnitudes,
  and 30 deterministic seeds per magnitude. CPU runtime was 4.402825972 s; no
  GPU was used and mining was not interrupted.
- Observation: at independent signed 1.00 m perturbations of source-reported
  roof depth, the IDW proxy-surface MAE was 0.2604278413437194 m with sample
  standard deviation 0.018737111659730712 m. Metrics SHA256 is
  `85fc812b25b622831f5714ea297c9e2b320ea31f2b67da6db8bfa81873647b94`.
- Claim boundary: the result is `protocol_only`. It is not an extraction metric,
  QC comparison, true coal-seam surface, geological sensitivity estimate,
  Ground Truth study, or formal Paper III experiment. Formal Paper III run count
  remains zero.

## 2026-08-13 — Constraint configuration and applicability audit

- Problem: C1-C10 were implemented and non-mutating, but
  `configs/constraints/default_v001.yaml` did not instantiate the engine. Its
  enable flags and module parameters therefore could not serve as reproducible
  ablation controls. Also, zero evaluated checks were serialized as
  `passed=true, score=1.0`, which could reward missing or inapplicable data in a
  naive aggregation.
- Implementation: added a strict versioned YAML loader that rejects missing or
  unknown sections/keys, validates numeric ranges, and instantiates enabled
  modules with configured tolerance, severity, percentage fields/range, digit
  bounds, and C8 confusables. B1-B6/native audit runners now accept
  `--constraint-config` and freeze its path and SHA256 in future run metadata.
- Semantics: constraint results now expose `status` as `passed`, `violated`, or
  `not_evaluated`. The last state has `score=null` and `evaluated_count=0`;
  `passed=true` remains only for backward compatibility. A directional-source
  record without stratigraphic intervals produces ten `not_evaluated` results,
  not ten successful geological checks.
- Scope: existing immutable experiment outputs were not rewritten. New status
  fields and config hashes apply to future runs. Formal Paper II results still
  require human Ground Truth and the complete one-module ablation matrix.

## 2026-08-13 — Binhai public-version inventory reconciliation

- Objective: determine whether the 10 borehole records and laboratory tests
  named in the Binhai abstract were present in repository version 1 but omitted
  by the acquired version 2.
- Frozen evidence: a focused survey captured two DataCite DOI responses and the
  anonymous Mendeley root-file inventories for v1/v2. All four requests returned
  HTTP 200. The verified 13-artifact manifest SHA256 is
  `bf58363dfe09af09b8b4053f8622ea2e92c84c13754ea061cd3d9746e4e66045`.
- Observation: v1 exposes 44 XLSX totaling 5,954,240 bytes; v2 exposes 44 XLSX
  totaling 5,923,040 bytes. Both inventories cover A1-A16, B1-B15, C1-C5, and
  D1-D8. Version 2 changes filenames to `_update`; neither root inventory lists
  a separate borehole-record or laboratory package.
- Decision: retain Binhai only for non-spatial CPTU protocol development. Phrase
  the discrepancy as abstract scope versus public inventory, not as evidence
  that the stated data do not exist elsewhere. No additional files were
  downloaded, no GPU was used, and formal experiment counts remain unchanged.

## 2026-08-13 — Priority CAD headless-renderer feasibility audit

- Objective: test whether the installed LibreCAD can provide a second explicit
  batch export for the three prioritized Chinese DWGs and quantify only the
  technical pixel occupancy of existing independent rasters.
- LibreCAD result: version 2.1.3 help advertises file opening and debug level,
  with no PDF/PNG/print/export flag. All three isolated `offscreen` probes
  stayed in the GUI event loop for the configured three seconds and were
  terminated; no fatal Qt marker and no export were observed. This is not proof
  that each DXF parsed completely.
- Raster result: ezdxf PNGs for all three were nonblank. The LibreDWG-SVG chain
  produced explicit invalid-geometry placeholders for 009/010, making those
  pairs not comparable. For 011, normalized foreground IoU was
  `0.0005905677887454653`; symmetric F1 with a two-pixel grid tolerance was
  `0.003955665965985095`, below the configured 0.50 diagnostic threshold.
  This is renderer disagreement, not a fidelity verdict or model metric.
- Preserved failure: v001 used nearest-neighbour reduction, which could erase
  one-pixel CAD lines and yielded a spurious exact-zero overlap. It remains
  immutable under `priority_renderer_audit_v001_superseded_nearest_downsampling_error`.
  v002 corrected the resampling; canonical v003 additionally verifies the DXF
  hashes and records the audit-script hash. It uses BOX aggregation followed by
  a nonzero threshold, with a thin-line regression test. Canonical manifest
  SHA256 is `51173c63c25dbe3f47a339a6f4a3429faed1e622bf63339cd2cd770ff4dca4d9`.
- Decision: stop this LibreCAD batch-export route. Keep all 33 DWGs and all
  derivatives quarantined. Human visual, font, privacy, location, and embedded
  content reviews remain zero; Chinese Benchmark pages and GT remain zero. No
  GPU was used and mining was not interrupted.

## 2026-08-13 — Privacy-minimized slopes OCR coverage audits

- Objective: exercise the B1 OCR-to-regex path on all 28 automatically triaged
  engineering-log candidates from the CC BY 4.0 slopes source while preserving
  the source-review and Ground Truth gates.
- Evidence boundary: both runs consumed the frozen 180 DPI review-pack PNGs
  only after preflight verification of the pack manifest, all selected image
  hashes, and all original PDF hashes. OCR pixel boxes were retained only as
  rendered-image `display_bbox` evidence in ephemeral records; PDF
  `source_bbox` remained null. Persisted predictions contain presence/count
  diagnostics and full-record hashes, not OCR text or extracted field values.
- Tesseract run: `P1_B1_TESSERACT_SLOPES_AUDIT_001` completed 28/28 pages with
  no page failures. It emitted borehole-ID candidates on 27 pages and two
  interval candidates on two pages; 14 constraint checks produced four
  violations. Mean CPU latency was 1.6401253737857198 s/page. Metrics SHA256 is
  `f5b6a9a5a5573a6cdc0e5db41d10fcb63bc249c7222a424524084bff7f8d66ba`.
- RapidOCR run: `P1_B1_RAPIDOCR_SLOPES_AUDIT_001` completed 28/28 pages with no
  page failures after verifying all three ONNX model hashes. It emitted
  borehole-ID candidates on 28 pages and no interval candidates. Mean CPU
  latency was 4.1580961258928255 s/page. Metrics SHA256 is
  `377f0540bccc1da53fc672920634139fd09343e3bef79c2f967f3b86af89fe22`.
- Interpretation: field presence and emitted intervals measure extraction-path
  coverage only. They do not establish correctness or rank the OCR engines.
  Both runs explicitly set `accuracy_metrics=null`, human review and human GT
  counts to zero, and Paper I eligibility to `audit_only`. The weak interval
  coverage motivates layout-aware proposal generation after source review; it
  is not evidence of a model-performance difference. No GPU was used and
  mining was not interrupted.

## 2026-08-13 — Single-page Tiber OCR coverage failure

- Objective: apply the same frozen-input, privacy-minimized B1 path to the only
  automatically triaged Tiber stratigraphic-column candidate, providing a
  different layout class without treating one page as a benchmark.
- Runs: `P1_B1_TESSERACT_TIBER_AUDIT_001` and
  `P1_B1_RAPIDOCR_TIBER_AUDIT_001` each completed the one selected page without
  a runtime failure. Tesseract produced 34 OCR text regions and RapidOCR 47,
  but neither downstream regex path emitted a borehole-level target field or
  interval candidate. Metrics SHA256 values are respectively
  `2f7179f2cb7a37980a2ff98aa9e8db70570d158b74ad389bf4952bbcee9f8a54`
  and `a23497ef30e126e632957f4f3a241e9789c1b07bcd0f6cad418a49222c520b02`.
- Interpretation: this is a template-specific structured-coverage failure. It
  shows that OCR text availability is insufficient for the current generic
  regex extractor, but a one-page unreviewed source cannot support an accuracy
  or generalization claim. Both runs remain `audit_only`, with null accuracy,
  zero human review, and zero human GT. No GPU was used.

## 2026-08-13 — SedLog evidence normalization and source-review queue

- Problem: the original SedLog acquisition record predated the frozen
  Mendeley acquisition and page-content contracts and described project-agent
  visual inspection with language that could be mistaken for an independent
  human source review.
- Acquisition: the one public PDF was reacquired from frozen official inventory
  evidence into the mechanical-disk v002 dataset directory. Its 10,549,922
  bytes and SHA256
  `007d26b081677478bd0534b26309c696871c6735237eac7669c53ac7e8e6dd02`
  matched the inventory. Acquisition SHA256 is
  `2c58aaa361285c6aa46a5ad2d2c192ec01d0f6cab9cfa3d083a913fe71835c5f`.
- Content evidence: a versioned automated classification config covers exactly
  18/18 native-PDF pages and labels them provisional digitised SedLog lithology
  columns. Content manifest SHA256 is
  `a00f9079cc9fb5a5ae5bc8328cdedfa6222b193a141bb58ced8f32a36a24b0af`;
  classification is not human review.
- Review pack: 18 complete 180 DPI renders range from 1,120 to 1,345 pixels
  wide and 6,228 to 14,495 pixels high. Every PNG hash was verified, including
  exact HTTP delivery for the first and last items. Review-pack manifest SHA256
  is `85d8cba35d615a7be4e33b010374df07c2600b9f72d3e32fef6974cc69bb5833`.
  Review-status SHA256 is
  `9f2cfa3fc49929fc6e961b339cdfb9e5a1a4c14b409f127997fe9e214b7cc4ca`.
- Boundary: all 18 items remain unreviewed; annotation eligibility, benchmark
  eligibility, and human GT are zero. The source is English international
  layout/transfer material, never Chinese core-Benchmark data. The independent
  review UI runs on port 8003. No GPU was used.

## 2026-08-13 — SedLog native-text and positioned-layout coverage audit

- Objective: measure only whether the existing generic regex and B3
  positioned-depth-range paths produce structured candidates on all 18 SedLog
  pages, without persisting unreviewed source text, field values, or bboxes.
- Run: `P1_NATIVE_LAYOUT_SEDLOG_AUDIT_001` verified the frozen content-summary,
  content-manifest, original PDF, regex implementation, B3 implementation, and
  constraint-config hashes before creating the result directory. It completed
  18/18 pages and observed 1,279 native positioned text regions.
- Observation: generic regex emitted zero intervals, and B3 emitted zero
  intervals. B3 requires at least three distinct explicit `top-bottom` text
  ranges in one x-position bin; the SedLog source primarily expresses
  lithological boundaries as graphics/depth-axis geometry. Mean combined CPU
  latency was 0.08669244633337156 s/page. Metrics SHA256 is
  `1672f03403ccd0a307e1ce4047d1715363d56fe507163c72911862b5655d1fe4`.
- Boundary: this is an `audit_only` structured-coverage failure, not evidence
  of zero geological errors or an interval-recall estimate. Accuracy remains
  null; human review and human GT remain zero. Persisted predictions contain
  hashes/counts only. No GPU was used.

## 2026-08-13 — Manuscript literature-evidence audit

- Objective: replace unresolved related-work placeholders only where verified
  metadata and inspected source text support a bounded claim, without altering
  any empirical `TBD` or publication-readiness state.
- Full-text evidence: archived the published Han and Suh borehole-log article,
  the EMNLP grammar-constrained-decoding paper, the BGS lithology-vocabulary
  paper, and the Solid Earth borehole-interpretation uncertainty paper under
  `/data/GeoLogParser/artifacts/literature`. SHA256 values are recorded in
  `docs/literature_evidence.yaml`; PDFs and extracted text are not committed.
- Han and Suh comparison: verified 47 Korean abandoned-mine reports, 908
  borehole-log pages, five manually assigned types, an 8:2 page split for
  type classification, and Type-1-only spreadsheet structuring. Their OCR
  comparison is example/qualitative rather than GeoLogParser's field/interval
  protocol, so their classification score is not reused or treated as a
  structured-extraction baseline.
- Additional scope: verified that grammar constraints address formal output
  validity rather than factual geology; that published lithology schemes are
  hierarchical and purpose-dependent; and that uncertainty in interpreted
  contacts/drillhole observations can propagate into downstream models.
  Interactive-ML literature motivates measuring users but provides no project
  time-saving effect size.
- Engineering gate: the paper-package audit now requires every manuscript
  citation key to have a structured literature-evidence entry with identifier,
  verification source/level, and permitted claim scope. Missing or malformed
  entries fail structural completeness.
- Boundary: all three manuscripts retain their formal empirical `TBD` values,
  zero-formal-run status, and `DRAFT_NOT_SUBMISSION_READY` label. No GPU was
  used and mining was not interrupted.

## 2026-08-13 — Source-review operator workflow

- Objective: reduce avoidable navigation and form-entry overhead in the human
  content/privacy review queue while preserving the distinction between a
  source decision and geological Ground Truth.
- Interface: added queue filters, previous/next controls, stable image zoom,
  explicit reviewer-ID handling, an unsaved `Set all absent` form helper, live
  progress, and automatic movement to the next unreviewed item after save.
- Integrity: API saves remain revision-conflict protected, stored review
  bindings are checked before update, a process-local lock serializes writes,
  and the live status snapshot is atomically refreshed under the mutable review
  root. A server-fixed reviewer ID rejects a conflicting browser-supplied ID.
- Boundary: these changes create no review decisions. The international and
  SedLog queues still have zero completed human reviews, zero annotation-
  eligible pages, zero benchmark-eligible pages, and zero human GT. The form
  helper does not save or infer eligibility. No GPU was used.

## 2026-08-13 — Source-review-gated annotation proposal builder

- Objective: make the transition from a completed human source/privacy review
  to machine-generated annotation candidates explicit, reproducible, and
  independently auditable.
- Implementation: `build_eligible_annotation_pack` first reruns the complete
  page-review audit into a temporary manifest and requires a byte-identical
  eligible manifest. It then verifies review JSON, source-file, and frozen
  rendered-image hashes before copying panels and creating revision-1 `auto`
  annotations.
- Coordinate policy: native PDF direct text keeps PDF-point `source_bbox` and
  derives `display_bbox` with the frozen PDF transform. Scanned PDFs and images
  read the frozen review PNG with the injected OCR adapter and keep OCR boxes
  only as `display_bbox` (`ocr_rendered_pixels_v001`); pixel coordinates are
  never represented as PDF coordinates.
- Integrity policy: output roots are immutable; metadata binds the eligible
  manifest, content-review revision/hash/reviewer, source acquisition/file
  hash, rendered hash, dataset DOI/license, and explicit non-GT status. Tests
  cover incomplete review, manifest/review/source/render tampering, both
  coordinate modes, and overwrite refusal.
- Boundary: no real page has passed human source review yet. The new builder
  generated no project dataset or benchmark result in this run. Human GT,
  accuracy, F1, calibration, and publication readiness remain unchanged and
  unreported (`TBD`). No GPU was used.

## 2026-08-13 — Swiss paired-sample audit and authoritative metadata benchmark

- Inspected the public `swisstopo/swissgeol-boreholes-dataextraction` repository
  at commit `3e8fdc10ba3ff158392a3a44fce2e62f6e9b0e12`.
- The repository includes `example/example_borehole_profile.pdf` and
  `example/example_layers_groundtruth.json`, but the JSON describes 0–3 m
  gravel/sand layers while the paired PDF visibly contains the SST KB5 tunnel
  profile with approximately 0–30 m slate/sandstone intervals. The example
  fixture is therefore not a defensible image-to-interval reference and was
  not promoted to Gold.
- Repository issues document an approximately 6,550-file Thurgau collection and
  database-derived coordinate/elevation/depth references, but the source files
  and GT are not publicly downloadable from the cloned repository; comments
  also document coarse-layer definitions and known GT inconsistencies. These
  records remain a source lead, not a frozen Real Gold interval set.
- The official BGS fixed-record sample was rerun as
  `P1_METADATA_BGS_TESSERACT_FORMAL_002` on 2026-08-13. Four official scan PDFs
  (20 pages) were paired by source record ID with official BGS metadata. The
  experiment is indexed as `formal_authoritative_metadata`, with
  `reference_ground_truth_tier=AUTHORITATIVE_METADATA`; it evaluates only
  borehole ID and coordinate metadata because interval labels are absent.
  Results: ID exact match 2/4 (0.5), X MAE 0 m with 4/4 coverage, Y MAE 0 m
  with 4/4 coverage, final-depth coverage 0/4, and zero emitted intervals.
  These are real public-authoritative metadata results, not interval or
  lithology accuracy.

## 2026-08-13 — Expanded BGS authoritative-metadata comparison

- Froze 31 official BGS scan PDFs (106 pages) in
  `/data/GeoLogParser/datasets/public/bgs_authoritative_metadata_v001`; the
  manifest binds each `source_record_id`, official metadata row, local file,
  size, and SHA256. Requested record 74 was unavailable and is explicitly
  listed as missing rather than silently substituted.
- `P1_METADATA_BGS_TESSERACT_FORMAL_003` completed on all 31 documents.
  Borehole-ID exact match was 29/31. X/Y coverage was 31/31; one lost leading
  X digit produced an X MAE of 9,677.419 m, while Y MAE was 0 m. Final-depth
  coverage was 0/31. One unsupported interval was emitted. Runtime was 2.210
  s/page on CPU.
- `P1_METADATA_BGS_RAPIDOCR_FORMAL_001` completed on the identical frozen set.
  Borehole-ID exact match was 31/31 and both coordinate fields had 31/31
  coverage with zero paired MAE. Final-depth coverage was only 1/31; the sole
  value was 192.0 m against catalogue LENGTH 58.52 m, an absolute error of
  133.48 m. No intervals were emitted. Runtime was 3.815 s/page on CPU.
- Because the first expanded Tesseract run used 150-DPI rendering while
  RapidOCR used 300 DPI, a matched 300-DPI Tesseract run was added as
  `P1_METADATA_BGS_TESSERACT_FORMAL_004`. It recovered 25/31 IDs, covered X/Y
  on 31/31 records with zero paired MAE, covered final depth on 0/31, and
  emitted no intervals at 3.562 s/page. Formal backend comparisons use this
  matched-DPI run; the 150-DPI result remains separate resolution-sensitivity
  evidence.
- Both runs are indexed only as `formal_authoritative_metadata`. BGS catalogue
  `LENGTH` is a final-depth proxy, and the source has no interval/lithology
  reference. Consequently these results support a real metadata and critical
  failure analysis, not a complete borehole-log extraction benchmark.

## 2026-08-13 — Real metadata consensus and abstention study

- Added a reference-blinded decision policy over the matched 300-DPI
  Tesseract/RapidOCR BGS first-pass outputs. The policy accepts only equal,
  non-null values from both readers; authoritative references are consulted
  only after decisions are frozen for scoring.
- `P2_BGS_METADATA_CONSENSUS_ABSTENTION_001` evaluated 124 field decisions
  across 31 documents. It auto-accepted 87/124 fields (coverage 0.7016) with
  1.000 accepted accuracy, routed 37 fields to review, and captured all 37
  observed errors/omissions (review recall 1.000).
- Field results: borehole ID accepted 25/31 at 1.000 accuracy; X and Y each
  accepted 31/31 at 1.000 accuracy; final depth accepted 0/31 and routed all
  cases to review. The outcome demonstrates a real coverage–reliability tradeoff
  for authoritative metadata, not a geological-constraint or interval result.

## 2026-08-13 — Real structured-source downstream QC comparison

- Added a controlled dual-channel study on 602 real structured-source records.
  Each channel independently received a 10% rate of fixed-magnitude signed
  scalar errors; source reference values were used only after each downstream
  policy was frozen.
- The first deletion-only run showed that exact-consensus rejection retained
  about 81.5% of points but increased IDW surface MAE to approximately
  0.73–0.74 m across all injection magnitudes. Diagnostic tests confirmed that
  the dominant mechanism was loss of spatial support, not only same-error
  acceptance.
- The final indexed run `P3_COAL602_CONSENSUS_QC_CONTROLLED_003` compared raw,
  consensus deletion, and support-preserving mean fusion over 30 paired
  repetitions per magnitude. Mean fusion reduced surface MAE by 18.3%–22.0%
  relative to raw, improved 26–29/30 paired repetitions per magnitude, and had
  two-sided exact sign-test p values below `6e-5` for every magnitude.
- Earlier v001/v002 runs remain immutable but are labelled failure-analysis or
  audit evidence. V003 is the sole formal result from this experiment chain.
  The source has no declared CRS and is not image-derived extraction or human
  Ground Truth, so those claims remain out of scope.

## 2026-08-13 — Autonomous data-tier and controlled benchmark track

- Objective: remove the human source-review UI from the only path of project
  progress while preserving scientific and licensing boundaries. The UI remains
  available as an optional override, but automated compliance, Synthetic, and
  Silver are now explicit separate data tiers.
- Compliance: `scripts/run_automated_compliance_review.py` generated
  `/data/GeoLogParser/artifacts/compliance/automated_compliance_v002.json`.
  Across the 33 registry entries the automated evidence gate reported 14
  `ELIGIBLE`, 17 `AMBIGUOUS`, and 2 `EXCLUDE` decisions. The report is explicitly
  `review_type=automated_compliance_review`, `human_reviewed=false`; for visual
  sources its privacy scope is text metadata only and does not establish visual
  privacy or sensitive-location absence.
- Synthetic data: generated immutable
  `/data/GeoLogParser/datasets/synthetic_borehole_logs_v001` with 32 PNG pages,
  32 schema-valid known labels, 8 template families, deterministic seed
  `20260813`, degradation metadata, and manifest SHA256
  `9a28a97bc69a9950b755acf203d99003f32eb439caa24952160f40f041b50acd`.
  Labels use `ground_truth_tier=SYNTHETIC` and `validation_status=synthetic_verified`;
  human GT remains zero.
- Controlled OCR result: `P1_B1_SYNTHETIC_CONTROLLED_001` is preserved as
  failure-analysis evidence (Tesseract+regex initially misread the title as
  borehole ID on 32/32 pages). After a regex boundary fix,
  `P1_B1_SYNTHETIC_CONTROLLED_002` measured on the same frozen 32-page set:
  borehole-ID exact match `23/32 = 0.71875`, final-depth MAE `0 m` with 32/32
  coverage, interval precision `1.0`, interval recall `0.7086614173`, interval
  F1 `0.8294930876`, matched top/bottom boundary MAE `0 m`, and CPU latency
  `0.3787452128 s/page`. These are controlled Synthetic metrics only, not Real
  Gold benchmark results; formal Paper I count remains zero.
- Silver protocol: added isolated Extractor A/B and adjudicator contracts that
  produce `SILVER_HIGH_CONFIDENCE` or `SILVER_UNCERTAIN` plus constraint-bound
  hard cases. An 8-page PSM-6 versus PSM-11 smoke produced 8
  `SILVER_HIGH_CONFIDENCE`, 0 uncertain cases, and 1 automatically collected
  hard case; accuracy metrics remain null and the pack is not Gold.
- Boundary: no public or internal source was promoted to Gold, no Human Review
  was fabricated, and no GPU was used.

## 2026-08-13 — BGS first-page controlled robustness benchmark

- Dataset: built `/data/GeoLogParser/datasets/public/bgs_metadata_robustness_v001`
  from the frozen 31-document BGS authoritative-metadata manifest. Each source
  PDF was rendered at 300 DPI on page 1 and transformed into seven deterministic
  profiles (`clean`, resolution 0.50, blur radius 2.0, Gaussian noise 16,
  3-degree skew, JPEG quality 30, and contrast 0.40), producing 217 derived
  images. The degradation manifest SHA256 is
  `5a1205c944a5cb652967b99e6478169805db35f749dffe44124076eafd766628`.
- Scope: official borehole ID, easting, and northing only. Final depth is not
  scored in this first-page robustness study; interval and lithology reference
  data remain unavailable. The transformations are controlled synthetic
  perturbations of real scans, not naturally sampled document damage.
- Tesseract result: `P1_BGS_METADATA_ROBUSTNESS_TESSERACT_001`. Complete ID/X/Y
  exact extraction was 24/31 on clean pages, 15/31 under blur, and 9/31 under
  3-degree skew. Non-missing X/Y values had zero paired MAE except for two
  gross Y-coordinate errors under 3-degree skew (paired Y MAE 54,162.4 in the
  non-missing subset); degradation otherwise primarily caused omissions.
- RapidOCR result: `P1_BGS_METADATA_ROBUSTNESS_RAPIDOCR_001`. Complete ID/X/Y
  exact extraction was 31/31 on clean pages, 31/31 under 3-degree skew, and
  7/31 under JPEG quality 30. Non-missing X/Y values again had zero paired
  MAE. The two backends therefore exhibit distinct perturbation sensitivities.
- Decision: index both runs as `formal_authoritative_metadata_robustness`, add
  separate claim-registry entries, and keep all interval/lithology and
  cross-template conclusions `TBD`.

## 2026-08-13 — Swissgeol example Ground-Truth pairing audit

- Audited public repository commit
  `3e8fdc10ba3ff158392a3a44fce2e62f6e9b0e12` using
  `scripts/audit_swissgeol_example_groundtruth.py`.
- `example_groundtruth.json` matches the visible
  `example_borehole_profile.pdf` header: coordinates 615790/157500, drilling
  date 1995-09-03, reference elevation 788.6, and borehole name SST KB5.
- `example_layers_groundtruth.json` does not match the same PDF. Its shallow
  gravel/sand layers conflict with the visible German tunnel profile, whose
  material text includes Tonschiefer, Sandstein, Schiefer, and Kakirit.
- Artifact: `/data/GeoLogParser/artifacts/source_surveys/`
  `swissgeol_example_groundtruth_audit_v001.json`. Decision:
  `EXCLUDE_MISMATCHED_FROM_GOLD`; no interval/lithology labels were promoted.

## 2026-08-14 — Swissgeol Thurgau authoritative interval pilot

- Acquisition: froze 32 published Swissgeol Thurgau PDF/database pairs under
  `/data/GeoLogParser/datasets/public/swissgeol_thurgau_paired_v001`. The
  collection contains 42 PDF pages and 145 official database intervals. The
  acquisition manifest SHA256 recorded by `dataset.json` is
  `c1156060ad706731fb7c604e4e263cc45d1d21db35adefedff3db027310de388`;
  the canonical record-set SHA256 is
  `2bfa3f6c8ff55a3938bad1eda0527119aff603db4f39c5c9a6447770a6b85af0`.
- Pairing audit: official database intervals were not assumed to match visible
  PDF tables. A conservative native-layout-text audit classified 9 documents
  (21 intervals) as exact complete source-table/database agreement, 8 as
  partial or mismatched, and 15 as having no conservatively parsed explicit
  interval table. Only the 9 exact documents form
  `gold_interval_manifest_v001.jsonl`; scope is top/bottom/thickness only.
  `human_reviewed=false`, and lithology, description, bbox, and material
  semantics remain excluded.
- Diagnostic result: `P1_SWISSGEOL_TG_INTERVAL_TESSERACT_FORMAL_001` rendered the
  9 selected PDFs at 250 DPI and predicted only from Tesseract `eng`, PSM 3
  raster OCR plus the conservative interval parser. It predicted 15 of 21
  reference intervals. All 15 matched within ±0.05 m: precision 1.000, recall
  0.7142857143, F1 0.8333333333, and matched top/bottom MAE 0 m. Six of nine
  documents were completely exact. The six unmatched intervals comprise one
  partial extraction and two complete section-detection failures; there were
  no spurious intervals. Wall time was 28.143690 s (3.127077 s/document) on
  CPU.
- Validity correction: review of the executed code found that run 001 supplied
  the official final depth to interval candidate filtering/ranking. The output
  files remain immutable, but the result index reclassifies it as
  `diagnostic_oracle_metadata`; it is excluded from independent extraction and
  formal benchmark claims.
- Reference-independent result:
  `P1_SWISSGEOL_TG_INTERVAL_TESSERACT_FORMAL_002` uses the same 250-DPI,
  Tesseract `eng`, PSM 3 raster path but passes no reference field to
  prediction. It predicted 16 of 21 intervals, all matched within ±0.05 m:
  precision 1.000, recall 0.7619047619, F1 0.8648648649, matched top/bottom MAE
  0 m, and 6/9 complete documents. Five reference intervals were omitted and
  no spurious interval was emitted. Wall time was 28.620007 s (3.180001
  s/document) on CPU. This is the only Swissgeol run in the formal
  authoritative-interval evidence tier.
- Evidence boundary: this is a source-agreement-selected explicit-table pilot,
  not a representative random sample or human annotation. It supports a
  narrow real-document interval-boundary result but not lithology accuracy,
  cross-template generalization, or the full Paper I benchmark claim.
- Rights: source/item licence, attribution, privacy, sensitive-location,
  embedded-content, and redistribution status remain
  `PENDING_MANUAL_PRE_SUBMISSION_REVIEW`. The project may use the source
  internally, but source PDFs and derived assets are not released.

## 2026-08-14 — Swissgeol incremental held-out interval evaluation

- Successor acquisition: froze 96 PDF/database pairs under
  `/data/GeoLogParser/datasets/public/swissgeol_thurgau_paired_v002`, covering
  492 official database intervals. Acquisition examined 600 candidate rows
  with zero download failures. The acquisition manifest SHA256 is
  `13fde359ffcbf67173fc9fda17815e321cdb0064fbfb028ed982cf4262aaaad4`;
  the canonical record-set SHA256 is
  `d1c1506eff68d156abfdc5ac26263b98a457696ba7f3a794734f642511265c53`.
- Pairing audit: 29 documents/76 intervals had exact complete agreement between
  a conservatively parsed explicit source-PDF table and the official database;
  34 documents were partial or mismatched and 33 exposed no conservatively
  parsed explicit table. After excluding every one of the nine v001
  parser-development records, the incremental held-out manifest contains 20
  documents, 24 pages, and 55 intervals. Its SHA256 is
  `a73e2195d871429d4d8e27ff140ac45cd5cc8b1ffdf16a990089540de0319539`.
- Paper I result: `P1_SWISSGEOL_TG_INCREMENTAL_TESSERACT_FORMAL_003` applied the
  previously frozen 250-DPI Tesseract `eng` PSM-3 raster parser without any
  reference-field conditioning. It predicted 55 intervals; 47 matched and
  eight were spurious, while eight reference intervals were unmatched.
  Precision, recall, and F1 were all `0.8545454545`; matched top/bottom MAE was
  `0 m`; 17/20 documents were completely exact. Wall time was `76.635878 s`,
  or `3.831794 s/document`. Run 002 is retained as development evidence and is
  excluded from held-out claims.
- Paper II result: `P2_SWISSGEOL_TG_CONSTRAINT_REREAD_HELDOUT_001` evaluated a
  reread policy frozen on v001 and having zero record overlap with v002. The
  first-pass and final F1 were both `0.8545454545`. None of three incorrect
  first-pass documents triggered rereading; one of 17 correct documents
  triggered; no reread was accepted. Incorrect-document trigger recall was
  `0/3`; false correction rate is undefined rather than zero because there
  were no automatic corrections. The result is retained as a formal negative
  result: structural and reader-disagreement triggers missed plausible but
  incorrect sequences.
- Validity boundary: the observed v002 failures must not be used to tune and
  re-evaluate a successor trigger on the same records. Any redesigned policy
  requires a new disjoint acquisition or a separately frozen untouched subset.
- Rights: reuse and redistribution remain
  `PENDING_MANUAL_PRE_SUBMISSION_REVIEW`; all source PDFs and derived page
  assets remain local.

## 2026-08-14 — Swissgeol v003 preregistered development/held-out freeze

- Acquisition: extended the public Swissgeol collector with start-page,
  canton, record-prefix, and prior-manifest exclusion controls. The v003 run
  scanned 1,200 candidate rows from sorted pages 7–18, froze 160 new public
  PDF/database pairs with 767 official intervals, and recorded zero failures.
  Manifest SHA256:
  `2e665fbb7c3505a7f81c6f06a830a4798aa46cb4c5c38a1fbe8cc3f2408c6a45`;
  record-set SHA256:
  `424196ec97d3a4a325e8099f5f5ef948c3ed2289a96190dbd71ddca36524ab2b`.
- Pairing audit: 72 documents/165 intervals had exact complete explicit-table
  agreement with the official database; 44 were partial/mismatched and 44 had
  no conservatively parsed table. Gold manifest SHA256:
  `a4d19e8f83d8065bfa1cb92687c94b7d88c7f0f97d5406d3e9db460802b3a974`.
- Split freeze: before model evaluation, salted PDF-content groups were assigned
  to development and held-out partitions. Development contains 37 documents/85
  intervals (SHA256
  `e18e1378c4e718e9658c9cd45057fc55ae4e8df9d97fb4e7e7a92f38a3c443a8`);
  held-out contains 35 documents/80 intervals (SHA256
  `afb921fb606bd2e5f6213438edab775c41285cec78747e44319dadad6d355dc7`).
  Record and PDF-hash overlap between partitions and against v002 are zero. One
  duplicate PDF-content group is kept wholly within a single partition.
- Decision: only the development partition may be used to inspect errors and
  redesign triggers. The v003 held-out partition must remain unobserved until
  the successor policy and configuration are frozen in Git.
- Rights: source/item terms remain
  `PENDING_MANUAL_PRE_SUBMISSION_REVIEW`; source and derived assets remain
  internal and are not redistributed.

## 2026-08-14 — Swissgeol v003 development-only reread redesign

- v1 development diagnostic:
  `P2_SWISSGEOL_TG_CONSTRAINT_REREAD_DEV_V003_001` ran only on the frozen
  37-document/85-interval development partition. First-pass F1 was
  `0.9156626506`; final F1 was `0.9285714286`. Four of six incorrect documents
  triggered, three of 31 correct documents triggered, and two rereads were
  accepted, but neither produced a completely correct document. Development
  correction success was `0/2`; development FCR was `0/2` because neither
  accepted change corrupted a previously correct document.
- Error diagnosis: two missed sequences arose from conservative parsing of OCR
  table separators and leading `O`/zero confusion. Other errors showed that
  PSM-4 and repeated high-resolution readings could agree on a complete
  zero-based interval sequence while the v1 preservation rule retained a
  spurious first-pass split. A non-zero-start high-resolution sequence was also
  observed and was judged insufficient for automatic completion.
- v2 development result:
  `P2_SWISSGEOL_TG_CONSTRAINT_REREAD_DEV_V003_002` added narrowly scoped OCR
  normalization and conservative peer/high-resolution sequence consensus.
  First-pass F1 rose to `0.9467455621`; final F1 was `0.9880952381`. All four
  incorrect first-pass documents triggered, three rereads were accepted and all
  three corrected their documents, development FCR was `0/3`, and one error was
  safely left for review. Three of 33 correct documents triggered. These are
  development results and are excluded from held-out paper claims.
- Freeze: ADR-012 records the v2 policy. Code, tests, parser normalization,
  trigger set, and acceptance criteria must be committed before the v003
  35-document/80-interval held-out manifest is evaluated.

## 2026-08-14 — Swissgeol v2 held-out interval result

- Freeze evidence: policy v2 was committed as `e1cec13` before the held-out
  manifest was first passed to the runner. Evaluation and development manifests
  have zero record overlap and zero PDF-content-hash overlap.
- Experiment:
  `P2_SWISSGEOL_TG_CONSTRAINT_REREAD_HELDOUT_V003_001` evaluated 35 documents
  and 80 authoritative source-agreement intervals. The held-out manifest SHA256
  is `afb921fb606bd2e5f6213438edab775c41285cec78747e44319dadad6d355dc7`.
- First pass: 66 of 74 predictions matched; precision `0.8918918919`, recall
  `0.825`, F1 `0.8571428571`, and 25/35 documents were completely exact.
- v2 result: 70 of 72 predictions matched; precision `0.9722222222`, recall
  `0.875`, F1 `0.9210526316`, and 29/35 documents were completely exact.
  Matched top/bottom MAE remained `0 m`.
- Review/correction: seven of ten erroneous documents triggered; two of 25
  correct documents triggered. Four rereads were accepted, all four converted
  an erroneous document to an exact document, and no correct document was
  corrupted. Correction success was `4/4`; FCR was `0/4`. Five documents were
  routed to review. Three errors did not trigger and three triggered errors
  remained unresolved.
- Evidence boundary: the held-out improvement is evidence for the complete v2
  package of conservative parser normalization, reader disagreement, high-
  resolution rereading, and sequence consensus. It does not isolate the causal
  contribution of geological constraints, and the four-correction FCR
  denominator is too small for a broad safety claim.
- Immutable hashes: metrics
  `936daadc70b6d4f45d7114d48799d74d4c6a00d24fbe21ffee4ce3c430f1dc80`;
  predictions
  `1fb1e909fb613cfd9211c983e96cc38a69c038e2524085758220840bb9c5eb63`;
  artifact manifest
  `a3b23489591da90b5663546ef2ca64834480d54aa9433aa2d003e666cbd43ddf`.

## 2026-08-14 — Frozen-artifact secondary component analysis

- Experiment: `P2_SWISSGEOL_TG_V2_SECONDARY_ABLATION_001` was specified and
  executed after the full v2 held-out result. It is labelled
  `secondary_descriptive_post_result_ablation`, not an independent confirmatory
  experiment, and it does not retune or rerun the held-out policy.
- Legacy parser first pass: precision `0.8714285714`, recall `0.7625`, F1
  `0.8133333333`, 23/35 exact documents.
- v2 parser first pass: precision `0.8918918919`, recall `0.825`, F1
  `0.8571428571`, 25/35 exact documents.
- v2 parser with v1 preservation-based acceptance: precision `0.8933333333`,
  recall `0.8375`, F1 `0.8645161290`, 26/35 exact documents.
- Full v2: precision `0.9722222222`, recall `0.875`, F1 `0.9210526316`, 29/35
  exact documents.
- Interpretation: narrow OCR normalization and the complete-sequence consensus
  acceptance rule both contributed on the frozen artifacts. This analysis does
  not isolate geological-constraint causality. Legacy-parser change counts are
  parser differences and must not be reported as corrections or FCR.

## 2026-08-14 — Paper I v003 content-group held-out baseline

- Experiment: `P1_SWISSGEOL_TG_CONTENT_HELDOUT_TESSERACT_FORMAL_004` used only
  250-DPI raster pages, Tesseract `eng` PSM 3, and the parser frozen before the
  v003 held-out test. It did not use PSM-4, high-resolution rereading, or any
  reference field during prediction.
- Dataset: 35 PDF-content-group held-out documents and 80 authoritative source-
  agreement intervals; manifest SHA256
  `afb921fb606bd2e5f6213438edab775c41285cec78747e44319dadad6d355dc7`.
- Result: 74 predicted intervals, 66 matches, 14 unmatched references, and
  eight unmatched predictions. Precision was `0.8918918919`, recall `0.825`,
  F1 `0.8571428571`, and 25/35 documents were completely exact. Matched
  top/bottom MAE was `0 m`; wall time was `106.628839 s` or
  `3.046538 s/document`.
- Cross-paper boundary: Paper I uses this run as the single-pass benchmark.
  Paper II reuses the same frozen input and first-pass baseline only to measure
  the additional rereading/correction effect; the method gain and correction
  safety are not claimed as Paper I contributions.

## 2026-08-14 — Paper III image-boundary surface diagnostic

- A direct attempt to apply the single-page high-resolution reread runner to
  the full 72-document source-agreement pool stopped at a multi-page PDF. The
  failure exposed an implementation boundary, not a scientific result; the
  partial run is not indexed or used for claims.
- Instead, the downstream diagnostic was computed from the already completed,
  reference-blinded Paper II held-out predictions in
  `P2_SWISSGEOL_TG_CONSTRAINT_REREAD_HELDOUT_V003_001`. The new run
  `P3_SWISSGEOL_TG_BOUNDARY_SURFACE_FROM_FROZEN_REREAD_002` adds only the
  authoritative coordinates and collar elevations after extraction decisions
  were frozen.
- On 35 held-out documents and 423 fixed IDW queries inside the authoritative
  coordinate convex hull, raw first-boundary depth MAE was `1.470588 m` and
  reread final-boundary depth MAE was `0.941176 m`. Raw surface MAE was
  `3.401597 m`; reread surface MAE was `3.049677 m`. Four rereads were
  accepted and five documents remained in review.
- Scope limitation: this is not complete end-to-end spatial extraction.
  Coordinates and collar elevations are inherited from the authoritative
  structured record, only the first interval boundary is evaluated, and the
  sample is a one-canton source-agreement held-out pilot. The result is indexed
  as `formal_authoritative_boundary_downstream`, while full spatial metadata
  extraction and real stratigraphic modelling remain `TBD`.

## 2026-08-14 — USGS-142 cross-source interval diagnostic

- An official USGS Idaho borehole PDF with an explicit generalized-lithology
  legend was acquired to test a genuinely different source family. The local
  file is 115,476 bytes with SHA256
  `4eea58daf59f014b5cd71172bc80e0a3a360b8b44fbe2a8494a90b693fcf50d4`.
- The frozen reference contains 12 depth/lithology intervals from the PDF
  legend. Prediction uses only a 400-DPI raster crop of page 2 and Tesseract
  PSM 11; native PDF text is excluded from prediction.
- Experiment `P1_USGS142_CROSS_SOURCE_INTERVAL_FORMAL_002` recovered all 12
  intervals exactly: precision/recall/F1 `1.000`, complete-document exact
  `1/1`, and matched top/bottom MAE `0.000 m`.
- This is a one-document source-specific diagnostic, not representative
  source-disjoint generalization. The source licence and redistribution scope
  remain pending manual pre-submission verification and are recorded in the
  data registry and source ledger.

## 2026-08-14 — USGS-144 cross-source interval diagnostic

- A second official Idaho release, USGS-144, was frozen as a separate source
  diagnostic. The local three-page PDF has SHA256
  `bae4d58bda8c5d134be39866f3b5b23fad4b52c8d3f63866873210fd53ef1258`.
- The reference manifest preserves eight explicit depth/lithology descriptions,
  including the printed 635–639 ft interval even though the header reports a
  638 ft total depth. No correction was applied to resolve this source
  inconsistency.
- Experiment `P1_USGS144_CROSS_SOURCE_INTERVAL_FORMAL_001` rendered all three
  pages at 400 DPI and used Tesseract PSM 11 without native-PDF text. It
  recovered 8/8 intervals exactly: precision/recall/F1 `1.000`, complete-
  document exact `1/1`, and matched top/bottom MAE `0.000 m`.
- Interpretation remains deliberately narrow: this is a one-document transfer
  diagnostic, not a representative source-disjoint estimate. Item-level rights
  and redistribution terms remain pending manual pre-submission verification.

## 2026-08-14 — USGS-151 explicit-interval source audit

- The 98-page scanned lithologic core log was rendered at 250 DPI and processed
  independently with Tesseract PSM 11 and PSM 6. The audit used no native PDF
  text because the file is image-only.
- PSM 11 parsed 71 explicit `LITHOLOGY` intervals; PSM 6 parsed 61. Exact
  agreement on page, normalized lithology, top depth, and bottom depth retained
  61 intervals across 40 pages. Ten PSM-11-only rows remain unresolved.
- The output tier is `SOURCE_EXPLICIT_MACHINE_CONSENSUS`, with
  `human_reviewed=false` and `eligible_for_human_gold_claims=false`. It is a
  transfer/audit candidate, not a formal accuracy reference.
- The exact public source record, licence, redistribution scope, and precise-
  coordinate sensitivity remain unresolved. The files and derived OCR stay
  local under `/data/GeoLogParser`; the source is recorded as `AMBIGUOUS` in
  the verification ledger rather than entering the formal benchmark.

## 2026-08-14 — USGS-151 cross-engine corroboration

- RapidOCR/ONNX processed the same 98 frozen 250-DPI page rasters using model
  hashes recorded in the audit output. It parsed 67 explicit lithology
  intervals in 171.36 seconds.
- Fifty-seven intervals agreed exactly with the earlier Tesseract PSM-6/PSM-11
  consensus on page, normalized lithology, top depth, and bottom depth. These
  rows cover 40 pages; four Tesseract-consensus rows and ten RapidOCR rows did
  not agree across engines.
- The evidence tier was strengthened to
  `SOURCE_EXPLICIT_CROSS_ENGINE_CONSENSUS`, but remains machine transcription
  of one source image and is not Human Gold or formal accuracy evidence.

## 2026-08-14 — USGS source reconstruction and Raft River external interval benchmark

- Reconstructed the exact USGS-151 release as Trcka and Twining (2023), DOI
  `10.5066/P9KOXCE5`, ScienceBase item `6307a9e2d34e3b967a8c11e7`. The local
  196,855,513-byte lithologic PDF and 13,392-byte driller-notes CSV match the
  official file inventory. The CSV is not interval GT, but supplies sparse
  independent companion evidence for contacts near 48.1, 580, 1197, and
  1680 ft.
- Acquired the official Raft River 12-borehole release (Dorn and Twining,
  2023; DOI `10.5066/P9JELNQ5`). The 12 driller reports contain 47 pages. Well
  1 and Well 2 expose 62 explicit `From`-`To`-lithology rows; ten other reports
  contain point-depth descriptions and were excluded from interval scoring.
- Frozen `datasets/manifests/usgs_raft_river_interval_gold_v001.jsonl` with two
  documents and 62 source-explicit intervals. Prediction reads only fixed
  normalized raster crops, with no reference conditioning.
- `P1_USGS_RAFT_RIVER_TESSERACT_INTERVAL_FORMAL_001` predicted 56 intervals,
  matched 49, and achieved precision `0.875`, recall `0.7903225806`, and F1
  `0.8305084746`. Only `4/49` matched lithology strings were exact after the
  declared normalization. Real failures included separator loss and depth
  substitutions `245->265`, `275->276`, `375->875`, and `735->736`.
- `P1_USGS_RAFT_RIVER_RAPIDOCR_INTERVAL_FORMAL_001` matched all `62/62`
  boundaries with F1 `1.0` and zero matched-boundary MAE; `61/62` normalized
  lithology strings were exact. Its sole semantic error assigned a water-column
  `X` to the 10-25 ft gravel-and-sand row. The error is retained rather than
  silently repaired.

## 2026-08-14 — Frozen v2 external validation on Swissgeol v002

- The Paper II v2 policy was applied without modification to the earlier
  20-document/55-interval v002 incremental set, using the v003 development
  partition only as the declared development manifest. Record overlap was zero.
- First-pass and final F1 were both `0.8545454545`; 17/20 documents were exact.
  Only one correct document triggered, no reread was accepted, and all three
  erroneous documents evaded triggering. Incorrect-document trigger recall was
  `0/3`; correction success and FCR were undefined because the correction
  denominator was zero.
- This external result does not reproduce the positive v003 held-out gain and
  is retained as a formal negative result rather than being omitted.

## 2026-08-14 — Multi-boundary image-to-surface propagation

- Frozen v003 Paper II predictions were propagated for all four available
  ordered interval-boundary positions using authoritative coordinates and
  collar elevations. No reference-guided interval repair was used.
- Across 80 reference boundary observations, raw and reread outputs supplied 70
  and 71 positional observations. Aggregate boundary MAE decreased from
  `11.1714 m` to `2.7887 m`; aggregate IDW surface MAE decreased from
  `21.3969 m` to `20.6154 m` across 1,265 boundary-query pairs.
- The first two boundaries benefited most. Third and fourth boundary surfaces
  were dominated by support loss: only 4/7 and 2/3 predicted points were
  available, despite zero positional depth error among available points. This
  demonstrates that omission and positional alignment can dominate numerical
  boundary error downstream.
## 2026-08-14 — Authoritative multi-error downstream propagation

- Experiment: `P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002`; 35 held-out
  Swissgeol records, 80 ordered boundary observations, 1,265 fixed IDW
  queries, six error classes, three within-class severities, and 30 seeds per
  condition (540 repetitions total).
- Observation: a 1.00 m boundary-shift condition produced 0.168353 m surface
  MAE; a 500 m coordinate-shift condition produced 1.564117 m; and 50%
  missing-boundary prevalence reduced support to 0.775 and produced 8.620714 m
  surface MAE despite zero error among retained boundary values. At the 50%
  class-specific prevalence, merged, split, and duplicated ordered layers
  produced 40.956927, 30.747222, and 20.663361 m surface MAE.
- Validation: the clean self-comparison had zero boundary/surface error and
  complete support. Numeric boundary shifts retained topology; coordinate
  shifts retained boundary values; missing slots reduced support without
  position-shifting deeper slots; merge/split/duplicate operations changed
  ordered sequence topology as designed.
- Limitation: coordinates and collar elevations are authoritative structured
  fields, not image-derived predictions. Parameters have different units and
  do not establish a universal between-class ranking or natural error
  frequency. The source rights decision remains
  `PENDING_MANUAL_PRE_SUBMISSION_REVIEW`.
- Decision: admit the run as
  `formal_authoritative_controlled_error_downstream`, retain the exact
  operation audit for every repetition, and use the result to distinguish
  numeric error, coordinate geometry, spatial-support loss, and positional
  topology in Paper III.
- Next step: add wrong-lithology/correlation perturbations only after a
  defensible unit-correlation reference is available; continue seeking a
  complete image-derived spatial workflow and timed human study.

## 2026-08-14 — External page spatial metadata and partial surface workflow

- Development failure: `P3_SWISSGEOL_EXTERNAL_SPATIAL_METADATA_001` exposed a
  collar parser error: five `Klemm 805-2` drill-rig model numbers were accepted
  as 805 m elevations. The run was not indexed. The parser was restricted to a
  plausible value immediately adjacent to the collar label, with a regression
  test for the equipment-number case.
- Formal spatial experiment:
  `P3_SWISSGEOL_EXTERNAL_SPATIAL_METADATA_002` evaluated all 88 paired records
  outside interval-v003. It emitted 53 unambiguous page-coordinate pairs; 51
  agreed exactly with the database. Conditional pair agreement was 0.9623 and
  whole-set exact coverage was 0.5795. Two page/database differences remain
  unresolved rather than being assigned to recognition. Collar coverage was
  0/88 after the safety fix.
- Partial downstream experiment: `P3_SWISSGEOL_PAGE_SPATIAL_SURFACE_001`
  combined frozen page coordinates and image-derived first boundaries on the
  35-document held-out set. Page-coordinate coverage was 17/35 and all 17
  available raw/reread boundaries were exact, yet surface MAE was 9.514211 m.
  The authoritative-coordinate reread variant used 34 points and produced
  3.049677 m MAE on the same 423 queries.
- Decision: treat page/database mismatch separately from recognition error;
  retain abstention as the correct collar behavior; describe the surface run
  as partial because all collar elevations are still authoritative.
- Next step: investigate layout/visual collar evidence on sources that
  explicitly print elevation, while preserving zero-coverage abstention on
  pages that only state a tolerance.

## 2026-08-14 — Four-canton source-disjoint interval transfer

- Frozen all 42 acquired Swissgeol PDF/database pairs outside the Thurgau
  development source: Bern 7, Solothurn 3, St. Gallen 26, and Vaud 6. The
  reference contains 787 official database intervals. Complete page/database
  interval agreement is unverified, so the tier is
  `AUTHORITATIVE_STRUCTURED_SOURCE`, not interval Gold.
- Low-resolution visual hashing identified 35 independent content groups. Eight
  St. Gallen records share one 21-page report; OCR was executed once for that
  content, and a content-group-equal macro result was reported alongside the
  record-weighted result.
- Formal Tesseract transfer run
  `P1_SWISSGEOL_CROSS_CANTON_TESSERACT_TRANSFER_003` emitted nine intervals on
  2/42 records and matched one of 787 references: precision 0.111111, recall
  0.001271, F1 0.002513, and content-group macro F1 0.003008. Bern,
  Solothurn, and Vaud had zero matches.
- Formal RapidOCR transfer run
  `P1_SWISSGEOL_CROSS_CANTON_RAPIDOCR_TRANSFER_002` emitted seven intervals on
  the same 2/42 records and matched none: precision, recall, micro F1, and
  content-group macro F1 were all 0.000000.
- Post-hoc reference-token visibility diagnostics found parser-section failure
  despite at least 50% boundary-number visibility in 12 Tesseract records and
  26 RapidOCR records. Tesseract showed substantial numeric evidence loss in
  16 records. These counts are diagnostic and cannot distinguish all OCR,
  formatting, and page/database mismatch mechanisms.
- Source inspection of the two nonempty records found sample-depth ranges being
  selected as strata and a critical Tesseract column-fusion event in which a
  printed 7.00 m boundary contributed to a spurious 217.00 m value.
- Two interrupted/failed attempts were retained outside the formal index: run
  001 was stopped after discovering repeated visual content and run 002 exposed
  a nullable official final-depth field. Both defects were corrected before the
  indexed run.
- Decision: retain the very low transfer results as primary evidence of domain
  shift. Do not tune on these 42 records before reporting the frozen-policy
  result, and do not label database agreement as page-level extraction accuracy.
- Next step: evaluate a layout-aware, field-specialized extraction policy on a
  separately frozen development subset or independent source, preserving these
  42 records as untouched external evidence for any revised method.

## 2026-08-14 — Incremental Aargau deep-log transfer extension

- Availability probing separated index size from usable interval pairing.
  Aargau and Zürich exposed 1,097 and 13,149 profile-filtered index records,
  respectively, but the first 200 records in each canton had no published
  stratigraphy paired with the profile. Stratified page sampling found no
  Zürich pair in 75 sampled records and one Aargau pair on the final page.
- Freezing all 97 Aargau final-page candidates produced four paired deep-log
  records and 2,545 official database intervals. The pages are unusually tall:
  up to 1,684 × 8,504.64 PDF points. The empty Aargau v001 and Zürich v001
  freezes are retained as negative availability evidence and are not benchmark
  data.
- The five-canton v002 transfer freeze contains 46 records, 39 independent
  visual content groups, and 3,332 official intervals. It adds Aargau without
  changing or filtering the earlier 42-record panel.
- Formal Tesseract experiment
  `P1_SWISSGEOL_FIVE_CANTON_TESSERACT_TRANSFER_001` emitted nine candidates on
  2/46 records and matched one interval: precision 0.111111, recall 0.000300,
  F1 0.000599, and content-group macro F1 0.002699. Aargau contributed zero
  candidates and zero matches. OCR of the four new long pages took 1,166.59 s
  in the resumed run; complete end-to-end latency is excluded because the
  previous 42 OCR artifacts were reused.
- Formal RapidOCR experiment
  `P1_SWISSGEOL_FIVE_CANTON_RAPIDOCR_TRANSFER_001` emitted seven candidates on
  2/46 records and matched none. The four Aargau pages again emitted zero
  candidates. Pillow warned that two rendered pages contained approximately
  173 million and 107 million pixels, documenting the extreme page geometry.
- Post-hoc evidence analysis found one 77-interval Aargau page for which native
  text and Tesseract each contained every official bottom-boundary token, yet
  the frozen parser emitted no section. RapidOCR retained only 7.8% of those
  tokens. A 1,319-interval page retained 22.8% under native text and Tesseract
  but zero under RapidOCR. Thus the new source contains both layout/section
  failure and OCR numeric-evidence loss.
- Decision: use v002 as the primary external transfer panel, retain v001 as the
  preregistered predecessor, and keep all Aargau results out of parser tuning.
  Future method development must use a separate development source or a newly
  frozen internal partition.

## 2026-08-14 — California published manual-transcription Gold benchmark

- Acquired the official USGS California lithology version 3.0 release (DOI
  `10.5066/P9M85U0T`) and attributed WCR version 6.0 release (DOI
  `10.5066/P93ICKAF`). The lithology table contains 602,125 data rows; the WCR
  table contains 302,511 data rows and 283,348 public report links.
- Source metadata states that USGS staff manually keyed lithologic intervals
  verbatim from the DWR WCR images without OCR and performed post-entry depth
  sequence, gap, and completeness checks. This is external published manual
  Gold, not project-created annotation or machine Silver.
- Deterministic joining produced 12,732 report candidates/225,150 intervals.
  A county-first seeded filter froze 60 reports/850 intervals from 58 counties.
  Ten reports were assigned to development and 50 reports/48 counties/77
  pages/697 intervals to held-out test before backend evaluation.
- Development-only selection compared three RapidOCR parser variants and one
  Tesseract PSM-11 variant. The chosen RapidOCR development F1 was 0.425;
  Tesseract development F1 was 0.477. No test result was used for selection.
- Formal RapidOCR test `P1_CALIFORNIA_WCR_RAPIDOCR_TEST_FORMAL_001` emitted 195
  intervals and matched 174: precision 0.8923, recall 0.2496, F1 0.3901, and
  matched lithology exactness 75/174. Eleven of 50 reports had no prediction.
- Formal Tesseract test `P1_CALIFORNIA_WCR_TESSERACT_TEST_FORMAL_001` emitted
  176 intervals and matched 142: precision 0.8068, recall 0.2037, F1 0.3253,
  and matched lithology exactness 30/142. Twelve reports had no prediction.
- Real error analysis found RapidOCR more successful on 22 reports, Tesseract
  on 15, and equal on 13. The primary failures were omissions (523 and 555
  missing reference intervals), zero-output documents, column contamination,
  and lithology corruption rather than small errors among matched boundaries.
- Paper II formal run `P2_CALIFORNIA_WCR_CONSTRAINT_TEST_FORMAL_001` ranked 353
  positioned candidates with monotonicity, adjacent continuity, and layout
  stability. It raised precision/recall/F1 from 0.892/0.250/0.390 to
  0.915/0.357/0.514. It added 81 correct and 12 incorrect boundaries, removed
  10 incorrect and six correct boundaries, and produced FCR 18/109 = 0.165.
  Sixteen reports improved, 29 were unchanged, and five worsened.
- Decision: make California the primary current real Gold evidence for Papers I
  and II. Preserve the non-negligible FCR as a central safety result. Do not
  re-tune on the 50-report test. Next method work must fit abstention and
  component attribution on development or a new independent freeze.

## 2026-08-14 — California non-overlapping external replication

- Froze `california_wcr_gold_v002` by excluding every v001 record and taking
  the next 100 deterministic clean candidates. The external set contains 100
  reports, 23 counties, 154 pages, 1,770 published manually transcribed
  intervals, and coordinates for all reports; overlap with v001 is zero.
- The manifest SHA256 is
  `5cfbf20673bef235ae5b7d9c9e1d806898d9826511e1f6ffb4c0337b146ededc`;
  the split SHA256 is
  `bb2363bc324d90404b1272ac30d2a7a652981511252b23ab995ca84f514014c1`.
- Formal RapidOCR external run
  `P1_CALIFORNIA_WCR_V002_RAPIDOCR_EXTERNAL_FORMAL_002` emitted 673 intervals,
  matched 550, and obtained precision 0.8172, recall 0.3107, and F1 0.4503.
  It produced output for 92/100 reports and exactly matched lithology for
  284/550 matched boundaries.
- Formal Tesseract external run
  `P1_CALIFORNIA_WCR_V002_TESSERACT_EXTERNAL_FORMAL_002` emitted 497 intervals,
  matched 392, and obtained precision 0.7887, recall 0.2215, and F1 0.3458.
  It produced output for 79/100 reports and exactly matched lithology for
  149/392 matched boundaries.
- RapidOCR recovered more matches on 46 reports, Tesseract on 20, and the
  engines tied on 34. This replicates the aggregate engine ordering while
  retaining substantial per-document complementarity.
- Formal constraint run
  `P2_CALIFORNIA_WCR_V002_CONSTRAINT_EXTERNAL_FORMAL_002` increased F1 from
  0.4503 to 0.5640, with precision 0.9253 and recall 0.4056. It added 212
  correct and 17 incorrect boundaries, removed 80 incorrect and 46 correct
  boundaries, and yielded FCR 63/355 = 0.1775.
- At document level, 36 reports improved, 56 were unchanged, and eight
  worsened. The largest gain was 3 to 23 matches; the largest loss was 6 to 2.
- Decision: treat v002 as an independent external replication, not as evidence
  of model improvement over v001. The repeated recovery gain and stable
  16.5–17.7% false-correction range strengthen the conclusion that sequence
  constraints are useful but unsafe for unconditional automatic correction.
- A 20,000-repetition paired document-cluster bootstrap estimated the
  RapidOCR-minus-Tesseract F1 difference as 0.0648 with 95% interval
  [−0.0346, 0.1684] on v001 and 0.1044 [0.0164, 0.1915] on v002. The combined
  descriptive difference was 0.0941 [0.0216, 0.1642]. Therefore the external
  set and combined analysis support the ordering, while v001 alone does not.
- Constraint-minus-raw F1 gains were 0.1238 [0.0583, 0.1860] on v001 and
  0.1138 [0.0762, 0.1535] on v002; the combined descriptive gain was 0.1160
  [0.0839, 0.1498]. Both independently frozen sets therefore support a
  positive sequence-recovery effect, distinct from the unresolved correction
  safety problem measured by FCR.

## 2026-08-14 — Prospective California selective-correction validation

- Designed `california_selective_net_expansion_v001` after inspecting v001 and
  v002. The rule accepts a constraint-selected document sequence only when it
  contains more intervals than the raw sequence; otherwise it retains raw and
  abstains from correction. The configuration explicitly marks v001/v002 as
  design evidence and forbids a prospective claim on those freezes.
- Committed the policy and implementation before acquiring v003. Then froze
  the next 100 deterministic eligible reports after excluding all 160 v001/v002
  records. v003 contains 31 counties, 154 pages, 1,788 intervals, coordinates
  for all reports, and zero predecessor overlap. Manifest SHA256 is
  `aab4df46be806f10e2475be63ade6654cd1d4d86a28ef41ae576b0a740e7f0c1`.
- Prospective RapidOCR produced 559 intervals and matched 449: precision 0.8032,
  recall 0.2511, F1 0.3826, with exact lithology for 244/449 matches. Tesseract
  produced 507 and matched 379: precision 0.7475, recall 0.2120, F1 0.3303.
- Unselective constraints raised F1 to 0.4699 (gain 0.0872; paired document
  bootstrap 95% interval [0.0392, 0.1392]) but incurred FCR 59/281 = 0.2100.
  Twenty-three reports improved, 67 were unchanged, and ten worsened.
- The frozen selective policy accepted 23/57 changed-document proposals,
  producing F1 0.4636 and gain over raw 0.0810 [0.0342, 0.1325]. Relative to
  unselective ranking its F1 difference was −0.0062 [−0.0154, 0.0028]. FCR
  remained 37/188 = 0.1968 and one report worsened.
- The failure was `WCR2014-011949`: the sequence expanded from 28 to 37
  predictions but matches fell from 12 to 6; the constraint output added 18
  incorrect boundaries and removed eight correct ones. This falsifies the
  proposed net-expansion safety heuristic and motivates candidate-level risk,
  field localization, and calibrated abstention in the next method revision.

## 2026-08-15 — BGS Offshore cross-source interval benchmark

- Queried the official BGS GeoIndex Offshore Activity and Scan layer and
  Borehole Geology Data layer. The layers returned 593 scan records and 10,727
  geology rows; joining on `ACTIVITY_ID` and retaining only metre-unit graphic-
  log interpretations with legal positive intervals, no overlaps, and adjacent
  continuity >=0.95 yielded 251 candidates across 30 survey/source groups.
- Froze one deterministic record per source group where a reachable PDF exposed
  a `BH_COMP_LOG` composite page and the remote PDF was <=30 MB. The resulting
  set contains 26 PDFs, 372 total pages, 34 evaluation pages, 341 intervals,
  and 26 distinct source groups. Manifest SHA256 is
  `d85f6c862b81d80c793887f73ca8b70658d42de358f25230dc4a15104520c99c`; split
  SHA256 is `03adfecca7f2c97c1612752ff1ca387fe1f22f31ee20cdf8981ef1f2cee8d096`.
- Formal RapidOCR run `P1_BGS_OFFSHORE_V001_RAPIDOCR_CROSS_SOURCE_FORMAL_001`
  emitted 28 intervals across nine documents and matched seven boundaries:
  precision 0.2500, recall 0.02053, F1 0.03794; matched lithology exactness
  was 2/7. Formal Tesseract run
  `P1_BGS_OFFSHORE_V001_TESSERACT_CROSS_SOURCE_FORMAL_001` emitted 54 intervals
  across 13 documents and matched eight boundaries: precision 0.14815,
  recall 0.02346, F1 0.04051; matched lithology exactness was 2/8.
- These are real source-disjoint interval results, not annotation failure or
  a California extrapolation. The historical composite pages contain low-
  contrast and handwritten depth annotations. The source is recorded as
  `GOLD_AUTHORITATIVE_SOURCE_AGREEMENT`, not project human annotation.
- Three candidates lacked a `BH_COMP_LOG` page and one 89.9 MB candidate was
  excluded by the reproducibility size cap; all exclusions are preserved in
  `/data/GeoLogParser/datasets/public/bgs_offshore_paired_v001/metadata/acquisition.json`.
- Rights decision remains `ELIGIBLE_INTERNAL_ONLY`: ArcGIS records state OGL
  v3.0, while scan footers include legacy all-rights-reserved wording. Original
  PDFs remain local pending the user's final manual source verification.

## 2026-08-15 — USGS Idaho image-only lithologic-log source audit

- Acquired five official ScienceBase release inventories covering USGS 144,
  145, 150, 152/152A/152B, and CFPP-B01. The frozen local set contains seven
  lithologic-log PDFs and 608 pages; manifest SHA256 is
  `40126bfe0e27e75155627af2ebb9d95cc4279279d4bdfec229c3cf8abe603383`.
- Run `P1_USGS_IDAHO_LITHOLOGIC_V001_CROSS_ENGINE_COVERAGE_001` rendered every
  page at 180 DPI and applied Tesseract PSM 11 and RapidOCR independently.
  Tesseract emitted non-empty text on 608/608 pages and RapidOCR on 607/608.
- Both engines detected an explicit lithology label on 281 pages. RapidOCR
  alone detected it on 49 pages and Tesseract alone on zero. The disagreements
  occurred only in USGS 144 (2), USGS 145 (33), and USGS 150 (14); the other
  four documents had zero label-presence disagreement.
- RapidOCR emitted 3,107 numeric depth-range candidates versus 2,922 for
  Tesseract. This 185-candidate difference is an engine detection event, not an
  accuracy result. No independent interval reference exists, so precision,
  recall, F1, and correctness are intentionally undefined.
- The source remains internal pending final item-level rights, attribution,
  precise-location, and embedded-content review. No human review is claimed.

## 2026-08-15 — California v004 prospective candidate-risk validation

- Committed candidate-risk policy `california_addition_only_high_confidence_v002`
  before acquiring v004. Development used only v001/v002 correction events;
  v003 and v004 were explicitly excluded.
- Froze 100 new reports, 147 pages, 28 counties, and 1,944 published manually
  transcribed intervals after excluding every v001-v003 record. Manifest SHA256
  is `054848cca5b5eac0e67b46151842a31d63d6e94558664ab8f15cec5b5ba4ca4c`;
  split SHA256 is `f0548634c811ab9392431d527ca6f38de6f2a813838ab4587e43cb5fc0597694`.
- RapidOCR first pass matched 549/622 predictions, precision 0.8826, recall
  0.2824, and F1 0.4279. Unselective sequence ranking matched 783/822,
  reaching F1 0.5662 but FCR 43/354 = 0.1215.
- The frozen addition-only risk policy accepted 43 candidates across eight
  documents. All 43 matched the reference, eight documents improved, 92 were
  unchanged, and none worsened. F1 rose to 0.4538; observed FCR was 0/43.
- Paired document bootstrap estimated the F1 gain over raw as 0.0259 with 95%
  interval [0.0052, 0.0541]. The exact two-sided 95% upper bound for a zero-error
  observation over 43 actions is 0.0822, so universal safety is not claimed.
## 2026-08-15 — California WCR v005 independent external replication

- Frozen `datasets/manifests/california_wcr_gold_v005.jsonl` after excluding every record in v001–v004; overlap checks were zero for all four predecessors.
- The freeze contains 100 reports, 141 pages, 35 counties, and 2,069 published USGS manual-transcription intervals. Manifest SHA256: `b37fb6f5fde0fa1ffa2f41f91da0c6f685cd48ed4d07972c983255f89ec5e6f9`.
- RapidOCR was run without reference conditioning on all 100 reports. It emitted 741 intervals and matched 549/2,069, giving precision 0.736842, recall 0.263896, and F1 0.388612. One report was completely exact; 15 reports emitted no interval prediction.
- This is an external replication for Paper I only. No v005 record was used for model, parser, prompt, or candidate-policy development; no Paper II correction claim is made from this run.
- The result is indexed as `P1_CALIFORNIA_WCR_V005_RAPIDOCR_EXTERNAL_FORMAL_001`; source rights and report-image redistribution remain subject to the existing pre-submission verification ledger.

## 2026-08-15 — California v005 constraint and candidate-risk replication

- The frozen v005 raw predictions were passed unchanged to the existing constraint sequence runner and the candidate-level addition-only policy; no v005 record was used for development.
- Unselective constraint ranking increased interval F1 from 0.388612 to 0.530360 (precision 0.913712, recall 0.373610) and produced an action-based false-correction rate of 35/417 = 0.083933.
- Candidate-risk selection increased F1 to 0.410670, accepted 39 additions, all 39 correct against the published reference, worsened no document, and improved 11/100 documents. This is an external safety replication, not evidence of zero population error.
- Runs indexed as `P2_CALIFORNIA_WCR_V005_CONSTRAINT_EXTERNAL_FORMAL_001` and `P2_CALIFORNIA_WCR_V005_CANDIDATE_RISK_EXTERNAL_FORMAL_001`.

## 2026-08-15 — Cross-source constraint detectability audit

- Applied the frozen C1--C10 engine reference-blind to six real prediction sets:
  BGS offshore RapidOCR/Tesseract, Raft River RapidOCR/Tesseract, and the
  USGS-142/USGS-144 interval diagnostics. References were read only after the
  constraint decisions to label observed omissions, spurious intervals, and
  lithology mismatches.
- BGS RapidOCR had boundary-omission events in 26/26 documents, but only 1/26
  documents triggered any constraint violation; event detectability was 0.038.
  BGS Tesseract likewise had 26/26 omission documents, with 7/26 documents
  flagged and detectability 0.269.
- Raft River RapidOCR contained one observed semantic mismatch and no constraint
  violation. Raft River Tesseract contained omission, spurious-interval, and
  semantic events in both documents, and both documents triggered a violation.
  USGS-142 and USGS-144 each retained a lithology-string mismatch while all
  structural constraints passed.
- This is a post-hoc detectability analysis, not a correction-effect experiment;
  it narrows Paper II's claim by showing that continuous, internally consistent
  sequences can still omit intervals or carry semantic column errors.
- Artifact: `experiments/paper2/analysis/cross_source_constraint_detectability_v001.json`
  (SHA256 `adea561ce4f5e3fcf750be16c0b200a9b200c1a3b00005eaaae28dd9563fdb72`).

## 2026-08-15 — Real stratigraphic layer-volume diagnostic

- Added `scripts/run_swissgeol_stratigraphic_layer_model.py` and ran
  `P3_SWISSGEOL_STRATIGRAPHIC_LAYER_MODEL_002` on the frozen 35-document
  Swissgeol held-out set. The run converts ordered boundary surfaces into three
  adjacent layer-thickness surfaces and IDW volume estimates on common reference
  domains; coordinates and collars remain authoritative structured values.
- Raw predictions produced mean layer-thickness MAE 45.952 m and relative
  absolute volume error 0.138942. The frozen reread channel produced 45.679 m
  and 0.121565, respectively. Mean top/bottom support was 0.784/0.698 for raw
  and 0.784/0.708 for reread; one of three layers retained negative predicted
  thickness at some query points.
- This is a real downstream stratigraphic-model baseline, not a validated
  geological interpretation. Sparse deep-layer support, authoritative spatial
  metadata, and ordered-index alignment remain explicit limitations.

## 2026-08-15 — California random-versus-grouped split leakage diagnostic

- Pooled the ten v001 development records with the 50 county-first test records,
  froze all existing RapidOCR predictions, and sampled 100 random 50-record test
  sets without retraining. The random-record mean F1 was 0.393523 ± 0.020757
  (range 0.353591–0.442127), compared with grouped-test F1 0.390135.
- Random samples contained 16.82% of their records from the original development
  partition on average. Random precision/recall were 0.819111 ± 0.025269 and
  0.259199 ± 0.016981; grouped precision/recall were 0.892308/0.249641.
- The result is a split-leakage diagnostic, not a retrained generalization
  benchmark. It narrows the Paper I TBD claim without presenting the random
  sample as independent evidence.

## 2026-08-15 — California Qwen3-VL Gold page aggregation

- Fixed page identity handling in `scripts/run_vlm_audit.py` and the California
  Gold aggregator so multi-page reports use the rendered page stem rather than
  the repeated source-record identifier.
- Aggregated four completed GPU shards covering all 77 pages of the frozen
  50-report/697-interval California v001 test split. All 77 page responses were
  schema-valid, but only one report emitted any interval candidates (five in
  total); none matched a published boundary within the 0.05 m tolerance.
- The formal page-aggregated result is interval precision 0.000, recall 0.000,
  F1 0.000, and boundary-exact documents 0/50. Summed page-generation latency
  was 3,438.996 s (68.780 s/report); the four shards were run independently,
  so this is not a single-process wall-clock measurement.
- Indexed as `P1_B4_QWEN3VL4B_CALIFORNIA_TEST_FORMAL_001R`. This is a real
  VLM baseline against published manual-transcription Gold; schema validity is
  not treated as extraction accuracy.

## 2026-08-15 — BGS long-page field-aware method development gate

- Reclassified BGS offshore v001 as a development/failure-attribution source
  because its document-level baseline failures had already been inspected.
  Froze v002 with zero record-ID or source-title overlap: 3 documents, 3 new
  source groups, 4 evaluation pages, and 49 official intervals. Manifest SHA256
  is `f84a8b282ec054dbe0a06bd3a6f6cf3136f3f6e22f9d92fcc7907ffe03af16ae`.
- Semantic panel inference localized 33/34 v001 pages. Full-page exact boundary
  visibility was 75/367. Overlapping 2x panel tiles increased the union to
  96/367. Adaptive boundary/scale strips with 4x rereading and table-line
  removal supplied a different evidence channel; the final union was 110/367.
- Implemented explicit depth-scale calibration, graphic-layer transition
  candidates, multi-view OCR evidence, header final-depth candidates, a small
  probabilistic ranker, provenance, monotone sequence inference, and selective
  acceptance. Five-fold splits are deterministic and source-group disjoint.
- The v007 method added mutually exclusive same-location hypotheses and strict
  page/y ordering. It still failed the deployment gate: at ±0.05 m its monotone
  output had boundary precision/recall/F1 0.4552/0.1662/0.2435 and interval F1
  0.1099. At ±0.10 m critical numerical error rate was 0.5448. The selective
  policy accepted 4 boundaries, of which 2 were wrong.
- This is a useful negative result: layout localization is not the primary
  bottleneck, multiscale visibility remains insufficient, and independent
  candidate classification cannot distinguish mutually exclusive depth roles.
  ADR-015 prevents consuming BGS v002 until explicit development thresholds are
  met. No v002 extraction result has been viewed or used for tuning.

## 2026-08-15 — BGS v018 mixed-page semantic-role development

- Re-ran the multiscale and field-ROI readers after fixing plural semantic
  headers (for example, ``DESCRIPTIONS``); BGS v001 now detects 34/34 layouts.
  Field-specific exact candidate visibility is 97/367 (26.43%). The updated
  multiscale and field artifacts are frozen with SHA256 values
  ``e665e71a73cb01bdf31caaa2283d6c949880d5ccd6dafa9b670716f4994a8d2a`` and
  ``f2ee1b78c1645e8c4cf02defdf47f140327d55eebc6cfe9a4630f340d5bbea4e``.
- v018 uses candidate semantic-role experts for printed boundaries, calibrated
  graphic transitions, and terminal metadata, with global-model shrinkage,
  nested source-disjoint Platt calibration, explicit zero-depth topology, and
  threshold-relative monotone decoding. It produced boundary P/R/F1
  0.4940/0.2262/0.3103 and interval F1 0.1116 at ±0.05 m; at ±0.10 m boundary
  CNER was 0.4940. Candidate ECE fell from 0.2475 to 0.0352 and Brier score
  from 0.1652 to 0.0916. The v018 analysis SHA256 is
  ``cd2f60e2b5de8db4816d25753e983e03dd239177f007e53587d2ce4362af54aa``.
- A sequence-level selective point accepted 43 boundaries, 40 correct, with
  precision 0.9302, reference coverage 0.1172, and CNER 0.0698. This passes
  the selective-risk development condition but does not pass interval F1 or
  full-coverage precision; BGS v002 remains unopened. The result is a
  development finding, not an external generalization claim.

## 2026-08-15 — BGS long-page Qwen3-VL negative audit

- Ran the frozen long-page prompt ``prompts/bgs_long_page_boundary_v001.md``
  with local Qwen3-VL-4B on 79 independently rendered BGS tiles. GPU use was
  temporary and mining was restored after completion. All 79 responses were
  valid JSON, but the model matched only 12 reference boundaries, produced 33
  false positives, and missed 355. At ±0.10 m, precision/recall/F1 were
  0.2667/0.0327/0.0583; wall time was 746.479 s.
- The false positives were concentrated on depth-scale ticks, page headers,
  and terminal-depth metadata. This is a failure-attribution audit, not a
  positive method result. The output artifact SHA256 is
  ``5759c69e776d266c6142d17f5fb661ae2f9ffa1e011634555c7ac6a7c602d793``.
- The result is excluded from v018 training, threshold selection, and external
  confirmation. It is retained as evidence that unconstrained long-page VLM
  boundary extraction is not a deployable substitute for field-aware parsing.

## 2026-08-15 — BGS v019 correlated-evidence failure

- Corrected the feature-construction order so cross-source event/value support
  and metadata cross-field interactions entered the nested source-disjoint
  ranker rather than being computed after derived interactions. This was a
  development-only hypothesis test on BGS v001; BGS v002 remained unopened.
- The additional agreement features reduced boundary precision/recall/F1 at
  ±0.05 m to 0.4691/0.2071/0.2873 and interval F1 to 0.1004. The selective
  point accepted 51 boundaries at precision 0.8627 and CNER 0.1373, also worse
  than v018. Candidate ECE was 0.0370 and Brier score 0.0913.
- The analysis SHA256 is
  ``b238bb6d6893e5b9eb19804c554ae0b56fa6bfef6b0ce6901279dd0d4c38649f``;
  the serialized model SHA256 is
  ``d6a15173a3604c3b9e78c96e9751e72a8c8ea72ddeabfcef11c9f66269811369``.
  v019 is rejected. Multi-reader agreement is correlated by shared scale ticks
  and semantic-role ambiguity, so it cannot be treated as independent positive
  evidence. v018 remains the best development model and ADR-015 remains closed.

## 2026-08-15 — BGS v020 depth-scale alignment ablation

- Added reference-blind candidate features for the residual between a numeric
  candidate and the page's calibrated y-depth geometry, then reran the same
  five-fold source-disjoint BGS v001 development protocol without using v002.
- v020 reached boundary precision/recall/F1 0.5063/0.2207/0.3074 and interval
  F1 0.1092 at ±0.05 m. Its selective point accepted 43 boundaries with
  precision 0.9070, coverage 0.1172, and CNER 0.0930. The selective gate alone
  passed, but interval recovery and full-coverage precision did not improve
  over v018, so v020 was rejected for external release.
- The analysis SHA256 is
  ``173e61c4638295aeff9f9a74735839b252c09c233797e7d0dba8c7a73a8e9ef4`` and
  the serialized model SHA256 is
  ``ff5ff7ff835f8b6119375d8762135b31004acef2346294451813ef3bb6a6cf5b``.
  BGS v002 remains unopened. The negative result narrows the bottleneck to
  candidate-role discrimination and interval pairing, not only scale
  calibration.

## 2026-08-15 — Swissgeol cross-canton long-page resource audit

- A frozen v2 reread attempt on the 46-record five-canton transfer manifest
  exposed a resource limitation before any metrics were finalized: a single
  Aargau profile rendered at 250 DPI was 5,848 x 29,531 pixels and took several
  minutes for one Tesseract pass. The run was terminated without writing a
  formal result and is not indexed.
- A low-resolution multi-page implementation was then smoke-tested on the
  four-canton transfer manifest. It removed the one-page assumption and
  accumulated reread evidence page by page, but the 42-record stress run was
  stopped at 6/42 records because the same multi-view OCR cost remained too
  high. Partial artifacts are retained only for performance diagnosis.
- No partial transfer values are used as accuracy evidence. The implementation
  now records `max_ocr_dimension_px`, first-pass/reread DPI, and supports
  multi-page reread aggregation; a future throughput study must use a bounded
  page budget or a faster OCR backend before claiming cross-canton method
  performance.

## 2026-08-15 — PaperII-NativeMM v002 structural branch

- The NativeMM training/decoding loop was audited on a one-sample boundary task.
  The apparent zero-quality result was traced to an old evaluation invocation
  that capped generation at approximately 96 tokens and truncated the JSON.
  With a 384-token cap, the language-only adapter's overfit output terminated
  at EOS; the new v002 adapter (language q/v plus visual projector LoRA) also
  passed the protocol with JSON-valid rate 1.0 and boundary P/R/F1 1.0 on its
  single training sample. These are closure diagnostics only.
- Synthetic v002 was generated with 512 pages, 32 template IDs, deterministic
  known labels, and recorded degradation parameters.  The combined development
  corpus `paper2_nativemm_v002r2` contains 1,826 task samples (1,415 train,
  411 development), with 1,484 synthetic task samples, 82 BGS-v001 development
  samples, and 260 California-v001–v003 development documents. Frozen BGS-v002
  and California-v004/v005 sources remain excluded by runtime leakage checks.
- A two-epoch v002 synthetic structural pretraining run was launched on the
  RTX 5090 with the mining service stopped. Formal quality metrics will be
  written only after checkpoint completion and source-disjoint development
  evaluation.

## 2026-08-16 — PaperII-NativeMM source-disjoint no-go decision

- Synthetic structural pretraining completed on 1,160 task samples for two
  epochs (580 optimizer steps; mean loss 0.10793; 525.18 s; 5.99 GiB peak
  allocated). BGS bundle development produced JSON-valid rate 0 and structural
  evidence coverage 0.
- Real-Gold SFT resumed from the synthetic adapter and completed on 255 samples
  (64 optimizer steps; mean loss 0.67462; 78.97 s; 9.00 GiB peak allocated).
  BGS bundle JSON-valid rate improved to 0.2857 but coverage remained 0.
- California source-disjoint interval evaluation completed on 68 documents:
  sequence-boundary F1 was 0.0015, interval F1 0, JSON-valid rate 0.1029 and
  CNER 0.875. Frozen California v004/v005 and BGS v002 were not used.
- Auditing the BGS training targets showed that the initial spatial labels were
  numeric-text bounding boxes rather than graphical boundary positions. A new
  immutable dense corpus projected official depths through page-scale fits and
  contained 269 samples, including 26 BGS pages/228 projected boundaries.
- A frozen-backbone dense row head and column-aware pixel-only, visual-only and
  fused heads were trained with source-group-disjoint fold 0 held out. Their
  boundary F1 values were 0.0667, 0.0789, 0.0488 and 0.0364; interval F1 values
  were 0, 0.0312, 0 and 0. All missed ADR-016 gates.
- ADR-016 is closed as `NO_GO`. No external frozen run was spent. The result
  identifies missing real field-region/event supervision, rather than training
  scale, as the next prerequisite for a future native multimodal attempt.

## 2026-08-16 — BGS v021 multi-column structural-event development

- Replaced the single graphic-column assumption with reference-blind detection
  of up to eight narrow recovery/lithology/formation/contact columns around the
  calibrated depth field. Added column position, activity, rank and cross-column
  event support to the source-disjoint ranker.
- v021 generated 21,632 candidates. The monotonic sequence reached boundary
  precision/recall/F1 0.5659/0.1989/0.2944 and interval F1 0.1213 at ±0.05 m.
  Interval F1 improved over v018's 0.1116, while boundary F1 declined from
  0.3103. The selective point accepted 41 boundaries at precision 0.9268,
  coverage 0.1117 and CNER 0.0732.
- A source-disjoint pairwise interval ranker then evaluated 77,637 candidate
  pairs. It reduced interval F1 to 0.0445 and boundary F1 to 0.2066, so the
  pairwise route was rejected.
- The v021 analysis SHA256 is
  `cae1787d8803f6e9d2052407fa69dae5fdfd51da81e0fad758cc30278cbd70a4`;
  the serialized model SHA256 is
  `b8839f1c44cddfc52a67c09762feb6600adbba0552f4f2f568050212affbf3ff`;
  the rejected pairwise analysis SHA256 is
  `9415e2f5271aa5b323abaa64fc0f3350a6e281ae69bd671d055358f0cebe5653`.
  BGS v002 remains unopened because the 0.15 interval-F1 gate was not met.

## 2026-08-16 — BGS v022 semantic column gate

- Trained a source-disjoint column-level ranker over v021 graphic candidates,
  using column position, width, texture activity, transition strength, scale
  quality and cross-column support. The gate was fitted only on other source
  folds and applied before monotonic sequence decoding.
- Retaining six columns per page produced boundary precision/recall/F1
  0.6610/0.2125/0.3216 and interval F1 0.1475 at ±0.05 m. CNER was 0.3390.
  This exceeds v018 on boundary F1 and is the closest result to the interval
  release gate, but remains below 0.15 and is not externally released.
- The analysis SHA256 is
  `8923bac3204a8048c7ebaf3ca8de41bf8285218c0d91dc281b3e7add997c063a`.

- A fine-grained coverage-risk sweep found threshold 0.65 to be the strongest
  high-reliability point: 40 accepted boundaries, precision 0.9500, coverage
  0.1090 and CNER 0.0500. Threshold 0.60 accepts 46 boundaries at precision
  0.9130, coverage 0.1253 and CNER 0.0870. The risk-curve artifact SHA256 is
  `855ef7113f03cba887e3fa1c665f7c3ea7cd6965d80ce855748b7d79bd6ecb33`.

## 2026-08-16 — BGS v023 continuous-depth geometry refinement

- Tested a source-disjoint post-sequence risk pruner over v022. It retained 106
  of 118 events but reduced boundary F1 to 0.2960 and interval F1 to 0.1137;
  the route is rejected because it removed true adjacent boundaries.
- Traced a separate numerical failure to coarse integer snapping after valid
  y-to-depth calibration. A nested source-disjoint geometry refiner now keeps
  integer-like values snapped while retaining calibrated decimal depth on pages
  whose scale residual passes a threshold selected on the other folds.
- At ±0.05 m, v023 reached boundary precision/recall/F1
  0.6949/0.2234/0.3381 and interval F1 0.1797. At ±0.10 m, boundary
  precision/recall/F1 were 0.7203/0.2316/0.3505.
- Threshold 0.60 accepted 46 boundaries with precision 0.9565, coverage 0.1253,
  and CNER 0.0435. All 118 full-sequence boundaries retained page/bbox
  provenance. The result passes every predeclared ADR-015 development gate.
- The final all-v001 geometry settings are integer radius 0.10 m, two decimal
  places, and maximum page-scale RMSE 0.08. The development artifact SHA256 is
  `81a962a8211d2b1a4de60d0b420d8100d8dbe07039f3e05693428d78a57f5e11`;
  the rejected pruner artifact SHA256 is
  `1d5422ffeea92cd8b55538b9dcaa9afc5d8761c225b609c4ec430b6b63109751`.
- The all-v001 column gate plus geometry parameters were serialized before any
  external evaluation as
  `experiments/paper2/models/bgs_layout_column_geometry_v023.json`, SHA256
  `1aa0389ae520c62115e6c6e737727d694937b6e9c0cdb36971137b95af169db4`.

## 2026-08-16 — BGS v023 one-time external no-go

- Commit `9ce6fd6` froze v023 before opening BGS v002. The external evaluation
  used 3 unseen source titles, 4 pages, 49 official intervals and 52 unique
  boundaries. Predictions were fixed before references were loaded for scoring.
- At ±0.05 m, boundary precision/recall/F1 were
  0.0227/0.0385/0.0286, interval F1 was 0, and CNER was 0.9773. The frozen
  threshold 0.60 accepted 50 boundaries at precision 0.0400 and CNER 0.9600.
- Provenance was complete for 88/88 full outputs. Post-OCR inference required
  1.600 s/page and 206,792 KiB peak RSS. Thus traceability and low compute did
  not yield reliable unseen-source inference.
- The result is a formal negative external confirmation and is not tuned away.
  BGS v002 is consumed. Its artifact SHA256 is
  `6e01d60b2be0328652658169276c4606fbfb7abd6297a58d4bf727eaf9258ee1`.
- Paper II remains experimental. Further structural changes require a new
  independent development source and a separately frozen v003 test.

## 2026-08-16 — BGS v003 replacement freeze

- Re-ran the official BGS eligibility query after excluding all 29 v001/v002
  source titles. One source group remained. Its eight-page PDF uses legacy
  `BH_LOG` labels, so the generic `BH_COMP_LOG` locator initially rejected it.
- Page-type inspection identified pages 2--6 as the continuous geological log
  with explicit thickness/depth columns; page 1 is a cover and pages 7--8 are
  daily drilling reports. The page decision did not use interval values.
- Froze one new source title, five pages, seven official intervals, and zero
  record/source overlap with v001/v002. Manifest SHA256 is
  `12f683ca0312740dbeb68ee3bebcd92b0a0644dce22de92115c46c8faf2236d4`;
  split SHA256 is
  `d6a2160ea74a65c70b3a0df3d8ad2da10629e88bf12ddea46e6dceaa805be56e`.
- v003 is frozen and unopened. Its single-source size is a severe limitation;
  it is a replacement confirmation check, not sufficient generalization proof.

## 2026-08-16 — BGS v002 validation-role transition

- Preserved the v023 v002 result as its formal failed external confirmation.
- After v003 was frozen, explicitly demoted v002 to validation for subsequent
  failure attribution and method development. No later v002 score may be called
  external evidence.
- v003 remains unopened. A future method must be frozen before its one allowed
  evaluation, and the one-source denominator must remain explicit.

## 2026-08-16 — BGS v002r2 corrected-page validation diagnosis

- Rebuilt the consumed BGS v002 set as a validation-only manifest after visual
  page localization showed that the original evaluation included a blank
  continuation page and a duplicated page. The corrected pages are page 11 for
  `BGS_OFFSHORE_2015092`, page 2 for `BGS_OFFSHORE_1983444`, and page 3 for
  `BGS_OFFSHORE_1944782`.
- The corrected manifest contains the same three source groups, 49 official
  intervals and 52 unique boundaries on three actual log pages. Its SHA256 is
  `56f35abcfec28a6f71b8bc79d3cfcfc965654a5707fdcdf673eb4dde2db9cadb`.
- Re-evaluated frozen v023 strictly as validation evidence. At +/-0.05 m,
  boundary precision/recall/F1 were 0.0115/0.0192/0.0144, interval F1 was 0,
  and CNER was 0.9885. The frozen selective point accepted 49 boundaries at
  precision 0.0204 and CNER 0.9796. Thus corrected page localization does not
  explain the external transport failure.
- Failure attribution is structural: `2015092` detected a layout but generated
  zero candidates; `1983444` generated 2,021 candidates and retained 1,847
  after column gating, producing 87 boundaries from a long scaled log;
  `1944782` failed layout detection and generated zero candidates despite an
  explicit thickness/depth table.
- The validation artifact SHA256 is
  `9bed480b911b2a4e3cd12870c7527a29c025b033fd204b2287696cac9eba0bab`.
  These records may inform v024 development but can no longer provide external
  confirmation. BGS v003 remains frozen and unopened.

## 2026-08-16 — BGS v024 page-family and structural-risk route

- Added a reference-blind page-family router for explicit depth-range tables,
  scaled composite logs, graphical contact logs and unsupported pages. The
  explicit route localizes the `Depth from Surface` header, re-renders its ROI
  at 2x/4x, removes table rules and fuses multiple Tesseract views.
- The parser accepts only a zero-starting contiguous sequence of at least three
  ranges. On corrected BGS v002r2 it recovered `0.00–6.00`, `6.00–8.00` and
  `8.00–10.00` with complete bbox provenance, and abstained from later rows
  whose decimal evidence was not reliable.
- Added document-level risk gates for unsupported pages, zero structural
  evidence and the specific candidate-explosion/output-density pattern seen on
  BGS v002. The route is designed to avoid the v023 failure mode of emitting
  dozens of ungrounded boundaries from a long scale.
- Source-disjoint BGS v001 v024 development results: boundary F1 `0.3313`,
  interval F1 `0.1801`, boundary precision `0.6897`, and CNER `0.3103`.
  This is not a material boundary-F1 improvement over v023 (`0.3381`), but
  interval F1 is marginally higher (`0.1797` to `0.1801`). Therefore v024 is
  retained as a reliability branch and is not promoted as the primary method.
- Corrected BGS v002r2 validation results: boundary precision/recall/F1
  `1.0000/0.0769/0.1429`, interval F1 `0.1154`, CNER `0.0000`, with four
  accepted boundaries and no false positives. This is validation evidence only;
  BGS v003 remains frozen and unopened.
- Development artifact SHA256:
  `fe5c055b4e276ae88211f79c81a6b1adeb179b9ff24adc0e426beffdb8740075`.
  Validation artifact SHA256:
  `c88525224a6e0b0cd218543c17cf0c218c33e62733f4e467766e66fc50ea7473`.

## 2026-08-16 — BGS semantic column-role diagnostic (v025/v026)

- Implemented a reference-blind OCR-header role layer for adjacent composite
  log columns. Split headers such as `Graphic` + `Log` are grouped, then
  detected vertical-rule intervals are assigned roles by x geometry and OCR
  confidence. Stratigraphy, depth-drilled and auxiliary columns are excluded
  from the primary graphic route; pages without a recoverable Graphic Log
  header can use an explicitly marked legacy fallback.
- Added `graphic_mode=role_multi`, tests in `tests/test_column_roles.py`, and
  ADR-023. Earlier `single`/`multi` routes are unchanged.
- Source-disjoint BGS v001 development: v025 role-gated sequence boundary F1
  `0.3265`, interval F1 `0.1458`; v026 role-gated plus no-anchor fallback
  boundary F1 `0.3094`, interval F1 `0.1179`. The route therefore does not
  pass the Paper II primary promotion gate relative to v024 (`0.3313` / `0.1801`)
  and remains a diagnostic page-family branch.
- On pages with an explicit Graphic Log header only (9 documents), v025 reached
  boundary F1 `0.4410` and interval F1 `0.2825`, supporting the failure
  attribution that semantic column selection is useful but not sufficient for
  cross-template coverage. BGS v003 remains frozen and unopened.

## 2026-08-16 — BGS page-family routed structural mixture (v027/v028)

- Integrated the v024 page-family/risk route and v025 semantic-role sequence as
  separate experts rather than continuing standalone v025 optimization.
  Explicit depth-range pages retain their deterministic range expert;
  unsupported or structurally unsafe pages abstain.
- Fixed reference-blind v027 routing reached boundary F1 `0.3327` and interval
  F1 `0.1806` on all 26 BGS v001 development documents, compared with v024
  `0.3313/0.1801`. The fixed route therefore supplied only a negligible gain.
- Added v028 nested source-disjoint family gating. For each target fold, the
  preference between v024 and semantic-role experts was selected only from the
  other folds' mean per-document interval F1; target-fold references were used
  only after predictions were fixed.
- The nested route reached overall boundary F1 `0.3475` and interval F1
  `0.1978`. Across five source-disjoint slices, routed boundary F1 was
  `0.3333 ± 0.1323` and interval F1 was `0.1841 ± 0.1294` (population SD),
  versus v024 means `0.3182/0.1688` and semantic-role-only means
  `0.3103/0.1276`.
- Fold interval F1 values were `0.0943`, `0.0000`, `0.2174`, `0.2278`, and
  `0.3810`. The variance is material and prevents interpreting the overall
  gain as uniform cross-source recovery.
- Decision: accept v028 as a development-only routed-MoE branch. It reuses
  v024/v025 artifacts built on BGS v001, so it is not untouched external
  confirmation. BGS v002/v002r2 remain validation-only; BGS v003 remains
  frozen and unopened. ADR-024 records the boundary.

## 2026-08-16 — Independent Swissgeol routed-coverage audit

- Prepared a reference-blind 250-DPI Tesseract page/OCR-region run for the
  independent Swissgeol Thurgau v003 development manifest: 37 documents and
  38 pages, disjoint from the BGS v001/v002/v003 source titles. The derived
  layout manifest records the official paired-reference provenance but no
  project human annotation.
- Applied the frozen BGS page-family classifier and routed parser without
  changing thresholds, prompts, or expert parameters. All 38 Swissgeol pages
  were classified `unsupported`; routed coverage was `0/38` pages and
  `0/37` documents. The route therefore abstained on every document.
- The existing Swissgeol RapidOCR interval baseline scored boundary F1
  `0.6667` and interval F1 `0.5714`; the conservative routed output scored
  `0.0000` because it correctly refused to force an unseen German-language
  page family through a BGS expert. This is a negative coverage/no-go audit,
  not evidence of a Swissgeol method gain.
- Failure attribution: OCR contains German structural headers such as
  `Tiefe`, `Beschreibung des Bohrguts`, and `Schichtenverzeichnis`, while the
  current BGS family and semantic-role lexicons are English-centric. The
  independent source therefore exposes a real cross-language family-coverage
  gap that must be addressed before claiming cross-source deployment.
- Decision: do not tune the BGS route on any frozen BGS external set. A future
  multilingual family expert may be developed on Swissgeol development and
  evaluated on its content-group-held-out split, with the present audit kept
  as the untouched pre-change baseline.

## 2026-08-16 — Swissgeol multilingual family alias development and held-out check

- Added only reference-blind German structural aliases to the page-family
  classifier (`Tiefe`, `bis`, `Beschreibung des Bohrguts`, and
  `Schichtenverzeichnis`). Existing BGS English routes and thresholds were not
  changed; the BGS v003 freeze was not opened.
- On the 37-document/38-page Swissgeol development source, aliases recognized
  8 pages (21.05%). The routed parser retained the existing baseline expert on
  those pages and abstained on the other 30 pages. Baseline interval F1 was
  `0.5714`; routed interval precision was `1.0000`, recall `0.2353`, and F1
  `0.3810`, with zero observed false-positive intervals in the accepted subset.
- On the content-group-held-out 35-document/35-page Swissgeol split, aliases
  recognized 7 pages (20.00%). Baseline interval F1 was `0.5854`; routed
  interval precision was `1.0000`, recall `0.2250`, and F1 `0.3673`, again with
  zero observed false-positive intervals in the accepted subset.
- Interpretation: multilingual family recognition restores a conservative,
  high-precision selective operating point on an independent source, but it
  does not improve unselective overall F1 and does not yet provide a new
  semantic-role expert. The result supports coverage/abstention value and
  exposes a remaining recall bottleneck; it is not a claim of full
  cross-language generalization.

## 2026-08-16 — Swissgeol learned risk-aware acceptance router

- Before fitting the router, tested a broader German alias set that increased
  held-out page-family support from 20.00% to 45.71%. This degraded accepted
  interval precision from `1.0000` to `0.5882`, reduced interval F1 to
  `0.3509`, and raised boundary CNER to `0.3800`. The broad alias expansion was
  rejected and the conservative alias set restored. The failure shows that
  lexical coverage alone is not a safe routing criterion.
- Implemented a document-level logistic risk gate over reference-blind page,
  OCR, family, and sequence features. The extraction expert itself is
  unchanged. Five-fold OOF probabilities on the 37-document development set
  selected threshold `0.7581` under a minimum accepted-document exactness
  requirement of `0.95`.
- Development: accepted 16/37 documents (`43.24%`) with exactness `1.0000`.
- Content-group-held-out validation: accepted 15/35 (`42.86%`) with exactness
  `1.0000`. Routed interval precision/recall/F1 were `1.0000/0.4375/0.6087`,
  versus unchanged baseline `0.5714/0.6000/0.5854`. Routed boundary F1 was
  `0.6061` with CNER `0.0000`.
- Calibration on the held-out split was Brier `0.0555`, ECE `0.1481`, and
  negative log-likelihood `0.2164`; the gate is useful for selective risk but
  not perfectly calibrated.
- The held-out split was previously consumed by the multilingual alias audit,
  so this is validation evidence rather than untouched external confirmation.
  Decision: retain the router as a promising risk-aware acceptance branch;
  do not promote it to the BGS primary method or open BGS v003.

## 2026-08-16 — BGS safe-sequence risk gate no-go

- Repaired and ran the nested source-disjoint BGS v028 risk-acceptance script
  with a safety label that permits incomplete recall but rejects every emitted
  boundary not supported by the reference sequence within 0.05 m.
- The development-fitted threshold was `0.968716`. It accepted only 1/26
  documents (`3.85%` coverage) with observed document safety `1.0000`.
- Selective boundary F1 was `0.0054` and selective interval F1 was `0.0000`;
  the single accepted document emitted one supported boundary while omitting
  the rest. Unfiltered v028 remained boundary/interval F1 `0.3475/0.1978`.
- Decision: `NO_GO`. The gate is retained as a negative risk/coverage
  diagnostic and is not promoted. It cannot solve the structural recall
  bottleneck, and no further BGS threshold complexity will be added. BGS v003
  remains frozen and unopened.

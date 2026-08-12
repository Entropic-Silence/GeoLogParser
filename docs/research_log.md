# Research log

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

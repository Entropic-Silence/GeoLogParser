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

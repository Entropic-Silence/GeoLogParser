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

# Publication evidence bundle

This directory is the minimal evidence subset intended for repository review.
It contains exact `run.json` and aggregate `metrics.json` bytes for every run in
the three paper result indexes, together with privacy-minimized projections of
the source-audit assertions used by manuscript claims.

The bundle deliberately excludes source PDFs/images, model weights, per-record
predictions, error rows, OCR text, run logs, ROI crops, and complete databases.
External projections retain only asserted count/status values and the SHA-256
of the controlled original evidence file.
Those materials remain in the controlled local evidence store because their
redistribution, privacy, or source terms require a separate item-level review.
Their immutable SHA-256 values remain in the result indexes and claim registry.

Run the following commands from a fresh checkout:

```bash
python scripts/build_paper_packages.py
pytest -q
```

The paper-package audit verifies the exact publication core. Full internal-run
verification remains available through `geologparser.result_index.verify_index`
when the controlled files are mounted.

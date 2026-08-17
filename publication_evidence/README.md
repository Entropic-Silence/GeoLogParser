# Publication evidence bundle

This directory is the minimal evidence subset intended for repository review.
It contains exact `run.json` and aggregate `metrics.json` bytes for every run in
the three paper result indexes, privacy-minimized projections of source-audit
assertions, and selected pseudonymized per-document outputs for the main
California and Swissgeol reanalyses. It also contains the privacy-minimized
inputs needed to recompute the Paper II same-candidate-pool ablation and the
Paper III spatial-support diagnostics without access to the source PDFs.

The bundle deliberately excludes source PDFs/images, model weights, unselected
development/audit predictions, OCR text, run logs, ROI crops, and complete databases.
External projections retain only asserted count/status values and the SHA-256
of the controlled original evidence file.
Released `document_outputs/` rows use a stable hashed `record_key` so raw,
sequence, and risk-policy outputs can be joined. County, source paths, page
text, OCR regions, and bounding boxes are removed; references, predictions,
match counts, decisions, and correction taxonomies are retained.
Those materials remain in the controlled local evidence store because their
redistribution, privacy, or source terms require a separate item-level review.
Their immutable SHA-256 values remain in the result indexes and claim registry.

These projections are not anonymous. Exact ordered-depth signatures uniquely
link 198/200 Paper II records within the two released cohort manifests, and
pairwise-distance fingerprints uniquely link all 35 transformed Paper III
points to the matching original point set. Aggregate attack results, with no
record mapping, are included under `analysis_inputs/linkage/`. Release review
must therefore cover source rights, record linkage, and sensitive locations;
removing direct identifiers is not a non-reidentifiability guarantee.

The two public-input recomputations are separate from table regeneration from
already frozen analysis JSON:

```bash
python scripts/recompute_paper2_candidate_pool_public.py \
  --input publication_evidence/analysis_inputs/paper2/candidate_pool_v001.jsonl \
  --output /tmp/paper2_candidate_pool_recomputed.jsonl
python scripts/recompute_paper3_spatial_public.py \
  --input publication_evidence/analysis_inputs/paper3/spatial_input_v001.jsonl \
  --output /tmp/paper3_spatial_recomputed.json
```

Run the following commands from a fresh checkout:

```bash
python scripts/build_paper_packages.py
pytest -q
```

The paper-package audit verifies the exact publication core. Full internal-run
verification remains available through `geologparser.result_index.verify_index`
when the controlled files are mounted.

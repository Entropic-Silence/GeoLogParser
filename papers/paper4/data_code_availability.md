# Data and code availability

The repository release contains the integrated manuscript, supplementary
methods, figure captions, source-manifest hashes, legally redistributable
structured or reanalysis assets, transformed public-analysis inputs, aggregate
metrics, model/runtime configuration records, and deterministic scripts for
rebuilding the Paper 4 figures, tables, audits, and public downstream
recomputations.

The release does **not** redistribute source PDFs, rendered source pages, raw
OCR text or regions, model weights, private service credentials, or
source-derived page assets whose item-level rights or linkage review is still
pending. For those materials, the package retains the publisher/source URL,
retrieval date, evidence tier, and SHA-256 hash so an authorized evaluator can
obtain the original material under the applicable terms. The transformed
public inputs are pseudonymized or geometrically transformed for analysis, but
they may remain linkable; the release makes no claim of anonymity or
non-reidentifiability.

The reproducibility entry point is:

```bash
python scripts/reproduce_paper4.py --with-tests
```

The public Paper II and Paper III reanalysis inputs can additionally be
recomputed with:

```bash
python scripts/recompute_paper2_candidate_pool_public.py \
  --input publication_evidence/analysis_inputs/paper2/candidate_pool_v001.jsonl \
  --output /tmp/paper2_candidate_pool_recomputed.jsonl

python scripts/recompute_paper3_spatial_public.py \
  --input publication_evidence/analysis_inputs/paper3/spatial_input_v001.jsonl \
  --output /tmp/paper3_spatial_recomputed.json
```

The upload bundle is a convenience assembly of the manuscript-facing files;
it is not a substitute for final author, rights, linkage, or journal-format
review. The repository package remains labelled
`SUBMISSION_READY_CANDIDATE` until those external checks are complete.


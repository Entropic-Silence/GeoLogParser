# Data and code availability

The `paper4-cageo-v1.0.0` repository release contains the final article,
supplementary methods, figure captions, source-manifest hashes, structured or
reanalysis assets, transformed public-analysis inputs, aggregate metrics,
model/runtime configuration records, and deterministic scripts for rebuilding
the figures, tables, audits, and public downstream recomputations.

The release does **not** redistribute source PDFs, rendered source pages, raw
OCR text or regions, model weights, private service credentials, or other
third-party assets where their terms prohibit redistribution. For those
materials, the package retains the publisher/source URL, retrieval date,
evidence tier, and SHA-256 hash so an authorized evaluator can obtain the
original material under the applicable terms. The transformed public inputs
may remain linkable; the release makes no claim of anonymity or
non-reidentifiability.

Yifan Du, sole and corresponding author, confirms that the GitHub release
materials were reviewed and screened for public dissemination, that
source-specific attribution and linkage information is retained in the
repository manifests, and that the public package is sufficient to reproduce
the reported result-level analyses. The archival DOI will be added after the
author deposits the tagged release.

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

The upload bundle is the fixed manuscript-facing assembly. Author metadata,
rights/linkage sign-off, and scientific audits are complete. DOI registration
and the submission portal's final formatting checks remain external actions.

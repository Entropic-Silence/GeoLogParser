# Data and code availability

The `paper4-cageo-v1.0.3` repository release contains the final article,
supplementary methods, figure captions, source-manifest hashes, structured or
reanalysis assets, transformed public-analysis inputs, aggregate metrics,
model/runtime configuration records, and deterministic scripts for rebuilding
the figures, tables, audits, and public downstream recomputations.

The separate `data-v002` release is the portable data companion. It contains
the author-reviewed selected source files and structured datasets used by the
principal experiments, with repository-relative paths, source-specific rights
records, and per-file SHA-256 hashes. It is not the complete Paper 4 package.
Model weights and private service credentials are not redistributed. The
transformed public inputs may remain linkable; the releases make no claim of
anonymity or non-reidentifiability.

Yifan Du, sole and corresponding author, confirms that the `paper4-cageo-v1.0.3`
package and the exact `data-v002` selection were reviewed and screened for
public dissemination. The `data-v002` review
covered source terms, selected item scope, privacy, sensitive locations,
embedded third-party content, attribution, and linkage. Source-specific
content review supersedes earlier provisional ledger statuses for the exact
named release scope; historical experiment-run metadata remains historical.
Source-specific obligations remain in the release ledger. Archival DOI fields remain pending
until the author deposits and verifies the archive record.

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

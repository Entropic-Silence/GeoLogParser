# Reproducing the integrated Paper 4 package

This workflow reproduces the committed Paper 4 manuscript, figures, tables,
publication evidence projections, review-package manifest, and all scientific
audits. It is intentionally a **result-reproduction** workflow: it does not
rerun a VLM/OCR model, download model weights, access source PDFs, or require
the restricted source-page archive.

## Environment

From the repository root, create a Python 3.10+ environment and install the
test extra:

```bash
python -m pip install -e ".[test]"
```

The CI workflow additionally installs `ghostscript`, `poppler-utils`, and
`tesseract-ocr` on Ubuntu. They are not needed for the committed Paper 4
figure/table regeneration, but are required by the full repository test suite.

## One-command rebuild

```bash
python scripts/reproduce_paper4.py
```

To include the complete repository test suite:

```bash
python scripts/reproduce_paper4.py --with-tests
```

The workflow performs, in order:

1. Rebuilds the four integrated C&G figures from committed Paper I–III
   analysis JSON.
2. Rebuilds `publication_evidence/` from committed result indexes and public
   reanalysis inputs.
3. Regenerates publication-facing tables and the manuscript metric audit from
   the publication evidence core.
4. Rebuilds `papers/package_manifest.json`.
5. Runs the Paper 4 claim, evidence-tier, submission, and UTF-8/LF audits.

The expected final state is:

```text
package_label: SUBMISSION_READY_CANDIDATE
scientific_content_ready: true
submission_ready: false
```

`submission_ready=false` is intentional: final rights, linkage, authorship,
and journal-format checks remain external gates.

## What is and is not redistributed

The repository includes the manuscript, supplement, tables, figures, configs,
analysis JSON, manifests, hashes, pseudonymized/transformed public reanalysis
inputs, and deterministic scripts. It does not redistribute source PDFs,
rendered source pages, raw OCR regions/text, model weights, or source-derived
assets whose item-level rights are still pending. The public projections are
explicitly linkable and are not claimed to be anonymous; see
`publication_evidence/README.md` and the linkage diagnostics under
`publication_evidence/analysis_inputs/linkage/`.

## Recomputing public downstream analyses

The Paper II candidate-pool and Paper III spatial diagnostics can be
recomputed independently from the committed transformed inputs:

```bash
python scripts/recompute_paper2_candidate_pool_public.py \
  --input publication_evidence/analysis_inputs/paper2/candidate_pool_v001.jsonl \
  --output /tmp/paper2_candidate_pool_recomputed.jsonl

python scripts/recompute_paper3_spatial_public.py \
  --input publication_evidence/analysis_inputs/paper3/spatial_input_v001.jsonl \
  --output /tmp/paper3_spatial_recomputed.json
```

The exact expected aggregate outputs are recorded in the corresponding
`publication_evidence/analysis_inputs/*recomputed*` files and in the Paper 4
claim-evidence map.

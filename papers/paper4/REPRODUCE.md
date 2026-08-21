# Reproducing the integrated Paper 4 package

This workflow reproduces the committed Paper 4 manuscript, figures, tables,
publication evidence projections, review-package manifest, and all scientific
audits. It is intentionally a **result-reproduction** workflow: it does not
rerun a VLM/OCR model or download model weights. The author-reviewed selected
source/data inputs are available separately in the portable `data-v002`
companion when source-level inspection is required.

## Environment

From the repository root, create a Python 3.10+ environment and install the
test extra:

```bash
python -m pip install -e ".[test]"
```

The final manuscript rebuild also requires PowerShell 7, Pandoc 3.10.2, and
Tectonic 0.17.0. Put `pandoc` and `tectonic` on `PATH`, or set `PANDOC` and
`TECTONIC` to their executable paths. The Elsevier C&G class/style files are
tracked with the manuscript. The exact DejaVu 2.37 fonts used by the canonical
artwork are tracked under `papers/paper4/fonts/` with their licence and
SHA-256 values.

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
   analysis JSON, plus the three supplementary figures.
2. Rebuilds the final Markdown, LaTeX, and PDF manuscript from
   `papers/paper4/manuscript.md`.
3. Assembles the complete portal-facing manuscript bundle, including the
   freshly built final PDF.
4. Rebuilds `publication_evidence/` from committed result indexes and public
   reanalysis inputs.
5. Regenerates publication-facing tables and the manuscript metric audit from
   the publication evidence core.
6. Runs the Paper 4 claim, evidence-tier, and submission audits.
7. Rebuilds `papers/package_manifest.json` after the submission gate so the
   repository-level status captures the newly audited state.
8. Runs the UTF-8/LF audit and
   verifies the frozen release artifact manifests without rewriting their Git
   provenance.

The expected final state is:

```text
package_label: SUBMISSION_READY_CANDIDATE
scientific_content_ready: true
submission_ready: false
```

The Paper 4 scientific content, release artifacts, authorship metadata, and
item-scoped rights/linkage attestation are complete. The gate remains
`submission_ready=false` until the author completes the Computers & Geosciences
portal upload and final artwork/metadata checks. The published Zenodo software
record is v1.0.6 at DOI `10.5281/zenodo.22030229`; the published `data-v002`
record is at DOI `10.5281/zenodo.22031703`. Neither DOI identifies a journal
article, and a v1.0.8 Zenodo software record would require creating a new
version rather than relabelling the v1.0.6 record.

## What is and is not redistributed

The `paper4-cageo-v1.0.8` package includes the manuscript, supplement, tables,
figures, configs, analysis JSON, manifests, hashes, transformed public
reanalysis inputs, and deterministic scripts. The separate `data-v002`
companion was originally paired with an earlier Paper 4 package and is reused
unchanged; it contains the selected source files and structured datasets used by
the principal experiments. Its paths are repository relative and its item-
scoped author sign-off covers rights, attribution, linkage, privacy, sensitive
locations, and embedded content. Model weights and private credentials are not
included. Public projections are explicitly linkable and are not claimed to be
anonymous; see
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

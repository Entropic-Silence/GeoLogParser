# Integrated Computers & Geosciences manuscript

This directory is an independent fourth manuscript. It does not replace or
modify `papers/paper1`, `papers/paper2`, or `papers/paper3`; those remain frozen
fallback analyses.

## Package

- `manuscript.md`: integrated main text (C&G-length, structured abstract, one
  narrative, and exactly three research questions).
- `supplement.md`: detailed provenance, split, ablation, source-shift, and
  spatial sensitivity material.
- `supplementary_captions.md`: standalone captions for Supplementary Figures
  S1–S3 and Supplementary Tables S1–S3.
- `main_tables.md`: headline tables, including exact VLM runtime provenance.
- `figure_manifest.json` and `figures/`: four integrated C&G main figures plus
  supplementary risk/threshold/error-mechanism figures.
- `build_cg_figures.py`: deterministic main-figure generator from frozen JSON
  analyses.
- `claim_evidence_map.md`: claim-to-artifact audit map.
- `audit_claim_evidence.py` and `claim_evidence_audit.json`: claim/evidence
  existence and evidence-tier audit.
- `submission_gate.json`: C&G-facing package gate; author metadata,
  declarations, and rights/linkage sign-off are fixed, while DOI registration
  and submission-portal checks remain external.
- `cover_letter_points.md`: C&G-oriented submission framing and disclosure
  checklist.
- `data_code_availability.md`: upload-facing data/code availability statement.
- `submission_bundle/`: generated, hash-manifested manuscript-facing files for
  individual portal upload; it excludes third-party source files where their
  terms prohibit redistribution.
- `../../experiments/paper1/analysis/modern_vlm_transport_comparison_v001.json`: exploratory open-model source-shift roster; specialist decoder/task coverage is kept separate from direct-JSON F1.
- `REPRODUCE.md`: fresh-checkout commands for rebuilding the Paper 4 figures,
  publication evidence, tables, package manifest, and audits without source
  PDFs or model weights.

## Scientific positioning

The central claim is not that a VLM is inaccurate. The central claim is that
high boundary-pair interval F1 does not, by itself, establish a trustworthy
geological database. The manuscript therefore couples modern VLM proposals to
independent positioned evidence, deterministic geometry checks, selective
accept/review decisions, abstention, and downstream spatial-support diagnostics.

## Rebuild

The main-figure assets are regenerated from frozen Paper I/II/III analysis JSON
files by `build_cg_figures.py`; no model is rerun. Before submission, run the
repository-wide numeric audit, `audit_claim_evidence.py`, and the C&G submission
gate, then confirm the final artwork/reference requirements.

For the complete result-reproduction workflow, run
`python scripts/reproduce_paper4.py`; see `REPRODUCE.md` for the exact
environment, publication-evidence scope, and expected gate state.

To assemble the portal-facing files after rebuilding the figures, run:

```bash
python scripts/build_paper4_upload_bundle.py
```

The resulting `submission_bundle/Paper4_Upload_Manifest.json` is the canonical
file list and checksum record. The complete Paper 4 package is identified by
`paper4-cageo-v1.0.2`; its portable source/data companion is `data-v002`.
Archival DOI fields remain intentionally pending until the author deposits
and verifies the archive record.

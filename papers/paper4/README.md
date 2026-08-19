# Integrated Computers & Geosciences manuscript

This directory is an independent fourth manuscript. It does not replace or
modify `papers/paper1`, `papers/paper2`, or `papers/paper3`; those remain frozen
fallback analyses.

## Package

- `manuscript.md`: integrated main text (C&G-length, structured abstract, one
  narrative, and exactly three research questions).
- `supplement.md`: detailed provenance, split, ablation, source-shift, and
  spatial sensitivity material.
- `main_tables.md`: headline tables, including exact VLM runtime provenance.
- `figure_manifest.json` and `figures/`: four integrated C&G main figures plus
  supplementary risk/threshold/error-mechanism figures.
- `build_cg_figures.py`: deterministic main-figure generator from frozen JSON
  analyses.
- `claim_evidence_map.md`: claim-to-artifact audit map.
- `audit_claim_evidence.py` and `claim_evidence_audit.json`: claim/evidence
  existence and evidence-tier audit.
- `submission_gate.json`: C&G-facing scientific package gate; rights,
  authorship, linkage, and final journal formatting remain external gates.
- `cover_letter_points.md`: C&G-oriented submission framing and disclosure
  checklist.
- `experiments/paper1/analysis/modern_vlm_transport_comparison_v001.json`: exploratory open-model source-shift roster; specialist decoder/task coverage is kept separate from direct-JSON F1.

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

# Integrated Computers & Geosciences manuscript

This directory is an independent fourth manuscript. It does not replace or
modify `papers/paper1`, `papers/paper2`, or `papers/paper3`; those remain frozen
fallback analyses.

## Package

- `manuscript.md`: integrated main text (target C&G length, one narrative and
  three research questions).
- `supplement.md`: detailed provenance, split, ablation, source-shift, and
  spatial sensitivity material.
- `main_tables.md`: headline tables, including exact VLM runtime provenance.
- `figure_manifest.json` and `figures/`: standalone main-figure assets copied
  from the frozen code-generated analyses.
- `claim_evidence_map.md`: claim-to-artifact audit map.
- `cover_letter_points.md`: C&G-oriented submission framing and disclosure
  checklist.

## Scientific positioning

The central claim is not that a VLM is inaccurate. The central claim is that
high boundary-pair interval F1 does not, by itself, establish a trustworthy
geological database. The manuscript therefore couples modern VLM proposals to
independent positioned evidence, deterministic sequence/geometry checks,
selective risk decisions, abstention, and downstream spatial-support diagnostics.

## Rebuild

The figure assets originate from the frozen Paper I/II/III generation scripts.
The manuscript values are bound to the existing claim registry and generated
analysis files. Before submission, run the repository-wide manuscript metric
audit and confirm the final C&G artwork/reference requirements.

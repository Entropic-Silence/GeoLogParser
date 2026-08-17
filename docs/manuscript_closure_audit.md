# Manuscript closure audit

Date: 2026-08-17  
Repository: `GeoLogParser`  
Latest pre-audit commit: `9ea1b30`

## Automated checks

The following were run after the closure edits:

```text
scripts/audit_publication_readiness.py
scripts/build_paper_packages.py
```

All three manuscripts passed structural section, bibliography, literature
evidence, local-link, result-index, and claim-source checks. No manuscript
contains an unresolved ``TBD`` or ``[CITATION TO VERIFY]`` marker. Generated
review packages are labelled `SUBMISSION_READY` by the repository's evidence
auditor; this label means scientific-content/evidence closure and does not
override the external rights and source-verification gate in
`docs/submission_blockers.md`.

## Paper I

Status: `SUBMISSION_READY_CANDIDATE`

The manuscript is bounded as a benchmark and failure-characterization paper.
California published manual-transcription references, BGS source-shift tests,
USGS Idaho disagreement audits, Raft River, Swissgeol, degradation metadata,
and the fixed-parser random/grouped leakage diagnostic are all separated by
evidence tier. The random/grouped result is explicitly not described as a
retraining generalization experiment. The paper does not claim broad
multilingual human Gold or independent annotator agreement.

## Paper II

Status: `SUBMISSION_READY_CANDIDATE`

The manuscript is bounded around the converged v028 routed structural parser,
geological constraints, candidate-level risk control, and abstention. It reports
both positive California/Swissgeol results and the one-time BGS v003 zero-coverage
external failure. The finite-sample certificate is stated with its iid-action
assumption and is not promoted to a cross-source guarantee. NativeMM/Qwen
branches remain documented as no-go exploratory evidence, not as hidden primary
methods. Real-document component results are described as diagnostic artifact
comparisons rather than a fabricated factorial ablation.

## Paper III

Status: `SUBMISSION_READY_CANDIDATE`

The manuscript is bounded around provenance-bearing database export, controlled
error propagation, spatial support, and the real three-layer risk-aware IDW
diagnostic. It no longer implies that a timed human study or GemPy integration
was completed. It reports the 15/35 acceptance trade-off and the authoritative
collar/coordinate limitation directly. The workflow is presented as a
reproducible downstream diagnostic, not a validated production geological
interpretation system.

## Closure decision

The scientific manuscripts are closed for this cycle. No new model, training
branch, threshold, prompt, alias, or frozen external evaluation is authorized
by this closure audit. Any future change to a result-bearing claim must create a
new experiment/result version and update the claim-evidence matrix.


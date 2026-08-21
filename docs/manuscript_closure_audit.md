# Manuscript closure audit

Date: 2026-08-18
Repository: `GeoLogParser`  
Adviser-reviewed baseline commit: `0f4d2d5`
Closure commit: `54587ae`

Correction-release note (2026-08-21): the commit above records the historical
closure baseline. The corrected Paper IV v1.0.8 package now has a 246-word
abstract, 5,507 main-text words with inline tables and captions excluded, and
5,809 article-body words when inline table text is included. Its prompt hash,
DOI types, supplementary cross-references, declarations, and canonical artwork
bindings were re-audited without changing frozen scientific results.

## Automated checks

The following were run after the closure edits:

```text
scripts/audit_publication_readiness.py
scripts/build_paper_packages.py
papers/paper4/verify_claims.py
papers/paper4/audit_claim_evidence.py
scripts/audit_paper4_submission.py
scripts/audit_generated_text_format.py
```

All four manuscript packages passed structural section, bibliography, literature
evidence, local-link, result-index, and claim-source checks. No manuscript
contains an unresolved ``TBD`` or ``[CITATION TO VERIFY]`` marker. Generated
review packages are labelled `SUBMISSION_READY_CANDIDATE` by the repository's evidence
auditor; this label means scientific-content/evidence closure and does not
override the external rights and source-verification gate in
`docs/submission_blockers.md`.

## Paper I

Status: `SUBMISSION_READY_CANDIDATE`

The manuscript is bounded as a multi-cohort/cross-source evaluation and failure-
characterization paper, not a comprehensive benchmark. Five California cohorts
now use document-cluster bootstrap intervals, zero-output rates, per-document
recall, and exact-record rates. Source-agreement, authoritative metadata,
Machine Silver, and no-GT audits remain separate. The fixed-prediction random/
grouped result is supplementary and supports no general leakage claim.

## Paper II

Status: `SUBMISSION_READY_CANDIDATE`

The manuscript is bounded around same-candidate-pool sequence reconstruction,
addition-only acceptance, and document-level risk. The v004/v005 ablation shows
that monotonic decoding supplies most recovery, while the complete score trades
recall for precision. The primary safety statement is zero worsened documents
among 19 accepted documents with a one-sided 95% upper bound of 0.1459; the
0/82 action result is secondary. NativeMM and v018–v030 branch history is
supplementary, and BGS v003 is retained as one concise zero-coverage failure.

## Paper III

Status: `SUBMISSION_READY_CANDIDATE`

The manuscript is bounded as a stratigraphic surface/volume sensitivity
diagnostic. Full-support and strict matched-subset estimands are reported
separately; the latter shows that risk-aware and reread inputs are identical on
the accepted 15 documents and that the apparent full-support gain is mainly a
selection/spatial-support effect. Convex-hull coverage, neighbour spacing, IDW
sensitivity, and leave-one-borehole-out interpolation error are now central.
Software interoperability is supplementary, and no validated geological model
or production workflow is claimed.

## Paper IV (Computers & Geosciences integrated manuscript)

Status: `SUBMISSION_READY_CANDIDATE`

At the historical closure commit, the manuscript was counted as a single
5,843-word narrative with three research questions,
four integrated main figures, and a structured abstract. Its evidence chain is
explicitly ordered as modern VLM proposal, independently positioned evidence,
deterministic checks, selective accept/review, and downstream spatial-support
diagnostics. The primary reported VLM result is Qwen3.8-27B-FP8 boundary-pair
F1 0.896--0.932; the assurance result is held-out selective precision 0.993 at
proposal coverage 0.244, with only 4/100 complete-document auto-acceptance.
Matched-support analysis is retained to show that abstention changes the spatial
observation process. Runtime provenance is partially reconstructable where the
historical serving trace is incomplete; no unverified fields are inferred.
Source PDFs and derivatives without completed rights clearance are not claimed
as redistributable.

## Closure decision

The scientific manuscripts are closed for this cycle. No new model, training
branch, threshold, prompt, alias, or frozen external evaluation is authorized
by this closure audit. Any future change to a result-bearing claim must create a
new experiment/result version and update the claim-evidence matrix.

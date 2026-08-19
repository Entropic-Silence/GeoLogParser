# Paper 4 focus and simulated-review audit

Audit date: 2026-08-19

Scope: internal review of the focused Paper 4 narrative. This audit does not
authorize new experiments, model changes, threshold tuning, split changes, or
release actions.

## Central claim

The manuscript follows one chain: high extraction capability -> provenance gap
-> independently checkable evidence -> selective database decision -> spatial
consequence of abstention. Capability, assurance, and deployment utility are
kept as separate claim layers.

## Reviewer A - Computers & Geosciences editor

- Scope: supported. The manuscript presents a computational/informatics
  assurance layer and an explicit geoscientific consequence in borehole
  database support, matching the current Guide's dual-contribution scope.
- One-sentence innovation: a provenance-grounded acceptance gate connects VLM
  proposal extraction to auditable database admission and support-aware
  evaluation.
- Engineering-integration risk: reduced by making the hypothesis, RQs,
  selective operating point, negative results, and support estimands explicit;
  legacy recovery is secondary harm analysis and reproducibility is
  infrastructure, not a fourth contribution.
- First-two-pages test: passed in the review PDF. The title, abstract, three
  RQs, three contributions, and Fig. 1 expose the full chain.
- Remaining editorial gate: permanent archival DOI/data citation, Elsevier
  declarations-tool upload, item-level rights sign-off, and portal word-count
  confirmation. Author metadata is populated in the manuscript.

## Reviewer B - document AI / VLM

- Boundary-pair metric and semantic-correctness limitation remain explicit.
- Familiar California performance (0.896-0.932) is separated from Swissgeol
  source-shift performance (0.577); evidence tiers are not pooled.
- Contamination and source-selection limitations remain visible.
- Main assurance is described as v001 development, v002 validation, and v003
  held-out replication with fixed agreement tolerance; v004/v005 are not
  called main-assurance confirmation cohorts.
- Legacy addition-only threshold 2.999 is kept in its secondary policy context
  and is not conflated with the main VLM assurance gate.
- Proposal and acceptance denominators remain distinct: 1,833 proposals,
  1,450 both-endpoint anchors, 447 owned/accepted intervals, 4/100 complete
  documents, and 3,099/3,666 endpoint fields.
- The 0.993 precision claim is not presented as document-level correctness.

## Reviewer C - geoscience

- Borehole relevance is stated through interval boundaries, source provenance,
  database admission, and downstream spatial support.
- Full-support and matched-support are labelled as different estimands; the
  matched-support reversal is retained.
- IDW remains a diagnostic rather than a validated geological model.
- Abstention is interpreted as a spatial sampling/support decision, with
  selection bias and retained-hull reduction stated as limitations.
- No new geological modelling experiment or stronger geological claim was
  introduced.

## Automated checks

- `verify_claims.py`: passed.
- `audit_claim_evidence.py`: passed (15 claims, no errors).
- `audit_paper4_submission.py`: passed as `SUBMISSION_READY_CANDIDATE`; the
  remaining external requirements are archival, portal, and rights actions.
- LaTeX clean build: completed for the 21-page internal review PDF and the
  20-page final PDF; no undefined citations/references, duplicate PDF
  destinations, or table overfull warnings. The remaining 117 pt CAS
  title-box warning is an invisible template box with no clipped content.
- Vector artwork check: passed for Figure_1.pdf through Figure_4.pdf and the
  graphical abstract; figures render without clipping or overlap.
- `pytest`: not run because `pytest` is not installed in this environment.

## Open P0/P1/P2 items

- P0: none identified in the frozen scientific content or evidence mapping.
- P1: create/authorize a permanent archival DOI and data citation; complete
  Elsevier's competing-interest declarations-tool `.docx`; confirm item-level
  source rights/linkage in Editorial Manager.
- P2: run the final Editorial Manager word-count/artwork preview; install
  `pytest` if a local test rerun is required. The internal banner/footer and
  adviser-question page are absent from `manuscript_final.pdf`.

## Deliverables checked

- `manuscript_review_v2.pdf`: internal review artifact with single-column,
  double-spacing, continuous line numbers, page numbers, review footer, and
  adviser questions.
- `manuscript_final.pdf` and `manuscript_final.md`: metadata-populated pair;
  final PDF has no preprint or review footer and Markdown retains the same
  scientific text, declarations, metrics, limitations, and references.
- Main figures: `Figure_1.pdf` through `Figure_4.pdf`; graphical abstract:
  `graphical_abstract.pdf`.
- Supplementary upload bundle: `papers/paper4/submission_bundle` with S1-S3
  captions, methods, artwork, and SHA-256 manifest.

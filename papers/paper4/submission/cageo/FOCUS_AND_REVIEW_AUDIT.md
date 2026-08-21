# Paper 4 focus and simulated-review audit

Audit date: 2026-08-21

Scope: final review of the focused Paper 4 narrative and release package. No
new experiment, model change, threshold tuning, or split change was introduced.

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
- Remaining editorial gate: final Editorial Manager upload/artwork preview and
  the publisher-assigned article DOI. The published Zenodo software and data
  records are cited by their actual resource types; author metadata and the
  sole-author rights/linkage sign-off are complete.

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
- `audit_paper4_submission.py`: passed as
  `SUBMISSION_READY_CANDIDATE`; scientific content and release artifacts are
  ready, while `submission_ready` remains false until final portal checks.
- LaTeX clean build: completed for the 22-page final PDF; no undefined
  citations/references, duplicate PDF destinations, or visible overfull
  document boxes. A non-fatal underfull warning occurs on the digest line
  because the 64-character token is intentionally unbreakable. The final
  source retains `lineno` as required by C&G, while the prompt digest is
  emitted as one unbreakable box so line numbers cannot be inserted inside
  its hexadecimal characters.
- Vector artwork check: passed for Figure_1.pdf through Figure_4.pdf and the
  graphical abstract; figures render without clipping or overlap, all PDF
  fonts are embedded, and the manuscript contains zero raster image objects.
- PDF metadata check: passed for title, author (`Yifan Du`), subject, and
  keywords; no template-default author/subject metadata remains.
- Canonical source-Markdown estimate: 5,507 main-text words with tables and
  captions excluded, and 5,809 article-body words when inline table text is
  included; abstract, captions, keywords, highlights, declarations, and
  references are excluded from both. The submission gate uses the 5,809-word
  article-body measure against a 6,050 working limit.
- Canonical full-repository local test run: `478 passed, 10 skipped` after
  `python -m pip install -e ".[test]"`. The skipped tests require optional
  Ghostscript/Tesseract fixture tools, external RapidOCR model assets, or the
  PyVista extra; both CI operating systems run the same collected test set.
  Other historical environment counts are not used as the release claim. No
  test was represented as passed without being run.
- Table/citation checks: Tables 1 and 2 have numbered captions and labels;
  Table 1 has an explicit continuation caption; duplicate author-year/citation
  text was removed from its first column.

## Open P0/P1/P2 items

- P0: none identified in the frozen scientific content or evidence mapping.
- P1: complete the Editorial Manager upload/artwork preview and, if desired,
  create a new Zenodo v1.0.8 software version. Do not relabel the published
  v1.0.6 software DOI as an article DOI.
- P2: confirm the portal-computed word count (source estimate: 5,507 main-text
  words; 5,809 body words). The internal banner/footer and
  adviser-question page are absent from `manuscript_final.pdf`.

## Archive-level qualification

The v1.0.8 correction release fixes final-PDF hash rendering, publication
metadata, deterministic figure PDFs, and submission-material consistency. It
does not turn the result-level workflow
into an end-to-end replay of the historical Qwen runtime, and it does not
claim byte-for-byte deterministic regeneration across operating systems.

## Deliverables checked

- `manuscript_final.pdf` and `manuscript_final.md`: metadata-populated pair;
  final PDF has no preprint or review footer and Markdown retains the same
  scientific text, declarations, metrics, limitations, and references.
- No adviser-review PDF was generated or updated in this round.
- Main figures: `Figure_1.pdf` through `Figure_4.pdf`; graphical abstract:
  `graphical_abstract.pdf`.
- Supplementary upload bundle: `papers/paper4/submission_bundle` with S1-S3
  captions, methods, paired PDF/PNG artwork, and SHA-256 manifest.

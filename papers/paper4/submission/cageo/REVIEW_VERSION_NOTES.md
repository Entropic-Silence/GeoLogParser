# Paper 4 review and final build notes

Status: `manuscript_review_v2.pdf` is an internal academic review artifact;
`manuscript_final.pdf` and `manuscript_final.md` are the metadata-populated
final pair. Both are generated from the frozen scientific source
`papers/paper4/manuscript.md`; no Paper I-III scientific manuscript was edited.

The internal review PDF has a visible `DRAFT FOR INTERNAL ACADEMIC REVIEW --
NOT FOR SUBMISSION` banner, review footer, and adviser-question page. The
final PDF removes all three and also removes the CAS default `Preprint
submitted to Elsevier` footer. It retains single-column layout, double
spacing, page numbers, editable tables, author-year
references, declarations, and vector figure links.

Build command:

```text
powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1 -Final
```

The build uses Pandoc 3.10.2 and Tectonic 0.17.0 from the local workspace
toolchain; `PANDOC` and `TECTONIC` may override those paths.

## Final QA

- `manuscript_review_v2.pdf`: 21 pages; the current `manuscript_final.pdf` is
  22 pages after the v1.0.8 rebuild. Page count is recorded from the emitted
  PDF rather than copied from an earlier review note.
- Both PDFs render with no clipped figures, missing glyph blocks, undefined
  citations/references, duplicate PDF destinations, or table overfull boxes.
- The final page footer contains page numbers only; no preprint or review text.
- Author metadata is Yifan Du, North China University of Water Resources and
  Electric Power, ORCID `0009-0008-7740-5408`,
  `duyifan619916@gmail.com`, sole corresponding author.
- Declarations state self-funded work and no competing interests.
- Extracted PDF text retains the frozen headline values and limitations:
  California F1 0.896-0.932, Swissgeol F1 0.577, BGS zero utility, 0.993 at
  0.244 coverage, 444/447, 4/100 complete-document automation, matched-
  support reversal, contamination, partially reconstructable runtime, and
  diagnostic-only IDW.
- The canonical source estimate is 5,507 main-text words (5,809 including
  inline Markdown table text; captions and references excluded by the
  estimate). The submission gate uses the same 5,809-word article-body
  measure against the 6,050 working limit.
- Bibliography contains 33 cited entries, corrected `Amini, A.` metadata, full
  Borkovich author list, protected acronym capitalization, and no `et al.` in
  the rendered reference list.
- `verify_claims.py`, `audit_claim_evidence.py`, and
  `audit_paper4_submission.py` pass. The canonical local test profile
  (`pip install -e ".[test]"`) reports `480 passed, 10 skipped`; the skipped
  tests require optional Ghostscript/Tesseract fixture tools, external
  RapidOCR model assets, or PyVista. No test result is inferred from an unrun
  command.

## Reproducibility scope

The package supports result-level reproduction from frozen predictions through
matching, metrics, tables, figures, and audits. It does not claim byte-for-byte
cross-platform regeneration or replay of the historical Qwen inference runtime;
the manuscript discloses that the execution provenance is partially
reconstructable. The artwork builder searches standard Linux, macOS-style user,
and Windows font locations, so a normal Linux checkout no longer fails solely
because DejaVu Sans is stored under `/usr/share/fonts/truetype/dejavu`.

Cross-platform reruns may serialize PDF/PNG metadata or path separators
differently while preserving numeric outputs and rendered pixels. The frozen
release manifests remain the authoritative checksums for the published assets.

## Non-fatal template note

The legacy CAS class emits one 117 pt overfull title-box warning at
`\maketitle`; it is an invisible internal box, not clipped page content. The
visible title page and all body/table boxes were inspected after rendering.
The review and final builds load `lineno.sty` and retain line numbering for the
editable C&G source. The final hash is emitted as an unbreakable box, so a line
number cannot be inserted between hexadecimal characters; the PDF regression
test extracts the complete 64-character value.

## External author actions

The published data DOI and historical software DOI are recorded with their
actual resource types. The C&G article DOI is assigned by the publisher; an
optional Zenodo v1.0.8 software record must be created as a new version.
Rights/linkage review is complete and recorded in `RIGHTS_LINKAGE_SIGNOFF.md`.
Editorial Manager still requires its own upload, declarations-tool, word-count,
and artwork-preview steps.

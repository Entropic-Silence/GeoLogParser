# Paper 4 review and final build notes

Status: `manuscript_review_v2.pdf` is an internal academic review artifact;
`manuscript_final.pdf` and `manuscript_final.md` are the metadata-populated
final pair. Both are generated from the frozen scientific source
`papers/paper4/manuscript.md`; no Paper I-III scientific manuscript was edited.

The internal review PDF has a visible `DRAFT FOR INTERNAL ACADEMIC REVIEW --
NOT FOR SUBMISSION` banner, review footer, and adviser-question page. The
final PDF removes all three and also removes the CAS default `Preprint
submitted to Elsevier` footer. It retains single-column layout, double
spacing, continuous line numbers, page numbers, editable tables, author-year
references, declarations, and vector figure links.

Build command:

```text
powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1 -Final
```

The build uses Pandoc 3.10.2 and Tectonic 0.17.0 from the local workspace
toolchain; `PANDOC` and `TECTONIC` may override those paths.

## Final QA

- `manuscript_review_v2.pdf`: 21 pages; `manuscript_final.pdf`: 20 pages.
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
- The final source estimate is 5,193 main-text words (5,586 including inline
  Markdown table text, captions and references excluded by the estimate).
- Bibliography contains 31 cited entries, corrected `Amini, A.` metadata, full
  Borkovich author list, protected acronym capitalization, and no `et al.` in
  the rendered reference list.
- `verify_claims.py`, `audit_claim_evidence.py`, and
  `audit_paper4_submission.py` pass. The requested pytest suites could not run
  because `pytest` is not installed in this Python environment.

## Non-fatal template note

The legacy CAS class emits one 117 pt overfull title-box warning at
`\maketitle`; it is an invisible internal box, not clipped page content. The
visible title page and all body/table boxes were inspected after rendering.
The template's `lineno.sty` invalid-UTF-8 warning is external to the manuscript
source and does not affect output glyphs.

## External author actions

A permanent Zenodo/DataCite DOI and data citation remain to be created from the
annotated release tag. Rights/linkage review is complete and recorded in
`RIGHTS_LINKAGE_SIGNOFF.md`. Editorial Manager still requires its own upload,
declarations-tool, word-count, and artwork-preview steps.

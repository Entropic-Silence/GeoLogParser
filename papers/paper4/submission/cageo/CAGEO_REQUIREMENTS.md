# Computers & Geosciences submission requirements

Status: requirements verification and submission-workspace preparation only.
The scientific source of truth remains `papers/paper4/manuscript.md` and
`papers/paper4/supplement.md`. This file does not authorize scientific edits,
new experiments, threshold changes, or changes to frozen headline values.

Verification date: 2026-08-21 (Asia/Shanghai)

## Official sources checked

1. Elsevier Guide for Authors (official journal page):
   https://www.sciencedirect.com/journal/computers-and-geosciences/publish/guide-for-authors
2. Official CAGEO LaTeX template repository:
   https://github.com/cageo/CAGEO_LaTeXTemplate
   - checked branch: `main`
   - checked commit: `965ebcc5e8eb8e77fd72b84ca975161a8bb85e68`
   - commit date: 2021-03-24
   - relevant files: `main_document.tex`, `README`, `cas-sc.cls`,
     `cas-common.sty`, `cas-model2-names.bst`

The journal page is the authority for current submission rules. The GitHub
template is used for the editable LaTeX structure and checklist, but its
older commit cannot override the live Guide for Authors.

The current Aims and Scope explicitly require a substantive contribution in
both computing/informatics and geoscience, and state that code access is
mandatory at submission for papers presenting software, workflows, trained
models, or computational pipelines. Papers that are only routine
implementations, benchmark comparisons without transferable insight, or
geoscience applications without genuine computational innovation are outside
scope. Paper 4 is therefore framed as a provenance-grounded
document-to-database assurance study; the VLM benchmark, reject option, and
spatial diagnostic are supporting evidence for that interface.

## Verified journal rules

### Article type and length

- **Article type:** Original research article. The manuscript makes an
  integrated computational and geoscientific contribution; it is not a review,
  book/software review, or letter.
- **Initial submission word limit:** Research Articles and Application Articles
  have a 5,500-word maximum. The Guide permits a maximum of 10% above the
  stated limit for these article types, giving an effective ceiling of 6,050
  words for an initial submission. The word count excludes the abstract,
  keywords, highlights, references, and captions.
- **Revised submission limit:** 6,500 words, with the same 10% allowance for
  non-review articles.
- **Current source estimate:** `manuscript.md` contains a 246-word abstract.
  The build script estimates 5,507 main-text words with tables and captions
  excluded and 5,809 article-body words when inline table text is included;
  the repository submission gate uses the same 5,809-word article-body
  measure. Both body measures are below the 6,050-word initial
  allowance; a final Editorial Manager count remains required.

### Abstract, keywords, and highlights

- **Abstract:** Maximum 300 words. It must be concise, factual, standalone,
  and normally contain no references. The Guide does not require a structured
  abstract. The current source abstract is 246 words and uses Background,
  Methods, Results, and Conclusions labels; this is length-compliant and does
  not conflict with an explicit structure requirement.
- **Keywords:** 1 to 6 English keywords. Avoid multiword phrases and
  non-established abbreviations where possible. The current source has 6
  keywords.
- **Highlights:** Required as a separate editable file whose filename includes
  `highlights`; 3 to 5 bullets, each no more than 85 characters including
  spaces. Current source and review package contain 4 compliant bullets (68,
  83, 72, and 82 characters); an editable `highlights.txt` is included in the
  submission workspace.

### Layout and editable source

- Editable source files are required for the whole submission, including text,
  tables, figures, and text graphics. A PDF alone is not an acceptable source.
- **Single-column layout:** mandatory for the journal. Double-column layout is
  allowed only for LaTeX submissions generally, but the CAGEO-specific section
  explicitly requires single column.
- **Double spacing:** mandatory.
- **Line numbering:** mandatory for every submission.
- The final editable source retains `cas-sc`, `\usepackage{lineno}`,
  `\linenumbers`, `\usepackage{setspace}`, and `\doublespacing`. The
  machine-readable prompt digest is emitted as one unbreakable box so a line
  number cannot be inserted inside its 64 hexadecimal characters; the PDF
  regression test extracts and validates the complete digest.
- The final package must use numbered, clearly defined article sections. The
  current manuscript section structure is compatible; Markdown itself is not
  the final editable submission format.

### Title page and authorship

The title-page information must include:

- concise and informative article title;
- given and family names of every author, in the same order as the submission
  system;
- affiliations indicating where the work was carried out, marked after author
  names, with full institutional name, postal address, and country, plus email
  where available;
- one clearly identified corresponding author with current email and contact
  details;
- present/permanent address footnotes where an author has moved or was visiting;
- ORCID identifiers when available (supported by the template author fields).

The Guide requires all authors to have made substantial contributions to the
conception/design or data acquisition/analysis/interpretation, to drafting or
critical revision, and to final approval, and to be accountable for the work.
A single corresponding author must communicate with the journal. A CRediT
author-contribution statement is required; the template uses `\credit` for
author roles and `\printcredits` for the rendered statement.

### Declarations

- **Competing interests:** Every author must complete the declarations tool.
  Authors with no conflicts select the "I have nothing to declare" option. The
  resulting declaration document must be uploaded as a `.doc` or `.docx` file;
  signatures are not required. Financial and personal relationships, grants,
  employment, consultancies, patents, editorial roles, and similar interests
  must be considered.
- **Funding:** Funding sources and grant numbers must be disclosed, together
  with any sponsor role in study design, data collection, analysis,
  interpretation, writing, or submission. If there was no specific funding,
  use the Guide's recommended no-specific-grant statement.
- **Generative AI in manuscript preparation:** Authors must declare use of
  generative AI or AI-assisted tools in preparing the manuscript, in a new
  section before References, using the tool/service name and purpose and
  confirming human review and responsibility. Basic spelling/grammar/reference
  tools are exempt. Authors must not list an AI tool as an author. The author
  must decide the exact disclosure for any AI assistance used in this
  submission-preparation cycle.
- **Generative AI artwork:** AI may support explanatory diagrams or
  reproducible data visualizations, but may not create or alter primary
  observed/experimental data images. Any generative-AI artwork requires
  disclosure in the figure caption and the general AI statement. Figure
  production provenance must remain recorded in repository scripts and the
  figure manifest.

### Computer Code Availability

For manuscripts presenting software, code, workflows, trained models, or
computational pipelines, the journal requires a public repository at
submission and for acceptance. The repository must be documented and support
evaluation, reuse, and long-term utility. At minimum it must include:

- a clear license;
- an English README with installation and basic usage;
- dependencies and computational requirements;
- enough material to reproduce the main results, or an explanation of justified
  data limitations plus a dummy model or synthetic test dataset;
- how-to files/tutorials and a user guide describing inputs, outputs, options,
  and expected behavior;
- English code comments; and
- ordinary repository files rather than only one compacted archive.

The template's code-availability checklist also asks for code/library name,
contact details, hardware requirements, programming language, required
software, program size, and a public URL.

Current Paper 4 status: **scientific and release package complete; portal and archival follow-up pending**.
The manuscript names the public GeoLogParser URL, MIT source-code license,
corresponding-author contact, and reproducibility scope. A local final Git
commit is created for this package and recorded in
`CAGEO_ARTIFACT_MANIFEST.json`. Creating an optional corrected Zenodo v1.0.8
version requires the author's Zenodo authorization; the publisher-assigned
article DOI remains pending rather than being fabricated. The
published Zenodo identifier `10.5281/zenodo.22030229` is a software DOI for
`paper4-cageo-v1.0.6`, not a journal-article DOI; a corrected v1.0.8 archive
would have to be created as a new version.

### Data Availability and research data

- A data-availability statement is required at submission and will appear with
  the published article.
- This journal follows research-data Option C: deposit research data in a
  relevant repository, cite and link the dataset in the article, or explain
  why sharing is impossible.
- Data references should include author(s), dataset title, repository, version
  if available, year, and a persistent identifier, with `[dataset]` before the
  reference in the submission reference list.
- Source rights, attribution, linkage, privacy, sensitive-location review, and
  any third-party material must be checked before release.

Current Paper 4 status: **repository, reproducibility materials, data companion,
and author rights/linkage sign-off supplied; final portal and archival steps
pending**. The complete article/result package candidate is
`paper4-cageo-v1.0.8`; the selected source
and structured-data companion is `data-v002`. The latter passed the author's
item-scoped rights, privacy, sensitive-location, embedded-content, attribution,
and linkage review. Source-specific obligations remain explicit. The completed
sign-off is recorded in `RIGHTS_LINKAGE_SIGNOFF.md`.

### Supplementary material

Supplementary files should be accurate and relevant, cited in the manuscript,
submitted at the same time as the manuscript, and accompanied by concise,
descriptive captions. After initial submission they can generally only be
added/replaced during revision, and they are published exactly as supplied.

The current `supplement.md` remains the scientific source. The
`papers/paper4/submission_bundle` directory now contains normalized
supplementary methods, standalone S1-S3 captions, S1-S3 artwork, main tables,
an editable C&G LaTeX main-manuscript archive, and a SHA-256 upload manifest.
A journal-specific editable supplementary conversion and portal upload remain
a production step; no scientific text is changed by that conversion.

### Artwork, figures, and tables

- Cite every figure and table in the manuscript and number them in order of
  appearance.
- Supply each artwork item as a separate file with a logical filename such as
  `Figure_1`.
- Every artwork item needs a caption with a short title and description. C&G's
  journal-specific rule says not to use the definite article `the` in figure or
  table captions.
- Preferred artwork formats are EPS/PDF for vector drawings and TIFF/JPG/PNG
  for raster artwork. The Guide gives minimum raster requirements of 300 dpi
  for photographs/halftones, 1000 dpi for bitmapped line drawings, and 500 dpi
  for line/halftone combinations, with corresponding single-column pixel
  minimums.
- Tables must be editable text, cited, consecutively numbered, captioned, and
  free of unnecessary vertical rules and cell shading.
- Current Paper 4 figures are regenerated from frozen analysis inputs and
  supplied as separate vector PDF exports (`Figure_1.pdf`--`Figure_4.pdf`)
  plus review PNGs. The graphical abstract is supplied separately as
  vector PDF/PNG at the Guide's proportional 1328 x 531 geometry and contains
  no source-page crop. The artwork is programmatic repository output, not
  generative-AI artwork and not a primary observed-data image. Final portal
  readability and rights confirmation remain author checks.

### References and citations

- Use a consistent author-date citation style; citations and reference-list
  entries must match one another.
- Include all author names, full (not abbreviated) journal titles, title, year,
  volume/chapter, article number or pages as applicable; DOI links are strongly
  encouraged.
- Arrange references alphabetically and then chronologically; distinguish
  same-author same-year items with `a`, `b`, `c`.
- Web references need the full URL and access date. Preprints must be labelled
  as preprints and include the DOI. Data references follow the data rules above.
- The CAGEO template uses `natbib` author-year citations and
  `cas-model2-names.bst` for the final bibliography.

Current Paper 4 status: **LaTeX conversion and bibliography audit passed**.
The final build renders 33 author-date entries with full author lists and full
journal titles; the Amini metadata is `Amini, A.` (Afshin), and the Borkovich
entry is not truncated with `et al.`. No undefined citations or duplicate
References heading was found. The published data and historical software
records are cited with their actual resource types; the journal article DOI is
intentionally absent until the publisher assigns it.

### Other verified points

- A graphical abstract is encouraged but not mandatory. If supplied, it is a
  separate file and must meet the Guide's dimensions/readability and rights
  rules.
- The journal follows single-anonymized peer review.
- Equations must remain editable text and receive punctuation when they end a
  sentence. The CAGEO template documents a PDF or Word 2003 fallback for
  equation conversion problems in Editorial Manager.
- The CAGEO template README checklist explicitly includes a cover letter,
  highlights, authorship statement, single-column/double-spacing, author-date
  references, and code availability.

## Baseline safety and scientific gates

Repository clone and safety check:

- branch: `agent/publication-evidence-bundle`
- initial `git status`: clean; no uncommitted user changes
- Paper I, II, and III scientific source files were not modified
- source-of-truth files retained: `manuscript.md`, `supplement.md`,
  `main_tables.md`, figure manifest, claim/evidence map and audits

Commands run on the clean baseline:

```text
python papers/paper4/verify_claims.py                 PASS
python papers/paper4/audit_claim_evidence.py         PASS
python scripts/audit_paper4_submission.py            PASS
python -m pytest -q                                PASS (480 passed, 10 skipped)
```

The passing gates verified the frozen headline values, including California
Qwen F1 0.896-0.932, Swissgeol F1 0.577, held-out selective precision 0.993 at
0.244 coverage, 4/100 complete-document auto-acceptance, 82 accepted actions
in 19 documents, the zero-utility BGS external abstention, full-support risk
discrepancy 0.0821 with hull ratio 0.636, matched-support reversal (risk and
reread 0.0754 versus raw 0.0326), and the partially reconstructable runtime.
No negative result or limitation was removed or improved.

## Current status summary

### Satisfied or substantively satisfied

- Scientific content/evidence gate is green
  (`SUBMISSION_READY_CANDIDATE`); the repository package is fixed.
- Article type can be classified as Original research article.
- Abstract length and standalone structure are within the Guide's 300-word
  limit; no structured-abstract format is required by the Guide.
- Keyword count is 6 (within 1-6).
- Four highlights are present (required count 3-5); their lengths are 68, 83,
  72, and 82 characters.
- The manuscript contains code-availability, data-availability, and
  declaration sections in the scientific source.
- Four main figures are cited in order, have manifest entries, and have vector
  PDF exports; main tables are editable LaTeX tabular text in the final source.
- The CAGEO template provides a single-column class, line numbering,
  double-spacing, CRediT hooks, highlights, author-year bibliography, and a
  cover-letter environment.

### Not satisfied or still pending

- A new Zenodo software version for v1.0.8 may be created after the GitHub
  release; the published v1.0.6 software DOI must not be relabelled as v1.0.8
  or as a journal-article DOI.
- Elsevier declarations-tool competing-interest `.docx` upload and any
  portal-specific cover-letter file must be produced in Editorial Manager.
- The final Editorial Manager word count and artwork preview remain portal
  checks; the source estimate is 5,507 main-text words and 5,809 body words,
  with the latter used by the repository gate against the 6,050 working limit.

## Information still required from the author

1. If desired, create and publish a new Zenodo software version for v1.0.8;
   retain the published software and data DOIs as historical identifiers.
2. Complete Elsevier's declarations-tool `.docx` upload and confirm the final
   cover-letter text in Editorial Manager.
3. Run the final Editorial Manager word-count and artwork preview checks.

## Planned submission-workspace files

The following files are now present in the review/submission workspace; the
portal-specific declarations and archival DOI remain external author actions.

### Upload files

- `manuscript.tex` - editable CAGEO single-column source with line numbers,
  double spacing, title page, CRediT, declarations, author-date citations,
  editable tables, and figure captions.
- `manuscript_review_v2.pdf` - internal review proof with review footer.
- `manuscript_final.pdf` and `manuscript_final.md` - final metadata-populated
  PDF/Markdown pair with matching scientific content and no review footer.
- `highlights.docx` (or another accepted editable format) - 3-5 bullets,
  each <=85 characters.
- `cover_letter.docx` or editable CAGEO cover-letter source/PDF - author-
  approved cover letter using the points in `cover_letter_points.md`.
- `declaration_competing_interests.docx` - output of Elsevier's declarations
  tool, completed by the authors.
- `submission_bundle/Paper4_Supplementary_Methods.md` and
  `Paper4_Supplementary_Figure_Captions.md` - normalized supplementary source
  and captions, with S1-S3 artwork and hashes in `Paper4_Upload_Manifest.json`.
- `figures/Figure_1.pdf` through `figures/Figure_4.pdf` - main figures,
  preferably vector exports; supplementary `Figure_S1` through `Figure_S3`
  when retained after the caption/citation audit.

### Build and audit support

- `references.bib` - final author-date bibliography derived from
  `papers/references.bib` and checked against rendered citations.
- `CAGEO_SUBMISSION_CHECKLIST.md` - final file-by-file upload checklist.
- `CAGEO_BUILD.md` - reproducible build instructions and required toolchain.
- `CAGEO_ARTIFACT_MANIFEST.json` - final filenames, SHA-256 hashes, source
  links, figure provenance, rights status, and local Git commit anchor.
- `AUTHOR_INPUT_REQUIRED.md` - a fill-in worksheet for the author information
  listed above; it is not a scientific source and is not uploaded unless
  requested.

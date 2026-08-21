# Paper 4 manuscript-facing upload bundle

This directory contains the fixed files for individual upload to a
Computers & Geosciences submission portal. Author metadata, declarations, and
rights/linkage sign-off are complete. `Paper4_Supplementary_Figure_Captions.md`
is the standalone caption file for Supplementary Figures S1–S3 and
Supplementary Tables S1–S4; the detailed supplementary methods are in
`Paper4_Supplementary_Methods.md`.

The final manuscript pair is `Paper4_Final_Manuscript.md` and
`Paper4_Final_Manuscript.pdf`; the Markdown and PDF carry the same audited
scientific content, declarations, metrics, limitations, and references. The
editable main-manuscript upload is
`Paper4_CAGEO_LaTeX_Source_v1.0.8.zip`; it contains the final TeX, BibTeX,
C&G class/style files, four canonical vector figures, and an internal source
manifest. The
artwork files are the four main figures, the graphical abstract, and three
supplementary figures in paired PDF/PNG form. Each main PNG is rendered from
the same canonical PDF page used in the final manuscript; each supplementary
PNG is rendered at 600 DPI from its matching vector PDF. The other
Markdown files are repository-native supplementary/reproducibility sources;
`Paper4_Highlights.txt` is the separate editable highlights upload required by
the journal;
convert them to the journal's required manuscript format at submission time
without changing audited text or numbers. `Paper4_Upload_Manifest.json`
records source paths and SHA-256 hashes for every file.

The manuscript-facing bundle does not duplicate the large source/data archive
or include model weights or private credentials. The author-reviewed selected
source files and structured datasets are published separately as `data-v002`.
The complete result-reproduction workflow is documented in
`Paper4_Reproduce.md` and the repository-level `publication_evidence/` bundle.
The corrected Paper 4 release is `paper4-cageo-v1.0.8`. The published
Zenodo software archive is `paper4-cageo-v1.0.6` at
`https://doi.org/10.5281/zenodo.22030229`; that is a software DOI, not a
journal-article DOI. The published `data-v002` companion is at
`https://doi.org/10.5281/zenodo.22031703` and is reused without changing its
contents. A future Zenodo v1.0.8 archive must be created as a new version.

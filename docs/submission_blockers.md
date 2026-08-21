# Shared pre-submission blockers and release gates

This is the repository-wide gate for Papers 1--3 and for quarantined or
out-of-scope source material. The exact Paper 4 `paper4-cageo-v1.0.9` package
and exact `data-v002` selection have an item-scoped author review and sign-off;
that sign-off does not grant a blanket licence or constitute an independent
legal opinion. The published Zenodo software DOI
`10.5281/zenodo.22043933` identifies `paper4-cageo-v1.0.9`, not a journal
article. The published `data-v002` companion is
`10.5281/zenodo.22031703`.

## Required for Papers 1--3 or additional public releases

1. Verify item-level licence, attribution, redistribution, and embedded-content
   terms for the California WCR/USGS reference material outside the named
   `data-v002` scope. Metrics may be retained internally, but additional source
   PDFs or derived pages must not be uploaded until their exact release scope is
   confirmed.
2. Verify the BGS scan-footer/OGL scope conflict for v001--v003, including
   offshore coordinate sensitivity and derived-page rights. BGS v003 has been
   consumed once as a frozen external evaluation and must not be rerun.
3. Verify Swissgeol Thurgau PDF/database pairing, citation, source terms, and
   whether any page crop or derived spatial asset may be redistributed.
4. Verify USGS Idaho, Raft River, Padova, Mendeley, and other auxiliary source
   terms against the exact downloaded item versions. Quarantined Chinese/DWG
   candidates remain excluded from benchmark claims.
5. Complete a human author pass over every abstract, table, figure caption,
   numerical value, DOI, and licence statement for each paper. No automated
   compliance record is a substitute for that review.

## Paper 4 external steps

- Upload the v1.0.9 package to the Computers & Geosciences portal and
  complete its final format, artwork, and metadata checks.
- Upload the prepared v1.0.9 source archive to the reserved Zenodo record
  `10.5281/zenodo.22043933` and complete the author-controlled Publish action.
  This DOI is a software DOI, not an article DOI.
- Obtain the journal article DOI from the publisher; neither current Zenodo DOI
  is an article DOI.

## Not blockers for the closed scientific claims

- No additional OCR/VLM model or Qwen3.8/NVFP4 training run is required.
- No second BGS v003 evaluation is permitted.
- Human-efficiency timing, page-derived collar extraction, and production GemPy
  integration remain outside the quantitative claims.

Until the external steps above are complete, use
`SUBMISSION_READY_CANDIDATE` for Paper 4 and keep the repository-wide
`all_submission_ready=false` flag because Papers 1--3 remain gated.

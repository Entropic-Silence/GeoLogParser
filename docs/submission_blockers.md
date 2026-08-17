# Pre-submission blockers and release gates

The three manuscripts are scientifically closed candidates, but they are not
authorised for immediate public upload until the following external checks are
completed. These are source, licence, privacy, and author-review gates rather
than missing experiments.

## Required before submission or public data release

1. Verify item-level licence, attribution, redistribution, and embedded-content
   terms for the California WCR/USGS reference material. The metrics may be
   retained internally, but source PDFs or derived pages must not be uploaded
   until the exact release scope is confirmed.
2. Verify the BGS scan-footer/OGL scope conflict for v001--v003, including
   offshore coordinate sensitivity and derived-page rights. BGS v003 has been
   consumed once as a frozen external evaluation and must not be rerun.
3. Verify Swissgeol Thurgau PDF/database pairing, citation, source terms, and
   whether any page crop or derived spatial asset may be redistributed.
4. Verify USGS Idaho, Raft River, Padova, Mendeley, and other auxiliary source
   terms against the exact downloaded item versions. Quarantined Chinese/DWG
   candidates remain excluded from benchmark claims.
5. Complete a human author pass over every abstract, table, figure caption,
   numerical value, DOI, and licence statement. This is the final scientific
   sign-off; no automated compliance record is a substitute for it.

## Not blockers for the current manuscripts

- No additional OCR/VLM model is required for the stated claims.
- No Qwen3.8/NVFP4 training run is required or permitted by the closure plan.
- No second BGS v003 evaluation is permitted.
- Human-efficiency timing, page-derived collar extraction, and production GemPy
  integration are explicitly outside the quantitative claims of the closed
  manuscripts.

Until the required checks are signed, use the status
`SUBMISSION_READY_CANDIDATE`, not `SUBMISSION_READY` in an external report.


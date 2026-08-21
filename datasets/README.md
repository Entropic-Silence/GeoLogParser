# Dataset handling

The repository includes formal manifests, record-disjoint splits, hashes,
evidence tiers, and the source/licence ledger needed to audit every reported
cohort. Lightweight cards for locally acquired public sources are under
`datasets/public`. The exact source/data selection in `data-v002` passed the
sole author's item-level redistribution, attribution, linkage, privacy,
sensitive-location, and embedded-content review. That sign-off is release
scoped; all other original PDFs and page images remain excluded unless their
own record carries an explicit public-release sign-off.

`data_registry.yaml` records candidates and verified access/licensing facts.
Listing a source is not permission to download or redistribute it. Public
release requires `public_release_signoff.status=verified_for_public_release`
for the named release scope.

Large content belongs under `/data/GeoLogParser/datasets`. Repository folders
contain only manifests, schemas, small legal metadata, and redistribution-safe
examples. Before ingestion, record access date, exact terms URL, permitted use,
redistribution, citation, checksums, and any privacy/anonymization requirement.

Reproducible metadata discovery is configured in
`configs/datasets/open_metadata_survey_*.yaml` and run with
`scripts/survey_open_metadata.py`. Survey artifacts belong under
`/data/GeoLogParser/artifacts/source_surveys/`; the runner refuses to overwrite
an existing output. Verify a frozen run with
`scripts/verify_open_metadata_survey.py`.

A metadata search hit is never an acquired dataset count. An open licence plus
a PDF/JPG/PNG file inventory only creates a content-review candidate; privacy,
embedded rights, format fitness, human annotation, and Benchmark eligibility
remain separate gates.

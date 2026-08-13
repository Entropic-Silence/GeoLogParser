# Dataset handling

`data_registry.yaml` records candidates and verified access/licensing facts.
Listing a source is not permission to download or redistribute it.

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

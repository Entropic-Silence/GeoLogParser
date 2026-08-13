# Dataset manifests

Manifest units are explicit per schema: acquisition manifests use one row per
source file, while `page_content_manifest_v001` uses one row per PDF page or
standalone image. Rows bind source/acquisition hashes, rights state, provisional
content class, phase-1 scope, annotation state, and eligibility blockers.

Multiple public-source, annotation, degradation, CAD, and structured-data
manifests now exist under `/data/GeoLogParser`. A rights-cleared, human-verified
Chinese Benchmark manifest and its leakage-resistant split assignments remain
`NOT COMPLETED`.

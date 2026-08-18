# Public dataset metadata

This directory publishes lightweight dataset cards only. Formal interval
manifests, split IDs, hashes, evidence tiers, and licence-review status are
versioned in `datasets/manifests`, `datasets/splits`,
`datasets/data_registry.yaml`, and `datasets/source_verification_ledger.yaml`.

The formal source files needed for the main paper experiments are published in
the GitHub Release `data-v001` as
`GeoLogParser-public-data-v001.tar.zst`. The release archive preserves
repository-relative paths and is accompanied by a per-file SHA-256 manifest in
`datasets/public/dataset_bundle_v001/manifest.json`.

The release is a project-owner-authorized public research bundle. It keeps
source-specific attribution and any remaining final-author rights checks
explicit: California uses the published CC0 table/report pairing, BGS retains
the OGL acknowledgement and scan-footer caveat, and Swissgeol remains marked
for final source-term verification. The evidence tier in each manifest is not
changed by publication.

Large intermediate renders, duplicate freezes, failed experiments, model
weights, and quarantine-only sources are intentionally not included. They are
not required to reproduce the principal paper claims.

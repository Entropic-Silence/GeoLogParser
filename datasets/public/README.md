# Public dataset records

This directory publishes lightweight dataset cards and versioned release
metadata. Formal interval manifests, split IDs, hashes, evidence tiers, and
rights-review status are versioned in `datasets/manifests`, `datasets/splits`,
`datasets/data_registry.yaml`, and `datasets/source_verification_ledger.yaml`.

The source files selected for the principal paper experiments are published as
the GitHub Release `data-v002` in
`GeoLogParser-public-data-v002.tar.zst`. The archive uses repository-relative
paths and has both a per-file manifest and a separately downloadable archive
SHA-256 file. See `dataset_bundle_v002/README.md`.

`data-v001` remains available as a historical prerelease only. It is superseded
because its embedded metadata retained absolute host paths, an inconsistent
synthetic v001/v002 identity, and pre-sign-off rights states. It should not be
used for a DOI or described as the complete Paper 4 package.

Yifan Du manually reviewed the exact `data-v002` selection for source terms,
item scope, privacy, sensitive locations, embedded third-party content,
attribution, and linkage. The source-specific obligations remain in
`dataset_bundle_v002/DATA_LICENSES.md`; the sign-off does not create a blanket
licence for other repository sources. Evidence tiers are unchanged by release.

The complete Paper 4 manuscript/code/evidence package is separately identified
by `paper4-cageo-v1.0.1`.

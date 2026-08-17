# Supplementary Material for Paper III

## S1. Software and interoperability

GeoLogParser writes SQLite, CSV, JSON, XLSX, Parquet, GeoJSON, GeoParquet, and GeoPackage outputs while retaining field provenance. Unknown or mixed CRSs are rejected rather than silently transformed. VTP and off-screen PNG adapters verify that regular surface outputs can be rendered. These are software checks, not evidence for geological interpretation or a production 3D model.

The Padova coordinate inventory contains 11 source-provided EPSG:4326 points but zero interval records; all coordinates remain needs-review. The quarantined Sanming database smoke test checks table connectivity only. Neither dataset enters the propagation estimand.

## S2. Protocol-only controlled checks

A four-borehole fixture applies the production constraint/rereading ranker before IDW. Errors of 0.01 and 0.05 m fall within the configured tolerance and cause abstention; larger controlled inconsistencies trigger rereading and are corrected when both candidate channels contain the known source value. This verifies the implemented threshold and data path, not real-site effectiveness.

The single-channel 602-record scalar protocol perturbs the source-reported roof-depth field and measures the deterministic IDW response. It does not establish extraction accuracy, the semantics of a coal-seam elevation, privacy clearance, or site geology. The main paper uses the paired-channel experiment because it directly tests support deletion versus support-preserving fusion.

## S3. Page-coordinate coverage

On 88 external Swissgeol documents, the conservative native-text parser emitted one unambiguous coordinate pair for 53 documents. Fifty-one pairs agreed with the database, while two remained unresolved page/database disagreements. The parser abstained on every collar elevation after a predecessor incorrectly accepted drill-rig numbers.

In the 35-document boundary set, page coordinates were available for 17 documents and 15 agreed with the database. Page-coordinate surface variants therefore used about half the spatial support and had substantially higher error than the authoritative-coordinate variant. Because collars remained authoritative and two coordinate disagreements were unresolved, this is a coverage diagnostic rather than a complete page-to-surface workflow.

## S4. Visualization artifacts

PyVista meshes, PNGs, Padova location plots, and structured-source proxy figures are derived visualizations. The quantitative conclusions come from the frozen JSON analyses. A plot does not upgrade a surface proxy to a validated geological model.

## S5. Monte Carlo repeatability

For the 602-record paired-channel experiment, support-preserving fusion improved over the raw channel in 26–29 of 30 repetitions at each magnitude. Two-sided exact sign-test p values range from 5.77×10⁻⁸ to 5.95×10⁻⁵. These values describe repeatability across perturbation seeds for one dataset and protocol; they are not inference over 30 independent sites.

## S6. Reanalysis boundary

The public spatial input is translated, rigidly rotated, and stripped of absolute origin and source identifiers. Grid construction and polygon area are evaluated in a local coordinate frame so results are invariant to that transform. The public recomputation regenerates the principal support, IDW, LOO, and jackknife diagnostics; this is distinct from redrawing tables from already frozen analysis JSON.

Exact experiment metrics and hashes remain in [current results](generated/current_results.md), the result index, claim registry, and publication-evidence bundle.

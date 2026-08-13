<!-- AUTO-GENERATED REVIEW BUNDLE. DO NOT EDIT. -->
> Package status: **DRAFT_NOT_SUBMISSION_READY**
> This bundle combines the versioned manuscript and generated results for review.
> Blockers: unresolved TBD/citation markers remain; no formal experiment is indexed.

# From Legacy Borehole Logs to Structured Geological Models: An Automated Extraction and Error-Propagation Workflow

## Abstract

This paper studies the downstream consequences of automatically structured legacy borehole logs. The workflow exports provenance-bearing extraction into SQLite and GeoJSON, performs quality control, correlates stratigraphic boundaries, and evaluates how controlled extraction errors propagate to geological surfaces and human review effort. A traceable database exporter, transparent IDW error-propagation baseline, and PyVista/VTP surface adapter are implemented. Synthetic four-borehole runs validate the propagation and interoperability protocols but are not real-world evidence. A separate 602-record licensed structured-source run validates origin-suppressed, multi-seed source-field perturbation mechanics; it is neither image-derived automated extraction output nor a geological reference. Spatially coherent reference records, raw-versus-validated-versus-reference comparisons, real 3D modelling, and timed human studies are `TBD`.

## 1. Introduction

Document extraction is useful only if its output supports defensible engineering workflows. A small boundary error may be negligible in one setting and distort a thin layer in another; a wrong coordinate may be catastrophic. We ask: (RQ1) how extraction-depth errors affect model surfaces; (RQ2) whether constraint QC stabilizes downstream models; (RQ3) how much human time is saved; and (RQ4) which error classes dominate downstream impact.

This contribution boundary is workflow and error propagation. It reuses extraction/data definitions with disclosure but does not repeat Paper I benchmark or Paper II method contributions.

## 2. Related Work

Shepard's irregular-data interpolation provides the provenance for the transparent inverse-distance baseline used in our controlled propagation protocol [@shepard1968interpolation]. It is intentionally not treated as a universal geological model. GemPy demonstrates an open-source route to stochastic geological modelling and inversion [@delavarga2019gempy], which motivates a later interoperable model adapter rather than making GemPy a prerequisite for document extraction. The 2024 borehole OCR/database study by Han and Suh connects document recognition to structured borehole data in an applied setting, but does not evaluate extraction-error propagation into a geological surface [@han2024boreholeocr].

Downstream uncertainty begins before interpolation. In a designed cross-section experiment, Lark et al. compared geologists' interpreted contact elevations with withheld boreholes and quantified modeller/site variation, showing why interpretation uncertainty must be separated from document-extraction error [@lark2014crosssection]. Pakyuz-Charrier et al. explicitly propagated drillhole path and log uncertainty through alternative 3D model realizations with Monte Carlo perturbations [@pakyuzcharrier2018drillhole]. Paper III isolates an earlier error source—automated structuring of legacy logs—and holds the downstream correlation/interpolation configuration fixed when comparing raw automated extraction, constraint-validated extraction, and reference records. Interactive-machine-learning literature further argues that users and learning systems must be studied together [@amershi2014interactive]; it motivates a timed, event-logged human study here but supplies no transferable GeoLogParser time-saving estimate.

## 3. Workflow

Legacy PDF/JPG/PNG enters GeoLogParser and produces validated records with provenance. SQLite separates boreholes, intervals, and field provenance. GeoJSON exports coordinates without implicit CRS transformation. CSV, JSON, XLSX, and Parquet are supported with separate borehole, interval, and provenance tables. GeoParquet and GeoPackage point exports carry an explicit EPSG CRS for QGIS-compatible consumption and reject unknown or mixed CRSs rather than combining them. A Padova source-coordinate snapshot now exports 11 EPSG:4326 points to SQLite/GeoJSON/GeoParquet/GeoPackage, but all coordinate fields remain `needs_review`, the snapshot contains zero intervals, and it is not a geological model. <!-- evidence:p3.padova_spatial_catalog --> A separate gate requires at least three eligible points and human-verified collar elevations/target boundaries before surface modelling. A neutral regular-surface adapter now exports IDW surfaces to PyVista VTP and off-screen PNG; it was exercised only on the synthetic four-borehole fixture and therefore establishes interoperability, not geological validity. GemPy integration remains `TBD`.

Human review is triggered by missing MVP fields, low confidence, field warnings, unknown terminology, and constraint violations. Start/completion events record real duration and corrected-field count. No human timing result exists yet.

## 4. Error-Propagation Method

For a selected correlated boundary, depth is converted to elevation as collar elevation minus depth. A transparent IDW baseline interpolates the surface. Controlled perturbations of 0.01, 0.05, 0.10, 0.50, and 1.00 m are applied with recorded seeds; shared interval boundaries remain continuous and thickness is recomputed. Surface MAE, RMSE, and maximum absolute error are evaluated on a fixed grid. Formal experiments require multiple seeds and confidence intervals.

Protocol development additionally uses a CC BY 4.0 workbook containing 602 complete, unique directional gas-drainage borehole records. Its audit records numeric local X/Y/Z and roof-depth fields, but no CRS, and flags precise-location review as pending. <!-- evidence:p3.coal602_source_audit --> The source Y/X values are translated independently to zero-origin local `u/v`; the translation origin and source identifiers are not persisted. Source-reported No. 3 coal-roof depth is interpolated only as a scalar surface proxy on a 41 by 41 grid clipped to the collar-coordinate convex hull. It is not converted to elevation or named a coal-seam surface because trajectory and field-reference semantics are not established by the released files.

The main comparison will be raw automated extraction versus constraint-validated extraction versus reference records using identical correlation/interpolation settings. Error types will also be injected separately: depth, missing interval, wrong lithology correlation, coordinate, and elevation. Exact site, grid, model, and repetitions are `TBD`.

## 5. Database and Interoperability

The database preserves source hash, raw/normalized values, page/bbox/text, method, confidence, validation, warnings, and units. Upserts replace a document's interval projection transactionally. GeoJSON skips missing coordinates and reports encountered CRS labels; it never guesses or transforms an unknown CRS. GeoParquet writes WKB point geometry only when all located records share one explicit `EPSG:<code>` identifier. A quarantine-only internal run built four auto boreholes, 12 intervals, and 224 provenance rows; because data are not human-validated or release-cleared, this is connectivity evidence only. <!-- evidence:p3.sanming_database_connectivity -->

## 6. Results

See [generated/current_results.md](generated/current_results.md). A 30-seed synthetic extension exercises mean/std and explicitly named normal-approximation confidence intervals for perturbations 0.01–1.00 m. At 1.00 m, synthetic surface MAE was 0.662470 ± 0.110565 m across seeds. <!-- evidence:p3.idw_multiseed --> A separate indexed PyVista interoperability run wrote 121 points and 200 triangle cells, with VTP and PNG hashes reported in the generated table. <!-- evidence:p3.pyvista_interop --> These four-artificial-borehole artifacts are neither a real geological sensitivity estimate nor a real 3D model.

The 602-record structured-source protocol used 30 seeds per magnitude and 80 convex-hull grid points. Under independent signed 1.00 m perturbations of the source-reported roof-depth scalar, proxy-surface MAE was 0.260428 ± 0.018737 m; the output persisted neither absolute coordinate origin nor source identifiers. <!-- evidence:p3.coal602_source_proxy --> This is a deterministic response of one source-field/IDW protocol, not extraction accuracy, a constraint-QC effect, Ground Truth agreement, a true coal-seam surface, or a privacy clearance. Real-site sensitivity from image-derived records, raw/QC/GT comparison, real 3D figures, human time, and confirmatory statistical analysis remain `TBD`.

The [Padova source-location plot](generated/figures/padova_locations.png) shows
three separated site groups and therefore rules out interpolation across the
whole collection as one local surface. Coordinates remain source-provided and
unverified. The [synthetic propagation curve](generated/figures/synthetic_error_propagation.png)
is explicitly protocol-only and must not be interpreted as real-site response.
The [structured-source proxy curve](generated/figures/coal602_source_proxy.png)
is kept separate from the synthetic curve and carries the same non-formal
interpretation limits described above.

## 7. Human-in-the-Loop Evaluation

Planned measures are manual-entry time, automated extraction time, extraction-plus-correction time, auto-accept rate, review rate, post-review error, and fields corrected/minute. Sessions must use anonymized annotator IDs, fixed instructions, counterbalanced task order where feasible, and real event timestamps. Sample size and analysis are `TBD`.

## 8. Discussion and Threats to Validity

The synthetic smoke shows that the code responds to controlled perturbations, not that real geology has the same response. The structured-source run improves scale and spatial-pattern realism for protocol development but still lacks image-derived predictions, human GT, CRS confirmation, trajectory reconstruction, and field-reference verification. IDW is a transparent baseline rather than a universal geological model. Correlation errors, anisotropy, structural geology, spatial sampling, and model choice may dominate boundary noise. Rights-cleared spatial coherence remains a major data risk.

## 9. Reproducibility and Ethics

Database and surface artifacts will be linked to extraction experiment IDs and hashes. Spatially sensitive project information will be anonymized or withheld. Automated output is not an engineering sign-off; provenance and review status travel into downstream exports.

## 10. Conclusion

We define and partially implement a traceable path from legacy logs to geological surfaces and human review measurements. The central claim—whether constraint QC improves real downstream stability and efficiency—remains `TBD` until the full real-data study is complete.

The repository's auto-generated [publication-readiness audit](../../docs/generated/publication_readiness.md)
currently reports zero formal Paper III runs; the synthetic runs, structured-source
proxy run, and PyVista interoperability run are protocol-only and cannot satisfy the real
downstream completion gate.

## References

Shared bibliography: [../references.bib](../references.bib). Citation metadata and permitted claim scope are logged in [../../docs/literature_evidence.yaml](../../docs/literature_evidence.yaml).

# Appendix: Machine-Generated Current Results

<!-- AUTO-GENERATED. DO NOT EDIT. -->
### Synthetic error-propagation protocol

| Experiment | Perturbation (m) | Seed | Repetitions/grid points | Surface MAE (m) | RMSE (m) | Max abs. error (m) | Eligibility |
|---|---:|---:|---:|---:|---:|---:|---|
| P3_SYNTHETIC_ERROR_PROPAGATION_SMOKE_001 | 0.01 | 20260812 | 36 | 0.006136 | 0.006702 | 0.010000 | protocol_only |
| P3_SYNTHETIC_ERROR_PROPAGATION_SMOKE_001 | 0.05 | 20260813 | 36 | 0.024720 | 0.029174 | 0.050000 | protocol_only |
| P3_SYNTHETIC_ERROR_PROPAGATION_SMOKE_001 | 0.10 | 20260814 | 36 | 0.061361 | 0.067018 | 0.100000 | protocol_only |
| P3_SYNTHETIC_ERROR_PROPAGATION_SMOKE_001 | 0.50 | 20260815 | 36 | 0.306805 | 0.335092 | 0.500000 | protocol_only |
| P3_SYNTHETIC_ERROR_PROPAGATION_SMOKE_001 | 1.00 | 20260816 | 36 | 1.000000 | 1.000000 | 1.000000 | protocol_only |
| P3_SYNTHETIC_ERROR_PROPAGATION_MULTISEED_001 | 0.01 | multiple | 30 | 0.006780 ± 0.001256 | 0.007309 ± 0.001056 | 0.010000 ± 0.000000 | protocol_only |
| P3_SYNTHETIC_ERROR_PROPAGATION_MULTISEED_001 | 0.05 | multiple | 30 | 0.035460 ± 0.007308 | 0.037903 ± 0.006103 | 0.050000 ± 0.000000 | protocol_only |
| P3_SYNTHETIC_ERROR_PROPAGATION_MULTISEED_001 | 0.10 | multiple | 30 | 0.070823 ± 0.012221 | 0.075573 ± 0.010385 | 0.100000 ± 0.000000 | protocol_only |
| P3_SYNTHETIC_ERROR_PROPAGATION_MULTISEED_001 | 0.50 | multiple | 30 | 0.359916 ± 0.067800 | 0.383214 ± 0.056993 | 0.500000 ± 0.000000 | protocol_only |
| P3_SYNTHETIC_ERROR_PROPAGATION_MULTISEED_001 | 1.00 | multiple | 30 | 0.662470 ± 0.110565 | 0.717275 ± 0.093319 | 1.000000 ± 0.000000 | protocol_only |

These rows are synthetic protocol results only; they are not evidence of real geological-model sensitivity. Multi-seed rows show mean ± sample standard deviation across seeds.

### Licensed structured-source field proxy protocol

| Experiment | Perturbation (m) | Seed | Repetitions/grid points | Proxy-surface MAE (m) | RMSE (m) | Max abs. error (m) | Eligibility |
|---|---:|---:|---:|---:|---:|---:|---|
| P3_COAL602_SOURCE_ROOF_PROXY_PROTOCOL_001 | 0.01 | multiple | 30 | 0.002636 ± 0.000244 | 0.003600 ± 0.000234 | 0.009927 ± 0.000038 | protocol_only |
| P3_COAL602_SOURCE_ROOF_PROXY_PROTOCOL_001 | 0.05 | multiple | 30 | 0.012762 ± 0.000883 | 0.017592 ± 0.000913 | 0.049641 ± 0.000187 | protocol_only |
| P3_COAL602_SOURCE_ROOF_PROXY_PROTOCOL_001 | 0.10 | multiple | 30 | 0.025873 ± 0.001824 | 0.035878 ± 0.001331 | 0.099203 ± 0.000258 | protocol_only |
| P3_COAL602_SOURCE_ROOF_PROXY_PROTOCOL_001 | 0.50 | multiple | 30 | 0.131606 ± 0.013952 | 0.181193 ± 0.012088 | 0.496435 ± 0.001052 | protocol_only |
| P3_COAL602_SOURCE_ROOF_PROXY_PROTOCOL_001 | 1.00 | multiple | 30 | 0.260428 ± 0.018737 | 0.361223 ± 0.020639 | 0.992077 ± 0.003371 | protocol_only |

These rows use source-reported tabular values with origin-suppressed local coordinates. They are protocol-development evidence only, not image-derived automated extraction, a geological reference, constraint-QC, a true geological surface, absolute-location evidence, or formal downstream evidence. Multi-seed rows show mean ± sample standard deviation across seeds.

### Synthetic 3D interoperability protocol

| Experiment | Points | Triangle cells | Bounds (x0, x1, y0, y1, z0, z1) | VTP SHA256 | PNG SHA256 | Eligibility |
|---|---:|---:|---|---|---|---|
| P3_SYNTHETIC_PYVISTA_INTEROP_001 | 121 | 200 | 0.000, 10.000, 0.000, 10.000, 96.800, 100.800 | 283830930242804c7fa378972153c93a0da317c10a099739b8e13604fa62478b | ade2507596b32db5ab15e9898c8007b948f9536d68ce226eea640c6b249c98b5 | protocol_only |

Interoperability rows establish reproducible artifact generation only; they do not establish geological validity or real-site performance.

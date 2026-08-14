<!-- AUTO-GENERATED REVIEW BUNDLE. DO NOT EDIT. -->
> Package status: **DRAFT_NOT_SUBMISSION_READY**
> This bundle combines the versioned manuscript and generated results for review.
> Blockers: manuscript evidence tags are absent from claim registry; unresolved TBD/citation markers remain.

# From Legacy Borehole Logs to Structured Geological Models: An Automated Extraction and Error-Propagation Workflow

## Abstract

This paper studies the downstream consequences of automatically structured legacy borehole logs. The workflow exports provenance-bearing extraction into SQLite and GeoJSON, performs quality control, correlates stratigraphic boundaries, and evaluates how controlled extraction errors propagate to geological surfaces and human review effort. A traceable database exporter, transparent IDW error-propagation baseline, and PyVista/VTP surface adapter are implemented. On 602 real structured-source records, a controlled dual-channel experiment found that strict consensus deletion retained approximately 81.5% of points but increased surface MAE to approximately 0.73–0.74 m. In contrast, support-preserving mean fusion reduced MAE by 18.3%–22.0% relative to a single channel across 0.01–1.00 m injections; paired exact sign-test p values were all below `6×10⁻⁵`. In a separate 35-document held-out image-boundary diagnostic, rereading reduced first-boundary depth MAE from 1.471 m to 0.941 m and reference-surface MAE from 3.402 m to 3.050 m. Thus downstream QC must account for spatial support, not only field acceptance. Complete image-derived spatial metadata extraction, real stratigraphic modelling, and timed human studies remain `TBD`.

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

The first real structured-source comparison injects independent signed errors into two channels at a 10% per-channel rate. It compares the raw first channel, exact-consensus deletion, and a support-preserving mean of both channels against the unchanged source-reference surface. All three policies are reference-blinded; source values are used only for post-decision scoring. A complementary image-boundary diagnostic reuses the frozen held-out Paper II predictions and adds only authoritative coordinates and collar elevations after extraction decisions are frozen. Other error types—missing interval, wrong lithology correlation, coordinate, and elevation extraction—remain `TBD`.

## 5. Database and Interoperability

The database preserves source hash, raw/normalized values, page/bbox/text, method, confidence, validation, warnings, and units. Upserts replace a document's interval projection transactionally. GeoJSON skips missing coordinates and reports encountered CRS labels; it never guesses or transforms an unknown CRS. GeoParquet writes WKB point geometry only when all located records share one explicit `EPSG:<code>` identifier. A quarantine-only internal run built four auto boreholes, 12 intervals, and 224 provenance rows; because data are not human-validated or release-cleared, this is connectivity evidence only. <!-- evidence:p3.sanming_database_connectivity -->

## 6. Results

A controlled experiment on all 602 structured-source records used 30 paired-channel repetitions at each 0.01, 0.05, 0.10, 0.50, and 1.00 m error magnitude. Mean retained point coverage after exact consensus was 0.813–0.817. Raw surface MAE rose from 0.000575 ± 0.000147 m at 0.01 m injection to 0.054885 ± 0.010986 m at 1.00 m. Consensus-deletion MAE remained approximately 0.729–0.743 m because deleting disagreeing records changed interpolation support; 73–93 same-error acceptances also occurred across 30 repetitions per condition. Support-preserving mean fusion instead reduced MAE by 18.3%–22.0% relative to raw, improved 26–29 of 30 paired repetitions per magnitude, and had two-sided exact sign-test p values from `5.77×10⁻⁸` to `5.95×10⁻⁵`. The experiment therefore distinguishes unsafe downstream deletion from beneficial support-preserving multi-reader fusion. <!-- evidence:p3.coal602_consensus_qc -->

An executed controlled comparison now applies the production constraint/rereading ranker before the same IDW surface model. Across 30 seeds and four boreholes, raw surface MAE increased from 0.006741 m at a 0.01 m injected boundary error to 0.665164 m at 1.00 m. At 0.01 and 0.05 m the configured tolerance produced 120/120 abstentions per condition, so constrained and raw surfaces were identical. At 0.10, 0.50, and 1.00 m the violated thickness/final-depth relations triggered rereading; two candidate channels agreed on the known source value, all 120 boundaries per condition were accepted, and constrained surface MAE was 0 in this controlled fixture. This demonstrates the implemented threshold and propagation mechanics only; it is not a real-site effectiveness estimate. <!-- evidence:p3.executed_synthetic_comparison -->

See [generated/current_results.md](generated/current_results.md). A 30-seed synthetic extension exercises mean/std and explicitly named normal-approximation confidence intervals for perturbations 0.01–1.00 m. At 1.00 m, synthetic surface MAE was 0.662470 ± 0.110565 m across seeds. <!-- evidence:p3.idw_multiseed --> A separate indexed PyVista interoperability run wrote 121 points and 200 triangle cells, with VTP and PNG hashes reported in the generated table. <!-- evidence:p3.pyvista_interop --> These four-artificial-borehole artifacts are neither a real geological sensitivity estimate nor a real 3D model.

The separate single-channel 602-record source protocol used 30 seeds per magnitude and 80 convex-hull grid points. Under independent signed 1.00 m perturbations of the source-reported roof-depth scalar at every point, proxy-surface MAE was 0.260428 ± 0.018737 m; the output persisted neither absolute coordinate origin nor source identifiers. <!-- evidence:p3.coal602_source_proxy --> This is a deterministic response of one source-field/IDW protocol, not extraction accuracy, a true coal-seam surface, or a privacy clearance. The image-boundary diagnostic is reported in [generated/current_results.md](generated/current_results.md): on 35 held-out documents and 423 fixed convex-hull queries, raw versus reread surface MAE was 3.402 versus 3.050 m, with four accepted rereads and five review decisions. <!-- evidence:p3.image_boundary_surface -->

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

The synthetic smoke shows that the code responds to controlled perturbations, not that real geology has the same response. The structured-source comparison improves scale and spatial-pattern realism and directly demonstrates that field-level abstention can degrade a surface when deletion changes support geometry. The image-boundary diagnostic provides real extraction-to-surface evidence, but it uses authoritative coordinates and collar elevations, covers one canton/source family, and evaluates only the first interval boundary. It still lacks image-derived spatial metadata, human GT, CRS confirmation beyond the source label, trajectory reconstruction, real stratigraphic modelling, and field-reference verification. IDW is a transparent baseline rather than a universal geological model. Correlation errors, anisotropy, structural geology, spatial sampling, and model choice may dominate boundary noise. Rights-cleared spatial coherence remains a major data risk.

## 9. Reproducibility and Ethics

Database and surface artifacts will be linked to extraction experiment IDs and hashes. Spatially sensitive project information will be anonymized or withheld. Automated output is not an engineering sign-off; provenance and review status travel into downstream exports.

## 10. Conclusion

We define and partially implement a traceable path from legacy logs to geological surfaces and human review measurements. On a 602-record real structured source, strict dual-reader deletion worsened the interpolated surface because the loss of spatial support outweighed the small injected errors, whereas support-preserving mean fusion consistently improved it. On a separate 35-document held-out image-boundary diagnostic, reference-blinded rereading reduced both boundary and surface error, but the use of authoritative spatial metadata and the single-boundary design limit the claim. Whether the complete workflow improves real downstream stability across spatial fields, stratigraphic correlations, and human efficiency remains `TBD`.

The repository's auto-generated [publication-readiness audit](../../docs/generated/publication_readiness.md)
tracks the real structured-source controlled comparison separately from Synthetic
and protocol-only runs. It does not substitute for an image-derived real-site
raw/QC/reference comparison.

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

### Executed Synthetic raw/constrained/reference comparison

| Experiment | Injected boundary error (m) | Raw surface MAE (m) | Constrained surface MAE (m) | Accepted corrections | Abstentions | Eligibility |
|---|---:|---:|---:|---:|---:|---|
| P3_EXECUTED_SYNTHETIC_RAW_QC_REFERENCE_001 | 0.01 | 0.006741 | 0.006741 | 0 | 120 | formal_synthetic_downstream |
| P3_EXECUTED_SYNTHETIC_RAW_QC_REFERENCE_001 | 0.05 | 0.035126 | 0.035126 | 0 | 120 | formal_synthetic_downstream |
| P3_EXECUTED_SYNTHETIC_RAW_QC_REFERENCE_001 | 0.10 | 0.069805 | 0.000000 | 120 | 0 | formal_synthetic_downstream |
| P3_EXECUTED_SYNTHETIC_RAW_QC_REFERENCE_001 | 0.50 | 0.356582 | 0.000000 | 120 | 0 | formal_synthetic_downstream |
| P3_EXECUTED_SYNTHETIC_RAW_QC_REFERENCE_001 | 1.00 | 0.665164 | 0.000000 | 120 | 0 | formal_synthetic_downstream |

This table executes the production constraint/rereading ranker and the same IDW surface for all inputs. It is controlled Synthetic algorithm evidence, not a real-site sensitivity estimate.

### Real structured-source controlled raw/QC/reference comparison

| Experiment | Injected error (m) | Raw MAE (m) | Consensus-drop MAE (m) | Mean-fusion MAE (m) | Relative reduction | Fusion better | Sign-test p | Retained coverage | False accepted | Eligibility |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P3_COAL602_CONSENSUS_QC_CONTROLLED_001 | 0.01 | 0.000575 ± 0.000147 | 0.731944 ± 0.111704 | TBD | TBD | TBD | TBD | 0.813 | 93 | failure_analysis_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_001 | 0.05 | 0.002874 ± 0.000689 | 0.729222 ± 0.166501 | TBD | TBD | TBD | TBD | 0.816 | 73 | failure_analysis_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_001 | 0.10 | 0.005539 ± 0.001343 | 0.736137 ± 0.128284 | TBD | TBD | TBD | TBD | 0.817 | 74 | failure_analysis_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_001 | 0.50 | 0.029294 ± 0.006825 | 0.743434 ± 0.135452 | TBD | TBD | TBD | TBD | 0.815 | 90 | failure_analysis_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_001 | 1.00 | 0.054885 ± 0.010986 | 0.737065 ± 0.104432 | TBD | TBD | TBD | TBD | 0.817 | 85 | failure_analysis_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_002 | 0.01 | 0.000575 ± 0.000147 | 0.731944 ± 0.111704 | 0.000453 ± 0.000093 | TBD | TBD | TBD | 0.813 | 93 | audit_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_002 | 0.05 | 0.002874 ± 0.000689 | 0.729222 ± 0.166501 | 0.002291 ± 0.000496 | TBD | TBD | TBD | 0.816 | 73 | audit_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_002 | 0.10 | 0.005539 ± 0.001343 | 0.736137 ± 0.128284 | 0.004334 ± 0.000899 | TBD | TBD | TBD | 0.817 | 74 | audit_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_002 | 0.50 | 0.029294 ± 0.006825 | 0.743434 ± 0.135452 | 0.022854 ± 0.004454 | TBD | TBD | TBD | 0.815 | 90 | audit_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_002 | 1.00 | 0.054885 ± 0.010986 | 0.737065 ± 0.104432 | 0.044844 ± 0.005753 | TBD | TBD | TBD | 0.817 | 85 | audit_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_003 | 0.01 | 0.000575 ± 0.000147 | 0.731944 ± 0.111704 | 0.000453 ± 0.000093 | 0.212 | 29/30 | 5.77e-08 | 0.813 | 93 | formal_source_controlled_downstream |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_003 | 0.05 | 0.002874 ± 0.000689 | 0.729222 ± 0.166501 | 0.002291 ± 0.000496 | 0.203 | 29/30 | 5.77e-08 | 0.816 | 73 | formal_source_controlled_downstream |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_003 | 0.10 | 0.005539 ± 0.001343 | 0.736137 ± 0.128284 | 0.004334 ± 0.000899 | 0.218 | 27/30 | 8.43e-06 | 0.817 | 74 | formal_source_controlled_downstream |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_003 | 0.50 | 0.029294 ± 0.006825 | 0.743434 ± 0.135452 | 0.022854 ± 0.004454 | 0.220 | 26/30 | 5.95e-05 | 0.815 | 90 | formal_source_controlled_downstream |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_003 | 1.00 | 0.054885 ± 0.010986 | 0.737065 ± 0.104432 | 0.044844 ± 0.005753 | 0.183 | 28/30 | 8.68e-07 | 0.817 | 85 | formal_source_controlled_downstream |

This controlled experiment uses 602 real source records and post-decision source-reference scoring. It is not image-extraction accuracy or human Ground Truth. Consensus deletion changes interpolation support and can worsen the surface; support-preserving fusion is reported separately.

### Real image-derived boundary to surface diagnostic

| Experiment | Documents | Reference points | Query points | Raw boundary MAE (m) | Reread boundary MAE (m) | Raw surface MAE (m) | Reread surface MAE (m) | Accepted rereads | Needs review | Eligibility |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P3_SWISSGEOL_TG_BOUNDARY_SURFACE_FROM_FROZEN_REREAD_002 | 35 | 35 | 423 | 1.471 | 0.941 | 3.402 | 3.050 | 4 | 5 | formal_authoritative_boundary_downstream |

This diagnostic inherits frozen reference-blinded image boundaries from the Paper II held-out run. Coordinates and collar elevations are taken from the authoritative structured record; image extraction of spatial metadata is not evaluated, so this is not a complete end-to-end spatial workflow.

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

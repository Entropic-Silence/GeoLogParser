<!-- AUTO-GENERATED REVIEW BUNDLE. DO NOT EDIT. -->
> Package status: **SUBMISSION_READY**
> This bundle combines the versioned manuscript and generated results for review.

# From Legacy Borehole Logs to Structured Geological Models: An Automated Extraction and Error-Propagation Workflow

## Abstract

This paper studies the downstream consequences of automatically structured legacy borehole logs. The workflow exports provenance-bearing extraction into SQLite and GeoJSON, performs quality control, correlates stratigraphic boundaries, and evaluates controlled errors on geological surfaces and layer volumes. A traceable database exporter, transparent IDW error-propagation baseline, and PyVista/VTP surface adapter are implemented. On 602 real structured-source records, strict consensus deletion retained approximately 81.5% of points but increased surface MAE to approximately 0.73–0.74 m, whereas support-preserving mean fusion reduced MAE by 18.3%–22.0% relative to a single channel. On 35 held-out authoritative records, 540 seeded injections across six error classes separated numeric, coordinate, support, and topology failures. An external 88-document spatial-field evaluation extracted unambiguous page coordinates for 53 documents; 51 agreed exactly with the database, while no explicit collar elevation was safely extracted. In a real three-layer downstream diagnostic on 35 held-out documents, raw, constraint-reread, and risk-aware variants had relative absolute volume errors of 0.1389, 0.1216, and 0.0824, respectively; the risk-aware route reduced mean layer-thickness MAE from 45.952 m to 34.808 m and eliminated negative-thickness layers, while retaining only 15/35 documents. This is a quantified reliability–coverage result, not a claim of validated geological interpretation. Human time savings and page-derived collar accuracy are not evaluated.

## 1. Introduction

A four-boundary extension reduced aggregate positional MAE from 11.171 m to 2.789 m but surface MAE only from 21.397 m to 20.615 m, revealing that missing spatial support can dominate otherwise correct available boundaries.

Document extraction is useful only if its output supports defensible engineering workflows. A small boundary error may be negligible in one setting and distort a thin layer in another; a wrong coordinate may be catastrophic. We ask: (RQ1) how extraction-depth errors affect model surfaces; (RQ2) whether constraint QC stabilizes downstream models; (RQ3) how risk-aware abstention changes reliability and spatial support; and (RQ4) which error classes dominate downstream impact.

This contribution boundary is workflow and error propagation. It reuses extraction/data definitions with disclosure but does not repeat Paper I benchmark or Paper II method contributions.

## 2. Related Work

Shepard's irregular-data interpolation provides the provenance for the transparent inverse-distance baseline used in our controlled propagation protocol [@shepard1968interpolation]. It is intentionally not treated as a universal geological model. GemPy demonstrates an open-source route to stochastic geological modelling and inversion [@delavarga2019gempy], which motivates a later interoperable model adapter rather than making GemPy a prerequisite for document extraction. The 2024 borehole OCR/database study by Han and Suh connects document recognition to structured borehole data in an applied setting, but does not evaluate extraction-error propagation into a geological surface [@han2024boreholeocr].

Downstream uncertainty begins before interpolation. In a designed cross-section experiment, Lark et al. compared geologists' interpreted contact elevations with withheld boreholes and quantified modeller/site variation, showing why interpretation uncertainty must be separated from document-extraction error [@lark2014crosssection]. Pakyuz-Charrier et al. explicitly propagated drillhole path and log uncertainty through alternative 3D model realizations with Monte Carlo perturbations [@pakyuzcharrier2018drillhole]. Paper III isolates an earlier error source—automated structuring of legacy logs—and holds the downstream correlation/interpolation configuration fixed when comparing raw automated extraction, constraint-validated extraction, and reference records. Interactive-machine-learning literature further argues that users and learning systems must be studied together [@amershi2014interactive]; it motivates a timed, event-logged human study here but supplies no transferable GeoLogParser time-saving estimate.

## 3. Workflow

Legacy PDF/JPG/PNG enters GeoLogParser and produces validated records with provenance. SQLite separates boreholes, intervals, and field provenance. GeoJSON exports coordinates without implicit CRS transformation. CSV, JSON, XLSX, and Parquet are supported with separate borehole, interval, and provenance tables. GeoParquet and GeoPackage point exports carry an explicit EPSG CRS for QGIS-compatible consumption and reject unknown or mixed CRSs rather than combining them. A Padova source-coordinate snapshot now exports 11 EPSG:4326 points to SQLite/GeoJSON/GeoParquet/GeoPackage, but all coordinate fields remain `needs_review`, the snapshot contains zero intervals, and it is not a geological model. <!-- evidence:p3.padova_spatial_catalog --> A separate gate requires at least three eligible points and human-verified collar elevations/target boundaries before surface modelling. A neutral regular-surface adapter exports IDW surfaces to PyVista VTP and off-screen PNG. This paper uses the transparent IDW implementation for controlled propagation and does not claim GemPy integration or production geological-model interoperability.

For native Swissgeol PDFs, a conservative direct-text spatial parser emits a coordinate pair only when exactly one distinct LV95-shaped pair follows a coordinate label. It handles grouped apostrophe, period, and space formats plus restricted `l/I/|→1` confusables. Multiple page pairs and absent values cause abstention. Collar elevation is accepted only as a plausible value immediately adjacent to a `Bohrkote` or `Terrainkote` label; tolerance-only strings and later equipment numbers are rejected. The parser was frozen before evaluating all 88 paired records outside the interval-v003 split. Database values are used only after page prediction, and disagreement is not automatically classified as recognition error because page and database values can differ.

Human review is triggered by missing MVP fields, low confidence, field warnings, unknown terminology, and constraint violations. Start/completion events record real duration and corrected-field count. No human timing result exists yet.

## 4. Error-Propagation Method

For a selected correlated boundary, depth is converted to elevation as collar elevation minus depth. A transparent IDW baseline interpolates the surface. Controlled perturbations of 0.01, 0.05, 0.10, 0.50, and 1.00 m are applied with recorded seeds; shared interval boundaries remain continuous and thickness is recomputed. Surface MAE, RMSE, and maximum absolute error are evaluated on a fixed grid. Formal experiments require multiple seeds and confidence intervals.

Protocol development additionally uses a CC BY 4.0 workbook containing 602 complete, unique directional gas-drainage borehole records. Its audit records numeric local X/Y/Z and roof-depth fields, but no CRS, and flags precise-location review as pending. <!-- evidence:p3.coal602_source_audit --> The source Y/X values are translated independently to zero-origin local `u/v`; the translation origin and source identifiers are not persisted. Source-reported No. 3 coal-roof depth is interpolated only as a scalar surface proxy on a 41 by 41 grid clipped to the collar-coordinate convex hull. It is not converted to elevation or named a coal-seam surface because trajectory and field-reference semantics are not established by the released files.

The first real structured-source comparison injects independent signed errors into two channels at a 10% per-channel rate. It compares the raw first channel, exact-consensus deletion, and a support-preserving mean of both channels against the unchanged source-reference surface. All three policies are reference-blinded; source values are used only for post-decision scoring. A complementary image-boundary diagnostic reuses the frozen held-out Paper II predictions and adds only authoritative coordinates and collar elevations after extraction decisions are frozen.

A second controlled experiment separates six downstream error classes on the 35-document held-out authoritative set: boundary shift, coordinate shift, missing boundary, merged layer, split layer, and duplicated boundary. Boundary and coordinate shifts affect 25% of eligible values or records at three metric magnitudes. The four structural conditions affect 10%, 25%, or 50% of eligible records. All conditions use 30 recorded seeds and the same 1,265 queries over per-boundary reference convex hulls. Missing values retain their ordered slot; merge deletes an internal boundary; split inserts a midpoint boundary; and duplicate inserts a repeated value. Predicted sequences are evaluated by ordered index without reference-guided repair or rematching. This design distinguishes numeric boundary error, coordinate geometry, spatial-support loss, and positional topology, but it does not model wrong lithology correlation or image-derived coordinate/elevation extraction.

The partial page-spatial experiment combines frozen direct-text coordinates with frozen raster boundary predictions before loading references. It compares: page coordinates plus reference boundary depth, page coordinates plus raw boundary depth, page coordinates plus reread boundary depth, and authoritative coordinates plus reread boundary depth. All variants are scored on the same authoritative 35-point convex-hull query domain. Because the frozen page parser extracts no collar elevations, every variant still receives authoritative collar elevation; the experiment therefore isolates progress and remaining coverage failure rather than claiming a complete end-to-end surface workflow.

## 5. Database and Interoperability

The database preserves source hash, raw/normalized values, page/bbox/text, method, confidence, validation, warnings, and units. Upserts replace a document's interval projection transactionally. GeoJSON skips missing coordinates and reports encountered CRS labels; it never guesses or transforms an unknown CRS. GeoParquet writes WKB point geometry only when all located records share one explicit `EPSG:<code>` identifier. A quarantine-only internal run built four auto boreholes, 12 intervals, and 224 provenance rows; because data are not human-validated or release-cleared, this is connectivity evidence only. <!-- evidence:p3.sanming_database_connectivity -->

## 6. Results

A controlled experiment on all 602 structured-source records used 30 paired-channel repetitions at each 0.01, 0.05, 0.10, 0.50, and 1.00 m error magnitude. Mean retained point coverage after exact consensus was 0.813–0.817. Raw surface MAE rose from 0.000575 ± 0.000147 m at 0.01 m injection to 0.054885 ± 0.010986 m at 1.00 m. Consensus-deletion MAE remained approximately 0.729–0.743 m because deleting disagreeing records changed interpolation support; 73–93 same-error acceptances also occurred across 30 repetitions per condition. Support-preserving mean fusion instead reduced MAE by 18.3%–22.0% relative to raw, improved 26–29 of 30 paired repetitions per magnitude, and had two-sided exact sign-test p values from `5.77×10⁻⁸` to `5.95×10⁻⁵`. The experiment therefore distinguishes unsafe downstream deletion from beneficial support-preserving multi-reader fusion. <!-- evidence:p3.coal602_consensus_qc -->

An executed controlled comparison now applies the production constraint/rereading ranker before the same IDW surface model. Across 30 seeds and four boreholes, raw surface MAE increased from 0.006741 m at a 0.01 m injected boundary error to 0.665164 m at 1.00 m. At 0.01 and 0.05 m the configured tolerance produced 120/120 abstentions per condition, so constrained and raw surfaces were identical. At 0.10, 0.50, and 1.00 m the violated thickness/final-depth relations triggered rereading; two candidate channels agreed on the known source value, all 120 boundaries per condition were accepted, and constrained surface MAE was 0 in this controlled fixture. This demonstrates the implemented threshold and propagation mechanics only; it is not a real-site effectiveness estimate. <!-- evidence:p3.executed_synthetic_comparison -->

See [generated/current_results.md](generated/current_results.md). A 30-seed synthetic extension exercises mean/std and explicitly named normal-approximation confidence intervals for perturbations 0.01–1.00 m. At 1.00 m, synthetic surface MAE was 0.662470 ± 0.110565 m across seeds. <!-- evidence:p3.idw_multiseed --> A separate indexed PyVista interoperability run wrote 121 points and 200 triangle cells, with VTP and PNG hashes reported in the generated table. <!-- evidence:p3.pyvista_interop --> These four-artificial-borehole artifacts are neither a real geological sensitivity estimate nor a real 3D model.

The separate single-channel 602-record source protocol used 30 seeds per magnitude and 80 convex-hull grid points. Under independent signed 1.00 m perturbations of the source-reported roof-depth scalar at every point, proxy-surface MAE was 0.260428 ± 0.018737 m; the output persisted neither absolute coordinate origin nor source identifiers. <!-- evidence:p3.coal602_source_proxy --> This is a deterministic response of one source-field/IDW protocol, not extraction accuracy, a true coal-seam surface, or a privacy clearance. The image-boundary diagnostic is reported in [generated/current_results.md](generated/current_results.md): on 35 held-out documents and 423 fixed convex-hull queries, raw versus reread surface MAE was 3.402 versus 3.050 m, with four accepted rereads and five review decisions. <!-- evidence:p3.image_boundary_surface -->

The multi-boundary extension propagates all four ordered boundary positions without reference-guided interval repair. Across 80 reference boundary observations, raw and reread output supplied 70 and 71 positional predictions. Aggregate boundary MAE decreased from 11.171 m to 2.789 m, while aggregate surface MAE decreased more modestly from 21.397 m to 20.615 m over 1,265 per-boundary grid queries. For boundary 2, rereading reduced positional MAE from 24.400 m to 5.355 m and surface MAE from 19.960 m to 17.974 m. Boundaries 3 and 4 had zero depth error among available predictions but only 4/7 and 2/3 spatial support; their surface MAE remained 50.651 m and 19.594 m. Thus correct available values do not guarantee a correct surface when omissions remove spatial support. <!-- evidence:p3.image_multiboundary_surface -->

To move beyond isolated contact surfaces, a real three-layer stratigraphic volume diagnostic converted the same ordered boundaries into adjacent layer-thickness surfaces and IDW volume estimates on common reference-domain grids. Across the three available layers, the raw channel had mean layer-thickness MAE 45.952 m and relative absolute volume error 0.1389; the constraint-reread channel reduced these to 45.679 m and 0.1216. We then propagated the held-out risk router into the same downstream decoder: it accepted 15/35 documents (coverage 0.4286), reduced mean layer-thickness MAE to 34.808 m and relative absolute volume error to 0.0824, and eliminated negative-thickness layers (1 in raw and reread, 0 in risk-aware). The gain is accompanied by reduced mean top/bottom support (0.387/0.378), and the deepest layers are supported by only seven and three reference records. The result is a reproducible real stratigraphic layer-model diagnostic, not a validated geological interpretation: collars and coordinates are authoritative, and ordered-index alignment can propagate upstream omissions. <!-- evidence:p3.stratigraphic_layer_model --> <!-- evidence:p3.stratigraphic_layer_model_risk_aware -->

The controlled error-class experiment executed 18 conditions and 540 seeded repetitions on the same 35 authoritative records, 80 ordered boundary observations, and 1,265 fixed queries. When 25% of boundary observations were displaced, surface MAE increased from 0.0158 m at a 0.10 m displacement to 0.1684 m at 1.00 m while support and topology remained unchanged. Moving 25% of borehole coordinates produced 0.0715, 0.2804, and 1.5641 m surface MAE at 25, 100, and 500 m displacement, respectively, with zero boundary-value error. Missing one boundary in 10%, 25%, and 50% of records reduced aggregate support to 0.950, 0.888, and 0.775 and produced 2.474, 4.284, and 8.621 m surface MAE despite zero boundary MAE among retained values. At 50% affected-record prevalence, deletion-based layer merging, midpoint layer splitting, and boundary duplication produced surface MAE of 40.957, 30.747, and 20.663 m, respectively, because ordered positions were shifted. Parameters are class-specific, so these values establish mechanisms and within-class severity trends rather than a universal ranking of real-world frequencies. <!-- evidence:p3.controlled_error_classes -->

On the external 88-document spatial set, the conservative parser emitted one unambiguous page-coordinate pair for 53 documents (60.2% coverage). Fifty-one pairs agreed exactly with the authoritative database, giving 96.2% conditional pair agreement and 58.0% exact coverage over all documents. The two disagreements included kilometre-scale component differences; without independent source adjudication they remain page/database disagreements rather than assigned recognition errors. The parser abstained on all 88 collar elevations. A failed predecessor had incorrectly accepted five drill-rig model numbers as elevations; its output was not indexed, and the adjacent-label rule eliminated those false extractions. <!-- evidence:p3.external_spatial_metadata -->

In the 35-document partial downstream experiment, page coordinates were available for 17 documents and 15 agreed exactly with the database. All 17 available raw and reread first-boundary predictions were exact, so the page-coordinate/reference-depth, raw-depth, and reread-depth variants were identical: coverage was 0.486 and surface MAE was 9.514 m over 423 fixed queries. With authoritative coordinates, the same reread-boundary channel supplied 34 points (0.971 coverage) and produced 3.050 m MAE. The result does not isolate missing coordinates from the two page/database disagreements, but it shows that correct available depths cannot compensate for incomplete spatial metadata. Every collar remained authoritative. <!-- evidence:p3.page_spatial_surface -->

The [Padova source-location plot](generated/figures/padova_locations.png) shows
three separated site groups and therefore rules out interpolation across the
whole collection as one local surface. Coordinates remain source-provided and
unverified. The real first-boundary surface export also writes reference and
reread VTP/PNG meshes for the 35-record held-out set; these files are
visualization artifacts and do not change the quantitative layer-volume
evaluation. <!-- evidence:p3.real_surface_visualization -->
The [synthetic propagation curve](generated/figures/synthetic_error_propagation.png)
is explicitly protocol-only and must not be interpreted as real-site response.
The [structured-source proxy curve](generated/figures/coal602_source_proxy.png)
is kept separate from the synthetic curve and carries the same non-formal
interpretation limits described above.
The [held-out image-boundary diagnostic](generated/figures/image_boundary_surface.png)
summarizes the raw-versus-reread boundary and surface errors; its caption
retains the authoritative-spatial-metadata limitation.
The [multi-boundary propagation diagnostic](generated/figures/image_multiboundary_surface.png)
separates per-boundary surface error from retained spatial support and shows why
zero error among available values can coexist with a poor interpolated surface.
The [controlled error-class diagnostic](generated/figures/controlled_error_classes.png)
separates surface error, support loss, and topological mismatch across the six
injected mechanisms; its severity axis is ordinal within each class because the
underlying parameters use different units.
The [page-coordinate surface diagnostic](generated/figures/page_spatial_surface.png)
contrasts the 17-point page-coordinate variants with the 34-point authoritative-
coordinate reread variant and explicitly retains the authoritative-collar limit.

## 7. Human-in-the-Loop Boundary

The software records review start/completion events and corrected-field counts, but no controlled timing study was executed. Consequently this paper makes no claim about manual-entry time, extraction-plus-correction time, fields corrected per minute, or labor savings. The measured operational quantity is selective data coverage: the risk-aware three-layer route retained 15/35 documents (42.9%) while reducing the reported layer-volume and thickness errors. This is a model-input reliability–support result, not a human-efficiency result.

## 8. Discussion and Threats to Validity

The synthetic smoke shows that the code responds to controlled perturbations, not that real geology has the same response. The structured-source comparison improves scale and spatial-pattern realism and directly demonstrates that field-level abstention can degrade a surface when deletion changes support geometry. The real three-layer risk-aware diagnostic provides the complementary result: rejecting uncertain documents reduced relative volume error by approximately 40.7% relative to the raw parser and removed negative-thickness cells, but reduced spatial support to 15/35 documents. This is a measurable reliability–coverage trade-off, not a universal improvement guarantee. The image-boundary diagnostics provide real extraction-to-surface evidence for up to four ordered boundaries. The partial page-spatial run replaces authoritative coordinates for 17/35 documents but still uses authoritative collars and one source family. The controlled error-class experiment isolates mechanisms but imposes class-specific prevalence and magnitude settings; between-class values are therefore not estimates of natural error frequency or universal geological sensitivity. The workflow still lacks page-derived collar coverage, human GT, explicit page CRS, trajectory reconstruction, validated geological interpretation, wrong-lithology correlation experiments, and field-reference verification. IDW is a transparent baseline rather than a universal geological model. Correlation errors, anisotropy, structural geology, spatial sampling, and model choice may dominate boundary noise. Rights-cleared spatial coherence remains a major data risk.

## 9. Reproducibility and Ethics

Database and surface artifacts will be linked to extraction experiment IDs and hashes. Spatially sensitive project information will be anonymized or withheld. Automated output is not an engineering sign-off; provenance and review status travel into downstream exports.

## 10. Conclusion

We define and execute a traceable path from legacy logs to geological surfaces and three-layer volumes. On a 602-record real structured source, strict dual-reader deletion worsened the interpolated surface because the loss of spatial support outweighed the small injected errors, whereas support-preserving mean fusion consistently improved it. On a separate 35-document held-out image-boundary diagnostic, reference-blinded rereading reduced aggregate error over four ordered boundaries, but deeper-boundary surfaces remained dominated by missing spatial support and positional alignment. In the real three-layer diagnostic, risk-aware abstention reduced relative absolute volume error from 0.1389 (raw) to 0.0824 and mean thickness MAE from 45.952 m to 34.808 m, while reducing accepted spatial support to 15/35 and eliminating negative-thickness layers. Controlled injections showed that numeric boundary shifts, coordinate displacement, support loss, and ordered-sequence errors generate measurably different downstream signatures. External spatial-field evaluation and partial page-coordinate propagation then demonstrated that spatial coverage, not only depth accuracy, remains an end-to-end bottleneck. Authoritative collars, one source family, class-specific injection assumptions, shallow support for the deepest layers, and the absence of a timed human study limit the claim. The complete workflow is therefore a reproducible downstream diagnostic with a quantified safety–coverage trade-off, not a validated production geological interpretation system.

The repository's auto-generated [publication-readiness audit](../../docs/generated/publication_readiness.md)
tracks the real structured-source comparison, image-derived boundary diagnostics,
controlled error injections, and protocol-only runs as distinct evidence classes.
It does not convert the IDW diagnostics into a validated site interpretation.

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
| P3_SWISSGEOL_TG_MULTIBOUNDARY_SURFACE_FROM_FROZEN_REREAD_001 | 35 | 80 | 1265 | 11.171 | 2.789 | 21.397 | 20.615 | 4 | 5 | formal_authoritative_boundary_downstream |

This diagnostic inherits frozen reference-blinded image boundaries from the Paper II held-out run. Coordinates and collar elevations are taken from the authoritative structured record; image extraction of spatial metadata is not evaluated, so this is not a complete end-to-end spatial workflow.

### Real stratigraphic layer-volume diagnostic

| Experiment | Variant | Documents | Layers | Mean layer-thickness MAE (m) | Relative absolute volume error | Mean top support | Mean bottom support | Layers with negative thickness | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| P3_SWISSGEOL_STRATIGRAPHIC_LAYER_MODEL_002 | final | 35 | 3 | 45.679 | 0.122 | 0.7841 | 0.7079 | 1 | formal_real_stratigraphic_model |
| P3_SWISSGEOL_STRATIGRAPHIC_LAYER_MODEL_002 | raw | 35 | 3 | 45.952 | 0.139 | 0.7841 | 0.6984 | 1 | formal_real_stratigraphic_model |
| P3_SWISSGEOL_STRATIGRAPHIC_LAYER_MODEL_RISK_AWARE_002 | final | 35 | 3 | 45.679 | 0.122 | 0.7841 | 0.7079 | 1 | formal_real_stratigraphic_model_risk_aware |
| P3_SWISSGEOL_STRATIGRAPHIC_LAYER_MODEL_RISK_AWARE_002 | raw | 35 | 3 | 45.952 | 0.139 | 0.7841 | 0.6984 | 1 | formal_real_stratigraphic_model_risk_aware |
| P3_SWISSGEOL_STRATIGRAPHIC_LAYER_MODEL_RISK_AWARE_002 | risk_aware | 35 | 3 | 34.808 | 0.082 | 0.3873 | 0.3778 | 0 | formal_real_stratigraphic_model_risk_aware |

These rows convert adjacent IDW contact surfaces into layer-thickness and volume estimates. They are real downstream diagnostics, not validated geological interpretations; sparse deep-layer support and authoritative collars/coordinates remain explicit limitations.

### Authoritative controlled error-class propagation

| Experiment | Error type | Severity | Parameter | Unit | Boundary MAE (m) | Surface MAE (m) | Support | Topology mismatch | Eligibility |
|---|---|---:|---:|---|---:|---:|---:|---:|---|
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | boundary_shift | 1 | 0.10 | m | 0.025000 ± 0.000000 | 0.015834 ± 0.004640 | 1.0000 | 0.0000 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | boundary_shift | 2 | 0.50 | m | 0.125000 ± 0.000000 | 0.081641 ± 0.020818 | 1.0000 | 0.0000 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | boundary_shift | 3 | 1.00 | m | 0.250000 ± 0.000000 | 0.168353 ± 0.042179 | 1.0000 | 0.0000 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | coordinate_shift | 1 | 25.00 | m | 0.000000 ± 0.000000 | 0.071537 ± 0.030763 | 1.0000 | 0.0000 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | coordinate_shift | 2 | 100.00 | m | 0.000000 ± 0.000000 | 0.280400 ± 0.106989 | 1.0000 | 0.0000 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | coordinate_shift | 3 | 500.00 | m | 0.000000 ± 0.000000 | 1.564117 ± 0.624882 | 1.0000 | 0.0000 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | missing_boundary | 1 | 0.10 | affected_document_fraction | 0.000000 ± 0.000000 | 2.473709 ± 1.946654 | 0.9500 | 0.1143 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | missing_boundary | 2 | 0.25 | affected_document_fraction | 0.000000 ± 0.000000 | 4.284154 ± 2.022886 | 0.8875 | 0.2571 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | missing_boundary | 3 | 0.50 | affected_document_fraction | 0.000000 ± 0.000000 | 8.620714 ± 2.456667 | 0.7750 | 0.5143 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | merged_layer | 1 | 0.10 | affected_document_fraction | 9.230263 ± 1.415854 | 9.849802 ± 2.763770 | 0.9500 | 0.1143 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | merged_layer | 2 | 0.25 | affected_document_fraction | 22.610798 ± 2.207236 | 20.851922 ± 4.236661 | 0.8875 | 0.2571 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | merged_layer | 3 | 0.50 | affected_document_fraction | 51.441398 ± 2.594455 | 40.956927 ± 4.477924 | 0.7750 | 0.5143 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | split_layer | 1 | 0.10 | affected_document_fraction | 7.134167 ± 1.499206 | 6.912026 ± 2.963111 | 1.0000 | 0.1143 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | split_layer | 2 | 0.25 | affected_document_fraction | 15.457500 ± 1.974436 | 14.205055 ± 3.021957 | 1.0000 | 0.2571 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | split_layer | 3 | 0.50 | affected_document_fraction | 31.817500 ± 2.717759 | 30.747222 ± 5.952748 | 1.0000 | 0.5143 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | duplicate_boundary | 1 | 0.10 | affected_document_fraction | 4.442083 ± 2.467289 | 5.066429 ± 3.591368 | 1.0000 | 0.1143 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | duplicate_boundary | 2 | 0.25 | affected_document_fraction | 9.656667 ± 2.854705 | 8.806453 ± 4.141115 | 1.0000 | 0.2571 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | duplicate_boundary | 3 | 0.50 | affected_document_fraction | 20.734167 ± 5.084878 | 20.663361 ± 6.530423 | 1.0000 | 0.5143 | formal_authoritative_controlled_error_downstream |

Each row aggregates 30 seeded injections on 35 held-out authoritative records and a fixed 1,265-query reference domain. Parameters are error-class specific and are not directly comparable across units. Coordinates and collar elevations are authoritative structured fields rather than image-derived predictions; no human Ground Truth is claimed.

### External page spatial-metadata extraction

| Experiment | Documents | Coordinate predictions | Coordinate coverage | Pair exact/all | Pair exact/predicted | X MAE (m) | Y MAE (m) | Page/database disagreements | Collar predictions | Eligibility |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P3_SWISSGEOL_EXTERNAL_SPATIAL_METADATA_002 | 88 | 53 | 53/88 (0.602) | 51/88 (0.580) | 51/53 (0.962) | 94.453 | 132.075 | 2 | 0 | formal_authoritative_spatial_extraction |

The frozen conservative parser was evaluated on every paired record outside the interval-v003 split. Database disagreement is not automatically attributed to recognition because the page and database can contain different values. Zero collar predictions is a measured abstention result, not missing evaluation output.

### Page-coordinate downstream surface diagnostic

| Experiment | Variant | Points | Coverage | Boundary MAE (m) | Surface MAE (m) | Surface RMSE (m) | Max error (m) | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P3_SWISSGEOL_PAGE_SPATIAL_SURFACE_001 | authoritative_coordinate_reread_boundary | 34 | 0.9714 | 0.941 | 3.050 | 5.014 | 29.590 | formal_partial_page_spatial_downstream |
| P3_SWISSGEOL_PAGE_SPATIAL_SURFACE_001 | page_coordinate_raw_boundary | 17 | 0.4857 | 0.000 | 9.514 | 13.751 | 69.821 | formal_partial_page_spatial_downstream |
| P3_SWISSGEOL_PAGE_SPATIAL_SURFACE_001 | page_coordinate_reference_boundary | 17 | 0.4857 | 0.000 | 9.514 | 13.751 | 69.821 | formal_partial_page_spatial_downstream |
| P3_SWISSGEOL_PAGE_SPATIAL_SURFACE_001 | page_coordinate_reread_boundary | 17 | 0.4857 | 0.000 | 9.514 | 13.751 | 69.821 | formal_partial_page_spatial_downstream |

Page coordinates and frozen image-boundary predictions are reference-free, but every collar elevation remains supplied by the authoritative record because page extraction coverage was zero. The comparison is therefore a partial spatial workflow, not complete end-to-end extraction.

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

<!-- AUTO-GENERATED REVIEW BUNDLE. DO NOT EDIT. -->
> Package status: **SUBMISSION_READY**
> This bundle combines the versioned manuscript and generated results for review.

# Propagation of Borehole-Log Extraction Errors into Stratigraphic Surface and Volume Diagnostics

## Abstract

This paper quantifies how borehole-log extraction errors and spatial-support loss propagate into stratigraphic surface proxies and layer-volume diagnostics. The analysis separates boundary-value error, coordinate displacement, missing support, and ordered-sequence topology under a transparent inverse-distance weighting (IDW) model. On 602 structured-source records, strict consensus deletion retained about 81.5% of points yet increased surface MAE to 0.73–0.74 m; support-preserving fusion reduced MAE by 18.3%–22.0%. On 35 source-agreement documents, 540 controlled perturbations showed distinct within-class dose responses for boundary, coordinate, support, merge, split, and duplicate errors. In the default full-support comparison, raw volume error 0.1389 and mean thickness MAE 45.952 m changed to risk-aware volume error 0.0824, mean thickness MAE 34.808 m, and document coverage 15/35. A strict matched-subset analysis reversed the apparent volume advantage: on the same 15 accepted documents, raw volume error was 0.0326, while reread and risk-aware error were both 0.0754. The risk-aware result therefore arose primarily from selection and changed spatial support, not an additional correction on accepted records. Across IDW power, neighbour, grid, and domain choices, method differences were comparable to spatial-model variability; leave-one-borehole-out reference interpolation error was about 47 m. The study is a sensitivity diagnostic, not validation of a geological interpretation or production 3D model. <!-- evidence:p3.coal602_consensus_qc --> <!-- evidence:p3.controlled_error_classes --> <!-- evidence:p3.stratigraphic_layer_model --> <!-- evidence:p3.stratigraphic_layer_model_risk_aware --> <!-- evidence:p3.spatial_sensitivity -->

## 1. Introduction

Document extraction is useful only if its output supports defensible downstream analysis. A small boundary error and a missing borehole have different propagation mechanisms; rejecting uncertain records can lower pointwise error while degrading the geometry of spatial support. We ask: (RQ1) how boundary, coordinate, omission, and topology errors alter surface and volume diagnostics; (RQ2) whether a lower-error extraction remains better on an identical borehole subset; (RQ3) how abstention changes convex-hull coverage and observation spacing; and (RQ4) whether conclusions persist across transparent IDW choices and leave-one-borehole-out validation.

This paper owns downstream error propagation and spatial-support sensitivity. It reuses the task definition from Paper I and frozen raw/risk outputs from Paper II, but does not claim their evaluation or extraction methods as contributions.

## 2. Related Work

Shepard's irregular-data interpolation provides the transparent IDW baseline used here [@shepard1968interpolation]. It is not treated as a universal geological model. GemPy demonstrates stochastic geological modelling and inversion [@delavarga2019gempy], while Wellmann and Caumon distinguish structural-model concepts, interpolation choices, and uncertainty sources [@wellmann2018uncertainty]. These works motivate sensitivity analysis across interpolation settings rather than presenting one surface as geological truth. Han and Suh connect recognition to a borehole database but do not quantify downstream propagation [@han2024boreholeocr].

Downstream uncertainty begins before interpolation. Lark et al. used withheld boreholes to quantify variation in interpreted contact elevations [@lark2014crosssection]. Pakyuz-Charrier et al. propagated drillhole path and log uncertainty through alternative 3D realizations [@pakyuzcharrier2018drillhole]. Recent studies separately quantify how borehole density changes hydrogeological statistics and 3D reconstruction fidelity [@tran2025boreholedensity; @zhang2026boreholedensity]. Our study isolates an earlier input channel—automated structuring of legacy logs—and separates value error from loss of spatial support and from the baseline interpolation error measured by leave-one-borehole-out prediction.

| Closest work | Uncertainty source | Difference in this study |
|---|---|---|
| Geological-model uncertainty reviews [@wellmann2018uncertainty] | Structural concepts, interpolation, and interpretation | Frozen document-extraction errors and spatial-support diagnostics |
| Withheld-borehole interpretation [@lark2014crosssection] | Human correlation/model variation | Automated boundary/value/support errors before interpretation |
| Drillhole Monte Carlo propagation [@pakyuzcharrier2018drillhole] | Survey path and logged observations | Raw versus reread versus risk-selected document outputs plus matched-subset analysis |
| Borehole-density sensitivity [@tran2025boreholedensity; @zhang2026boreholedensity] | Sampling density and spatial layout | Extraction-driven abstention and boundary omission measured through hull, spacing, and matched-support diagnostics |
| IDW interpolation [@shepard1968interpolation] | Deterministic spatial approximation | Power/neighbour/grid/domain sensitivity and LOOCV baseline |

## 3. Workflow

### 3.0 Evidence tiers and terminology

| Evidence type | Meaning | Supported claim |
|---|---|---|
| Published manual transcription Gold | External image transcription with publisher QC | Upstream extraction accuracy, when reused from Paper I/II |
| Source-agreement reference | Explicit PDF intervals aligned to authoritative records | Downstream consistency and sensitivity for that selected source |
| Authoritative metadata | Official coordinates/collars | Spatial coverage and page/database agreement |
| Machine Silver | Machine-derived reference | Agreement diagnostics only |
| Audit / no GT | No independent target reference | Coverage, runtime, and failure mechanisms only |

Throughout, *surface proxy*, *stratigraphic surface diagnostic*, *volume diagnostic*, and *downstream consistency* are used deliberately. The results do not establish geological interpretation accuracy, a validated 3D model, or an engineering-ready product.

Legacy PDF/JPG/PNG enters GeoLogParser and produces validated records with provenance. SQLite separates boreholes, intervals, and field provenance. GeoJSON exports coordinates without implicit CRS transformation. CSV, JSON, XLSX, and Parquet are supported with separate borehole, interval, and provenance tables. GeoParquet and GeoPackage point exports carry an explicit EPSG CRS for QGIS-compatible consumption and reject unknown or mixed CRSs rather than combining them. A Padova source-coordinate snapshot now exports 11 EPSG:4326 points to SQLite/GeoJSON/GeoParquet/GeoPackage, but all coordinate fields remain `needs_review`, the snapshot contains zero intervals, and it is not a geological model. <!-- evidence:p3.padova_spatial_catalog --> A separate gate requires at least three eligible points and human-verified collar elevations/target boundaries before surface modelling. A neutral regular-surface adapter exports IDW surfaces to PyVista VTP and off-screen PNG. This paper uses the transparent IDW implementation for controlled propagation and does not claim GemPy integration or production geological-model interoperability.

For native Swissgeol PDFs, a conservative direct-text spatial parser emits a coordinate pair only when exactly one distinct LV95-shaped pair follows a coordinate label. It handles grouped apostrophe, period, and space formats plus restricted `l/I/|→1` confusables. Multiple page pairs and absent values cause abstention. Collar elevation is accepted only as a plausible value immediately adjacent to a `Bohrkote` or `Terrainkote` label; tolerance-only strings and later equipment numbers are rejected. The parser was frozen before evaluating all 88 paired records outside the interval-v003 split. Database values are used only after page prediction, and disagreement is not automatically classified as recognition error because page and database values can differ.

Human review is triggered by missing MVP fields, low confidence, field warnings, unknown terminology, and constraint violations. Start/completion events record real duration and corrected-field count. No human timing result exists yet.

## 4. Error-Propagation Method

For a selected correlated boundary, depth is converted to elevation as collar elevation minus depth. A transparent IDW baseline interpolates the surface. Controlled perturbations of 0.01, 0.05, 0.10, 0.50, and 1.00 m are applied with recorded seeds; shared interval boundaries remain continuous and thickness is recomputed. Surface MAE, RMSE, and maximum absolute error are evaluated on a fixed grid. Formal experiments require multiple seeds and confidence intervals.

Protocol development additionally uses a CC BY 4.0 workbook containing 602 complete, unique directional gas-drainage borehole records. Its audit records numeric local X/Y/Z and roof-depth fields, but no CRS, and flags precise-location review as pending. <!-- evidence:p3.coal602_source_audit --> The source Y/X values are translated independently to zero-origin local `u/v`; the translation origin and source identifiers are not persisted. Source-reported No. 3 coal-roof depth is interpolated only as a scalar surface proxy on a 41 by 41 grid clipped to the collar-coordinate convex hull. It is not converted to elevation or named a coal-seam surface because trajectory and field-reference semantics are not established by the released files.

The first real structured-source comparison injects independent signed errors into two channels at a 10% per-channel rate. It compares the raw first channel, exact-consensus deletion, and a support-preserving mean of both channels against the unchanged source-reference surface. All three policies are reference-blinded; source values are used only for post-decision scoring. A complementary image-boundary diagnostic reuses the frozen held-out Paper II predictions and adds only authoritative coordinates and collar elevations after extraction decisions are frozen.

A second controlled experiment separates six downstream error classes on the 35-document held-out authoritative set: boundary shift, coordinate shift, missing boundary, merged layer, split layer, and duplicated boundary. Boundary and coordinate shifts affect 25% of eligible values or records at three metric magnitudes. The four structural conditions affect 10%, 25%, or 50% of eligible records. All conditions use 30 recorded seeds and the same 1,265 queries over per-boundary reference convex hulls. Missing values retain their ordered slot; merge deletes an internal boundary; split inserts a midpoint boundary; and duplicate inserts a repeated value. Predicted sequences are evaluated by ordered index without reference-guided repair or rematching. This design distinguishes numeric boundary error, coordinate geometry, spatial-support loss, and positional topology, but it does not model wrong lithology correlation or image-derived coordinate/elevation extraction.

The partial page-spatial experiment combines frozen direct-text coordinates with frozen raster boundary predictions before loading references. It compares: page coordinates plus reference boundary depth, page coordinates plus raw boundary depth, page coordinates plus reread boundary depth, and authoritative coordinates plus reread boundary depth. All variants are scored on the same authoritative 35-point convex-hull query domain. Because the frozen page parser extracts no collar elevations, every variant still receives authoritative collar elevation; the experiment therefore isolates progress and remaining coverage failure rather than claiming a complete end-to-end surface workflow.

The principal reanalysis has two estimands. The *full-support comparison* lets raw, reread, and risk-aware variants operate with their own available points over the reference convex hull; it measures deployed input packages, including selection. The *matched-subset comparison* restricts all three variants and the reference domain to the same 15 risk-accepted documents; it isolates value/sequence changes from document selection. Because risk-aware intervals equal reread intervals on accepted records, those two variants must be identical in the matched subset.

Spatial support is quantified for every ordered boundary by effective point count, point coverage, accepted/reference convex-hull area ratio, nearest-neighbour distance distribution, a diagnostic Clark–Evans ratio, and grid-to-nearest-observation distance. IDW sensitivity crosses powers 1, 2, and 3; all points versus four or eight nearest neighbours; 15, 25, and 41 grid nodes per axis; and the full reference versus matched accepted hull. The goal is not to select the most favourable IDW setting, but to compare method differences with spatial-model variability.

Leave-one-borehole-out (LOO) prediction removes each target borehole, interpolates each ordered boundary from the remaining records, and scores against the target reference elevation. A reference-input LOO baseline estimates interpolation error even with perfect structured inputs. Raw, reread, and risk-input LOO then show whether extraction effects are large relative to this baseline. Uncertainty sources are kept separate: borehole/document bootstrap for matched-subset boundary error, perturbation-seed variability for controlled injections, and range across IDW settings for model-choice sensitivity. Thirty perturbation seeds are repetitions of one site, not 30 independent sites.

## 5. Database Boundary and Interoperability

The database preserves source hash, raw/normalized values, page/bbox/text, method, confidence, validation, warnings, and units. GeoJSON and GeoParquet exports refuse unknown or mixed coordinate systems rather than guessing transformations. Database connectivity and visualization smoke tests are software-supplement evidence, not part of the downstream geological estimand. <!-- evidence:p3.sanming_database_connectivity --> Details are moved to [Supplementary Material](supplement.md).

## 6. Results

The main full-support, matched-subset, spatial-support, IDW-sensitivity, and leave-one-borehole-out tables are generated directly from the frozen analysis in [major-revision tables](generated/major_revision_tables.md). The full indexed catalogue is retained in [current results](generated/current_results.md).

A controlled experiment on all 602 structured-source records used 30 paired-channel repetitions at each 0.01, 0.05, 0.10, 0.50, and 1.00 m error magnitude. Mean retained point coverage after exact consensus was 0.813–0.817. Raw surface MAE rose from 0.000575 ± 0.000147 m at 0.01 m injection to 0.054885 ± 0.010986 m at 1.00 m. Consensus-deletion MAE remained approximately 0.729–0.743 m because deleting disagreeing records changed interpolation support; 73–93 same-error acceptances also occurred across 30 repetitions per condition. Support-preserving mean fusion instead reduced MAE by 18.3%–22.0% relative to raw, improved 26–29 of 30 paired repetitions per magnitude, and had two-sided exact sign-test p values from `5.77×10⁻⁸` to `5.95×10⁻⁵`. The experiment therefore distinguishes unsafe downstream deletion from beneficial support-preserving multi-reader fusion. <!-- evidence:p3.coal602_consensus_qc -->

An executed controlled comparison now applies the production constraint/rereading ranker before the same IDW surface model. Across 30 seeds and four boreholes, raw surface MAE increased from 0.006741 m at a 0.01 m injected boundary error to 0.665164 m at 1.00 m. At 0.01 and 0.05 m the configured tolerance produced 120/120 abstentions per condition, so constrained and raw surfaces were identical. At 0.10, 0.50, and 1.00 m the violated thickness/final-depth relations triggered rereading; two candidate channels agreed on the known source value, all 120 boundaries per condition were accepted, and constrained surface MAE was 0 in this controlled fixture. This demonstrates the implemented threshold and propagation mechanics only; it is not a real-site effectiveness estimate. <!-- evidence:p3.executed_synthetic_comparison -->

The 30-seed synthetic protocol and PyVista export smoke test are reported only in the software supplement. They verify perturbation and export mechanics, not real-site geological accuracy. <!-- evidence:p3.idw_multiseed --> <!-- evidence:p3.pyvista_interop -->

The separate single-channel 602-record source protocol used 30 seeds per magnitude and 80 convex-hull grid points. Under independent signed 1.00 m perturbations of the source-reported roof-depth scalar at every point, proxy-surface MAE was 0.260428 ± 0.018737 m; the output persisted neither absolute coordinate origin nor source identifiers. <!-- evidence:p3.coal602_source_proxy --> This is a deterministic response of one source-field/IDW protocol, not extraction accuracy, a true coal-seam surface, or a privacy clearance. The image-boundary diagnostic is reported in [generated/current_results.md](generated/current_results.md): on 35 held-out documents and 423 fixed convex-hull queries, raw versus reread surface MAE was 3.402 versus 3.050 m, with four accepted rereads and five review decisions. <!-- evidence:p3.image_boundary_surface -->

The multi-boundary extension propagates all four ordered boundary positions without reference-guided interval repair. Across 80 reference boundary observations, raw and reread output supplied 70 and 71 positional predictions. Aggregate boundary MAE decreased from 11.171 m to 2.789 m, while aggregate surface MAE decreased more modestly from 21.397 m to 20.615 m over 1,265 per-boundary grid queries. For boundary 2, rereading reduced positional MAE from 24.400 m to 5.355 m and surface MAE from 19.960 m to 17.974 m. Boundaries 3 and 4 had zero depth error among available predictions but only 4/7 and 2/3 spatial support; their surface MAE remained 50.651 m and 19.594 m. Thus correct available values do not guarantee a correct surface when omissions remove spatial support. <!-- evidence:p3.image_multiboundary_surface -->

To move beyond isolated contact surfaces, a real three-layer stratigraphic volume diagnostic converted the same ordered boundaries into adjacent layer-thickness surfaces and IDW volume estimates on common reference-domain grids. Across the three available layers, the raw channel had mean layer-thickness MAE 45.952 m and relative absolute volume error 0.1389; the constraint-reread channel reduced these to 45.679 m and 0.1216. We then propagated the held-out risk router into the same downstream decoder: it accepted 15/35 documents (coverage 0.4286), reduced mean layer-thickness MAE to 34.808 m and relative absolute volume error to 0.0824, and eliminated negative-thickness layers (1 in raw and reread, 0 in risk-aware). The gain is accompanied by reduced mean top/bottom support (0.387/0.378), and the deepest layers are supported by only seven and three reference records. The result is a reproducible real stratigraphic layer-model diagnostic, not a validated geological interpretation: collars and coordinates are authoritative, and ordered-index alignment can propagate upstream omissions. <!-- evidence:p3.stratigraphic_layer_model --> <!-- evidence:p3.stratigraphic_layer_model_risk_aware -->

The strict matched-subset comparison changes the interpretation. On the same 15 accepted documents, raw, reread, and risk-aware mean thickness MAE were 35.128, 34.670, and 34.670 m, but relative absolute volume error was 0.0326, 0.0754, and 0.0754. All 30 raw and all 31 reread/risk ordered boundaries available on this subset matched the reference exactly, so the remaining thickness and volume discrepancies arise from missing ordered positions and spatial interpolation support rather than pointwise depth error. Because reread and risk-aware inputs are identical after conditioning on acceptance, the lower full-support risk-aware error cannot be attributed to a further correction; it is a selection/support effect. <!-- evidence:p3.spatial_sensitivity -->

Spatial diagnostics quantify the support cost. For the first boundary, raw/reread used 34/35 points and retained the full reference convex-hull area; risk-aware used 14/35 points, retained 0.636 of that area, increased mean nearest-neighbour spacing from 1.39 km to 3.48 km, and increased mean grid-to-nearest-observation distance from 2.75 km to 4.62 km. Deeper boundaries had fewer eligible records and still lower effective support. These quantities explain why exact available depths can coexist with large surface error. <!-- evidence:p3.spatial_sensitivity -->

The 54-setting IDW sweep did not preserve a universal ordering. On the full reference hull, relative volume error ranged from 0.122–0.154 for raw, 0.093–0.132 for reread, and 0.033–0.125 for risk-aware. On the matched accepted hull, raw ranged from 0.021–0.065, whereas reread/risk ranged from 0.061–0.098. The default full-support result is therefore one point on an error–coverage–model-choice surface, not a general proof that abstention improves volume diagnostics. <!-- evidence:p3.spatial_sensitivity -->

At default IDW power 2 with all neighbours, leave-one-borehole-out mean absolute error using perfect reference inputs was 47.06 m across 80 ordered boundaries. Raw, reread, and risk-input LOO errors were 49.84, 46.62, and 47.05 m. On the matched accepted targets, the reference baseline was 52.99 m and reread/risk were 48.76 m. These differences are smaller than the baseline interpolation error itself, showing that spatial sampling and model choice dominate the extraction-policy differences in this source family. LOO evaluates a transparent surface proxy, not geological correlation accuracy. <!-- evidence:p3.spatial_sensitivity -->

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

The software records review start/completion events and corrected-field counts, but no controlled timing study was executed. Consequently this paper makes no claim about manual-entry time, extraction-plus-correction time, fields corrected per minute, or labour savings. The measured operational quantity is selective coverage: the risk-aware route retained 15/35 documents. Because the matched-subset volume result did not improve, this is primarily a support-selection result rather than evidence of downstream correction efficacy.

## 8. Discussion and Threats to Validity

The structured-source comparison demonstrates that deletion can degrade a surface when lost support outweighs value error. The full-support three-layer result initially suggested a 40.7% risk-aware reduction in relative volume error, but matched-subset analysis showed no value advantage over rereading and a worse volume diagnostic than raw on the same accepted documents. This is not a contradiction: the estimands differ. Full-support scoring measures the selected package; matched-subset scoring isolates the accepted records. Spatial-support and IDW sweeps show that selection geometry and interpolation choice can dominate extraction differences.

Controlled error classes are interpreted only within class. A 0.1 m boundary shift, 100 m coordinate shift, 50% missing-support condition, and merge/split event do not share a severity scale, so the paper reports dose–response mechanisms rather than a universal ranking. The 30 perturbation seeds quantify algorithmic variability at one site and are not independent fields. Authoritative collars, source-agreement rather than manual image GT, one source family, shallow support for deep boundaries, ordered-index alignment, and the absence of lithology correlation remain major limits. IDW is a transparent surface proxy; faults, anisotropy, geological correlation, and alternative spatial models may dominate.

## 9. Reproducibility and Ethics

Database and surface artifacts will be linked to extraction experiment IDs and hashes. Spatially sensitive project information will be anonymized or withheld. Automated output is not an engineering sign-off; provenance and review status travel into downstream exports.

## 10. Conclusion

This study reframes downstream evaluation around two coupled quantities: value error and spatial support. On 602 structured records, support-preserving fusion outperformed deletion. On 35 source-agreement documents, controlled boundary, coordinate, omission, and topology errors produced different within-class propagation signatures. The default full-support comparison favoured risk-aware selection, but the matched 15-document comparison did not: reread/risk volume error was 0.0754 versus 0.0326 for raw, and risk equalled reread because acceptance introduced no additional correction. First-boundary risk selection retained only 0.636 of the reference convex-hull area, while the IDW sweep and roughly 47 m reference-input LOO error showed that spatial sampling and model choice were at least as consequential as extraction differences. The defensible conclusion is therefore diagnostic: reliable geological-document systems must preserve provenance, quantify support geometry, and evaluate selection on matched subsets before claiming downstream benefit. No validated geological interpretation or production 3D model is claimed.

The repository's auto-generated [publication-readiness audit](../../docs/generated/publication_readiness.md)
tracks the real structured-source comparison, image-derived boundary diagnostics,
controlled error injections, and protocol-only runs as distinct evidence classes.
It does not convert the IDW diagnostics into a validated site interpretation.

## References

Shared bibliography: [../references.bib](../references.bib). Citation metadata and permitted claim scope are logged in [../../docs/literature_evidence.yaml](../../docs/literature_evidence.yaml).


# Linked Supplementary Material

# Supplementary Material for Paper III

## S1. Software and interoperability

The SQLite, CSV/JSON/XLSX/Parquet, GeoJSON/GeoParquet/GeoPackage, VTP, off-screen PNG, Padova location inventory, and quarantined Sanming connectivity runs demonstrate software paths only. They do not validate geological interpretation, spatial metadata, or a production 3D model.

## S2. Controlled protocol checks

Synthetic four-borehole perturbation, 30-seed IDW, structured-source scalar-proxy, and visualization outputs verify deterministic propagation mechanics. The main manuscript instead centers the 602-point support deletion/fusion analysis, the 35-document real boundary propagation, matched-subset comparison, spatial-support diagnostics, IDW sensitivity, leave-one-borehole-out error, and six within-class controlled mechanisms.

## S3. Interpretation boundary

Padova, PyVista, Sanming, and generic export artifacts are not included in the main downstream-effect claim. Exact metrics and hashes remain in [current results](generated/current_results.md), the result index, claim registry, and publication-evidence bundle.

# Appendix: Machine-Generated Current Results

<!-- AUTO-GENERATED. DO NOT EDIT. -->
# Paper III major-revision tables

## Full-support and strict matched-subset diagnostics

Evidence tier: **Source-agreement reference**. These are surface and volume diagnostics, not validated geological models.

| Estimand | Variant | Documents | Mean thickness MAE (m) | Relative absolute volume error | Mean top support | Mean bottom support | Negative-thickness layers |
|---|---|---:|---:|---:|---:|---:|---:|
| Full support | raw | 35 | 45.952 | 0.1389 | 0.784 | 0.698 | 1 |
| Full support | reread | 35 | 45.679 | 0.1216 | 0.784 | 0.708 | 1 |
| Full support | risk | 35 | 34.808 | 0.0824 | 0.387 | 0.378 | 0 |
| Matched accepted subset | raw | 15 | 35.128 | 0.0326 | 0.894 | 0.850 | 0 |
| Matched accepted subset | reread | 15 | 34.670 | 0.0754 | 0.894 | 0.872 | 0 |
| Matched accepted subset | risk | 15 | 34.670 | 0.0754 | 0.894 | 0.872 | 0 |

## First-boundary spatial support

| Variant | Effective points | Point coverage | Hull-area ratio | Mean nearest-neighbour distance (m) | Mean grid-to-observation distance (m) |
|---|---:|---:|---:|---:|---:|
| raw | 34/35 | 0.971 | 1.000 | 1387.5 | 2745.0 |
| reread | 34/35 | 0.971 | 1.000 | 1387.5 | 2745.0 |
| risk | 14/35 | 0.400 | 0.636 | 3479.5 | 4618.6 |

## IDW and leave-one-borehole-out sensitivity

| Domain | Variant | Relative volume-error range across IDW settings | Default LOO MAE (m) |
|---|---|---:|---:|
| Full reference | reference | -- | 47.06 |
| Full reference | raw | 0.122–0.154 | 49.84 |
| Full reference | reread | 0.093–0.132 | 46.62 |
| Full reference | risk | 0.033–0.125 | 47.05 |
| Matched accepted | reference | -- | 52.99 |
| Matched accepted | raw | 0.021–0.065 | 48.85 |
| Matched accepted | reread | 0.061–0.098 | 48.76 |
| Matched accepted | risk | 0.061–0.098 | 48.76 |

The full-support and matched-subset estimands answer different questions. The matched subset shows that risk-aware and reread inputs are identical after acceptance; the apparent full-support risk advantage is therefore a selection/support effect.


# Full Indexed Result Catalogue

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

<!-- AUTO-GENERATED REVIEW BUNDLE. DO NOT EDIT. -->
> Package status: **SUBMISSION_READY_CANDIDATE**
> This bundle combines the versioned manuscript and generated results for review.

# Propagation of Borehole-Log Extraction Errors into Stratigraphic Surface and Volume Diagnostics

## Abstract

This paper quantifies how borehole-log extraction error and spatial-support loss propagate into stratigraphic surface proxies and layer-volume diagnostics. With two synthetically perturbed reader channels on 602 real structured-source records, strict channel agreement retained about 81.5% of points yet increased surface MAE to 0.73–0.74 m; support-preserving channel fusion reduced MAE by 18.3%–22.0%. The records and spatial support are real structured-source data, whereas both reader-error channels are simulated. On 35 source-agreement documents, 540 controlled perturbations separated boundary-value, coordinate, missing-support, merge, split, and duplicate mechanisms. In the numerically stabilized full-support comparison, raw volume error 0.1387 and mean thickness MAE 45.623 m changed to risk-aware volume error 0.0821, mean thickness MAE 34.899 m, and document coverage 15/35. A matched-subset analysis reversed the apparent volume advantage: on the same 15 accepted documents, raw volume error was 0.0326, while reread and risk-aware error were both 0.0754. The risk-aware result therefore arose primarily from selection and changed spatial support, not additional correction on accepted records. IDW parameter effects were comparable to extraction-policy differences, and leave-one-borehole-out error with reference inputs was 47.06 m. This is an error-propagation and spatial-support sensitivity diagnostic, not validation of a geological interpretation or production 3D model. <!-- evidence:p3.coal602_consensus_qc --> <!-- evidence:p3.controlled_error_classes --> <!-- evidence:p3.spatial_sensitivity -->

## 1. Introduction

Downstream usefulness depends on more than pointwise extraction accuracy. A 0.1 m boundary displacement perturbs a value while retaining support; abstaining on a difficult borehole removes an observation and changes interpolation geometry; a missing or duplicated layer shifts every later ordered position. These mechanisms should not be pooled as interchangeable errors.

This paper asks:

- RQ1: how do boundary, coordinate, omission, and topology errors change surface and volume diagnostics?
- RQ2: does an apparently lower-error extraction remain better on an identical borehole subset?
- RQ3: how does abstention alter convex-hull coverage and observation spacing?
- RQ4: are method differences stable across transparent interpolation choices and leave-one-borehole-out prediction?

The contributions are:

1. a formal propagation protocol separating value, support, and positional-topology error;
2. full-support and matched-subset estimands that distinguish correction from selection;
3. spatial-support diagnostics and IDW/LOO sensitivity on existing borehole records; and
4. a mechanism-specific controlled study that avoids ranking incomparable error units.

Paper I owns extraction evaluation, and Paper II owns sequence reconstruction and risk policy. This paper reuses their frozen outputs only as upstream inputs.

## 2. Related Work

Inverse-distance weighting (IDW) provides a transparent irregular-data baseline [@shepard1968interpolation]. GemPy and geological-model uncertainty reviews describe richer structural concepts, stochastic realizations, and interpretation uncertainty [@delavarga2019gempy; @wellmann2018uncertainty]. We use IDW precisely because its support and weighting are inspectable; no one surface is presented as geological truth.

Uncertainty can enter through interpreted contacts, drillhole paths, observations, sampling density, and spatial layout [@lark2014crosssection; @pakyuzcharrier2018drillhole; @tran2025boreholedensity; @zhang2026boreholedensity]. Garzón et al. propose geology-informed sequence and spatial metrics for automated stratigraphic interpretations [@garzon2026stratigraphicmetrics]. Our analysis isolates an earlier channel: page-extraction and risk-selection errors before geological unit correlation. It additionally conditions all methods on an identical accepted subset to separate value changes from selection.

| Closest work | Uncertainty source | Difference here |
|---|---|---|
| Geological-model uncertainty [@wellmann2018uncertainty] | Structural concepts and interpretation | Frozen document-extraction and abstention inputs |
| Withheld-borehole interpretation [@lark2014crosssection] | Human correlation and model variation | Upstream value/support error before interpretation |
| Drillhole Monte Carlo propagation [@pakyuzcharrier2018drillhole] | Path and logged-observation uncertainty | Raw, reread, and risk-selected structured outputs |
| Borehole-density sensitivity [@tran2025boreholedensity; @zhang2026boreholedensity] | Sampling density/layout | Extraction-driven support deletion and matched-subset analysis |
| Geology-informed borehole metrics [@garzon2026stratigraphicmetrics] | Structured sequence and spatial consistency | Page-extraction error, abstention, and interpolation-support mechanisms |

## 3. Evidence and Data

### 3.1 Evidence tiers

| Evidence type | Meaning | Supported claim |
|---|---|---|
| Published manual transcription Gold | External image transcription with publisher QC | Upstream extraction accuracy when reused from Paper I/II |
| Source-agreement reference | Explicit page intervals aligned to authoritative records | Downstream consistency for that selected source |
| Authoritative metadata | Official coordinates and collar elevations | Spatial-support diagnostics |
| Machine Silver | Machine-derived reference | Agreement only |
| Audit / no GT | No independent reference | Coverage, runtime, and failure mechanisms |

Terms such as surface proxy, stratigraphic surface diagnostic, volume diagnostic, and downstream consistency are deliberate. No result establishes geological interpretation accuracy, a validated geological model, or an engineering-ready product.

### 3.2 Structured-source support experiment

The first track contains 602 complete, unique real structured-source records with local coordinates and one source-reported roof-depth scalar. The release contains no established CRS and its precise-location review remains pending. Two reader channels are generated by independently injecting recorded synthetic numerical errors into that scalar; no second OCR engine, human reading, or image transcription is observed. Coordinates are translated to a zero-origin local frame, source identifiers are removed, and the scalar is never relabelled as a geological surface elevation. This controlled track tests what happens when agreement-based deletion or fusion acts on real spatial support under simulated reader errors; it is not an image-extraction accuracy test. <!-- evidence:p3.coal602_source_audit -->

### 3.3 Image-boundary propagation experiment

The second track uses 35 held-out Swissgeol source-agreement documents and frozen raw, reread, and risk-aware interval sequences from Paper II. Authoritative coordinates and collar elevations are joined only after extraction decisions are fixed. The 35 records contain 80 ordered reference boundaries; support becomes sparse at depth, with 35, 35, 7, and 3 records across the four ordered boundary positions.

The risk router accepts 15/35 documents. Its accepted intervals are identical to reread intervals on those documents. This identity is central: any difference between reread and risk-aware output under full-support scoring is selection, not an additional interval correction.

## 4. Error-Propagation Method

For borehole \(i\) and ordered boundary \(r\), boundary elevation is

\[
z_{ir}=c_i-d_{ir},
\]

where \(c_i\) is collar elevation and \(d_{ir}\) is depth. At query location \(u\), IDW with power \(p\) and optional neighbour set \(N_k(u)\) is

\[
\hat z_r(u)=
\frac{\sum_{i\in N_k(u)}\lVert u-u_i\rVert^{-p}z_{ir}}
{\sum_{i\in N_k(u)}\lVert u-u_i\rVert^{-p}}.
\]

An observed value is returned directly at the same support location. Adjacent-boundary thickness is

\[
\hat h_\ell(u)=\hat z_\ell(u)-\hat z_{\ell+1}(u).
\]

For hull-clipped grid \(G\) and polygon area \(A\), the volume diagnostic is

\[
\hat V_\ell=\frac{A}{|G|}\sum_{u\in G}\hat h_\ell(u).
\]

Aggregate relative absolute volume error is

\[
\frac{\sum_\ell|\hat V_\ell-V_\ell|}
{\sum_\ell|V_\ell|},
\]

not the mean of per-layer percentages. Leave-one-borehole-out (LOO) removes record \(i\), predicts \(\hat z_{-i,r}(u_i)\), and scores

\[
|\hat z_{-i,r}(u_i)-z_{ir}|.
\]

### 4.1 Numerical invariance

Survey coordinates can be of order \(10^6\) m. Convex-hull area and edge tests are therefore evaluated in a translated local frame, with a scale-aware cross-product tolerance. IDW treats sub-micrometre coordinate differences as the same support location. This prevents arbitrary coordinate origin and decimal serialization from changing which boundary grid points are included. The transformed public input subtracts the horizontal centroid, applies a documented rigid rotation, subtracts mean collar elevation, and reproduces the stabilized diagnostics without restoring the absolute origin. Because this preserves pairwise distances, the coordinates are pseudonymized rather than anonymous and may be rigidly linked to a public point set.

### 4.2 Full-support and matched-subset estimands

The full-support comparison allows raw, reread, and risk-aware variants to use their own available records over the reference hull. It measures the deployed input package, including selection. The matched-subset comparison restricts every variant and the reference domain to the same 15 accepted documents. It measures sequence/value differences conditional on acceptance. Reread and risk-aware must be identical in the matched subset.

Spatial support is summarized by point coverage, accepted/reference convex-hull area ratio, nearest-neighbour distance, diagnostic Clark–Evans ratio, and grid-to-nearest-observation distance. These are support diagnostics, not evidence of spatial randomness.

### 4.3 Interpolation and sampling sensitivity

The IDW sweep crosses powers 1, 2, and 3; all points versus four or eight nearest neighbours; grid sizes 15, 25, and 41 per axis; and full-reference versus matched-accepted domains. LOO is computed for reference, raw, reread, and risk inputs. A leave-one-borehole-out volume jackknife recomputes the surfaces and volumes after each omission. Document bootstrap measures matched-subset boundary sampling; the IDW sweep measures spatial-model choice.

### 4.4 Controlled error mechanisms

On the 35-document reference, boundary and coordinate shifts affect 25% of eligible observations or records at three magnitudes. Missing boundary, merged layer, split layer, and duplicated boundary affect 10%, 25%, or 50% of eligible records. Thirty recorded seeds are used per condition, for 18 conditions and 540 repetitions. Missing values retain their ordered slot; merge deletes an internal boundary; split inserts a midpoint; duplicate inserts a repeated boundary. No reference-guided rematching repairs the perturbed sequence.

The seeds measure Monte Carlo repeatability at one source, not 30 independent sites. Each error class is interpreted by its own dose–response; metres of boundary shift, metres of coordinate displacement, and affected-record prevalence are not ranked on one universal severity scale.

## 5. Results

The generated main tables are in [major-revision tables](generated/major_revision_tables.md). All quantities below come from frozen or deterministically regenerated analysis files.

### 5.1 Support deletion versus fusion on 602 records

Across five error magnitudes and 30 repetitions of the two synthetically perturbed channels, exact channel agreement retained 0.813–0.817 of points. Despite rejecting disagreements, its surface MAE remained approximately 0.729–0.743 m because deletion changed interpolation support. Support-preserving channel-mean fusion reduced MAE by 18.3%–22.0% relative to the first simulated channel and improved 26–29 of 30 repetitions at each magnitude. The mechanism is clear: removing uncertain values can be worse than retaining a fused estimate when spatial support is valuable. These are controlled perturbation results on real spatial records, not an empirical comparison of two observed readers. <!-- evidence:p3.coal602_consensus_qc -->

### 5.2 Full support versus matched subset

The stabilized full-support three-layer comparison gave raw mean thickness MAE 45.623 m and relative absolute volume error 0.1387. Rereading changed these to 45.350 m and 0.1213. Risk-aware selection used 15/35 documents, gave mean thickness MAE 34.899 m and volume error 0.0821, and removed the one negative-thickness layer observed in raw and reread. Its mean top/bottom support was only 0.387/0.378. <!-- evidence:p3.spatial_sensitivity -->

The matched-subset result changes the interpretation. On the identical 15 documents, raw, reread, and risk-aware thickness MAE was 35.128, 34.670, and 34.670 m, while volume error was 0.0326, 0.0754, and 0.0754. All available raw and reread boundaries on this subset matched the reference exactly; remaining error came from missing ordered positions and interpolation support. Because reread and risk-aware are identical after conditioning on acceptance, the lower full-support risk result cannot be attributed to a further correction. <!-- evidence:p3.spatial_sensitivity -->

The router selected easier records. Accepted documents had raw ordered-boundary MAE 0.000 m and 12/15 exact raw sequences; rejected documents had MAE 19.550 m and 13/20 exact sequences. Accepted records covered 0.636 of the full convex-hull area, whereas rejected records covered 0.946. This selection explains much of the apparent full-support advantage. <!-- evidence:p3.spatial_sensitivity -->

### 5.3 Spatial-support diagnostics

For the first boundary, raw and reread used 34/35 points and retained the reference convex hull. Risk-aware input used 14/35 points, retained a hull-area ratio of 0.636, increased mean nearest-neighbour spacing from about 1.39 km to 3.48 km, and increased mean grid-to-nearest-observation distance from 2.75 km to 4.62 km. Deep boundaries began with only seven and three eligible records, making omission disproportionately influential. <!-- evidence:p3.spatial_sensitivity -->

The IDW sweep did not preserve a universal ranking. On the full reference hull, relative volume error varied across power, neighbour, and grid settings for all three inputs; on the matched hull, raw remained lower than reread/risk across the reported range. The default result is therefore one point on an error–coverage–model-choice surface, not proof that abstention improves volume estimates. <!-- evidence:p3.spatial_sensitivity -->

### 5.4 Leave-one-borehole-out and jackknife sensitivity

At power 2 with all neighbours, reference-input LOO mean absolute error was 47.06 m across 80 ordered boundary targets. Raw and reread also had 80 targets and mean errors 49.84 and 46.62 m; risk had 79 targets and 47.05 m. The risk calculation uses only risk-accepted records as interpolation support but predicts every reference target position for which a surface can be formed; it does not assign risk output to rejected documents. On the matched accepted set, only 34 targets were evaluable—15, 15, 4, and 0 by ordered boundary. Reference LOO was 52.99 m and reread/risk was 48.76 m. Thus the extraction-policy differences are smaller than the baseline interpolation error for this source and model. <!-- evidence:p3.spatial_sensitivity -->

The volume jackknife recomputes every surface after holding out each borehole rather than treating one full-data volume as fixed. Across 35 omissions, relative absolute volume error was 0.1348 [0.0884, 0.1659] for raw, 0.1177 [0.0489, 0.1699] for reread, and 0.0849 [0.0274, 0.1365] for risk-aware input. The broad overlap is more informative than the ordering of three full-data point estimates and reinforces the sensitivity conclusion. This spread is reported separately from pointwise LOO and document bootstrap, separating support sensitivity from perturbation-seed and model-choice variability.

### 5.5 Controlled error classes

Boundary displacement at 25% prevalence increased surface MAE from 0.0158 m at 0.10 m displacement to 0.1684 m at 1.00 m. Moving 25% of coordinates produced 0.0715, 0.2804, and 1.5641 m MAE at 25, 100, and 500 m. Missing one boundary in 10%, 25%, and 50% of records reduced aggregate support to 0.950, 0.888, and 0.775 and produced 2.474, 4.284, and 8.621 m MAE despite zero boundary error among retained values. At 50% prevalence, merge, split, and duplicate conditions produced 40.957, 30.747, and 20.663 m MAE because ordered positions shifted. These are within-class dose responses and mechanism demonstrations, not a ranking of real-world frequency or severity. <!-- evidence:p3.controlled_error_classes -->

## 6. Discussion

Value error and support loss are distinct. The 602-record controlled experiment shows that agreement between two synthetically perturbed channels can remove enough real spatial support to worsen a surface. The 35-document experiment shows the complementary selection effect: risk-aware full-support error appears lower because it retains a small, easier, spatially narrower subset. Conditioning on that subset eliminates any extra risk-versus-reread benefit and reverses the raw-versus-reread volume ordering.

Spatial-model uncertainty is not a nuisance to be hidden. The IDW sweep and 47.06 m reference-input LOO error show that interpolation and sparse deep support can dominate the differences among extraction variants. An upstream improvement smaller than this baseline should not be presented as validated geological improvement.

Limitations include one source-agreement family, authoritative rather than page-extracted coordinates/collars, sparse deep boundaries, ordered-index alignment without geological-unit correlation, and no faults or anisotropy. The controlled error conditions do not estimate real error prevalence. The analysis diagnoses propagation; it does not validate site geology.

## 7. Reproducibility and Data Protection

The public evidence bundle includes transformed spatial inputs for all 35 documents, normalized interval sequences, risk decisions, a documented rigid transform, and scripts that recompute full-support, matched-subset, support, LOO, and jackknife results. Source IDs, absolute spatial origins, text, paths, and PDFs are excluded. The transform preserves distances and therefore permits linkage to a matching public point set; the release is pseudonymized, not proven anonymous, and remains subject to rights and sensitive-location review. All manuscript tables and figures are generated from analysis JSON; public-input recomputation is explicitly distinguished from redrawing frozen outputs.

Software export, Padova coordinate inventory, PyVista smoke checks, page-coordinate coverage, and protocol-only synthetic runs are retained in [Supplementary Material](supplement.md) because they do not change the principal error-propagation estimand.

## 8. Conclusion

Reliable downstream evaluation must consider both value error and spatial support. In the 602-record controlled study, mean fusion of two synthetically perturbed channels preserved support better than strict agreement-based deletion; it is not evidence from two observed readers. On 35 source-agreement documents, the default full-support comparison favoured risk selection, but the matched 15-document comparison did not: risk equalled reread and both had volume error 0.0754 versus 0.0326 for raw. Risk acceptance retained only 0.636 of the reference hull. IDW sensitivity, overlapping volume-jackknife ranges, and 47.06 m reference-input LOO error showed that spatial sampling and model choice were at least as consequential as extraction-policy differences. The defensible conclusion is diagnostic: provenance, support geometry, matched-subset evaluation, and interpolation uncertainty must be quantified before claiming downstream geological benefit. <!-- evidence:p3.spatial_sensitivity --> <!-- evidence:p3.controlled_error_classes -->

## References

Shared bibliography: [../references.bib](../references.bib). Citation verification and permitted claim scope are recorded in [../../docs/literature_evidence.yaml](../../docs/literature_evidence.yaml).


# Linked Supplementary Material

# Supplementary Material for Paper III

## S1. Software and interoperability

GeoLogParser writes SQLite, CSV, JSON, XLSX, Parquet, GeoJSON, GeoParquet, and GeoPackage outputs while retaining field provenance. Unknown or mixed CRSs are rejected rather than silently transformed. VTP and off-screen PNG adapters verify that regular surface outputs can be rendered. These are software checks, not evidence for geological interpretation or a production 3D model.

The Padova coordinate inventory contains 11 source-provided EPSG:4326 points but zero interval records; all coordinates remain needs-review. The quarantined Sanming database smoke test checks table connectivity only. Neither dataset enters the propagation estimand.

## S2. Protocol-only controlled checks

A four-borehole fixture applies the production constraint/rereading ranker before IDW. Errors of 0.01 and 0.05 m fall within the configured tolerance and cause abstention; larger controlled inconsistencies trigger rereading and are corrected when both candidate channels contain the known source value. This verifies the implemented threshold and data path, not real-site effectiveness.

The single-channel 602-record scalar protocol perturbs the source-reported roof-depth field and measures the deterministic IDW response. It does not establish extraction accuracy, the semantics of a coal-seam elevation, privacy clearance, or site geology. The main paper uses two independently and synthetically perturbed channels on the same real structured records because that controlled design isolates support deletion versus support-preserving fusion; the channels are not observed OCR or human readers.

## S3. Page-coordinate coverage

On 88 external Swissgeol documents, the conservative native-text parser emitted one unambiguous coordinate pair for 53 documents. Fifty-one pairs agreed with the database, while two remained unresolved page/database disagreements. The parser abstained on every collar elevation after a predecessor incorrectly accepted drill-rig numbers.

In the 35-document boundary set, page coordinates were available for 17 documents and 15 agreed with the database. Page-coordinate surface variants therefore used about half the spatial support and had substantially higher error than the authoritative-coordinate variant. Because collars remained authoritative and two coordinate disagreements were unresolved, this is a coverage diagnostic rather than a complete page-to-surface workflow.

## S4. Visualization artifacts

PyVista meshes, PNGs, Padova location plots, and structured-source proxy figures are derived visualizations. The quantitative conclusions come from the frozen JSON analyses. A plot does not upgrade a surface proxy to a validated geological model.

## S5. Monte Carlo repeatability

For the 602-record synthetic dual-channel experiment, support-preserving fusion improved over the first perturbed channel in 26–29 of 30 repetitions at each magnitude. Two-sided exact sign-test p values range from 5.77×10⁻⁸ to 5.95×10⁻⁵. These values describe repeatability across perturbation seeds for one dataset and protocol; they are not inference over 30 independent sites or independent real readers.

## S6. Reanalysis boundary

The public spatial input is translated, rigidly rotated, and stripped of absolute origin and source identifiers. Grid construction and polygon area are evaluated in a local coordinate frame so results are invariant to that transform. The public recomputation regenerates the principal support, IDW, LOO, and jackknife diagnostics; this is distinct from redrawing tables from already frozen analysis JSON.

Exact experiment metrics and hashes remain in [current results](generated/current_results.md), the result index, claim registry, and publication-evidence bundle.

# Appendix: Reproducibly Generated Current Results

<!-- AUTO-GENERATED. DO NOT EDIT. -->
# Paper III major-revision tables

## Full-support and strict matched-subset diagnostics

Evidence tier: **Source-agreement reference**. These are surface and volume diagnostics, not validated geological models.

| Estimand | Variant | Documents | Mean thickness MAE (m) | Relative absolute volume error | Mean top support | Mean bottom support | Negative-thickness layers |
|---|---|---:|---:|---:|---:|---:|---:|
| Full support | raw | 35 | 45.623 | 0.1387 | 0.784 | 0.698 | 1 |
| Full support | reread | 35 | 45.350 | 0.1213 | 0.784 | 0.708 | 1 |
| Full support | risk | 35 | 34.899 | 0.0821 | 0.387 | 0.378 | 0 |
| Matched accepted subset | raw | 15 | 35.128 | 0.0326 | 0.894 | 0.850 | 0 |
| Matched accepted subset | reread | 15 | 34.670 | 0.0754 | 0.894 | 0.872 | 0 |
| Matched accepted subset | risk | 15 | 34.670 | 0.0754 | 0.894 | 0.872 | 0 |

## First-boundary spatial support

| Variant | Effective points | Point coverage | Hull-area ratio | Mean nearest-neighbour distance (m) | Mean grid-to-observation distance (m) |
|---|---:|---:|---:|---:|---:|
| raw | 34/35 | 0.971 | 1.000 | 1387.5 | 2745.0 |
| reread | 34/35 | 0.971 | 1.000 | 1387.5 | 2745.0 |
| risk | 14/35 | 0.400 | 0.636 | 3479.5 | 4618.6 |

## Accepted versus rejected document diagnostics

| Risk-router group | Documents | Reference boundaries | Raw available | Raw missing | Raw aligned MAE (m) | Raw exact documents | Hull-area ratio | Mean nearest-neighbour distance (m) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| accepted | 15 | 35 | 30 | 5 | 0.000 | 12/15 | 0.636 | 3080.7 |
| rejected | 20 | 45 | 44 | 5 | 19.550 | 13/20 | 0.946 | 2313.6 |

## IDW and leave-one-borehole-out sensitivity

| Domain | Variant | Relative volume-error range across IDW settings | Default LOO n | Default LOO MAE (m) |
|---|---|---:|---:|---:|
| Full reference | reference | -- | 80 | 47.06 |
| Full reference | raw | 0.122–0.153 | 80 | 49.84 |
| Full reference | reread | 0.092–0.132 | 80 | 46.62 |
| Full reference | risk | 0.033–0.124 | 79 | 47.05 |
| Matched accepted | reference | -- | 34 | 52.99 |
| Matched accepted | raw | 0.021–0.065 | 34 | 48.85 |
| Matched accepted | reread | 0.061–0.098 | 34 | 48.76 |
| Matched accepted | risk | 0.061–0.098 | 34 | 48.76 |

## Default LOO by ordered boundary

| Domain | Variant | B1 n / MAE (m) | B2 n / MAE (m) | B3 n / MAE (m) | B4 n / MAE (m) |
|---|---|---:|---:|---:|---:|
| Full reference | reference | 35 / 23.72 | 35 / 57.56 | 7 / 103.22 | 3 / 65.75 |
| Full reference | raw | 35 / 24.16 | 35 / 64.32 | 7 / 82.43 | 3 / 104.35 |
| Full reference | reread | 35 / 24.27 | 35 / 56.86 | 7 / 82.43 | 3 / 104.35 |
| Full reference | risk | 35 / 30.73 | 35 / 53.52 | 7 / 81.93 | 2 / 97.60 |
| Matched accepted | reference | 15 / 25.51 | 15 / 58.21 | 4 / 136.46 | 0 / -- |
| Matched accepted | raw | 15 / 27.00 | 15 / 59.03 | 4 / 92.60 | 0 / -- |
| Matched accepted | reread | 15 / 27.00 | 15 / 58.84 | 4 / 92.60 | 0 / -- |
| Matched accepted | risk | 15 / 27.00 | 15 / 58.84 | 4 / 92.60 | 0 / -- |

## Leave-one-borehole-out volume jackknife

| Domain | Variant | Replicates | Relative volume error, mean [min, max] | Thickness MAE, mean [min, max] (m) |
|---|---|---:|---:|---:|
| Full support | raw | 35 | 0.1348 [0.0884, 0.1659] | 45.06 [24.12, 54.80] |
| Full support | reread | 35 | 0.1177 [0.0489, 0.1699] | 44.78 [23.95, 54.75] |
| Full support | risk | 35 | 0.0849 [0.0274, 0.1365] | 35.27 [30.51, 44.03] |
| Matched accepted | raw | 15 | 0.0426 [0.0265, 0.0965] | 34.51 [2.67, 53.93] |
| Matched accepted | reread | 15 | 0.0780 [0.0165, 0.1108] | 33.96 [0.76, 53.37] |
| Matched accepted | risk | 15 | 0.0780 [0.0165, 0.1108] | 33.96 [0.76, 53.37] |

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
| P3_COAL602_CONSENSUS_QC_CONTROLLED_001 | 0.01 | 0.000575 ± 0.000147 | 0.731944 ± 0.111704 | N/A | N/A | N/A | N/A | 0.813 | 93 | failure_analysis_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_001 | 0.05 | 0.002874 ± 0.000689 | 0.729222 ± 0.166501 | N/A | N/A | N/A | N/A | 0.816 | 73 | failure_analysis_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_001 | 0.10 | 0.005539 ± 0.001343 | 0.736137 ± 0.128284 | N/A | N/A | N/A | N/A | 0.817 | 74 | failure_analysis_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_001 | 0.50 | 0.029294 ± 0.006825 | 0.743434 ± 0.135452 | N/A | N/A | N/A | N/A | 0.815 | 90 | failure_analysis_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_001 | 1.00 | 0.054885 ± 0.010986 | 0.737065 ± 0.104432 | N/A | N/A | N/A | N/A | 0.817 | 85 | failure_analysis_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_002 | 0.01 | 0.000575 ± 0.000147 | 0.731944 ± 0.111704 | 0.000453 ± 0.000093 | N/A | N/A | N/A | 0.813 | 93 | audit_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_002 | 0.05 | 0.002874 ± 0.000689 | 0.729222 ± 0.166501 | 0.002291 ± 0.000496 | N/A | N/A | N/A | 0.816 | 73 | audit_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_002 | 0.10 | 0.005539 ± 0.001343 | 0.736137 ± 0.128284 | 0.004334 ± 0.000899 | N/A | N/A | N/A | 0.817 | 74 | audit_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_002 | 0.50 | 0.029294 ± 0.006825 | 0.743434 ± 0.135452 | 0.022854 ± 0.004454 | N/A | N/A | N/A | 0.815 | 90 | audit_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_002 | 1.00 | 0.054885 ± 0.010986 | 0.737065 ± 0.104432 | 0.044844 ± 0.005753 | N/A | N/A | N/A | 0.817 | 85 | audit_only |
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

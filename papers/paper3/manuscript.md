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

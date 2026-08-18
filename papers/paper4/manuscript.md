# From High-F1 Vision-Language Extraction to Trustworthy Borehole Databases: Provenance-Grounded Assurance, Selective Risk, and Spatial-Support Diagnostics

## Abstract

Historical borehole columns are not ordinary text documents. A system may read most visible depth pairs correctly while assigning values to the wrong column, omitting a layer, silently changing a number, or producing a database record that cannot be traced back to a page region. This study asks whether a modern vision-language model (VLM) can therefore be converted from a high-recall reader into a trustworthy, selectively deployable geological-document system. We evaluate a frozen `Qwen/Qwen3.8-27B-FP8` direct page-to-JSON baseline on five record-disjoint California cohorts containing 450 reports and 8,268 published manual-transcription intervals, then test transport on source-agreement Swissgeol and BGS panels. The headline interval metric is explicitly boundary-pair interval F1: a predicted interval matches only when both top and bottom depths satisfy the tolerance and order-preserving matcher. The direct VLM obtains boundary-pair F1 0.896–0.932 and 69–74% complete boundary sequences on California, compared with 0.383–0.450 for a frozen positioned-OCR parser. However, the direct interface emits invalid numeric ranges before deterministic rejection (0.004–0.017), does not retain field-level page evidence, and falls to F1 0.577 on the Swissgeol source-agreement panel. We introduce provenance-grounded assurance: an independently positioned reader supplies page-local numeric evidence; a field-aware candidate graph and deterministic geometry decoder enforce ordered depth relations; and a risk policy accepts only complete, non-overlapping, independently supported proposals or abstains. On California v003, the policy converts 0.907 raw proposal precision into selective precision 0.993 [0.984, 1.000] at 0.244 proposal coverage, with 444/447 accepted intervals correct and errors distributed across three documents. Unselective sequence reconstruction improves pooled recovery but produces document harm and action-level false corrections, so it is not treated as safe by default. A downstream diagnostic on 35 source-agreement documents shows why abstention must be evaluated spatially: risk-aware full-support volume error is 0.0821 versus 0.1387 for raw extraction, but risk retains only 0.636 of the reference convex-hull area; on the identical 15-document accepted subset, risk and rereading are identical and both have volume error 0.0754, whereas raw is 0.0326. Reference-input leave-one-borehole-out error is 47.06 m, comparable to or larger than extraction-policy differences. The central conclusion is that modern VLM accuracy is valuable but insufficient: reliable geological databases require provenance, selective acceptance, explicit abstention, and downstream support diagnostics. The study is an evidence-tiered evaluation and deployability analysis, not a claim of universal model safety or a validated production geological model.

**Keywords:** borehole logs; geological document AI; vision-language models; provenance; selective prediction; abstention; source shift; spatial support; interpolation uncertainty; structured extraction

## Highlights

- A modern VLM reaches 0.896–0.932 boundary-pair interval F1 on five California cohorts, but high F1 does not establish auditable database records.
- Independent positioned evidence and deterministic geological sequence checks yield 0.993 selective precision at 0.244 coverage on a held-out cohort.
- Abstention changes spatial support: the apparent full-support volume gain disappears on an identical accepted subset.
- Provenance, acceptance policy, and downstream support must be evaluated together for geological document deployment.

## 1. Problem and research questions

Digitizing historical borehole logs is often described as an OCR problem. That description is operationally incomplete. A typical log combines a depth scale, cumulative boundary or thickness columns, sampling marks, lithology symbols, free-text descriptions, water-level annotations, and report metadata. The same number may be a top boundary, a bottom boundary, a sample depth, or a scale tick depending on its column and vertical context. A parser can therefore achieve a favourable character or interval score while creating an unusable geological record.

The central problem addressed here is the gap between visual extraction and trustworthy database acceptance. A trustworthy record must satisfy four conditions. First, the predicted interval sequence must be numerically coherent and sufficiently complete. Second, each critical value must retain provenance to a source page and region. Third, the system must distinguish a plausible proposal from an automatically acceptable update. Fourth, abstention must be assessed as a change in downstream support rather than treated as a harmless missing value.

Modern VLMs make the first condition substantially easier on familiar page families. They can associate typography, lines, symbols, and prose without a separate OCR pipeline. That capability changes, rather than eliminates, the scientific question. If a direct VLM produces high boundary-pair F1 but no field-level bbox, no calibrated acceptance state, and no independent evidence, a database curator cannot tell which records are safe to ingest. Conversely, a conservative system may reduce false corrections by rejecting difficult pages while deleting the spatial observations needed for a surface or volume diagnostic. The paper therefore evaluates extraction, assurance, and downstream consequence as one chain.

We retain exactly three research questions:

**RQ1 — Extraction reliability under cohort and source shift.** How stable are boundary-pair interval predictions, complete boundary sequences, and semantic/full-record outcomes across independent cohorts from the same publication program and across unrelated source families?

**RQ2 — Provenance-grounded selective assurance.** Can independent positioned evidence, field semantics, deterministic depth geometry, and geological constraints convert high-recall VLM proposals into auditable selective decisions with low critical error and explicit abstention?

**RQ3 — Downstream consequence of extraction error and abstention.** How do value errors, missing or altered ordered boundaries, and risk-driven support deletion propagate to spatial support, interpolated surfaces, and volume diagnostics?

The contributions are deliberately integrated rather than three separate benchmark claims:

1. an evidence-tiered multi-cohort evaluation showing that modern VLM extraction can be strong on a familiar source family and still transport poorly or lack auditability;
2. a provenance-grounded assurance stack whose VLM is a high-recall proposal reader, while independent positioned evidence and deterministic sequence reasoning control automatic acceptance;
3. a document-level risk and coverage analysis that distinguishes F1 improvement from harmful correction and makes abstention measurable;
4. a matched-subset and spatial-support diagnostic demonstrating that a lower full-support volume error may be caused by retaining an easier, spatially narrower subset rather than correcting values; and
5. a reproducible evidence bundle with exact model, prompt, rendering, parsing, split, and source provenance records.

The three original manuscripts remain frozen as fallback analyses. This article is a new integrated manuscript: Paper I supplies the reliability and source-shift evidence, Paper II supplies the assurance method and risk policy, and Paper III supplies only the downstream results needed to test the consequences of acceptance and abstention.

## 2. Related work and positioning

Document OCR and layout benchmarks have established that text recognition, region detection, and table topology are separable tasks [@smith2007tesseract; @xu2020layoutlm; @xu2021layoutlmv2; @zhong2019publaynet; @pfitzmann2022doclaynet; @smock2022pubtables]. OCR-free document models and high-resolution VLMs demonstrate that pixels, visual context, and language can be fused without an explicit OCR transcript [@kim2022donut; @hu2024docowl2]. These advances motivate a modern direct-VLM baseline, but generic document metrics do not encode ordered geological intervals, depth units, column ownership, missing sequence elements, or source-region provenance.

Direct borehole-log studies are more task-specific but typically use a single template, a small number of pages, or a structured target without an explicit acceptance policy. Zhang et al. evaluate 100 same-specification borehole images [@zhang2020boreholeimages]; Han and Suh classify 908 pages from 47 Korean reports before structuring one page family [@han2024boreholeocr]; Amini et al. separate PDF discovery, selection, and data capture in a geological survey workflow [@amini2023boreholepdf]; Ma et al. report extraction from 160 historical well records and identify image-based difficulty [@ma2024historicalwell]; and Shiga evaluates a VLM workflow on 12 pages from 10 Japanese boreholes [@shiga2026boreholevlm]. These studies establish feasibility, but they do not jointly report source-disjoint transport, complete-record exactness, independent evidence anchoring, abstention, and downstream support.

The closest geological metric work is Garzón et al., who evaluate automated stratigraphic interpretations of 1,394 already structured boreholes using geology-informed sequence and spatial measures [@garzon2026stratigraphicmetrics]. Our study operates one stage earlier. Before a stratigraphic interpretation can be evaluated, an interval must be grounded to the correct page region and assigned to the correct numerical and semantic columns. This distinction is central: a valid monotone sequence can still be the wrong sequence if it came from a depth-scale or sample column.

Selective prediction and calibration provide the statistical language for abstention [@geifman2017selective; @geifman2019selectivenet; @guo2017calibration; @angelopoulos2024crc]. We adapt that language to a clustered geological setting. Documents, rather than individual actions, are the primary safety unit because one report may contribute many correlated additions. A zero observed harmful action is therefore reported with a finite-sample document bound, not as a safety certificate. Interpolation and borehole-density studies likewise show that spatial support and model choice can dominate apparent downstream improvements [@shepard1968interpolation; @lark2014crosssection; @pakyuzcharrier2018drillhole; @wellmann2018uncertainty; @tran2025boreholedensity; @zhang2026boreholedensity].

The work is positioned as a trustworthy document-to-database study for geoscience computing. The novelty is not a claim that one VLM is universally superior. It is the explicit coupling of (i) modern VLM proposal recall, (ii) independent page-grounded evidence, (iii) geological sequence decoding and risk acceptance, and (iv) downstream spatial-support diagnostics.

## 3. Evidence, data, and task definition

### 3.1 Evidence tiers

The evaluation separates evidence types before any metric is calculated.

| Evidence type | Meaning | Claims supported here |
|---|---|---|
| Published manual-transcription Gold | External institution transcribed source images and applied reported QC | Formal boundary-pair and semantic extraction accuracy within that release |
| Source-agreement reference | An explicit page table agrees with an authoritative database sequence | Source-specific transfer and downstream consistency, not representative human image GT |
| Authoritative metadata | Official IDs, coordinates, collars, or final-depth fields | Field agreement and spatial-support diagnostics |
| Machine Silver | Multiple machines or deterministic rules construct a reference | Agreement and development analysis only |
| Audit/no reference | No independent target | Coverage, runtime, schema validity, and failure mechanisms |

Synthetic records are a separate controlled class with programmatically known labels. Evidence tiers are never pooled into a single accuracy estimate. In particular, source-agreement panels are not described as newly annotated human Gold, and synthetic dual-reader experiments are not described as two observed readers.

### 3.2 Primary California cohorts

The primary accuracy evidence is the USGS California lithology release and its paired public report links [@haugen2025californialithology; @borkovich2025californiawcr]. The publisher's metadata describes manual transcription from well-completion-report images, preservation of reported wording, and checks for sequencing, gaps, and final-depth completeness. The project formed mutually record-disjoint freezes v001–v005. The formal evaluation contains 450 reports and 8,268 intervals: v001 contributes 50 test reports and 697 intervals, while v002–v005 contribute 100 reports each and 1,770, 1,788, 1,944, and 2,069 intervals.

The selection flow begins with 12,732 deterministically paired reports and 225,150 exact-deduplicated intervals. Filters retain reports with 5–60 intervals, empty source comments, and adjacent continuity at least 0.99. County-diverse acquisition and record-disjoint freezing define the five cohorts. The resulting data are useful for independent replication but are not a random sample of every California log; the moderate interval-count and continuity filters are reported as part of the estimand.

### 3.3 Source-shift panels

The Swissgeol Thurgau held-out panel contains 35 source-agreement documents and 80 explicit top/bottom intervals. It is selected from pages whose published table agrees with the official database and is therefore a transfer panel rather than a national Gold benchmark. BGS Offshore contains 26 historical source groups and 341 graphic-log intervals joined from official survey, scan, and geology layers. Raft River contributes two reports with 62 explicit interval rows. These panels stress different page lengths, typography, scan quality, and column semantics. A one-time unseen BGS source-family run is reserved for the external risk gate and never used for tuning.

### 3.4 Structured spatial support

The downstream analysis uses the 35 Swissgeol documents and their authoritative coordinates/collars after extraction decisions are frozen. The 35 documents contain 80 ordered boundaries with sparse support at depth. A separate 602-record structured-source dataset is used only for controlled support-preservation experiments. Its coordinates and one source scalar are real structured records; two reader channels are generated by independent synthetic perturbation. No second OCR system or human reader is observed. This distinction prevents the controlled experiment from being mistaken for an image-extraction benchmark.

### 3.5 Task output and headline metric

The output schema stores borehole metadata, ordered intervals, raw and normalized terminology, page and bbox provenance, extraction method, confidence, validation state, and warnings. The headline interval metric is **boundary-pair interval F1**. Given reference intervals (G) and predictions (P), a prediction matches only when both top and bottom depths fall within the inclusive tolerance after unit conversion, under order-preserving maximum-cardinality matching with minimum total error as the tie-break. A single correct top boundary or a syntactically valid JSON object is not an interval match.

Boundary-exact rate requires the complete ordered boundary sequence for a document. Full-record exact additionally requires the evaluated semantic fields to agree. Matched lithology exact is reported when the reference and output contain comparable lithology fields. The direct Qwen evaluation schema and archived metrics do not include a validated lithology/full-record adjudication for every proposal; we therefore report boundary-pair F1 and boundary-exact for that model and explicitly mark semantic/full-record correctness as unavailable rather than infer it from JSON validity. The positioned OCR baselines provide matched-lithology and full-record exactness as a complementary lower-level diagnostic.

## 4. Methods: provenance-grounded selective assurance

### 4.1 Modern VLM proposal reader

The open modern baseline is the official `Qwen/Qwen3.8-27B-FP8` checkpoint [@qwen2026qwen38]. It is served as `qwen38-fp8-tp4-mtp4-long`; the frozen local revision is `local_Qwen3.8-27B-FP8_qwen3_5_architecture_fp8_e4m3`. The recorded component hashes are: `config.json` `74227dd615bf1ea975aa676bdf355a0379858c12f394b5365cd9dfa5fc2c70bc`, `preprocessor_config.json` `27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516`, and `model.safetensors.index.json` `f0838c766951bdfe76d6afbdb2771a8f67aaa2231dedb3d33cebd817729843a2`. The weights use fine-grained dynamic FP8 E4M3. Inference runs through a vLLM-compatible OpenAI server on four RTX 2080 Ti GPUs; the server did not expose a package version, so no version is inferred.

Pages are rendered at 200 DPI with PyMuPDF to lossless PNG, without crop, rotation, or enhancement. The prompt is `vlm_interval_source_units_v002`, SHA-256 `891bc6beb7ff9cf35c55389191a208c9b09e9e2dc76909f716603f413745104a`. Decoding uses temperature 0, provider-default top-p, thinking disabled, a 4,096-token maximum, zero automatic retries, and strict JSON parsing. No repair, reordering, deduplication, or reference-conditioned completion is performed. Non-finite or non-positive ranges are rejected during deterministic source-unit conversion. This protocol was frozen before each cohort result.

The VLM returns interval proposals (V=(v_1,ldots,v_n)). It is intentionally treated as a reader that proposes visible structure, not as an authority that can directly write a database. This separation allows the paper to evaluate the value of modern visual semantics without granting the model unobserved provenance or acceptance authority.

### 4.2 Independent positioned evidence

An independently frozen RapidOCR positioned parser produces candidates (C=(c_1,ldots,c_m)). Each candidate retains page index, normalized top and bottom column positions, y-order, OCR confidence, geological-term evidence, source text, and the original region bbox. The VLM and positioned parser do not exchange outputs. A proposal and positioned candidate are eligible for evidence agreement only when their top and bottom depths agree under a strict source-unit tolerance and the candidate retains both source regions.

The numeric anchor is weaker than semantic ownership: finding the same number somewhere on a page does not prove that it is the interval boundary. Automatic acceptance therefore requires complete top-bottom interval agreement, monotone order, non-overlap, positive thickness, and retained bboxes. Partial agreement is recorded as a proposal for review, not as a complete accepted interval.

### 4.3 Field-aware candidate graph and deterministic geometry

The positioned parser supplies candidates

\[
c_i=(t_i,b_i,p_i,y_i,x_i^t,x_i^b,e_i,q_i),
\]

where (t_i,b_i) are source-unit depths, (p_i) is page position, (y_i) is vertical order, (x_i^t,x_i^b) are normalized column coordinates, (e_i) is evidence text, and (q_i\in[0,1]) is normalized OCR confidence. Candidates require (0\le t_i<b_i\le5000) ft and a geological description. The raw node score is

\[
r_i=1+q_i+\mathbb{1}[\text{geological term in }e_i].
\]

The shallow-start prior is charged only at path initiation:

\[
I_i=r_i-0.0005t_i.
\]

An edge (i\rightarrow j) is admissible when page order increases, (t_j\ge t_i), and (b_i-t_j\le1) ft. The edge score is

\[
e_{ij}=\operatorname{continuity}(|b_i-t_j|)
-4(|x_i^t-x_j^t|+|x_i^b-x_j^b|)
-0.15\max(0,p_j-p_i-1),
\]

where the continuity term rewards gaps at most 0.05 ft, gives a decreasing score through 1 ft, and penalizes larger gaps. Dynamic programming selects

\[
F(j)=\max\left(I_j,\max_{i<j:i\rightarrow j}\{F(i)+r_j+e_{ij}\}\right),
\]

with path length as the tie-break. Depth conversion, thickness, and unit checks are deterministic after selection. This decoder provides a reproducible geometry layer even when the VLM has emitted a plausible but ambiguous proposal.

### 4.4 Selective risk policy

The unselective path is useful for recovery analysis but is not automatically safe. The addition-only policy keeps every first-pass interval immutable and considers only supported additions. A proposal is accepted when (r_c\ge2.999), its open depth interval does not overlap an existing or previously accepted interval, all source bboxes are retained, and the resulting sequence remains monotone and non-overlapping. Otherwise the proposal receives `NEEDS_REVIEW` and the raw record is preserved. Since (q_i\in[0,1]), the threshold requires a geological-term indicator and confidence approximately 0.999 or higher. The threshold was selected from v001/v002 development outcomes; v003–v005 were not used for threshold selection. The document is the primary risk unit, with action-level FCR reported secondarily.

For (n) accepted documents and zero observed worsened documents, the one-sided 95% upper bound is (1-0.05^{1/n}). This is a finite-sample statement under the declared document sampling unit, not a safety certification. Coverage is measured both as accepted actions divided by proposals and as accepted documents divided by documents containing a proposal. Critical numerical errors include invalid, non-finite, non-positive, or unit-inconsistent depth values; false correction means that an automatic change introduces an unmatched interval or removes a previously matched interval.

### 4.5 Spatial consequence protocol

For boundary (r) in borehole (i), elevation is (z_{ir}=c_i-d_{ir}), where (c_i) is collar elevation and (d_{ir}) is depth. IDW at query location (u) is

\[
\hat z_r(u)=\frac{\sum_{i\in N(u)}\lVert u-u_i\rVert^{-p}z_{ir}}{\sum_{i\in N(u)}\lVert u-u_i\rVert^{-p}}.
\]

Thickness is the difference between adjacent surfaces. For a hull-clipped grid (G), the volume diagnostic is (\hat V_\ell=A|G|^{-1}\sum_{u\in G}\hat h_\ell(u)), and aggregate relative absolute volume error is

\[
\frac{\sum_\ell|\hat V_\ell-V_\ell|}{\sum_\ell|V_\ell|}.
\]

We report two estimands. Full-support comparison lets each extraction policy use its own available points; it measures the deployed package, including selection. Matched-subset comparison restricts raw, reread, and risk-aware inputs to the same 15 accepted documents; it measures value/sequence differences conditional on acceptance. If risk and reread are identical on this subset, any full-support difference is selection and support, not an additional correction. Spatial diagnostics include point coverage, convex-hull area ratio, nearest-neighbour distance, grid-to-nearest-observation distance, IDW power/neighbour/grid sensitivity, leave-one-borehole-out error, and volume jackknife.

## 5. Experimental protocol and reproducibility

All California cohorts are project- and record-disjoint. The direct Qwen protocol is fixed before evaluation, and no Gold error case changes prompt, decoder, matcher, threshold, or model roster. Source-shift panels are scored with their declared evidence tier. Swissgeol development and held-out roles are separated by salted PDF-content groups. The BGS v003 external run is opened once after the development gate and its result is not used for tuning.

The direct-VLM baseline, positioned parser, sequence decoder, risk policy, and spatial diagnostics are deterministic given the frozen page renders, candidate pools, configuration files, and seeds. Document-cluster bootstrap resamples whole reports. The 602-record error study uses 30 perturbation seeds per condition; these are repeatability replicates at one spatial source, not independent sites. Public release metadata records source URLs, exact manifests, hashes, evidence tiers, and archive checksums. Source PDFs and transformed inputs are distributed under the project release policy; provenance and final rights checks remain explicit in the ledger.

## 6. Results

### 6.1 A modern VLM changes the extraction benchmark

On the five California cohorts, Qwen3.8-27B-FP8 obtains boundary-pair interval F1 of 0.932, 0.896, 0.918, 0.917, and 0.903. Its document-cluster 95% intervals are [0.888, 0.973], [0.841, 0.943], [0.878, 0.953], [0.876, 0.952], and [0.864, 0.939]. Complete boundary sequences occur in 74%, 70%, 72%, 74%, and 69% of documents. Zero-output rates are 0, 0, 0, 0.05, and 0.01. The corresponding frozen RapidOCR parser obtains 0.390, 0.450, 0.383, 0.428, and 0.389, with zero-output rates of 0.08–0.23 and full-record exactness of 0–2% in the available evaluated fields. The paired document-cluster F1 gains of Qwen over RapidOCR are 0.542, 0.445, 0.535, 0.489, and 0.514; every bootstrap probability that the gain is positive is 1.000.

The direct VLM is therefore not a failure case. It recovers visually implicit structure that the positioned parser misses. However, JSON-validity is not provenance. Before deterministic rejection, invalid numeric ranges occur at 0.004–0.017 across the five cohorts. The direct output contains no retained field bbox, no independent column-ownership witness, no calibrated acceptance state, and no auditable constraint trace. The headline F1 is a boundary-pair metric; it does not establish lithology correctness or complete semantic records. In the RapidOCR reference, matched lithology exactness ranges from 0.431 to 0.544 across the five cohorts, and full-record exactness remains 0–2%; these values illustrate why boundary recovery and semantic/full-record correctness must be reported separately.

### 6.2 Source shift reveals the missing assurance layer

Qwen's F1 on the Swissgeol source-agreement panel is 0.577 with zero boundary-exact documents, despite JSON validity of 1.000. RapidOCR and Tesseract on the same selected Thurgau panel obtain 0.679 and 0.857 respectively, while source-disjoint five-canton transfer falls to near zero for both conservative parsers. BGS offshore historical logs yield interval F1 0.038 for RapidOCR and 0.041 for Tesseract. Raft River's two explicit tabular reports yield F1 0.831 and 1.000 for Tesseract and RapidOCR. These source-specific outcomes are not pooled as one benchmark score. They show that source shift changes which representation is useful: direct visual semantics help on one family, while explicit tables and column geometry dominate another.

The one-time BGS v003 external gate is even more informative operationally. The converged routed parser classified all five visible pages as unsupported and abstained, giving zero utility but also no false positive or critical numerical error. This is a defensible transport outcome for a deployable system: unsupported pages should enter a review queue rather than produce an apparently complete database record. It is not evidence of universal generalization.

### 6.3 Independent evidence converts proposals into selective decisions

The assurance experiment keeps the Qwen proposals unchanged and adds an independently positioned reader. On development v001, complete positioned agreement covers 174/736 proposals and all are correct. On validation v002, 561 proposals are accepted at precision 0.979 [0.951, 0.997], compared with raw proposal precision 0.854. On held-out v003, the frozen rule accepts 447/1,833 proposals: 444 are correct, selective precision is 0.993 [0.984, 1.000], raw proposal precision is 0.907, and accepted coverage is 0.244. The three incorrect accepted intervals occur in three different documents. Numeric-anchor coverage is higher (0.845), confirming that finding a number is easier than proving semantic ownership.

The selective result is intentionally not reported as whole-document accuracy. Partial proposal acceptance cannot establish complete-record correctness, and non-accepted proposals remain in the review queue. The method's benefit is a reliable subset with explicit provenance, not an assertion that the unaccepted 75.6% are correct. This distinction is operationally important when a database ingestion job must state which rows were automatically accepted and which require review.

### 6.4 Sequence reconstruction improves recovery but can create harm

On the same candidate pools, unselective sequence ranking increases California interval F1 from 0.383–0.450 to 0.470–0.566. The gain is driven primarily by monotonic path selection: on v004/v005, monotonic decoding reaches F1 0.579/0.550, while adding continuity, column stability, and the semantic bonus moves the operating point toward precision without a consistent F1 gain. This is a useful explanation of the method rather than a claim that every constraint helps.

The recovery gain is not automatically safe. Unselective reconstruction produces action-level FCR 0.084–0.210 across the five cohorts and lowers document F1 on multiple reports. The addition-only policy accepts 43 additions on v004 and 39 on v005, for 82 actions in 19 documents. No accepted action is incorrect and no document is observed to worsen, but the primary one-sided document-level 95% upper risk bound is 0.1459. The action-level iid bound is smaller and secondary because actions cluster within reports. The policy yields a net gain of 41 matched intervals per 100 documents, compared with 230.5 under unselective reconstruction. The correct interpretation is a safety–recovery frontier: automatic acceptance is reliable on a small subset, while most potential recovery remains review or abstention.

### 6.5 Abstention changes spatial support and can reverse a downstream conclusion

On the 35-document source-agreement panel, full-support raw, reread, and risk-aware inputs produce relative absolute volume errors 0.1387, 0.1213, and 0.0821, with mean thickness MAE 45.623, 45.350, and 34.899 m. A superficial reading would call risk-aware selection an improvement. It would be incomplete. Risk accepts 15/35 documents and retains only 0.636 of the reference convex-hull area for the first boundary. Mean nearest-neighbour distance rises from approximately 1.39 km to 3.48 km, and mean grid-to-nearest-observation distance rises from 2.75 km to 4.62 km. Accepted documents have raw aligned boundary MAE 0.000 m and 12/15 exact raw sequences; rejected documents have 19.550 m and 13/20 exact sequences. The router selects easier and spatially narrower records.

The matched-subset estimand removes this selection difference. On the identical 15 accepted documents, raw, reread, and risk-aware thickness MAE are 35.128, 34.670, and 34.670 m, while volume error is 0.0326, 0.0754, and 0.0754. Reread and risk are identical after conditioning on acceptance. The lower full-support risk error therefore cannot be attributed to an additional correction; it is a consequence of selection and changed support. IDW sensitivity yields overlapping ranges, and reference-input leave-one-borehole-out MAE is 47.06 m across 80 targets. Full-support volume jackknife means are 0.1348 [0.0884, 0.1659] for raw, 0.1177 [0.0489, 0.1699] for reread, and 0.0849 [0.0274, 0.1365] for risk-aware input. The overlap is more scientifically informative than the ordering of three full-data estimates.

The 602-record controlled study provides a complementary mechanism result. Strict agreement-based deletion of two synthetically perturbed channels retains only about 0.813–0.817 of points and can worsen surface error by removing support. Support-preserving mean fusion improves 26–29 of 30 perturbation repetitions at each tested magnitude. Because the channels are simulated, this does not validate two readers or a geological interpretation. It does show why a deployed risk policy should track both value confidence and the support cost of abstention.

### 6.6 Evidence states make the system auditable

The integrated pipeline exposes a finite state for every proposed interval and every document. At the interval level, a record can be `PROPOSED` (VLM output only), `LOCATED` (a numeric value is found in a positioned source region), `OWNED` (top and bottom values agree with the same semantic column and retain both bboxes), `ACCEPTED` (all sequence and risk conditions pass), or `NEEDS_REVIEW` (evidence is incomplete, conflicting, or unsupported). At the document level, the corresponding states are `PROCESS`, `SELECTIVE_ACCEPT`, `ABSTAIN_UNSUPPORTED`, and `REVIEW_QUEUE`. The raw proposal is immutable across transitions.

This state machine prevents three common evaluation errors. First, it prevents a page with valid JSON from being counted as a complete record when only one field is supported. Second, it prevents an automatically rejected proposal from disappearing: the value, source page, and reason for abstention remain available for human review. Third, it prevents downstream users from confusing an accepted subset with the original population. The spatial analysis receives both the accepted point set and a support mask, so an analyst can see whether a lower error comes from corrected values, retained observations, or a smaller domain.

The execution provenance is similarly explicit. The open VLM row records official checkpoint name, served model ID, local revision string, component hashes, FP8 format, server interface, GPU hardware, prompt version/hash, render DPI, pixel format, temperature, top-p behavior, token limit, retry count, JSON policy, and test date. The positioned reader row records OCR package and model versions, parser revision, and source-region hash. The assurance row records the candidate-matching tolerance, risk threshold, and acceptance policy. A result without one of these fields is retained as an exploratory or transport record rather than silently promoted to the main comparison.

This separation is especially important for foundation models. Model names may refer to a moving endpoint, a locally modified checkpoint, or a server alias. Reporting only “Qwen direct” would not identify the evaluated object. Reporting the official model ID and local hash does not eliminate contamination or provider drift, but it makes those limitations inspectable and prevents an unreproducible product label from becoming the scientific baseline.

### 6.7 What the hybrid system contributes beyond a modern VLM

The comparison is asymmetric. Qwen contributes high-recall visual reading, especially when borders, symbols, or typography are difficult for OCR. GeoLogParser contributes independent positioned evidence, explicit semantic ownership, deterministic source-unit geometry, ordered sequence reasoning, an immutable raw record, an acceptance/abstention state, a review queue, and downstream support accounting. These components are not interchangeable with a high F1 score.

The evidence also suggests a practical division of labour. A VLM can generate broad candidates and identify visually implicit descriptions. A positioned reader can verify whether the exact numerical values occur in the expected columns and retain bboxes. The deterministic decoder can reject crossed or overlapping intervals and calculate thickness without allowing a generative model to invent arithmetic. The risk policy can accept only proposals that satisfy both visual and geometric evidence, while unsupported page families are routed to review. This architecture uses the VLM where it is strong and preserves deterministic, auditable control where a database needs evidence rather than plausibility.

## 7. Limitations and threats to validity

First, the five California cohorts are independent but come from one publication program. They establish cohort stability, not universal national or multilingual generalization. Swissgeol and BGS are source-agreement or stress panels with different evidence tiers, and their results must not be pooled with California Gold. The BGS zero-utility external result is a transport diagnosis, not a claim that all BGS pages are unsupported.

Second, direct-VLM semantic correctness is incompletely observed. The Qwen interface was scored for boundary-pair interval F1, boundary-exactness, numeric invalidity, and transport. The archived direct-VLM protocol does not provide a validated lithology/full-record target for every proposal, so semantic correctness cannot be inferred from JSON validity or boundary matching. Future releases should add field-level semantic adjudication with the same evidence hierarchy.

Third, foundation-model contamination cannot be ruled out. California report identifiers, lithology strings, and public USGS tables may have appeared in pretraining data. Record-disjoint and source-disjoint splits reduce ordinary leakage, but they do not establish that the model has never seen the source family. The Qwen checkpoint, revision fields, component hashes, prompt hash, render settings, and runtime limitations are therefore reported explicitly, and the results are interpreted as an operational benchmark rather than a contamination-free capability estimate.

Fourth, the provenance layer is conservative and incomplete by design. Independent positioned agreement is not statistical independence when both readers observe the same ambiguous page. A matched bbox proves localization, not geological truth. The 0.993 selective precision result has three errors and a document-level finite-sample bound; it is not safety certification. The direct closed host-managed visual pilot is excluded from headline comparisons because it contains only five pages and lacks provider trace, field bboxes, and complete runtime metadata.

Fifth, the spatial analysis is a diagnostic. Coordinates and collars are authoritative for the selected source-agreement panel, while page-derived coordinates are not fully available. IDW is transparent but not a complete geological modelling workflow. The 602-record perturbation channels are synthetic, and the 30 seeds are not independent locations. Ordered boundary indices are not a substitute for geological unit correlation, faults, anisotropy, or uncertainty-aware 3-D modelling.

Finally, abstention changes the population on which a downstream model operates. Full-support and matched-subset results answer different questions and should both be reported in deployment. A system that improves surface error by discarding difficult, spatially important boreholes may be useful for a conservative review queue but should not be advertised as universally improving geological models.

## 8. Conclusions

Modern VLMs materially improve borehole-log extraction on a familiar source family: `Qwen/Qwen3.8-27B-FP8` achieves 0.896–0.932 boundary-pair interval F1 and 69–74% complete boundary sequences across five California cohorts. That result is important, but it is not the same as a trustworthy geological database. The model's direct interface emits invalid numerical ranges, lacks independent page-grounded evidence and acceptance states, and loses performance under source shift.

Provenance-grounded assurance addresses this gap without discarding modern visual semantics. An independently positioned reader, field-aware candidate graph, deterministic depth geometry, and selective risk policy convert a subset of high-recall VLM proposals into auditable decisions. Held-out California v003 reaches selective precision 0.993 at 0.244 coverage, while unselective sequence reconstruction demonstrates why F1 gains alone are unsafe. The addition-only policy controls observed harm but intentionally sacrifices recovery and leaves most proposals for review.

The downstream analysis establishes the second half of the argument. Abstention is not a neutral null value: it deletes spatial support. Full-support risk-aware volume error appears lower, but matched-subset analysis shows that risk and reread are identical and both worse than raw for that selected subset; the apparent gain is selection and support geometry. Interpolation sensitivity and reference-input LOO error are of the same order as extraction-policy differences.

The resulting deployment principle is simple: use modern VLMs for high-recall visual proposals, require provenance-grounded independent evidence for automatic acceptance, preserve immutable raw outputs, abstain on unsupported structure, and report how acceptance changes downstream spatial support. High F1 is a useful capability indicator. It is not, by itself, a reliability argument for a geological database.

## Data and code availability

The formal source inputs, manifests, splits, hashes, model configuration, prompt hashes, public reanalysis inputs, and recomputation scripts are distributed in the GeoLogParser `data-v001` release and repository. Source-specific attribution, linkage risk, and final rights status remain recorded in the accompanying ledgers. The three original manuscripts remain frozen fallback documents; this integrated manuscript is independently versioned under `papers/paper4/`.

## Declarations

The authors should complete journal-specific authorship, funding, competing-interest, and data-rights declarations before submission. No claim in this manuscript relies on undisclosed human annotation, hidden reference-conditioned tuning, or a closed-model score that lacks a reproducible execution record.

## References

Shared bibliography: [../references.bib](../references.bib).

<!-- AUTO-GENERATED REVIEW BUNDLE. DO NOT EDIT. -->
> Package status: **SUBMISSION_READY_CANDIDATE**
> This bundle combines the versioned manuscript and generated results for review.

# Provenance-Aware Evaluation of Structured Extraction from Heterogeneous Borehole Logs: Multi-Cohort and Cross-Source Evidence

## Abstract

Legacy borehole logs combine numerical boundaries, geological descriptions, and source-specific column conventions; ordinary OCR scores therefore do not establish database reliability. We define a provenance-bearing structured-extraction task and separate five evidence tiers before scoring. The primary accuracy evidence comprises five mutually record-disjoint California cohorts containing 450 reports and 8,268 intervals manually transcribed and quality-controlled by the publishing institution. A fixed RapidOCR parser obtained interval F1 values of 0.383–0.450, with zero-output rates of 8%–23% and exact boundary sequences in only 3%–6% of reports. In contrast, a frozen Qwen3.8-27B-FP8 direct page-to-JSON baseline reached F1 0.896–0.932 and exact boundary sequences in 69%–74% of reports across all five cohorts, while emitting invalid numeric ranges at rates of 0.004–0.017 before deterministic rejection and providing no field-level bbox, calibrated confidence, or acceptance decision under the tested interface. Its performance then fell sharply on a separately tiered Swissgeol source-agreement panel. Other source-shift tests reached F1 0.857 on 35 selected Swissgeol source-agreement documents, 0.0379/0.0405 on 26 BGS historical logs with RapidOCR/Tesseract, and 0.831/1.000 on two Raft River tabular logs with Tesseract/RapidOCR. The evidence overturns a general “direct VLM failure” account but shows that extraction accuracy and database assurance remain distinct. This is a multi-cohort evaluation and source-shift stress test, not a comprehensive multilingual benchmark. <!-- evidence:p1.california_rapidocr_gold --> <!-- evidence:p1.california_external_rapidocr --> <!-- evidence:p1.california_prospective_rapidocr --> <!-- evidence:p1.california_v004_rapidocr --> <!-- evidence:p1.california_v005_rapidocr --> <!-- evidence:p1.modern_vlm_qwen38 --> <!-- evidence:p1.swissgeol_authoritative_interval --> <!-- evidence:p1.bgs_offshore_rapidocr --> <!-- evidence:p1.bgs_offshore_tesseract --> <!-- evidence:p1.raft_river_tesseract --> <!-- evidence:p1.raft_river_rapidocr -->

## 1. Introduction

Borehole logs become useful database records only when numerical boundaries, geological text, layout, and source evidence remain linked. Treating a page as plain OCR text loses column semantics; treating it as unconstrained image-to-JSON generation can conceal omission, hallucination, and provenance loss. The practical question is therefore not merely whether visible characters are recognized, but whether the complete ordered interval record is recovered and remains traceable to the page.

This paper asks four questions. RQ1 measures the stability of one frozen parser across independent batches from the same manually transcribed publication program. RQ2 measures transport across institutions, page families, and acquisition conditions. RQ3 asks when conditional precision and matched-boundary error conceal zero output and incomplete records. RQ4 identifies the error mechanisms responsible for the observed source shift.

The contributions are:

1. a provenance-aware task and evidence hierarchy that prevents manual transcription Gold, source agreement, metadata, Machine Silver, and no-reference audits from being pooled as equivalent evidence;
2. a five-cohort California evaluation with report-cluster uncertainty, complete-document measures, and an explicit selection flow;
3. separately reported Swissgeol, BGS, and Raft River source-shift tests; and
4. a modern direct-VLM comparison showing that high interval F1 can coexist with invalid emitted ranges and absent field-level assurance; and
5. failure analysis showing that omission and column ownership dominate conditional numerical error.

Paper II owns sequence reconstruction and correction-risk policy. Paper III owns downstream spatial propagation. The companion manuscripts reuse only the raw baselines required for their own questions.

## 2. Related Work

Tesseract provides a stable OCR reference layer [@smith2007tesseract]. LayoutLM and LayoutLMv2 combine text and spatial or visual features [@xu2020layoutlm; @xu2021layoutlmv2], while PubLayNet, DocLayNet, and PubTables-1M formalize region and table-topology evaluation [@zhong2019publaynet; @pfitzmann2022doclaynet; @smock2022pubtables]. Donut and DocOwl2 demonstrate OCR-free and high-resolution document modelling [@kim2022donut; @hu2024docowl2]. These methods motivate OCR, positioned-text, and local-VLM reference systems, but none by itself defines borehole interval identity, depth topology, complete-record omission, or field provenance.

Direct borehole-document studies are narrower than the present evidence design. Zhang et al. process 100 same-specification borehole-log images [@zhang2020boreholeimages]. Han and Suh classify 908 pages from 47 Korean reports into five types before structuring one type [@han2024boreholeocr]. Amini et al. evaluate borehole-PDF identification, selection, and capture as separate operational stages [@amini2023boreholepdf]. Ma et al. extract information from 160 historical well records and report greater difficulty on image-based material [@ma2024historicalwell]. Shiga uses a two-stage VLM workflow on 12 pages from 10 Japanese boreholes [@shiga2026boreholevlm]. Garzón et al. evaluate automated stratigraphic interpretations for 1,394 boreholes using sequence and spatial metrics, but begin from structured borehole information rather than page-grounded document extraction [@garzon2026stratigraphicmetrics].

| Closest work | Primary scope | Difference here |
|---|---|---|
| General layout/table benchmarks [@zhong2019publaynet; @pfitzmann2022doclaynet; @smock2022pubtables] | Regions and table topology | Ordered geological intervals, missing output, document exactness, and provenance |
| OCR-free/high-resolution models [@kim2022donut; @hu2024docowl2] | Generic transcription or document reasoning | Evidence-tiered source transport and document-level failure accounting |
| Template-specific borehole extraction [@zhang2020boreholeimages; @shiga2026boreholevlm] | One specification or one source system | Five independent cohorts plus institution-level stress tests |
| Borehole capture and historical-record extraction [@amini2023boreholepdf; @ma2024historicalwell] | Document selection or record extraction | Boundary matcher, zero-output rate, complete-record exactness, and error attribution |
| Borehole interpretation metrics [@garzon2026stratigraphicmetrics] | Quality of structured stratigraphic sequences | Image-grounded extraction and provenance before interpretation |

Dependence-aware validation cautions that records sharing producers, templates, or acquisition conditions are not exchangeable [@roberts2017crossvalidation]. We therefore report each California acquisition separately and never pool weaker source-agreement panels into the Gold estimate. A fixed-prediction random/grouped resampling is retained only in the supplement; because it retrains and retunes nothing, it cannot establish a general split-leakage effect.

## 3. Task and Evidence

The input unit is one borehole panel from PDF, JPG, or PNG. The output follows the versioned borehole Schema: borehole fields, ordered intervals, raw and normalized terminology, and for each field a source page, bbox, source text, extraction method, confidence, validation status, and warning list. Missing evidence remains null. SI values coexist with raw strings and units.

The primary interval fields are top depth, bottom depth, thickness, lithology, and description. The evaluation also records borehole ID, collar elevation, final depth, groundwater depth, and coordinates when a reference exists. A valid JSON object is not automatically a correct geological record.

### 3.1 Evidence hierarchy

| Evidence type | Meaning | Supported claim |
|---|---|---|
| Published manual transcription Gold | An external institution manually transcribed source images and applied reported quality control | Formal extraction accuracy within that publication scope |
| Source-agreement reference | An explicit page table agrees with an authoritative database record | Source-specific agreement, not representative human image GT |
| Authoritative metadata | Official database fields without independent image transcription | Field agreement and coverage |
| Machine Silver | Multi-reader or rule-derived reference | Agreement and training diagnostics only |
| Audit / no GT | No independent target reference | Coverage, candidates, runtime, and failure types only |

Synthetic fixtures are a separate controlled-evidence class. Different tiers are never mixed in one accuracy estimate or performance figure.

## 4. Data and Experimental Design

### 4.1 California manual-transcription cohorts

The principal Gold source is the USGS California lithology release [@haugen2025californialithology]. Its metadata states that staff opened well-completion-report images, manually keyed the reported lithologic intervals without OCR, preserved driller wording, and checked sequencing, gaps, and final-depth completeness. A second USGS release supplies links to redacted reports [@borkovich2025californiawcr].

The deterministic join contained 12,732 reports and 225,150 valid, exact-deduplicated intervals with usable report links. Sequential filters retained 10,961 reports with 5–60 intervals, 10,324 with empty source comments, and 10,085 with adjacent continuity of at least 0.99. County-first and seeded acquisition obtained 460 reports and 8,421 intervals; removing the ten v001 development reports left 450 formal reports and 8,268 intervals in v001–v005. The complete flow is regenerated in the [selection-flow figure](generated/figures/california_selection_flow.png). <!-- evidence:p1.california_replication_statistics -->

The five freezes are mutually record-disjoint. v001 contributes 50 test reports, 77 pages, and 697 intervals after a ten-report development partition. v002–v005 contribute 100 reports each and 1,770, 1,788, 1,944, and 2,069 intervals. Every freeze was fixed before its reported evaluation. These filters define a moderate-interval-count, internally continuous subset; the cohorts are not random samples of every California log.

### 4.2 Cross-source panels

| Source | Evidence tier | Documents | Reference intervals | Role |
|---|---|---:|---:|---|
| California v001–v005 | Published manual transcription Gold | 450 | 8,268 | Primary multi-cohort accuracy |
| Swissgeol Thurgau held-out | Source-agreement reference | 35 | 80 | Selected explicit-table transfer |
| BGS Offshore GeoIndex | Source-agreement reference | 26 | 341 | Historical long-page stress test |
| Raft River well reports | Source-agreement reference (source-explicit table subtype) | 2 | 62 | Independent tabular/column-semantic test |

The Swissgeol set was split by salted PDF-content group into 37 development documents/85 intervals and 35 held-out documents/80 intervals, with no record or PDF-hash overlap. Only explicit top, bottom, and thickness tables are scored. The selection process favours pages whose tables agree with the database, so it is a source-agreement panel rather than representative national Gold. <!-- evidence:p1.swissgeol_authoritative_interval -->

The BGS freeze joins official Activity, Scan, and Geology layers by activity identifier and retains metre-unit rows interpreted from graphic logs. One record per survey/source group produced 26 PDFs, 372 pages, 34 composite-log pages, and 341 intervals across 26 source groups. The ArcGIS terms field states OGL v3.0, while scan footers retain legacy rights wording; original PDFs remain local pending manual item-level rights verification. <!-- evidence:p1.bgs_offshore_rapidocr --> <!-- evidence:p1.bgs_offshore_tesseract -->

The Raft River release contains two reports with 62 explicit From–To–lithology rows on three evaluated pages. Ten other reports contain sampled point-depth descriptions and are excluded from interval scoring. The prediction path uses only declared report pages and fixed normalized crops; references are read after prediction. <!-- evidence:p1.raft_river_tesseract --> <!-- evidence:p1.raft_river_rapidocr -->

Candidate acquisitions, Chinese CAD conversion, no-GT coverage runs, metadata-only robustness, Machine-Silver studies, and tailored single-document checks are documented in [Supplementary Material](supplement.md) and the full result catalogue. They do not enter the four main result groups.

### 4.3 Baselines

The baselines are representative and reproducible, not a state-of-the-art leaderboard. Tesseract 4.1.1 with English language data and page-segmentation mode 11 is retained as a stable CPU OCR reference. RapidOCR-ONNXRuntime 1.4.4 (ONNX Runtime 1.23.2) uses the frozen `ch_PP-OCRv4_det_infer`, `ch_PP-OCRv4_rec_infer`, and `ch_ppocr_mobile_v2.0_cls_infer` models on CPU with four intra-op threads and a deterministic positioned-row parser. The parser detects log headings, constructs same-row From--To hypotheses, selects a stable normalized column pair and vertical run, and requires alphabetic description evidence; it contains no reference-conditioned rule. California pages are rendered at 300 DPI.

The historical local VLM reference is Qwen3-VL-4B-Instruct revision `ebb281ec...`, run in BF16 with SDPA on rendered page images constrained to 200,704--1,003,520 input pixels. Prompt `vlm_extract_california_compact_v001` requests visible intervals only in a fixed JSON schema; decoding is greedy (`do_sample=false`, 512 new-token limit). Schema-valid page intervals are concatenated by report and page order without repair or deduplication. This baseline is retained to document the earlier failure mode, not as a current VLM upper bound.

The modern open-model comparison uses the Apache-2.0 `Qwen/Qwen3.8-27B-FP8`
native vision-language checkpoint [@qwen2026qwen38], served as
`qwen38-fp8-tp4-mtp4-long`, through a local OpenAI-compatible endpoint on four
RTX 2080 Ti GPUs. Its frozen weight format is fine-grained dynamic FP8 E4M3;
the server did not expose a vLLM package version. Every 200-DPI page receives
the same `vlm_interval_source_units_v002` prompt (SHA-256
`891bc6beb7ff9cf35c55389191a208c9b09e9e2dc76909f716603f413745104a`),
temperature 0, provider-default top-p, thinking disabled, and a 4,096-token
completion ceiling. The decoder performs only JSON parsing, source-unit
conversion, and rejection of non-finite or non-positive ranges; it does not
complete, reorder, deduplicate, or reference-condition intervals. No California
Gold page was used to change the prompt, schema, decoder, model roster, or
matcher. MinerU2.5 and PaddleOCR-VL are separately registered document-specialist
interfaces; incomplete runs are not treated as results. The user-provided
closed endpoint served `gpt-5.6-sol` under the requested label
`chatgpt5.6-sol-high`, but its synthetic visual preflight returned HTTP 502 and
no real page was sent. Engine and parser choices, provider revisions, page
hashes, and latency are retained for every completed run.

## 5. Evaluation

Let references be \(G_1,\ldots,G_m\) and predictions \(P_1,\ldots,P_n\). A pair is eligible only when both top- and bottom-depth absolute errors are no greater than the inclusive tolerance \(\tau\). Dynamic programming preserves order and chooses the lexicographic optimum: maximum match cardinality, then minimum total top-plus-bottom error. Missing boundaries cannot match, one prediction cannot match twice, and crossed matches are forbidden.

Interval precision, recall, and F1 use this matching. Boundary MAE is conditional on matched intervals and is always reported with unmatched counts. Boundary-exact means the complete ordered boundary sequence is correct; full-record exact additionally requires the evaluated semantic fields to match. Zero-output rate counts documents with no interval prediction.

Documents are the primary statistical unit. Each cohort's confidence interval is a 20,000-repetition percentile bootstrap over whole reports. Pooled interval totals are descriptive. The main results are generated from frozen analysis JSON in [major-revision tables](generated/major_revision_tables.md).

## 6. Results

### 6.1 California cohort stability

RapidOCR interval F1 across v001–v005 was 0.390, 0.450, 0.383, 0.428, and 0.389. Precision remained 0.737–0.892 while recall remained 0.250–0.311. The document-cluster intervals overlap substantially, but all five cohorts reproduce the same central failure: a conditional high-precision subset coexists with severe omission. The [forest plot](generated/figures/california_cohort_forest.png) shows cohort estimates without treating 8,268 intervals as independent samples. <!-- evidence:p1.california_replication_statistics -->

On v001, RapidOCR emitted 195 intervals and matched 174 of 697 (precision 0.892, recall 0.250, F1 0.390); 11/50 reports had no interval output and 3/50 had an exact boundary sequence. Tesseract emitted 176 and matched 142 (precision 0.807, recall 0.204, F1 0.325). The local VLM produced schema-valid page records but only five interval candidates, none matching Gold. Valid syntax therefore did not imply structural recovery. <!-- evidence:p1.california_rapidocr_gold --> <!-- evidence:p1.california_tesseract_gold --> <!-- evidence:p1.california_vlm_gold -->

On v002, RapidOCR emitted 673 intervals and matched 550 of 1,770 (precision 0.817, recall 0.311, F1 0.450), with output on 92 reports. Tesseract matched 392 of 497 predictions (F1 0.346). The paired report-bootstrap F1 difference was 0.104 [0.016, 0.191]. On v003, RapidOCR matched 449 of 559 predictions (F1 0.383), while Tesseract matched 379 of 507 (F1 0.330); the paired difference interval included zero. Thus the point ordering replicated but was not uniformly decisive. <!-- evidence:p1.california_external_rapidocr --> <!-- evidence:p1.california_external_tesseract --> <!-- evidence:p1.california_prospective_rapidocr --> <!-- evidence:p1.california_prospective_tesseract --> <!-- evidence:p1.california_replication_statistics -->

On v004, RapidOCR emitted 622 intervals and matched 549 of 1,944 (precision 0.883, recall 0.282, F1 0.428), with 23 zero-output reports. The independent v005 freeze emitted 741 intervals and matched 546 (precision 0.737, recall 0.264, F1 0.389); it had 1/100 full-document exact, 4/100 boundary-exact, and 15/100 zero-output reports. <!-- evidence:p1.california_v004_rapidocr --> <!-- evidence:p1.california_v005_rapidocr -->

### 6.2 Modern direct-VLM baseline

Qwen3.8-27B-FP8 changed the empirical picture on the California source family. On v001 it matched 668 of 736 predictions against 697 references (precision 0.908, recall 0.958, F1 0.932); v002--v005 reached F1 0.896, 0.918, 0.917, and 0.903. Document-cluster F1 intervals were [0.888, 0.973], [0.841, 0.943], [0.878, 0.953], [0.876, 0.952], and [0.864, 0.939]. Exact boundary sequences occurred in 37/50, 70/100, 72/100, 74/100, and 69/100 reports. Against the paired frozen RapidOCR outputs, Qwen gained 0.445--0.542 F1 across the five cohorts; every document-cluster 95% interval excluded zero in the generated paired comparison. <!-- evidence:p1.modern_vlm_qwen38 -->

This gain is substantive, not a formatting artifact: zero-output rate was 0, 0, 0, 0.05, and 0.01, and JSON-valid page rate was 0.987–1.000. The v004 transport failures are retained rather than retried. However, the model emitted invalid numeric ranges before deterministic rejection at rates 0.0094, 0.0071, 0.0043, 0.0168, and 0.0107, and the frozen direct-JSON interface returned no field bbox, field confidence, constraint trace, or accept/review decision. These are measured properties of this interface, not claims that the underlying model can never produce grounding under another protocol. The generated [modern-VLM table](generated/modern_vlm_results.md) keeps completed and unavailable model slots separate. <!-- evidence:p1.modern_vlm_qwen38 -->

### 6.3 Source shift

On the 35-document Swissgeol held-out panel, Tesseract predicted 74 intervals and matched 66 of 80 (precision 0.892, recall 0.825, F1 0.857), with 25/35 exact documents. RapidOCR matched 54 of 79 predictions (F1 0.679). The frozen direct VLM produced 45 matched intervals from 76 predictions against 80 source-agreement references (P/R/F1 0.592/0.562/0.577); no document had a complete exact boundary sequence. Its document-cluster F1 interval was [0.535, 0.619]. Both OCR parsers had 0.000 m matched-boundary MAE, but their unmatched counts differed sharply. This is selected source-agreement evidence, not multilingual Gold. <!-- evidence:p1.swissgeol_authoritative_interval --> <!-- evidence:p1.swissgeol_authoritative_interval_rapidocr --> <!-- evidence:p1.modern_vlm_qwen38 -->

The BGS historical domain reversed that apparent transferability. RapidOCR emitted 28 intervals and achieved precision/recall/F1 0.250/0.0205/0.0379; Tesseract emitted 54 and achieved 0.148/0.0235/0.0405. RapidOCR produced zero output on 17/26 documents and missed 334/341 reference intervals; Tesseract produced zero output on 13/26 and emitted 46 spurious intervals. Every document had at least one omission. <!-- evidence:p1.bgs_offshore_rapidocr --> <!-- evidence:p1.bgs_offshore_tesseract --> <!-- evidence:p1.bgs_offshore_error_analysis -->

Raft River exposed a different failure. The Tesseract line parser matched 49 of 56 predictions against 62 explicit intervals (precision 0.875, recall 0.790, F1 0.831) but retained only 4/49 exact normalized lithology strings. Positioned RapidOCR recovered all 62 boundaries and 61/62 lithology strings. Its remaining error assigned a water-column mark to a lithology row, showing that perfect numerical boundaries do not prove semantic column ownership. <!-- evidence:p1.raft_river_tesseract --> <!-- evidence:p1.raft_river_rapidocr --> <!-- evidence:p1.raft_river_error_analysis -->

### 6.4 Failure mechanisms

Across California, the dominant error was omitted rows or whole reports, followed by spurious intervals and corrupted lithology text. On v003, RapidOCR had 12 zero-output reports, 110 spurious intervals, and 205 lithology errors among 449 boundary matches; Tesseract had 15, 128, and 247. Development-set engine ordering did not remove this source dependence. <!-- evidence:p1.california_error_analysis --> <!-- evidence:p1.california_external_error_analysis --> <!-- evidence:p1.california_prospective_error_analysis -->

Four observations explain why conventional summaries are insufficient. First, a conditional boundary MAE of 0.000 m can coexist with hundreds of missing intervals. Second, valid JSON can coexist with zero interval recall. Third, a parser can recover every boundary and still assign evidence to the wrong semantic column. Fourth, a strong direct VLM can recover most intervals while leaving automatic acceptance unsupported by field-level evidence or calibrated risk. We therefore recommend reporting unmatched references, zero-output documents, boundary-exact and full-record-exact rates, semantic-field scores, numerical invalidity, provenance coverage, and acceptance policy beside interval F1.

## 7. Discussion

The Gold evidence is broad across acquisition batches but narrow in institutional origin. The five California cohorts establish stability of one failure pattern within a publication program; they do not constitute a comprehensive international benchmark. Swissgeol, BGS, and Raft River broaden page and source conditions, but their references have different evidential meanings and sample sizes.

The results also caution against model-ranking narratives. Tesseract is not included as a modern accuracy champion but as a reproducible OCR reference. RapidOCR improves some California and Raft River outcomes, yet fails catastrophically on BGS. The historical 4B VLM produced valid syntax without interval recovery, whereas Qwen3.8-27B recovered most California intervals but did not transport equivalently to the Swissgeol source-agreement panel. The paired California result establishes a real visual-understanding gain, not a formatting artifact. It does not establish automatic database delivery: the frozen direct interface still lacks field-level evidence, numerical validity traces, calibrated acceptance, and a review route. The scientifically stable conclusion is therefore not that one architecture always fails, but that raw extraction, source transport, and auditable acceptance are separate axes.

Important threats are California selection filters, source-agreement selection in Swissgeol, the small Raft River document count, BGS page complexity, unavailable independent project annotation, and pending item-level rights verification. The fixed-prediction resampling in the supplement observed no strong random/grouped F1 difference for one frozen parser; because it includes no retraining or retuning, it supports no causal claim about split leakage.

## 8. Reproducibility and Rights

Every indexed run records experiment ID, Git commit, dataset and split versions, model and prompt versions, seed, hardware/software, metrics, predictions, errors, and logs. The public evidence bundle includes all indexed run/metrics files, pseudonymized per-document outputs, record hashes, and scripts that regenerate tables and figures. These projections remove direct identifiers but retain distinctive depth sequences and may be linkable to public source tables; they are not claimed to be anonymous. Source PDFs remain local where redistribution or privacy review is incomplete. The California reference is credited as published USGS manual transcription and is not represented as a new project annotation.

## 9. Conclusion

Five record-disjoint California cohorts totaling 450 reports and 8,268 published manually transcribed intervals yielded RapidOCR F1 values of 0.383–0.450, zero-output rates of 8%–23%, and boundary-exact rates of 3%–6%. A modern 27B direct VLM reached F1 0.896–0.932 on the same five cohorts, refuting any general claim that image-to-JSON models cannot recover these logs; its separate Swissgeol source-agreement result establishes that this California performance is not a general transport claim. Swissgeol, BGS, and Raft River separately exposed source selection, total omission, and semantic-column failure. The deployment conclusion is therefore more demanding than a model ranking: complete-record omission, numerical validity, semantic ownership, document dependence, provenance, and risk-controlled acceptance must be measured separately. <!-- evidence:p1.california_replication_statistics --> <!-- evidence:p1.modern_vlm_qwen38 --> <!-- evidence:p1.bgs_offshore_error_analysis --> <!-- evidence:p1.raft_river_error_analysis -->

## References

Shared bibliography: [../references.bib](../references.bib). Citation verification and permitted claim scope are recorded in [../../docs/literature_evidence.yaml](../../docs/literature_evidence.yaml).


# Linked Supplementary Material

# Supplementary Material for Paper I

## S1. Scope

The main paper reports only the California manual-transcription cohorts and the Swissgeol, BGS, and Raft River source-shift panels. This supplement retains acquisition, eligibility, degradation, CAD conversion, Machine-Silver, metadata-only, and no-reference material. These tracks are useful for reproducibility and failure discovery but do not support the same claims as published manual transcription Gold.

## S2. Candidate-source audits

The Padova acquisition contains 11 PDFs/15 pages under a recorded CC BY 4.0 release. Slopes/Tiber contributes 29 rendered candidates, and SedLog contributes 18 tall native-PDF lithology pages. None has independent human interval reference in this project. Their results are therefore limited to coverage, candidate counts, schema validity, runtime, and failure types.

A Chinese CAD acquisition contains 33 DWGs. Renderer audits identified incomplete graphical-entity coverage, empty rasters, and invalid geometry on some files. Structural handle/text agreement on three priority derivatives did not establish pixel fidelity. These records remain conversion-incomplete and rights-unverified and do not enter any accuracy table.

The annotation service supports distinct tracks, record-hash attestations, and adjudication, but the Padova tasks remain auto proposals. There are zero effective human attestations and no project-created Gold result.

## S3. Secondary source diagnostics

USGS-142 and USGS-144 are tailored single-document checks whose explicit interval lists were recovered after source-specific crop/parser choices. They show software transfer, not representative source generalization. A seven-document Idaho scan audit compares label and numeric-range detection between OCR engines without an independent interval reference; it reports agreement events, not accuracy.

A five-canton Swiss transfer panel contains authoritative database intervals but lacks complete explicit page/database agreement. The frozen Thurgau parser produced candidates on only 2/46 records. Because low agreement may reflect extraction failure, page coverage, or page/database mismatch, this remains an authoritative-metadata stress test rather than Gold accuracy.

BGS first-page metadata and controlled degradation runs evaluate borehole ID and coordinate fields only. They show backend-specific omission and degradation sensitivity but do not establish interval or lithology robustness.

## S4. Machine-Silver and no-GT experiments

The Padova A/B adjudication track produces Machine Silver. Agreement to that reference is not human accuracy, and one participating model contributes to reference construction. Slopes, Tiber, SedLog, Padova, BGS-VLM, and quarantined Chinese runs report only their eligible evidence types. Accuracy metrics are null when no independent reference exists.

## S5. Fixed-prediction resampling

A 100-seed calculation resamples already frozen California predictions. Random-record F1 averaged 0.394±0.021 versus 0.390 on the grouped test. Because neither training nor tuning is rerun, the result means only that this frozen prediction set showed no large resampling difference. It is not evidence for or against the general causal claim that random train/test splits inflate document-model performance.

All exact experiment IDs, evidence tiers, hashes, and outputs remain in [current results](generated/current_results.md), the claim registry, source ledger, and publication-evidence bundle.

# Appendix: Reproducibly Generated Current Results

<!-- AUTO-GENERATED. DO NOT EDIT. -->
# Paper I major-revision tables

## Five California cohorts

Evidence tier for every row: **Published manual transcription Gold**. The statistical unit for confidence intervals is the document; pooled interval counts are descriptive.

| Cohort | Documents | Reference intervals | Predicted | Matched | Precision (95% CI) | Recall (95% CI) | F1 (95% CI) | Zero output | Boundary exact | Full-record exact | Median document recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| California v001 | 50 | 697 | 195 | 174 | 0.892 [0.821, 0.952] | 0.250 [0.176, 0.335] | 0.390 [0.292, 0.489] | 11/50 | 3/50 | 0/50 | 0.200 |
| California v002 | 100 | 1770 | 673 | 550 | 0.817 [0.725, 0.887] | 0.311 [0.246, 0.378] | 0.450 [0.370, 0.526] | 8/100 | 5/100 | 2/100 | 0.222 |
| California v003 | 100 | 1788 | 559 | 449 | 0.803 [0.726, 0.870] | 0.251 [0.192, 0.317] | 0.383 [0.307, 0.460] | 12/100 | 5/100 | 0/100 | 0.149 |
| California v004 | 100 | 1944 | 622 | 549 | 0.883 [0.845, 0.914] | 0.282 [0.212, 0.360] | 0.428 [0.341, 0.513] | 23/100 | 3/100 | 1/100 | 0.143 |
| California v005 | 100 | 2069 | 741 | 546 | 0.737 [0.571, 0.878] | 0.264 [0.201, 0.333] | 0.389 [0.308, 0.472] | 15/100 | 4/100 | 1/100 | 0.127 |

The confidence intervals are 20,000-repetition percentile document-cluster bootstraps. Exact-record columns prevent high conditional precision from hiding whole-record omission.


# Full Indexed Result Catalogue

<!-- AUTO-GENERATED. DO NOT EDIT. -->
### OCR + regex audits

| Experiment | Model | Borehole ID EM | X coverage | X paired MAE | Final-depth coverage | Emitted intervals | s/page | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1_B1_BGS_AUDIT_001 | B1_tesseract_ocr_regex | 3/4 (0.750) | 4/4 (1.000) | 0.000 | 0/4 (0.000) | 1 | 6.369 | audit_only |
| P1_B1_RAPIDOCR_BGS_AUDIT_001 | B1_rapidocr_onnxruntime_ppocrv4_regex | 4/4 (1.000) | 0/4 (0.000) | N/A | 0/4 (0.000) | 0 | 3.525 | audit_only |
| P1_B1_RAPIDOCR_BGS_AUDIT_002 | B1_rapidocr_onnxruntime_ppocrv4_regex | 4/4 (1.000) | 4/4 (1.000) | 0.000 | 0/4 (0.000) | 0 | 3.506 | audit_only |
| P1_METADATA_BGS_TESSERACT_FORMAL_002 | B1_tesseract_ocr_regex | 2/4 (0.500) | 4/4 (1.000) | 0.000 | 0/4 (0.000) | 0 | 3.150 | formal_authoritative_metadata |
| P1_METADATA_BGS_TESSERACT_FORMAL_003 | B1_tesseract_ocr_regex | 29/31 (0.935) | 31/31 (1.000) | 9677.419 | 0/31 (0.000) | 1 | 2.210 | formal_authoritative_metadata |
| P1_METADATA_BGS_RAPIDOCR_FORMAL_001 | B1_rapidocr_onnxruntime_ppocrv4_regex | 31/31 (1.000) | 31/31 (1.000) | 0.000 | 1/31 (0.032) | 0 | 3.815 | formal_authoritative_metadata |
| P1_METADATA_BGS_TESSERACT_FORMAL_004 | B1_tesseract_ocr_regex | 25/31 (0.806) | 31/31 (1.000) | 0.000 | 0/31 (0.000) | 0 | 3.562 | formal_authoritative_metadata |

### Synthetic controlled OCR results (not Real Gold)

| Experiment | Model | Borehole ID EM | Final-depth coverage | Final-depth MAE (m) | Interval P | Interval R | Interval F1 | Matched top MAE (m) | s/page | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_B1_SYNTHETIC_CONTROLLED_002 | tesseract_eng_regex | 23/32 (0.719) | 32/32 (1.000) | 0.000 | 1.000 | 0.709 | 0.829 | 0.000 | 0.379 | audit_only |
| P1_B1_SYNTHETIC_CONTROLLED_001 | tesseract_eng_regex | 0/32 (0.000) | 32/32 (1.000) | 0.000 | 1.000 | 0.709 | 0.829 | 0.000 | 0.383 | failure_analysis_only |

These rows use programmatically known Synthetic labels. They validate controlled extraction and robustness paths but cannot establish performance on Real Gold borehole logs.

### Published manual-transcription Gold interval benchmark

| Experiment | Model | Documents | Counties | Pages | Reference intervals | Predicted intervals | Documents with predictions | Interval P | Interval R | Interval F1 | Matched lithology exact | Boundary-exact documents | s/document | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_CALIFORNIA_WCR_RAPIDOCR_TEST_FORMAL_001 | rapidocr_generic_positioned_interval_parser_v001 | 50 | 48 | 77 | 697 | 195 | 39 | 0.892 | 0.250 | 0.390 | 75/174 (0.431) | 3/50 (0.060) | 9.374 | formal_benchmark |
| P1_CALIFORNIA_WCR_TESSERACT_TEST_FORMAL_001 | tesseract_generic_positioned_interval_parser_v001 | 50 | 48 | 77 | 697 | 176 | 38 | 0.807 | 0.204 | 0.325 | 30/142 (0.211) | 1/50 (0.020) | 8.219 | formal_benchmark |
| P1_CALIFORNIA_WCR_V002_RAPIDOCR_EXTERNAL_FORMAL_002 | rapidocr_generic_positioned_interval_parser_v001 | 100 | 23 | 154 | 1770 | 673 | 92 | 0.817 | 0.311 | 0.450 | 284/550 (0.516) | 5/100 (0.050) | 9.773 | formal_external_benchmark |
| P1_CALIFORNIA_WCR_V002_TESSERACT_EXTERNAL_FORMAL_002 | tesseract_generic_positioned_interval_parser_v001 | 100 | 23 | 154 | 1770 | 497 | 79 | 0.789 | 0.221 | 0.346 | 149/392 (0.380) | 3/100 (0.030) | 9.184 | formal_external_benchmark |
| P1_CALIFORNIA_WCR_V003_RAPIDOCR_PROSPECTIVE_FORMAL_001 | rapidocr_generic_positioned_interval_parser_v001 | 100 | 31 | 154 | 1788 | 559 | 88 | 0.803 | 0.251 | 0.383 | 244/449 (0.543) | 5/100 (0.050) | 9.701 | formal_prospective_external_benchmark |
| P1_CALIFORNIA_WCR_V003_TESSERACT_PROSPECTIVE_FORMAL_001 | tesseract_generic_positioned_interval_parser_v001 | 100 | 31 | 154 | 1788 | 507 | 85 | 0.748 | 0.212 | 0.330 | 132/379 (0.348) | 4/100 (0.040) | 8.454 | formal_prospective_external_benchmark |
| P1_CALIFORNIA_WCR_V004_RAPIDOCR_PROSPECTIVE_FORMAL_001 | rapidocr_generic_positioned_interval_parser_v001 | 100 | 28 | 147 | 1944 | 622 | 77 | 0.883 | 0.282 | 0.428 | 244/549 (0.444) | 3/100 (0.030) | 9.086 | formal_prospective_external_benchmark |
| P1_CALIFORNIA_WCR_V005_RAPIDOCR_EXTERNAL_FORMAL_001 | rapidocr_generic_positioned_interval_parser_v001 | 100 | 35 | 141 | 2069 | 741 | 85 | 0.737 | 0.264 | 0.389 | 297/546 (0.544) | 4/100 (0.040) | 9.329 | formal_external_benchmark |
| P1_B4_QWEN3VL4B_CALIFORNIA_TEST_FORMAL_001R | Qwen3-VL-4B-Instruct_page_aggregate | 50 | 48 | 77 | 697 | 5 | 1 | 0.000 | 0.000 | 0.000 | N/A | 0/50 (0.000) | 0.000 | formal_external_benchmark |
The reference intervals were manually transcribed verbatim by USGS staff from California DWR well-completion-report images and received published depth-sequence and completeness checks. The project did not repeat human review of the 60-document freeze. Metrics therefore evaluate against published manual transcription, while report-image redistribution remains a separate pre-submission check.

### Held-out authoritative source-agreement interval result

| Experiment | Model | Documents | Reference intervals | Predicted intervals | Interval P | Interval R | Interval F1 | Matched top MAE (m) | Matched bottom MAE (m) | Full-document exact | s/document | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_SWISSGEOL_TG_INCREMENTAL_TESSERACT_FORMAL_003 | B1_tesseract_ocr_conservative_interval_parser | 20 | 55 | 55 | 0.855 | 0.855 | 0.855 | 0.000 | 0.000 | 17/20 (0.850) | 3.832 | formal_authoritative_interval |
| P1_SWISSGEOL_TG_CONTENT_HELDOUT_TESSERACT_FORMAL_004 | B1_tesseract_ocr_conservative_interval_parser | 35 | 80 | 74 | 0.892 | 0.825 | 0.857 | 0.000 | 0.000 | 25/35 (0.714) | 3.047 | formal_authoritative_interval |
| P1_SWISSGEOL_TG_CONTENT_HELDOUT_RAPIDOCR_FORMAL_005 | B1_rapidocr_onnx_ocr_conservative_interval_parser | 35 | 80 | 79 | 0.684 | 0.675 | 0.679 | 0.000 | 0.000 | 17/35 (0.486) | 4.117 | formal_authoritative_interval |
The reference contains only interval boundaries from official database records whose complete sequence exactly agrees with an explicit table in the paired official PDF. The reported run is incremental and disjoint from parser-development records, but the source-agreement selection is not a representative random sample and no human annotation is claimed.

### Source-disjoint official-database transfer agreement

| Experiment | Model | Records | Visual content groups | Official intervals | Predicted intervals | Records with predictions | Interval P | Interval R | Interval F1 | Content-group macro F1 | Full-record exact | s/record | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_SWISSGEOL_CROSS_CANTON_TESSERACT_TRANSFER_003 | B1_tesseract_ocr_conservative_interval_parser | 42 | 35 | 787 | 9 | 2 | 0.111 | 0.001 | 0.003 | 0.003 | 0/42 (0.000) | N/A | formal_authoritative_source_disjoint_transfer |
| P1_SWISSGEOL_CROSS_CANTON_RAPIDOCR_TRANSFER_002 | B1_rapidocr_onnx_ocr_conservative_interval_parser | 42 | 35 | 787 | 7 | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 0/42 (0.000) | N/A | formal_authoritative_source_disjoint_transfer |
| P1_SWISSGEOL_FIVE_CANTON_TESSERACT_TRANSFER_001 | B1_tesseract_ocr_conservative_interval_parser | 46 | 39 | 3332 | 9 | 2 | 0.111 | 0.000 | 0.001 | 0.003 | 0/46 (0.000) | N/A | formal_authoritative_source_disjoint_transfer |
| P1_SWISSGEOL_FIVE_CANTON_RAPIDOCR_TRANSFER_001 | B1_rapidocr_onnx_ocr_conservative_interval_parser | 46 | 39 | 3332 | 7 | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 0/46 (0.000) | N/A | formal_authoritative_source_disjoint_transfer |
These runs apply the frozen Thurgau parser without reference conditioning to all paired records in each successively frozen non-development-canton panel. Official database intervals belong to the same borehole objects, but complete page/database agreement was not established; the values therefore measure transfer agreement and combine extraction error with possible source mismatch. Content-group macro F1 prevents one repeated 21-page report from receiving eightfold weight. The indexed aggregations resumed completed OCR artifacts after earlier interrupted/metric-only runs, so end-to-end latency is not reported.

### Cross-source authoritative interval diagnostic

| Experiment | Model | Documents | Reference intervals | Predicted intervals | Interval P | Interval R | Interval F1 | Matched top MAE (m) | Matched bottom MAE (m) | Full-document exact | s/document | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_USGS142_CROSS_SOURCE_INTERVAL_FORMAL_002 | tesseract_roi_generalized_lithology_parser | 1 | 12 | 12 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 1/1 (1.000) | 3.298 | formal_authoritative_interval |
| P1_USGS144_CROSS_SOURCE_INTERVAL_FORMAL_001 | tesseract_raster_page_interval_parser | 1 | 8 | 8 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 1/1 (1.000) | 17.387 | formal_authoritative_interval |
| P1_USGS_RAFT_RIVER_TESSERACT_INTERVAL_FORMAL_001 | tesseract_raster_table_interval_parser | 2 | 62 | 56 | 0.875 | 0.790 | 0.831 | 0.000 | 0.000 | 0/2 (0.000) | 6.354 | formal_authoritative_interval |
| P1_USGS_RAFT_RIVER_RAPIDOCR_INTERVAL_FORMAL_001 | rapidocr_raster_table_interval_parser | 2 | 62 | 62 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 1/2 (0.500) | 7.736 | formal_authoritative_interval |
| P1_BGS_OFFSHORE_V001_RAPIDOCR_CROSS_SOURCE_FORMAL_001 | rapidocr_bgs_composite_interval_parser_v001 | 26 | 341 | 28 | 0.250 | 0.021 | 0.038 | 0.000 | 0.000 | N/A | 9.568 | formal_authoritative_interval |
| P1_BGS_OFFSHORE_V001_TESSERACT_CROSS_SOURCE_FORMAL_001 | tesseract_bgs_composite_interval_parser_v001 | 26 | 341 | 54 | 0.148 | 0.023 | 0.041 | 0.000 | 0.003 | N/A | 10.080 | formal_authoritative_interval |
This table adds a single official USGS Idaho PDF with an explicit generalized-lithology legend. It is a cross-source diagnostic, not evidence for a representative source-disjoint estimate; source rights remain pending manual verification.

### Reference-conditioned interval diagnostics excluded from formal claims

| Experiment | Model | Documents | Reference intervals | Predicted intervals | Interval P | Interval R | Interval F1 | Matched top MAE (m) | Matched bottom MAE (m) | Full-document exact | s/document | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_SWISSGEOL_TG_INTERVAL_TESSERACT_FORMAL_001 | B1_tesseract_ocr_conservative_interval_parser | 9 | 21 | 15 | 1.000 | 0.714 | 0.833 | 0.000 | 0.000 | 6/9 (0.667) | 3.127 | diagnostic_oracle_metadata |
These retained runs conditioned candidate filtering/ranking on an official reference field and are diagnostics only. They are excluded from formal extraction claims even when their output metrics are otherwise valid.

### Interval-parser development results excluded from held-out claims

| Experiment | Model | Documents | Reference intervals | Predicted intervals | Interval P | Interval R | Interval F1 | Matched top MAE (m) | Matched bottom MAE (m) | Full-document exact | s/document | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_SWISSGEOL_TG_INTERVAL_TESSERACT_FORMAL_002 | B1_tesseract_ocr_conservative_interval_parser | 9 | 21 | 16 | 1.000 | 0.762 | 0.865 | 0.000 | 0.000 | 6/9 (0.667) | 3.180 | development_authoritative_interval |
| P1_SWISSGEOL_TG_CONTENT_DEVELOPMENT_RAPIDOCR_001 | B1_rapidocr_onnx_ocr_conservative_interval_parser | 37 | 85 | 85 | 0.635 | 0.635 | 0.635 | 0.000 | 0.000 | 19/37 (0.514) | 4.150 | development_authoritative_interval |
These reference-independent runs used the v001 records on which parser/reread behavior was developed. They are retained as development evidence and excluded from the incremental held-out estimate.

### Machine-adjudicated Silver agreement benchmark (not human accuracy)

| Experiment | Model | Pages | Borehole ID agreement | Final-depth MAE (Silver) | Interval P | Interval R | Interval F1 | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1_SILVER_B4_UNIPD_FIELD_002 | qwen3-vl-4b-instruct | 10 | 9/10 (0.900) | 0.000 | 0.714 | 0.663 | 0.688 | formal_silver_benchmark |
| P1_SILVER_B3_HELDOUT_UNIPD_FIELD_001 | positioned-text-layout-rules | 10 | 9/10 (0.900) | N/A | 0.677 | 0.253 | 0.368 | formal_silver_benchmark |
These metrics measure agreement with an explicitly machine-adjudicated Silver reference. They are not human/expert accuracy, and the reference construction channels are recorded in the source ledger and experiment configuration.

### Real-source controlled-degradation robustness (metadata fields only)

| Experiment | Model | Profile | ID exact | X coverage | X MAE | Y coverage | Y MAE | Complete ID/X/Y | Field omissions | Eligibility |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| P1_BGS_METADATA_ROBUSTNESS_TESSERACT_001 | B1_tesseract_ocr_regex | blur_20 | 16 | 29 | 0.000 | 29 | 0.000 | 15 | 15 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_TESSERACT_001 | B1_tesseract_ocr_regex | clean | 24 | 31 | 0.000 | 31 | 0.000 | 24 | 1 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_TESSERACT_001 | B1_tesseract_ocr_regex | contrast_040 | 26 | 31 | 0.000 | 31 | 0.000 | 26 | 2 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_TESSERACT_001 | B1_tesseract_ocr_regex | jpeg_30 | 26 | 31 | 0.000 | 31 | 0.000 | 26 | 2 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_TESSERACT_001 | B1_tesseract_ocr_regex | noise_16 | 23 | 30 | 0.000 | 30 | 0.000 | 22 | 5 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_TESSERACT_001 | B1_tesseract_ocr_regex | resolution_050 | 29 | 30 | 0.000 | 30 | 0.000 | 29 | 4 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_TESSERACT_001 | B1_tesseract_ocr_regex | skew_30 | 17 | 15 | 0.000 | 15 | 54162.400 | 9 | 44 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_RAPIDOCR_001 | B1_rapidocr_onnxruntime_ppocrv4_regex | blur_20 | 31 | 27 | 0.000 | 27 | 0.000 | 27 | 8 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_RAPIDOCR_001 | B1_rapidocr_onnxruntime_ppocrv4_regex | clean | 31 | 31 | 0.000 | 31 | 0.000 | 31 | 0 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_RAPIDOCR_001 | B1_rapidocr_onnxruntime_ppocrv4_regex | contrast_040 | 31 | 31 | 0.000 | 31 | 0.000 | 31 | 0 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_RAPIDOCR_001 | B1_rapidocr_onnxruntime_ppocrv4_regex | jpeg_30 | 31 | 7 | 0.000 | 7 | 0.000 | 7 | 48 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_RAPIDOCR_001 | B1_rapidocr_onnxruntime_ppocrv4_regex | noise_16 | 31 | 29 | 0.000 | 29 | 0.000 | 29 | 4 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_RAPIDOCR_001 | B1_rapidocr_onnxruntime_ppocrv4_regex | resolution_050 | 31 | 28 | 0.000 | 28 | 0.000 | 28 | 6 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_RAPIDOCR_001 | B1_rapidocr_onnxruntime_ppocrv4_regex | skew_30 | 31 | 31 | 0.000 | 31 | 0.000 | 31 | 0 | formal_authoritative_metadata_robustness |
These rows use first-page borehole ID/X/Y references from official BGS metadata. Profiles are synthetic transformations of real scans; final depth, intervals, and lithology are excluded because the first-page scope does not provide those references.

### Privacy-minimized OCR coverage audits (no Ground Truth)

| Experiment | Model | Completed pages | Borehole-ID presence | Final-depth presence | Pages with intervals | Emitted intervals | OCR regions | Constraint evals | Violations | s/page | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_B1_TESSERACT_SLOPES_AUDIT_001 | B1_tesseract_ocr_regex_privacy_minimized | 28/28 | 27/28 | 0/28 | 2/28 | 2 | 1528 | 14 | 4 | 1.640 | audit_only |
| P1_B1_RAPIDOCR_SLOPES_AUDIT_001 | B1_rapidocr_ppocrv4_regex_privacy_minimized | 28/28 | 28/28 | 0/28 | 0/28 | 0 | 3920 | 0 | 0 | 4.158 | audit_only |
| P1_B1_TESSERACT_TIBER_AUDIT_001 | B1_tesseract_ocr_regex_privacy_minimized | 1/1 | 0/1 | 0/1 | 0/1 | 0 | 34 | 0 | 0 | 0.948 | audit_only |
| P1_B1_RAPIDOCR_TIBER_AUDIT_001 | B1_rapidocr_ppocrv4_regex_privacy_minimized | 1/1 | 0/1 | 0/1 | 0/1 | 0 | 47 | 0 | 0 | 3.262 | audit_only |

Presence and emitted-count columns are extraction coverage diagnostics, not accuracy estimates. Records and OCR text are not serialized; source pages remain unreviewed and have no human Ground Truth.

### Privacy-minimized native-PDF coverage audits (no Ground Truth)

| Experiment | Model | Completed pages | Text regions | Regex borehole-ID presence | Regex pages with intervals | Regex intervals | Layout pages with intervals | Layout intervals | Layout constraint evals | Violations | s/page | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_NATIVE_LAYOUT_SEDLOG_AUDIT_001 | direct_native_text_regex_plus_B3_positioned_layout_privacy_minimized | 18/18 | 1279 | 0/18 | 0/18 | 0 | 0/18 | 0 | 0 | 0 | 0.087 | audit_only |

Direct-text and positioned-layout columns are extraction-path coverage diagnostics, not accuracy estimates. Persisted rows contain hashes and counts only; source text, extracted values, and source bboxes are omitted.

### B2 text-only LLM engineering audits

| Experiment | Model | Pages | Schema-valid | Emitted intervals | Constraint evals | Violations | Input tokens | s/page | Peak GiB | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_B2_QWEN3VL4B_TEXT_UNIPD_AUDIT_002 | Qwen/Qwen3-VL-4B-Instruct | 15 | 13/15 (0.867) | 74 | 538 | 8 | 11973 | 35.332 | 8.658 | audit_only |
| P1_B2_QWEN3VL4B_TEXT_UNIPD_AUDIT_003 | Qwen/Qwen3-VL-4B-Instruct | 15 | 13/15 (0.867) | 74 | 538 | 8 | 11973 | 50.102 | 8.658 | audit_only |

### B3 positioned-text layout engineering audits

| Experiment | Model | Pages | Pages with intervals | Emitted intervals | Constraint evals | Violations | s/page | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1_B3_LAYOUT_UNIPD_AUDIT_001 | B3_native_positioned_text_depth_column_rules | 15 | 5/15 | 46 | 367 | 3 | 0.039 | audit_only |
| P1_B3_LAYOUT_UNIPD_AUDIT_002 | B3_native_positioned_text_depth_column_rules | 15 | 5/15 | 46 | 367 | 3 | 0.040 | audit_only |

### VLM engineering audits

| Experiment | Model | Images | Schema-valid | Emitted intervals | Constraint evals | Violations | s/image | Peak GiB | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| P1_B4_QWEN3VL4B_SANMING_AUDIT_SMOKE_001 | Qwen/Qwen3-VL-4B-Instruct | 1 | 0/1 (0.000) | 0 | 0 | 0 | 128.382 | 8.713 | failure_analysis_only |
| P1_B4_QWEN3VL4B_SANMING_AUDIT_SMOKE_002 | Qwen/Qwen3-VL-4B-Instruct | 1 | 0/1 (0.000) | 0 | 0 | 0 | 32.553 | 8.642 | failure_analysis_only |
| P1_B4_QWEN3VL4B_SANMING_AUDIT_SMOKE_003 | Qwen/Qwen3-VL-4B-Instruct | 1 | 1/1 (1.000) | 2 | 20 | 4 | 29.820 | 8.642 | audit_only |
| P1_B4_QWEN3VL4B_SANMING_AUDIT_001 | Qwen/Qwen3-VL-4B-Instruct | 4 | 3/4 (0.750) | 8 | 82 | 20 | 50.637 | 8.654 | audit_only |
| P1_B4_QWEN3VL4B_BGS_AUDIT_001 | Qwen/Qwen3-VL-4B-Instruct | 4 | 4/4 (1.000) | 0 | 0 | 0 | 6.397 | 8.642 | audit_only |
| P1_B5_QWEN3VL4B_SANMING_AUDIT_001 | Qwen/Qwen3-VL-4B-Instruct | 4 | 1/4 (0.250) | 3 | 29 | 3 | 59.301 | 8.656 | audit_only |
| P1_B4_QWEN3VL4B_UNIPD_AUDIT_001 | Qwen/Qwen3-VL-4B-Instruct | 15 | 11/15 (0.733) | 87 | 778 | 49 | 60.987 | 8.713 | audit_only |

### B6 conservative fusion engineering audits

| Experiment | Model | Items | VLM available | Agreements | Disagreements | Visual-only review | VLM unavailable | Emitted intervals | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| P1_B6_QWEN3VL4B_UNIPD_AUDIT_001 | B6_conservative_direct_text_plus_Qwen3-VL-4B | 15 | 11/15 | 17 | 1 | 34 | 4 | 87 | audit_only |
| P1_B6_QWEN3VL4B_UNIPD_AUDIT_002 | B6_conservative_direct_text_plus_Qwen3-VL-4B | 15 | 11/15 | 17 | 1 | 34 | 4 | 87 | audit_only |

### Public native-PDF engineering audits

| Experiment | Model | Documents | Borehole-ID coverage | Final-depth coverage | Emitted intervals | Violations | s/page | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1_DIRECTPDF_UNIPD_AUDIT_001 | direct_pdf_text_conservative_regex | 11 | 0/11 | 0/11 | 0 | 0 | 0.128 | failure_analysis_only |
| P1_DIRECTPDF_UNIPD_AUDIT_002 | direct_pdf_text_conservative_regex | 11 | 11/11 | 0/11 | 0 | 10 | 0.129 | failure_analysis_only |
| P1_DIRECTPDF_UNIPD_AUDIT_003 | direct_pdf_text_conservative_regex | 11 | 11/11 | 0/11 | 0 | 10 | 0.130 | failure_analysis_only |
| P1_DIRECTPDF_UNIPD_AUDIT_004 | direct_pdf_text_conservative_regex | 11 | 11/11 | 0/11 | 0 | 1 | 0.125 | audit_only |

All rows are audit-only and not representative benchmark estimates. `N/A` paired MAE indicates zero paired predictions or an inapplicable field, not zero error. VLM audits have no human Ground Truth, so they report parse/diagnostic behavior rather than accuracy.

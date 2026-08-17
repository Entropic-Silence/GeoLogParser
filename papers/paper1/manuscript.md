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

The modern open-model comparison uses the Apache-2.0 Qwen3.8-27B-FP8 native vision-language model [@qwen2026qwen38] through a local OpenAI-compatible endpoint on four RTX 2080 Ti GPUs. Every 200-DPI page receives the same `vlm_interval_source_units_v002` prompt, temperature 0, thinking disabled, and a 4,096-token completion ceiling. The decoder performs only JSON parsing, source-unit conversion, and rejection of non-finite or non-positive ranges; it does not complete, reorder, deduplicate, or reference-condition intervals. No California Gold page was used to change the prompt, schema, decoder, model roster, or matcher. MinerU2.5 and PaddleOCR-VL are separately registered document-specialist interfaces; incomplete runs are not treated as results. Closed-model slots require official provider endpoints and archived responses and remain excluded while valid credentials are unavailable. Engine and parser choices, provider revisions, page hashes, and latency are retained for every completed run.

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

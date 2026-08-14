<!-- AUTO-GENERATED REVIEW BUNDLE. DO NOT EDIT. -->
> Package status: **DRAFT_NOT_SUBMISSION_READY**
> This bundle combines the versioned manuscript and generated results for review.
> Blockers: unresolved TBD/citation markers remain.

# A Benchmark for Structured Information Extraction from Heterogeneous Borehole Logs

## Abstract

Legacy borehole logs encode coordinates, elevations, interval boundaries, and geological descriptions in heterogeneous tables, scans, and drawings. Existing OCR scores do not establish whether these records can be converted into reliable databases, and page-level random splits can leak project templates. We define a provenance-bearing extraction task, a panel-aware annotation unit, leakage-resistant split protocols, a four-level evaluation framework, degradation metadata, and an error taxonomy. A 31-document/106-page British Geological Survey authoritative-metadata sub-benchmark provides a real-source comparison at matched 300-DPI rendering: Tesseract and RapidOCR reached borehole-ID exact matches of 25/31 and 31/31 respectively, but neither recovered final depth reliably. A controlled first-page robustness extension evaluates 217 derived images (31 scans × 7 profiles) for ID/X/Y only. A separate Swissgeol source-agreement pilot contributes 9 official PDF/database pairs and 21 interval boundaries: a reference-independent 250-DPI Tesseract baseline predicted 16 intervals, all 16 matched within ±0.05 m (precision 1.000, recall 0.762, F1 0.865), and 6/9 documents were completely exact. This pilot was selected for complete PDF-table/database agreement and is not a representative random sample; its source rights remain pending pre-submission verification, and lithology is excluded. The broader rights-cleared interval/lithology benchmark, split-generalization gap, and human agreement remain `TBD`. The intended contribution is a reproducible benchmark centered on data quality, provenance, critical-field coverage, and cross-template generalization rather than a new network. <!-- evidence:p1.swissgeol_authoritative_interval -->

## 1. Introduction

Borehole logs are machine-readable only when numerical boundaries, geological text, layout, and source evidence remain linked. Treating a page as plain OCR text loses column semantics; treating it as an unconstrained image-to-JSON prompt obscures failures and provenance. This paper asks: (RQ1) how accurately do OCR, VLM, and hybrid systems structure heterogeneous borehole logs; (RQ2) how strongly does random page splitting overestimate deployment generalization; (RQ3) which degradation factors matter most; and (RQ4) which error classes dominate?

The paper's contribution boundary is data and benchmark. Geological constraint-guided correction belongs to Paper II; database/3D error propagation belongs to Paper III. Data or tables may be reused with disclosure, but method and downstream claims are not duplicated.

## 2. Related Work

OCR engines such as Tesseract provide a text-recognition layer but do not by themselves recover domain-specific table semantics [@smith2007tesseract]. Document-intelligence research has therefore combined text and spatial layout [@xu2020layoutlm] and later visual, textual, and layout modalities [@xu2021layoutlmv2]. PubLayNet and DocLayNet exemplify general-purpose layout benchmarks [@zhong2019publaynet; @pfitzmann2022doclaynet], whereas their label spaces are not a substitute for borehole interval and provenance annotation. Han and Suh provide the closest verified applied comparison: they assembled 908 borehole-log pages from 47 Korean abandoned-mine reports, manually grouped pages into five types, used an 8:2 page split to evaluate type classification, and demonstrated spreadsheet structuring on Type 1; their OCR discussion reports example misrecognitions rather than a shared field/interval benchmark [@han2024boreholeocr]. GeoLogParser instead targets heterogeneous multilingual field extraction with field-level provenance, numerical and interval metrics, project/template/source-disjoint evaluation, and explicit Ground-Truth gates. The studies are therefore complementary, and their reported page-type classification result is not comparable to structured-extraction accuracy here.

Dependence-aware validation literature cautions that ordinary cross-validation can be misleading when observations have spatial, temporal, or hierarchical structure [@roberts2017crossvalidation]. Borehole pages from one project similarly share templates, producers, and acquisition conditions. This motivates reporting random page split only as a reference and making project-, template-, and source-disjoint protocols primary. Cohen's coefficient provides one established option for nominal-scale annotation agreement [@cohen1960agreement], supplemented here by field-specific exact/numeric agreement.

## 3. Task Definition

One input unit is one borehole panel from PDF/JPG/PNG. Multi-borehole pages are split by a recorded normalized crop. Output follows `borehole_v001.schema.json`: borehole fields, ordered intervals, raw and normalized terminology, and an evidence envelope containing page, bbox, source text, extraction method, confidence, validation status, and warnings. Missing evidence remains null. SI values coexist with raw text/unit.

The first evaluation scope includes borehole ID, collar elevation, final depth, groundwater depth, interval top/bottom/thickness, lithology, and description. Coordinates are an extension already supported by the Schema.

## 4. Dataset Construction

### 4.1 Sources and rights

Every item records organization, URL, access date, licence, usage, redistribution policy, and citation. Public BGS audit material is governed by its captured OGL terms. The Swissgeol Thurgau pilot freezes 32 published public PDF/database pairs with 145 official database intervals. A deterministic native-text audit found exact complete agreement between an explicit PDF interval table and the database in 9 documents/21 intervals; 8 documents were partial or mismatched and 15 exposed no conservatively parsed explicit table. Only the 9 exact pairs enter the interval reference, and only top, bottom, and thickness are in scope. Source/item reuse and redistribution terms are separately recorded as pending manual pre-submission verification, so source PDFs and derived pages are not released. A University of Padova CC BY 4.0 dataset (DOI `10.25430/researchdata.cab.unipd.it.00001663`) contributes 11 international borehole PDFs/15 native-PDF pages after archive hash verification. All 15 pages have rendered, hashed `auto` proposals but remain unannotated by a human. <!-- evidence:p1.padova_inventory --> A separate CC BY 4.0 Mendeley source contributes 28 provisional English engineering-borelog candidates; all are single-page vector PDFs without extractable text and come from one highly repeated project template. The same acquisition contains 18 resistivity images that are excluded from phase 1. <!-- evidence:p1.slopes_content --> A second Mendeley PDF contributes one provisional English stratigraphic-column candidate, while its other 20 pages are excluded laboratory reports. <!-- evidence:p1.tiber_content --> A third Mendeley source contributes 18 provisional English SedLog lithology-column candidates in one unusually tall native PDF. <!-- evidence:p1.sedlog_content --> Its independent source-review queue contains 18 unreviewed items and zero annotation-eligible or Ground-Truth pages. <!-- evidence:p1.sedlog_source_review --> All classifications are automated content triage, not human content/privacy review or Ground Truth, and every page remains benchmark-ineligible. The separate slopes/Tiber 29-page rendered source-review pack likewise currently has 29 unreviewed items, zero annotation-eligible items, and zero Ground Truth; the model's render-legibility inspection is not counted as human review. <!-- evidence:p1.international_source_review --> A CC BY 4.0 Mendeley Chinese candidate (DOI `10.17632/vcpz47r3sv.2`) contains 33 DWGs; automatic text screening confirmed Chinese content in all 33 and conservatively risk-flagged 30. A full source-DWG-to-SVG audit inventoried 789,244 source graphical entities: 538,740 source IDs appeared in renderer output, 20 files produced non-empty review rasters, 11 produced empty rasters, and two emitted invalid sentinel geometry. None achieved complete entity-ID coverage. <!-- evidence:p1.cad_full_svg --> A separate source-DWG/derivative-DXF audit of three priority files matched 1,244, 1,905, and 7,173 modelspace entity handles and the ordered hashes of 363, 537, and 611 text entities, but those structural/text matches did not establish pixel fidelity. <!-- evidence:p1.cad_priority_fidelity --> All 33 files remain conversion-incomplete, visually unassessed, human-unreviewed, and benchmark-ineligible; no DWG is counted as a phase-1 page or Ground Truth. Other Chinese web candidates remain in quarantine because item-level redistribution, privacy, stamps, signatures, and precise-location review are incomplete. Additional CGS/SAGE/Zenodo DOI records remain metadata-only or out of scope because file inventory, image-log fit, access, or identifiable item licensing is absent. Therefore the rights-cleared Chinese benchmark currently has `TBD` documents/pages/intervals and is not released.

### 4.2 Annotation

The local UI shows a panel beside editable provenance-bearing fields and permits a reviewer to draw a tighter display-space evidence box without overwriting the original PDF bbox. Auto proposals have status `auto`; human stages are `single_verified`, `double_verified`, and `expert_verified`. Each human save appends an attestation bound to the canonical final-record SHA256. `double_verified` requires two distinct anonymized IDs on the identical record hash, while `expert_verified` requires a server-allowlisted expert ID. Thus an edit invalidates attestations for the earlier record rather than inheriting its status.

Independent agreement uses two service-separated, full-overlap annotation tracks created from byte-identical frozen `auto` proposals before review. Each service fixes its actor ID server-side, so a browser payload cannot select the peer actor; this binds a process to a track but does not authenticate the human user. Shared-host filesystem and human access therefore remain deployment/study controls. Agreement is computed only after both tracks independently pass the human GT gate, rejects overlapping annotator IDs, and freezes aggregate metrics, every v001 field disagreement, record hashes, and source annotation hashes before adjudication. The adjudication builder writes both answers and pending discrepancy cases but never creates final GT automatically; even equal answers require source confirmation. The current Padova assignment contains 15 source pages and two tracks (30 task files), but all task files remain `auto`: there are zero effective human attestations, zero GT-exportable track annotations, zero agreement artifacts, and zero adjudication manifests. <!-- evidence:p1.padova_annotation_assignment --> These are workflow-readiness counts, not annotation sample size or agreement results. Actual inter-annotator/repeated self-agreement and adjudication results remain `TBD`.

### 4.3 Metadata and splits

Metadata covers source, project, template, native/scanned/image type, resolution, blur/noise/skew, stamps, handwriting, and artifacts. Split A is random page/panel reference only. Primary splits are project-disjoint, template-disjoint, and, if data permit, source-disjoint. Group IDs are assigned before splitting. Exact split versions and counts are `TBD`.

### 4.4 Degradation benchmark

Real and synthetic degradation cover resolution, blur, noise, skew, JPEG compression, contrast reduction, broken lines, watermarks, stamps, and occlusion. Every synthetic parameter and source hash is saved. A protocol-only Padova input set contains 270 deterministic derivatives (15 pages × 18 profiles), with manifest SHA256 `ca6bc6d6f2eff3df6916b3a87d43f24df6dacb13f4e924048b79120a339c5ba9`; it has no accuracy values because the source pages are not human-annotated. <!-- evidence:p1.degradation_inventory --> The BGS robustness set contains 217 first-page derivatives from 31 real scans, 300-DPI source rendering, seven profiles (`clean`, resolution 0.50, blur radius 2.0, Gaussian noise 16, 3° skew, JPEG quality 30, contrast 0.40), and manifest SHA256 `5a1205c944a5cb652967b99e6478169805db35f749dffe44124076eafd766628`. It evaluates only official borehole ID/X/Y references; final depth, intervals, and lithology are excluded. <!-- evidence:p1.bgs_robustness_inventory --> Training variants never enter test. Chinese benchmark severity grids remain `TBD`.

## 5. Baselines

B1 OCR+regex; B2 OCR+LLM; B3 OCR+layout+rules; B4 zero-shot VLM; B5 few-shot VLM; B6 OCR+VLM fusion. Adapters and model revisions come from a registry. Current executed comparisons cover Tesseract+regex and RapidOCR+regex on 31 BGS documents, a formal Tesseract interval-boundary pilot on 9 Swissgeol pairs, B2 text-only and B3 positioned-text paths on Padova, plus Apache-2.0 Qwen3-VL-4B at fixed revision `ebb281ec...` through local B4/B5 adapters. The Swissgeol B1 run renders every PDF page at 250 DPI, applies Tesseract `eng` with PSM 3, and conservatively parses explicit interval tables; native PDF text is not used for prediction. B2 supplies only flattened PDF/OCR text to the language stack; B3 requires at least three distinct depth ranges in one repeated x-position bin and abstains when boundaries exist only as graphics. B4 uses greedy decoding and versioned prompt `vlm_extract_v002`; whole-image values are marked `VLM_UNGROUNDED`. B6 conservatively retains grounded evidence on disagreement and sends visual-only or conflicting fields to review. Formal multi-model interval and lithology comparisons remain `TBD`.

## 6. Evaluation

Level 1: CER, explicitly segmented WER, and numeric CER. Level 2: exact categorical matches, macro normalized description edit similarity, and numeric coverage plus paired MAE. Level 3: order-preserving, boundary-aware interval precision/recall/F1 and boundary MAE/accuracy at ±0.01/0.05/0.10 m. Level 4: component geological consistency with explicit evaluated coverage. Hierarchical lithology paths provide auxiliary ancestor-set precision/recall/F1 and never replace exact match. Latency, RAM/VRAM, tokens, and cost are logged.

Error taxonomy includes OCR digit/character/decimal errors, layout/column/row errors, interval errors, semantic/normalization errors, hallucination, constraint errors, and reread failures.

## 7. Results

The authoritative interval pilot contains 9 one-page Swissgeol PDF/database pairs and 21 numeric intervals selected because the complete explicit PDF table exactly agreed with the official database sequence. The independent raster path predicted 16 intervals without reading official final depth or any other reference field. All 16 matched a reference interval within ±0.05 m, yielding micro precision 1.000, recall 0.762, and F1 0.865; matched top- and bottom-boundary MAE were both 0.000 m. Six of nine documents were completely exact. The remaining errors were five omitted reference intervals: one partial extraction and two documents with no detected interval section. No spurious interval was emitted. Mean wall time was 3.180 s/document on CPU. An earlier retained diagnostic had supplied official final depth to candidate filtering/ranking; it is labelled `diagnostic_oracle_metadata` and excluded from formal extraction claims. These values characterize a deliberately selected explicit-table pilot, not the complete 32-document candidate pool or cross-template deployment performance. <!-- evidence:p1.swissgeol_authoritative_interval -->

The authoritative-metadata track contains 31 official BGS scan PDFs (106 pages) paired by source record ID with official borehole reference, easting, northing, and catalogue length. At matched 300-DPI rendering, Tesseract recovered 25/31 borehole IDs, covered X/Y on 31/31 records with zero paired error, and produced no final-depth or interval value. RapidOCR recovered 31/31 borehole IDs and both coordinates with zero paired error, but covered final depth on only 1/31 records, and that prediction was 192.0 m for an official catalogue length of 58.52 m (absolute error 133.48 m); it emitted no intervals. Thus the apparent strength of identifier/coordinate extraction did not transfer to the engineering-critical depth field. A separate 150-DPI Tesseract run is retained as a resolution-sensitivity observation rather than included in the matched comparison. These results are real authoritative metadata comparisons, but the catalogue `LENGTH` field is treated only as a final-depth proxy and no interval or lithology reference exists. <!-- evidence:p1.bgs_metadata_tesseract31 --> <!-- evidence:p1.bgs_metadata_rapidocr31 -->

The controlled BGS robustness runs use the same 31 first pages and evaluate only fields visible in that page-level scope. On clean pages, Tesseract achieved complete exact ID/X/Y extraction on 24/31 records; the rate decreased to 15/31 with blur radius 2.0 and 9/31 with 3° skew. RapidOCR achieved 31/31 on clean pages, 27/31 with blur, and 31/31 under 3° skew, but its JPEG-quality-30 condition fell to 7/31. Most degradation failures were omissions. Non-missing X/Y values had zero paired MAE in all RapidOCR profiles and in all Tesseract profiles except 3° skew, where Tesseract produced two gross Y-coordinate errors (paired Y MAE 54,162.4 in the non-missing subset). The backend profiles therefore exhibit different failure surfaces: Tesseract was sensitive to skew and blur, whereas RapidOCR was particularly sensitive to JPEG artifacts in this panel. These are controlled transformations of real scans rather than naturally sampled damage, and they do not establish robustness for interval or lithology extraction. <!-- evidence:p1.bgs_robustness_tesseract --> <!-- evidence:p1.bgs_robustness_rapidocr -->

Two explicitly named Silver-agreement runs are formal within the machine-reference track. The A/B field adjudicator aligned 15 Padova pages, retained 10 pages with two Schema-valid primary channels, produced one high-confidence and nine uncertain Silver records, and marked nine as hard cases. B4 agreed with this reference at interval F1 0.688 (precision 0.714, recall 0.663), while held-out B3 layout rules agreed at interval F1 0.368 (precision 0.677, recall 0.253). These are agreement-to-Silver values, not human accuracy; B4 participates in reference construction, whereas B3 is held out from the A/B-only reference version.

See [generated/current_results.md](generated/current_results.md). The remaining source-coverage rows are engineering audits. On the 28 unreviewed slopes candidates, privacy-minimized Tesseract processing completed 28/28 pages, emitted borehole-ID candidates on 27 pages and two interval candidates on two pages, and triggered four violations across 14 constraint evaluations in 1.640 s/page on CPU. <!-- evidence:p1.slopes_tesseract_coverage --> RapidOCR completed the same 28/28 pages, emitted borehole-ID candidates on 28 pages but no interval candidates, and averaged 4.158 s/page on CPU. <!-- evidence:p1.slopes_rapidocr_coverage --> Both engines also completed the single unreviewed Tiber stratigraphic-column page and produced OCR text regions, but neither emitted any target field or interval candidate. <!-- evidence:p1.tiber_tesseract_coverage --> <!-- evidence:p1.tiber_rapidocr_coverage --> All four runs set accuracy metrics to null and retained only field-presence/count diagnostics plus record hashes: the source pages have no human Ground Truth, so these counts neither establish correctness nor rank the OCR engines by accuracy. The one-page Tiber result is a template-specific coverage failure, not a generalization estimate. On the 18 SedLog pages, native extraction returned 1,279 positioned text regions, but neither generic regex nor B3 produced an interval; mean CPU latency for both paths together was 0.087 s/page. <!-- evidence:p1.sedlog_native_coverage --> B3 intentionally requires at least three distinct `top-bottom` ranges in one x-position bin, whereas these lithology columns expose their principal boundaries graphically. This explains the implemented abstention path, but without human GT it is not an accuracy or interval-recall estimate. On four quarantined Chinese panels, B4 produced 3/4 Schema-valid responses; one reached the 1024-token cap. Valid records emitted eight intervals, while C1–C10 diagnosed 20 violations across 82 evaluated items. Mean inference time was 50.637 s/image and peak allocated VRAM about 9.29 GB. <!-- evidence:p1.b4_sanming --> B5 few-shot produced only 1/4 Schema-valid responses; three hit the token cap and mean latency rose to 59.301 s/image. <!-- evidence:p1.b5_sanming --> Thus the current few-shot prompt did not improve structured-output stability. This is prompt/model behavior, not accuracy: annotations remain `auto` and rights-unverified. On four BGS first pages, B4 produced 4/4 valid empty records in 6.397 s/image on average, an abstention/coverage failure rather than successful extraction. <!-- evidence:p1.b4_bgs --> On the 11-document/15-page Padova set, direct native text covered 11/11 header IDs at 0.125 s/page but emitted no intervals. <!-- evidence:p1.directpdf_padova --> B2 text-only extraction produced 13/15 Schema-valid responses and 74 unverified intervals; two responses hit the 1536-token cap. Mean inference was 35.332 s/page and peak allocated GPU memory was 9.296 GB. <!-- evidence:p1.b2_padova --> B3 recovered 46 unverified interval ranges on 5/15 pages in 0.039 s/page; it abstained on the ten pages whose boundaries were graphical or lacked a repeated textual depth column. <!-- evidence:p1.b3_padova --> B4 produced 11/15 Schema-valid responses, emitted 87 unverified intervals, and hit the 1536-token cap on all four failed responses; mean inference was 60.987 s/page with 9.356 GB peak allocated GPU memory. <!-- evidence:p1.b4_padova --> B6 fused the 11 valid VLM records with grounded proposals: 17 field agreements, one explicit disagreement, 34 visual-only review decisions, and four pages retaining grounded data because VLM output was unavailable. <!-- evidence:p1.b6_padova --> These are coverage and decision-path counts, not correctness. The source itself includes a `TS5.pdf` whose header reads `TS2`, so filenames cannot be silently treated as GT. Representative multi-model comparison, random-versus-disjoint generalization, interval degradation curves, full GT-based error distribution, and statistical intervals remain `TBD`.

The formal pilot summary is [authoritative interval performance](generated/figures/authoritative_interval_pilot.png).
Additional audit visuals are [audit coverage](generated/figures/audit_coverage.png)
and [degradation inputs](generated/figures/degradation_inputs.png). The audit-coverage figure
mixes only explicitly labelled availability/parse-coverage diagnostics and is
not an accuracy plot; the second counts generated inputs and has no measured
performance axis.

## 8. Discussion and Threats to Validity

The BGS experiments demonstrate why coverage must accompany MAE: zero extracted final-depth values yield undefined MAE, not zero error. The matched 31-document comparison also exposes complementary critical failures: Tesseract made six ID errors while abstaining on final depth, whereas RapidOCR's sole depth prediction was a 133.48 m error. The controlled robustness extension shows that degradation sensitivity is backend-specific even when the reference fields are simple metadata: 3° skew was severe for Tesseract but not RapidOCR, while JPEG quality 30 was severe for RapidOCR. The Swissgeol pilot similarly shows that perfect precision and zero matched-boundary MAE can coexist with substantial omission: recall was only 0.762 because two tables were missed and one was partially recovered. Because the Swissgeol subset was selected for source agreement and explicit parsability, and the BGS perturbations are synthetic transformations of first pages, the current evidence supports only narrow conclusions about omission-aware reporting and field-/perturbation-dependent reliability, not representative interval extraction or cross-source generalization.

Major threats are Chinese source rights, project/template diversity, annotation reliability, field missingness, model version drift, prompt instability, and benchmark leakage. The engineering audit also shows that valid JSON is not equivalent to valid geology: absolute elevations were confused with measured depths, producing inverted/inconsistent intervals detected by C1/C2/C4. Formal effects will be quantified or marked `TBD` rather than inferred.

## 9. Reproducibility and Ethics

Experiment IDs, Git commits, dataset/split/model/prompt versions, seed, hardware/software, metrics, predictions, errors, and logs are frozen. Sensitive project names, contacts, signatures, and coordinates require anonymization decisions. No quarantined candidate will be redistributed without authorization.

## 10. Conclusion

We present the executable definition and infrastructure for a provenance-aware heterogeneous borehole-log benchmark, report a real authoritative-metadata comparison that reveals severe field-dependent reliability, and establish a hash-bound 9-document/21-interval authoritative source-agreement pilot. Its reference-independent baseline achieved interval precision 1.000 and F1 0.865 but recall only 0.762, demonstrating why omission and coverage must accompany boundary error. A representative conclusion about heterogeneous interval/lithology performance or split leakage remains `TBD` until the broader reference set and experiments are complete.

The repository's auto-generated [publication-readiness audit](../../docs/generated/publication_readiness.md)
currently reports zero exportable human-GT annotations, two formal machine-Silver
agreement runs, and one formal authoritative source-agreement interval run in
addition to the metadata tracks. Neither Silver agreement nor deterministic
source agreement is described as human annotation.

## References

Shared bibliography: [../references.bib](../references.bib). Citation metadata and permitted claim scope are logged in [../../docs/literature_evidence.yaml](../../docs/literature_evidence.yaml).

# Appendix: Machine-Generated Current Results

<!-- AUTO-GENERATED. DO NOT EDIT. -->
### OCR + regex audits

| Experiment | Model | Borehole ID EM | X coverage | X paired MAE | Final-depth coverage | Emitted intervals | s/page | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1_B1_BGS_AUDIT_001 | B1_tesseract_ocr_regex | 3/4 (0.750) | 4/4 (1.000) | 0.000 | 0/4 (0.000) | 1 | 6.369 | audit_only |
| P1_B1_RAPIDOCR_BGS_AUDIT_001 | B1_rapidocr_onnxruntime_ppocrv4_regex | 4/4 (1.000) | 0/4 (0.000) | TBD | 0/4 (0.000) | 0 | 3.525 | audit_only |
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

### Authoritative source-agreement interval pilot

| Experiment | Model | Documents | Reference intervals | Predicted intervals | Interval P | Interval R | Interval F1 | Matched top MAE (m) | Matched bottom MAE (m) | Full-document exact | s/document | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_SWISSGEOL_TG_INTERVAL_TESSERACT_FORMAL_002 | B1_tesseract_ocr_conservative_interval_parser | 9 | 21 | 16 | 1.000 | 0.762 | 0.865 | 0.000 | 0.000 | 6/9 (0.667) | 3.180 | formal_authoritative_interval |
The reference contains only interval boundaries from official database records whose complete sequence exactly agrees with an explicit table in the paired official PDF. It is a source-agreement-selected pilot, not a representative random sample, and no human annotation is claimed.

### Reference-conditioned interval diagnostics excluded from formal claims

| Experiment | Model | Documents | Reference intervals | Predicted intervals | Interval P | Interval R | Interval F1 | Matched top MAE (m) | Matched bottom MAE (m) | Full-document exact | s/document | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_SWISSGEOL_TG_INTERVAL_TESSERACT_FORMAL_001 | B1_tesseract_ocr_conservative_interval_parser | 9 | 21 | 15 | 1.000 | 0.714 | 0.833 | 0.000 | 0.000 | 6/9 (0.667) | 3.127 | diagnostic_oracle_metadata |
These retained runs conditioned candidate filtering/ranking on an official reference field and are diagnostics only. They are excluded from formal extraction claims even when their output metrics are otherwise valid.

### Machine-adjudicated Silver agreement benchmark (not human accuracy)

| Experiment | Model | Pages | Borehole ID agreement | Final-depth MAE (Silver) | Interval P | Interval R | Interval F1 | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1_SILVER_B4_UNIPD_FIELD_002 | qwen3-vl-4b-instruct | 10 | 9/10 (0.900) | 0.000 | 0.714 | 0.663 | 0.688 | formal_silver_benchmark |
| P1_SILVER_B3_HELDOUT_UNIPD_FIELD_001 | positioned-text-layout-rules | 10 | 9/10 (0.900) | TBD | 0.677 | 0.253 | 0.368 | formal_silver_benchmark |
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

All rows are audit-only and not representative benchmark estimates. `TBD` paired MAE indicates zero paired predictions, not zero error. VLM audits have no human Ground Truth, so they report parse/diagnostic behavior rather than accuracy.

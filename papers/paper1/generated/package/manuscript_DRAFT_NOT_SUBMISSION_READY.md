<!-- AUTO-GENERATED REVIEW BUNDLE. DO NOT EDIT. -->
> Package status: **DRAFT_NOT_SUBMISSION_READY**
> This bundle combines the versioned manuscript and generated results for review.
> Blockers: unresolved TBD/citation markers remain; no formal experiment is indexed.

# A Benchmark for Structured Information Extraction from Heterogeneous Chinese Borehole Logs

## Abstract

Legacy borehole logs encode coordinates, elevations, interval boundaries, and geological descriptions in heterogeneous tables, scans, and drawings. Existing OCR scores do not establish whether these records can be converted into reliable databases, and page-level random splits can leak project templates. We define a provenance-bearing extraction task, a panel-aware annotation unit, leakage-resistant split protocols, a four-level evaluation framework, degradation metadata, and an error taxonomy. The rights-cleared Chinese benchmark size, model comparison, split-generalization gap, robustness results, and human agreement are `TBD`. Four-document British Geological Survey audits validate the executable OCR/VLM paths and expose coverage failures; a rights-unverified four-panel Chinese audit exposes truncation and geological inconsistency. A 15-page CC BY 4.0 international audit further exposes output-length failures and exercises conservative OCR/VLM fusion. None is a representative benchmark result. The intended contribution is a reproducible benchmark centered on data quality, provenance, and cross-template generalization rather than a new network.

## 1. Introduction

Borehole logs are machine-readable only when numerical boundaries, geological text, layout, and source evidence remain linked. Treating a page as plain OCR text loses column semantics; treating it as an unconstrained image-to-JSON prompt obscures failures and provenance. This paper asks: (RQ1) how accurately do OCR, VLM, and hybrid systems structure Chinese borehole logs; (RQ2) how strongly does random page splitting overestimate deployment generalization; (RQ3) which degradation factors matter most; and (RQ4) which error classes dominate?

The paper's contribution boundary is data and benchmark. Geological constraint-guided correction belongs to Paper II; database/3D error propagation belongs to Paper III. Data or tables may be reused with disclosure, but method and downstream claims are not duplicated.

## 2. Related Work

OCR engines such as Tesseract provide a text-recognition layer but do not by themselves recover domain-specific table semantics [@smith2007tesseract]. Document-intelligence research has therefore combined text and spatial layout [@xu2020layoutlm] and later visual, textual, and layout modalities [@xu2021layoutlmv2]. PubLayNet and DocLayNet exemplify general-purpose layout benchmarks [@zhong2019publaynet; @pfitzmann2022doclaynet], whereas their label spaces are not a substitute for borehole interval and provenance annotation. Han and Suh reported a directly related deep-learning/OCR workflow for classifying and databasing borehole logs in abandoned-mine ground-stability investigations [@han2024boreholeocr]. Our benchmark differs in its Chinese heterogeneous-document scope, field-level provenance, disjoint project/template evaluation, and numerical/geological error layers; a full claim-by-claim comparison with that paper's dataset and results remains `[CITATION TO VERIFY]` until its full text is archived and reviewed.

Dependence-aware validation literature cautions that ordinary cross-validation can be misleading when observations have spatial, temporal, or hierarchical structure [@roberts2017crossvalidation]. Borehole pages from one project similarly share templates, producers, and acquisition conditions. This motivates reporting random page split only as a reference and making project-, template-, and source-disjoint protocols primary. Cohen's coefficient provides one established option for nominal-scale annotation agreement [@cohen1960agreement], supplemented here by field-specific exact/numeric agreement.

## 3. Task Definition

One input unit is one borehole panel from PDF/JPG/PNG. Multi-borehole pages are split by a recorded normalized crop. Output follows `borehole_v001.schema.json`: borehole fields, ordered intervals, raw and normalized terminology, and an evidence envelope containing page, bbox, source text, extraction method, confidence, validation status, and warnings. Missing evidence remains null. SI values coexist with raw text/unit.

The first evaluation scope includes borehole ID, collar elevation, final depth, groundwater depth, interval top/bottom/thickness, lithology, and description. Coordinates are an extension already supported by the Schema.

## 4. Dataset Construction

### 4.1 Sources and rights

Every item records organization, URL, access date, licence, usage, redistribution policy, and citation. Public BGS audit material is governed by its captured OGL terms. A University of Padova CC BY 4.0 dataset (DOI `10.25430/researchdata.cab.unipd.it.00001663`) contributes 11 international borehole PDFs/15 native-PDF pages after archive hash verification. All 15 pages have rendered, hashed `auto` proposals but remain unannotated by a human. <!-- evidence:p1.padova_inventory --> A CC BY 4.0 Mendeley Chinese candidate (DOI `10.17632/vcpz47r3sv.2`) contains 33 DWGs; automatic text screening confirmed Chinese content in all 33 and conservatively risk-flagged 30. A full source-DWG-to-SVG audit inventoried 789,244 source graphical entities: 538,740 source IDs appeared in renderer output, 20 files produced non-empty review rasters, 11 produced empty rasters, and two emitted invalid sentinel geometry. None achieved complete entity-ID coverage. <!-- evidence:p1.cad_full_svg --> A separate source-DWG/derivative-DXF audit of three priority files matched 1,244, 1,905, and 7,173 modelspace entity handles and the ordered hashes of 363, 537, and 611 text entities, but those structural/text matches did not establish pixel fidelity. <!-- evidence:p1.cad_priority_fidelity --> All 33 files remain conversion-incomplete, visually unassessed, human-unreviewed, and benchmark-ineligible; no DWG is counted as a phase-1 page or Ground Truth. Other Chinese web candidates remain in quarantine because item-level redistribution, privacy, stamps, signatures, and precise-location review are incomplete. Additional CGS/SAGE/Zenodo DOI records remain metadata-only or out of scope because file inventory, image-log fit, access, or identifiable item licensing is absent. Therefore the rights-cleared Chinese benchmark currently has `TBD` documents/pages/intervals and is not released.

### 4.2 Annotation

The local UI shows a panel beside editable provenance-bearing fields and permits a reviewer to draw a tighter display-space evidence box without overwriting the original PDF bbox. Auto proposals have status `auto`; human stages are `single_verified`, `double_verified`, and `expert_verified`. Each human save appends an attestation bound to the canonical final-record SHA256. `double_verified` requires two distinct anonymized IDs on the identical record hash, while `expert_verified` requires a server-allowlisted expert ID. Thus an edit invalidates attestations for the earlier record rather than inheriting its status.

Independent agreement uses two service-separated, full-overlap annotation tracks created from byte-identical frozen `auto` proposals before review. Track-specific write allowlists prevent cross-track saves through the application, although shared-host filesystem isolation remains an operational protocol requirement rather than a security guarantee. Agreement is computed only after both tracks independently pass the human GT gate, rejects overlapping annotator IDs, and freezes aggregate metrics, every v001 field disagreement, record hashes, and source annotation hashes before adjudication. The adjudication builder writes both answers and pending discrepancy cases but never creates final GT automatically; even equal answers require source confirmation. The current Padova assignment contains 15 source pages and two tracks (30 task files), but all task files remain `auto`: there are zero effective human attestations, zero GT-exportable track annotations, zero agreement artifacts, and zero adjudication manifests. <!-- evidence:p1.padova_annotation_assignment --> These are workflow-readiness counts, not annotation sample size or agreement results. Actual inter-annotator/repeated self-agreement and adjudication results remain `TBD`.

### 4.3 Metadata and splits

Metadata covers source, project, template, native/scanned/image type, resolution, blur/noise/skew, stamps, handwriting, and artifacts. Split A is random page/panel reference only. Primary splits are project-disjoint, template-disjoint, and, if data permit, source-disjoint. Group IDs are assigned before splitting. Exact split versions and counts are `TBD`.

### 4.4 Degradation benchmark

Real and synthetic degradation cover resolution, blur, noise, skew, JPEG compression, contrast reduction, broken lines, watermarks, stamps, and occlusion. Every synthetic parameter and source hash is saved. A protocol-only Padova input set now contains 270 deterministic derivatives (15 pages × 18 profiles), with manifest SHA256 `ca6bc6d6f2eff3df6916b3a87d43f24df6dacb13f4e924048b79120a339c5ba9`; it has no accuracy values because the source pages are not human-annotated. <!-- evidence:p1.degradation_inventory --> Training variants never enter test. Chinese benchmark severity grids and measured curves remain `TBD`.

## 5. Baselines

B1 OCR+regex; B2 OCR+LLM; B3 OCR+layout+rules; B4 zero-shot VLM; B5 few-shot VLM; B6 OCR+VLM fusion. Adapters and model revisions come from a registry. Current executed audits cover Tesseract+regex and RapidOCR+regex on four BGS documents, B2 text-only and B3 positioned-text paths on Padova, plus Apache-2.0 Qwen3-VL-4B at fixed revision `ebb281ec...` through local B4/B5 adapters. B2 supplies only flattened PDF/OCR text to the language stack; B3 requires at least three distinct depth ranges in one repeated x-position bin and abstains when boundaries exist only as graphics. B4 uses greedy decoding and versioned prompt `vlm_extract_v002`; whole-image values are marked `VLM_UNGROUNDED`. B6 conservatively retains grounded evidence on disagreement and sends visual-only or conflicting fields to review. Formal Chinese runs are `TBD`.

## 6. Evaluation

Level 1: CER, explicitly segmented WER, and numeric CER. Level 2: exact categorical matches, macro normalized description edit similarity, and numeric coverage plus paired MAE. Level 3: order-preserving, boundary-aware interval precision/recall/F1 and boundary MAE/accuracy at ±0.01/0.05/0.10 m. Level 4: component geological consistency with explicit evaluated coverage. Hierarchical lithology paths provide auxiliary ancestor-set precision/recall/F1 and never replace exact match. Latency, RAM/VRAM, tokens, and cost are logged.

Error taxonomy includes OCR digit/character/decimal errors, layout/column/row errors, interval errors, semantic/normalization errors, hallucination, constraint errors, and reread failures.

## 7. Results

See [generated/current_results.md](generated/current_results.md). These rows are audit-only. On four quarantined Chinese panels, B4 produced 3/4 Schema-valid responses; one reached the 1024-token cap. Valid records emitted eight intervals, while C1–C10 diagnosed 20 violations across 82 evaluated items. Mean inference time was 50.637 s/image and peak allocated VRAM about 9.29 GB. <!-- evidence:p1.b4_sanming --> B5 few-shot produced only 1/4 Schema-valid responses; three hit the token cap and mean latency rose to 59.301 s/image. <!-- evidence:p1.b5_sanming --> Thus the current few-shot prompt did not improve structured-output stability. This is prompt/model behavior, not accuracy: annotations remain `auto` and rights-unverified. On four BGS first pages, B4 produced 4/4 valid empty records in 6.397 s/image on average, an abstention/coverage failure rather than successful extraction. <!-- evidence:p1.b4_bgs --> On the 11-document/15-page Padova set, direct native text covered 11/11 header IDs at 0.125 s/page but emitted no intervals. <!-- evidence:p1.directpdf_padova --> B2 text-only extraction produced 13/15 Schema-valid responses and 74 unverified intervals; two responses hit the 1536-token cap. Mean inference was 35.332 s/page and peak allocated GPU memory was 9.296 GB. <!-- evidence:p1.b2_padova --> B3 recovered 46 unverified interval ranges on 5/15 pages in 0.039 s/page; it abstained on the ten pages whose boundaries were graphical or lacked a repeated textual depth column. <!-- evidence:p1.b3_padova --> B4 produced 11/15 Schema-valid responses, emitted 87 unverified intervals, and hit the 1536-token cap on all four failed responses; mean inference was 60.987 s/page with 9.356 GB peak allocated GPU memory. <!-- evidence:p1.b4_padova --> B6 fused the 11 valid VLM records with grounded proposals: 17 field agreements, one explicit disagreement, 34 visual-only review decisions, and four pages retaining grounded data because VLM output was unavailable. <!-- evidence:p1.b6_padova --> These are coverage and decision-path counts, not correctness. The source itself includes a `TS5.pdf` whose header reads `TS2`, so filenames cannot be silently treated as GT. Formal comparison, random-versus-disjoint generalization, degradation curves, GT-based error distribution, and statistical intervals remain `TBD`.

Auto-generated audit visuals are [audit coverage](generated/figures/audit_coverage.png)
and [degradation inputs](generated/figures/degradation_inputs.png). The first
mixes only explicitly labelled availability/parse-coverage diagnostics and is
not an accuracy plot; the second counts generated inputs and has no measured
performance axis.

## 8. Discussion and Threats to Validity

The BGS audit demonstrates why coverage must accompany MAE: zero extracted final-depth values yield undefined MAE, not zero error. RapidOCR correctly extracted header IDs but initially lost coordinates because OCR deleted header spaces; a versioned repair restored header extraction without improving interval coverage. These observations cannot be generalized beyond four documents.

Major threats are Chinese source rights, project/template diversity, annotation reliability, field missingness, model version drift, prompt instability, and benchmark leakage. The engineering audit also shows that valid JSON is not equivalent to valid geology: absolute elevations were confused with measured depths, producing inverted/inconsistent intervals detected by C1/C2/C4. Formal effects will be quantified or marked `TBD` rather than inferred.

## 9. Reproducibility and Ethics

Experiment IDs, Git commits, dataset/split/model/prompt versions, seed, hardware/software, metrics, predictions, errors, and logs are frozen. Sensitive project names, contacts, signatures, and coordinates require anonymization decisions. No quarantined candidate will be redistributed without authorization.

## 10. Conclusion

We present the executable definition and infrastructure for a provenance-aware Chinese borehole-log benchmark. A publishable conclusion about model performance or split leakage is `TBD` until the rights-cleared dataset and required experiments are complete.

The repository's auto-generated [publication-readiness audit](../../docs/generated/publication_readiness.md)
currently reports zero exportable human-GT annotations and zero formal Paper I
runs. Audit-only results above do not satisfy the completion gate.

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

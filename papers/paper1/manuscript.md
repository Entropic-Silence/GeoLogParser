# A Benchmark for Structured Information Extraction from Heterogeneous Chinese Borehole Logs

## Abstract

Legacy borehole logs encode coordinates, elevations, interval boundaries, and geological descriptions in heterogeneous tables, scans, and drawings. Existing OCR scores do not establish whether these records can be converted into reliable databases, and page-level random splits can leak project templates. We define a provenance-bearing extraction task, a panel-aware annotation unit, leakage-resistant split protocols, a four-level evaluation framework, degradation metadata, and an error taxonomy. The rights-cleared Chinese benchmark size, model comparison, split-generalization gap, robustness results, and human agreement are `TBD`. Four-document British Geological Survey audits validate the executable OCR/VLM paths and expose coverage failures; a rights-unverified four-panel Chinese audit exposes truncation and geological inconsistency. A 15-page CC BY 4.0 international audit further exposes output-length failures and exercises conservative OCR/VLM fusion. None is a representative benchmark result. The intended contribution is a reproducible benchmark centered on data quality, provenance, and cross-template generalization rather than a new network.

## 1. Introduction

Borehole logs are machine-readable only when numerical boundaries, geological text, layout, and source evidence remain linked. Treating a page as plain OCR text loses column semantics; treating it as an unconstrained image-to-JSON prompt obscures failures and provenance. This paper asks: (RQ1) how accurately do OCR, VLM, and hybrid systems structure Chinese borehole logs; (RQ2) how strongly does random page splitting overestimate deployment generalization; (RQ3) which degradation factors matter most; and (RQ4) which error classes dominate?

The paper's contribution boundary is data and benchmark. Geological constraint-guided correction belongs to Paper II; database/3D error propagation belongs to Paper III. Data or tables may be reused with disclosure, but method and downstream claims are not duplicated.

## 2. Related Work

Document OCR, table understanding, multimodal structured extraction, geological data standards, and benchmark leakage literature will be reviewed here. Verified citations are `TBD`; no unverified DOI or conclusion is included in this draft.

## 3. Task Definition

One input unit is one borehole panel from PDF/JPG/PNG. Multi-borehole pages are split by a recorded normalized crop. Output follows `borehole_v001.schema.json`: borehole fields, ordered intervals, raw and normalized terminology, and an evidence envelope containing page, bbox, source text, extraction method, confidence, validation status, and warnings. Missing evidence remains null. SI values coexist with raw text/unit.

The first evaluation scope includes borehole ID, collar elevation, final depth, groundwater depth, interval top/bottom/thickness, lithology, and description. Coordinates are an extension already supported by the Schema.

## 4. Dataset Construction

### 4.1 Sources and rights

Every item records organization, URL, access date, licence, usage, redistribution policy, and citation. Public BGS audit material is governed by its captured OGL terms. A University of Padova CC BY 4.0 dataset (DOI `10.25430/researchdata.cab.unipd.it.00001663`) contributes 11 international borehole PDFs/15 native-PDF pages after archive hash verification. All 15 pages have rendered, hashed `auto` proposals but remain unannotated by a human. Chinese web candidates remain in quarantine because item-level redistribution, privacy, stamps, signatures, and precise-location review are incomplete. Four additional CGS DOI records remain metadata-only because no identifiable item licence was found. Therefore the rights-cleared Chinese benchmark currently has `TBD` documents/pages/intervals and is not released.

### 4.2 Annotation

The local UI shows a panel beside editable provenance-bearing fields. Auto proposals have status `auto`; human stages are `single_verified`, `double_verified`, and `expert_verified`. Saves create immutable revisions. Inter-annotator or repeated self-agreement protocol and sample size are `TBD`.

### 4.3 Metadata and splits

Metadata covers source, project, template, native/scanned/image type, resolution, blur/noise/skew, stamps, handwriting, and artifacts. Split A is random page/panel reference only. Primary splits are project-disjoint, template-disjoint, and, if data permit, source-disjoint. Group IDs are assigned before splitting. Exact split versions and counts are `TBD`.

### 4.4 Degradation benchmark

Real and synthetic degradation cover resolution, blur, noise, skew, JPEG compression, contrast reduction, broken lines, watermarks, stamps, and occlusion. Every synthetic parameter and source hash is saved. Training variants never enter test. Severity grids are `TBD`.

## 5. Baselines

B1 OCR+regex; B2 OCR+LLM; B3 OCR+layout+rules; B4 zero-shot VLM; B5 few-shot VLM; B6 OCR+VLM fusion. Adapters and model revisions come from a registry. Current executed audits cover Tesseract+regex and RapidOCR+regex on four BGS documents, plus Apache-2.0 Qwen3-VL-4B at fixed revision `ebb281ec...` through local B4/B5 adapters. B4 uses greedy decoding and versioned prompt `vlm_extract_v002`; whole-image values are marked `VLM_UNGROUNDED`. B6 conservatively retains grounded evidence on disagreement and sends visual-only or conflicting fields to review. B2, B3, and formal Chinese runs are `TBD`.

## 6. Evaluation

Level 1: CER, WER, numeric CER. Level 2: exact categorical matches; numeric coverage plus paired MAE. Level 3: order-preserving, boundary-aware interval precision/recall/F1 and boundary MAE/accuracy at ±0.01/0.05/0.10 m. Level 4: component geological consistency with explicit evaluated coverage. Hierarchical lithology metrics supplement, never replace, exact match. Latency, RAM/VRAM, tokens, and cost are logged.

Error taxonomy includes OCR digit/character/decimal errors, layout/column/row errors, interval errors, semantic/normalization errors, hallucination, constraint errors, and reread failures.

## 7. Results

See [generated/current_results.md](generated/current_results.md). These rows are audit-only. On four quarantined Chinese panels, B4 produced 3/4 Schema-valid responses; one reached the 1024-token cap. Valid records emitted eight intervals, while C1–C10 diagnosed 20 violations across 82 evaluated items. Mean inference time was 50.637 s/image and peak allocated VRAM about 9.29 GB. B5 few-shot produced only 1/4 Schema-valid responses; three hit the token cap and mean latency rose to 59.301 s/image. Thus the current few-shot prompt did not improve structured-output stability. This is prompt/model behavior, not accuracy: annotations remain `auto` and rights-unverified. On four BGS first pages, B4 produced 4/4 valid empty records in 6.397 s/image on average, an abstention/coverage failure rather than successful extraction. On the 11-document/15-page Padova set, direct native text covered 11/11 header IDs at 0.125 s/page but emitted no intervals. B4 produced 11/15 Schema-valid responses, emitted 87 unverified intervals, and hit the 1536-token cap on all four failed responses; mean inference was 60.987 s/page with 9.356 GB peak allocated GPU memory. B6 fused the 11 valid VLM records with grounded proposals: 17 field agreements, one explicit disagreement, 34 visual-only review decisions, and four pages retaining grounded data because VLM output was unavailable. These are coverage and decision-path counts, not correctness. The source itself includes a `TS5.pdf` whose header reads `TS2`, so filenames cannot be silently treated as GT. Formal comparison, random-versus-disjoint generalization, degradation curves, GT-based error distribution, and statistical intervals remain `TBD`.

## 8. Discussion and Threats to Validity

The BGS audit demonstrates why coverage must accompany MAE: zero extracted final-depth values yield undefined MAE, not zero error. RapidOCR correctly extracted header IDs but initially lost coordinates because OCR deleted header spaces; a versioned repair restored header extraction without improving interval coverage. These observations cannot be generalized beyond four documents.

Major threats are Chinese source rights, project/template diversity, annotation reliability, field missingness, model version drift, prompt instability, and benchmark leakage. The engineering audit also shows that valid JSON is not equivalent to valid geology: absolute elevations were confused with measured depths, producing inverted/inconsistent intervals detected by C1/C2/C4. Formal effects will be quantified or marked `TBD` rather than inferred.

## 9. Reproducibility and Ethics

Experiment IDs, Git commits, dataset/split/model/prompt versions, seed, hardware/software, metrics, predictions, errors, and logs are frozen. Sensitive project names, contacts, signatures, and coordinates require anonymization decisions. No quarantined candidate will be redistributed without authorization.

## 10. Conclusion

We present the executable definition and infrastructure for a provenance-aware Chinese borehole-log benchmark. A publishable conclusion about model performance or split leakage is `TBD` until the rights-cleared dataset and required experiments are complete.

## References

`[CITATIONS TO VERIFY]`

<!-- AUTO-GENERATED REVIEW BUNDLE. DO NOT EDIT. -->
> Package status: **DRAFT_NOT_SUBMISSION_READY**
> This bundle combines the versioned manuscript and generated results for review.
> Blockers: unresolved TBD/citation markers remain.

# Geology-Constrained Multimodal Structured Information Extraction from Borehole Logs

## Abstract

We study whether geological and numerical constraints can improve the reliability of multimodal borehole-log extraction without rule-based overwriting. The method separates OCR, layout, VLM evidence, conservative fusion, constraint diagnosis, high-resolution ROI rereading, candidate ranking, terminology normalization, and confidence calibration. Constraints trigger review or evidence-based proposals; they never silently replace source values. The implemented system includes C1–C10, conservative candidate ranking, ROI OCR rereading, abstention, review queues, calibration primitives, and a Ground-Truth-gated batch evaluator. On 31 real BGS scans with authoritative metadata, exact non-null consensus between Tesseract and RapidOCR auto-accepted 87/124 evaluated metadata fields at 100% accepted accuracy and routed all 37 observed errors or omissions to review. A separately frozen constraint-reread policy was evaluated on 20 Swissgeol documents/55 intervals with zero overlap to development records. It failed to trigger on all three incorrect first-pass documents, triggered one of 17 correct documents, accepted no reread, and left interval F1 unchanged at 0.855; false correction rate was undefined because no correction was accepted. The negative result shows that structural validity and reader-disagreement triggers alone do not detect plausible but incorrect interval sequences. <!-- evidence:p2.swissgeol_heldout_constraint_reread -->

## 1. Introduction

Critical borehole errors are often numerical: a missed decimal, swapped column, inverted boundary, or wrong coordinate can corrupt downstream geology while character accuracy remains high. Pure OCR lacks domain structure; direct VLM-to-JSON extraction can hallucinate and hide provenance. We ask whether explicit geology constraints and targeted rereading reduce critical error while retaining safe abstention.

RQ1 tests constraint benefit; RQ2 compares constraint-guided rereading to single pass; RQ3 measures each constraint family; RQ4 targets depth/thickness/coordinate/elevation error; RQ5 evaluates `needs_review` detection. The method contribution is distinct from Paper I's benchmark and Paper III's downstream workflow.

## 2. Related Work

Multimodal document encoders demonstrate why text should be modelled jointly with page layout and visual evidence [@xu2020layoutlm; @xu2021layoutlmv2], but borehole reliability additionally depends on numerical and stratigraphic relations absent from generic document labels. The directly related borehole-log OCR/database study of Han and Suh confirms that this is an active applied extraction problem [@han2024boreholeocr]; the present paper isolates a different question: whether explicit, non-mutating geological constraints and targeted rereading improve safety.

Grammar-constrained decoding can restrict a language model to a formally defined output language [@geng2023grammar], which is useful for Schema-valid generation but cannot establish that a syntactically valid depth or lithology is correct. GeoLogParser consequently evaluates JSON validity separately from source grounding and geological consistency. Likewise, lithology normalization is not a flat string-replacement problem: published controlled vocabularies carry identifiers, definitions, and hierarchical relations, while different schemes reflect different institutional purposes [@mccormick2023lithology]. This motivates retaining the historical raw term, normalized term, vocabulary/version, and confidence rather than silently replacing the source wording.

Modern classifiers can be poorly calibrated, motivating post-hoc calibration such as temperature scaling [@guo2017calibration]. We therefore distinguish raw model confidence from an engineering confidence assembled from extraction, agreement, constraint, OCR, and layout evidence, and assess it with both calibration error and the proper squared-probability score introduced by Brier [@brier1950verification]. The verified literature supports the component choices and their limitations; it does not establish that constraint-guided rereading is effective on this benchmark. That effect remains an empirical question for the registered ablations and correction-safety study.

## 3. Method

### 3.1 Modular extraction

Document type detection routes native PDF text or rendered-page OCR. Layout preserves panel, region, column, and bbox. OCR and VLM adapters return common evidence; structured extraction writes the v001 Schema. Every module is independently switchable.

### 3.2 Geological constraints

C1 validates bottom>top. C2 checks thickness against bottom−top with configured tolerance. C3 marks gaps/overlap; C4 detects monotonic inversions; C5 compares final depth and last bottom; C6 reviews groundwater definitions/ranges; C7 enforces configurable percentages; C8 flags coordinate/elevation OCR formats; C9 weakly reviews simple layer-code sequences; C10 detects field-type/column inconsistency. Each result returns pass, score, severity, affected fields, reason, action, evaluated count, and violations. Missing inputs do not count as passes.

### 3.3 Constraint-guided rereading

Violations locate provenance bboxes. The system pads and upscales the ROI, runs registered readers, parses candidates, and stores raw evidence. Ranking combines evidence confidence, cross-model agreement, layout confidence, and change in target constraint violations. Candidates sharing a value reinforce agreement. An acceptance proposal requires reduced target violations, minimum total score, minimum margin against the best different value, and exactly one distinct value per contributing reader; a reader that sees multiple numbers forces review because the ROI may span columns. Otherwise the output is `NEEDS_REVIEW`. The source record is not mutated; proposals carry an audit warning and require subsequent policy/human handling. Numeric Tesseract ROI rereading is integrated into the annotation UI with revision and source/crop hashes. A local Qwen3-VL ROI adapter accepts only a strict numeric-token JSON schema, assigns no uncalibrated confidence or token bbox, and withholds uncertain tokens from ranking.

### 3.4 Normalization and confidence

Raw and normalized terms are separate. Ontology coverage is data-driven and source standards/periods are recorded. Confidence fusion renormalizes available extraction, agreement, constraint, OCR, and layout components. Temperature scaling is fitted only on labelled validation observations. ECE, Brier, and reliability curves evaluate calibration.

The auto-generated [method schematic](generated/figures/method_schematic.png)
is a design figure, not an empirical result.

## 4. Experimental Design

Data and splits follow Paper I without redefining the benchmark. Baselines are single-pass B1–B6. The full method is compared with one-module-at-a-time ablations: −constraints, −rereading, −layout, −OCR, −VLM, −normalization, and −calibration. The implemented ablation runner rejects case-set drift and any named variant that disables more or fewer modules than its declared single removal; all variants share exact case IDs, references, originals, review labels, GT status, and calibration/test partition. Seeds/repeats, model revisions, prompts, and compute are recorded. For the first real interval method test, the trigger and reread policy was frozen on the nine v001 development records before examining outcomes on the incremental v002 set. The evaluation contains 20 documents/55 intervals and has zero record overlap with development. First-pass extraction uses 250-DPI Tesseract PSM 3. Empty interval sections, suspicious numeric ranges, or disagreement with a PSM-4 trigger reader initiate 350-DPI full-page and fixed-ROI rereading with PSM 3/4/6; acceptance requires repeated identical support and preserves baseline intervals unless a unique supported sequence is available. Remaining multi-model interval ablations are `TBD`.

Primary metrics include interval/field scores, critical numerical error rate (`TBD` field thresholds), geological component consistency and coverage, manual-review recall, review rate, auto-accept error rate, and false correction rate. Critical numerical error counts a missing prediction or absolute error above a configured field threshold among present numeric GT; threshold equality is accepted and the domain thresholds remain frozen experiment inputs rather than universal constants. Auto-accept error rate is review-required fields not sent to review divided by all auto-accepted fields. FCR is incorrect automatic corrections divided by all automatic corrections; zero corrections or zero auto-accepted fields yields undefined, not zero.

The implemented Paper II evaluator refuses `auto` labels, requires human-verified cases, and requires disjoint calibration and test partitions before fitting temperature scaling or reporting correction/review/calibration metrics. The `−calibration` ablation explicitly bypasses temperature scaling rather than merely relabelling an otherwise identical run. This prevents engineering audits and ineffective module toggles from entering the formal result table.

## 5. Results

A real authoritative-metadata experiment applied a reference-blinded decision policy to the matched 300-DPI Tesseract and RapidOCR first-pass outputs for 31 BGS documents. The policy accepted a field only when both readers emitted the same non-null value; official references were read only after decisions were frozen. Overall coverage was 87/124 = 0.702, accepted accuracy was 1.000, and all 37 observed errors or omissions were routed to review. By field, borehole-ID coverage was 25/31 with 1.000 accepted accuracy and 6/6 erroneous or disagreeing cases reviewed; both coordinate fields achieved 31/31 coverage and 1.000 accepted accuracy. Final-depth coverage was 0/31, because Tesseract abstained throughout and RapidOCR emitted only one conflicting value; all 31 cases were routed to review. This is evidence that cross-reader agreement can safely trade coverage for reliability on these metadata fields, not evidence for geological-constraint correction or interval extraction. <!-- evidence:p2.bgs_metadata_consensus -->

A 127-case scripted-decision matrix exercised the metric and ablation plumbing but is retained only as failure analysis: because its variant outcomes were prescribed rather than generated by the corresponding extraction modules, its apparent differences are excluded from the method table. A replacement controlled experiment executes the actual constraint evaluator and rereading ranker on the same 127 Synthetic interval cases. On its 97-case test partition, the full ranker accepted 54 corrections, all successful, with FCR 0/54, review recall 1.000, review rate 0.443, and auto-accept error 0.000. Removing the constraint component accepted 97 proposals but corrected none of 97 accepted errors and had auto-accept error 0.144; removing rereading produced no automatic corrections and reviewed all cases. Calibration reduced full-method ECE from 0.108 to 0.040. These are controlled algorithm tests, not real-document effects. <!-- evidence:p2.executed_synthetic_ablation -->

The frozen real-interval policy produced a negative held-out result. On 20 Swissgeol documents and 55 source-agreement intervals, the first pass and final reread output both matched 47 intervals with precision = recall = F1 = 0.855. Three documents were incorrect after the first pass, but none met any reread trigger, so incorrect-document trigger recall was 0/3. One of 17 correct documents triggered and was routed to review; no reread proposal was accepted. Consequently there were zero automatic corrections, final F1 was unchanged, correction success was undefined, and FCR was undefined rather than zero. The observed result does not support an interval-level benefit for this trigger policy. <!-- evidence:p2.swissgeol_heldout_constraint_reread -->

See [generated/current_results.md](generated/current_results.md). One two-case public Padova engineering audit is indexed, but both source annotations remain `auto`; it is not a method-effect experiment. Qwen3-VL returned schema-valid numeric-token JSON for both ROIs, OCR and VLM shared at least one numeric candidate in both cases, and both decisions remained `NEEDS_REVIEW`; no proposal was accepted. Mean VLM generation time was 3.510 s/ROI and peak allocated GPU memory was 8.413 GiB. <!-- evidence:p2.roi_reread_audit --> Accuracy and false correction rate are undefined for that audit. The held-out Swissgeol result supplies a real interval test of the frozen trigger policy, but broader multi-model ablations, calibration on real intervals, correction-safety estimation with accepted corrections, and statistical tests remain `TBD`.

## 6. Failure Analysis

Categories include constraint false positive/negative, ambiguous ROI, OCR/VLM agreement on a wrong value, layout mislocalization, candidate omission, reread failure, normalization error, and unsafe correction. The Swissgeol held-out errors reveal a central blind spot: all three incorrect first-pass documents produced interval sequences plausible enough to evade empty-section, suspicious-range, and reader-disagreement triggers. Constraint consistency was therefore not equivalent to correctness, and the policy had no opportunity to generate or rank corrective candidates. Conversely, the single triggered correct document demonstrates avoidable review without corresponding error capture. In the public Padova audit, the narrow elevation crop contained one field and both readers found `35.22`; it remained under review because changing to the same value did not reduce a violation. The groundwater provenance bbox spanned worksite, borehole, total depth, water table, and date cells. Both readers therefore saw `15.00` and `-5.80`; the constraint score favored `15.0` because it removed a negative-depth warning even though that number belonged to total depth. The run abstained because candidates were ambiguous. This observed failure motivated a stricter post-run policy that forces review whenever one reader emits multiple distinct numbers. It demonstrates a layout-localization hazard, not an error rate, because the source annotation is not human Ground Truth.

## 7. Discussion

Constraint consistency is not correctness: a plausible but wrong continuous sequence can pass. The held-out trigger recall of 0/3 confirms this risk empirically for the present policy. Weak constraints must not dominate pixel evidence. Requiring violation reduction and abstention protects against some false corrections, but it cannot improve errors that never trigger rereading. Future trigger redesign must be developed on new records and evaluated on another untouched set; adapting the policy to these observed v002 failures and re-reporting on the same records would invalidate the held-out estimate.

## 8. Reproducibility, Safety, and Ethics

UI-triggered numeric runs store ROI crops and hashes, raw OCR regions, VLM generations and model revisions, prompt/configuration, candidates, component scores, before/after violations, and proposals. A recursive artifact manifest hashes each ROI and field-level result, while the result index hashes that manifest and all core outputs. Subsequent human review actions must follow the same trace. Paid APIs require explicit authorization; local models are preferred for privacy. Quarantined project data remain local. Human timing is event-based; development time is never substituted.

## 9. Conclusion

We provide an implemented non-mutating constraint and rereading architecture designed for safe geological structuring. Real authoritative metadata show that strict cross-reader consensus can reach error-free accepted output by abstaining on disagreements and missing values, but this narrows coverage to 70.2% overall and 0% for final depth. On the first disjoint real interval test, the frozen structural/disagreement trigger failed to identify any of three incorrect documents, accepted no corrections, and left interval F1 unchanged at 0.855. Thus the current trigger design did not improve held-out interval extraction, and FCR is undefined because no automatic correction occurred. The result narrows the method claim and motivates trigger evidence beyond sequence plausibility, followed by evaluation on a new untouched set.

The repository's auto-generated [publication-readiness audit](../../docs/generated/publication_readiness.md)
tracks the real authoritative-metadata abstention run, the controlled Synthetic
ablation, and the negative held-out real interval experiment as distinct evidence
classes.

## References

Shared bibliography: [../references.bib](../references.bib). Citation metadata and permitted claim scope are logged in [../../docs/literature_evidence.yaml](../../docs/literature_evidence.yaml).

# Appendix: Machine-Generated Current Results

<!-- AUTO-GENERATED. DO NOT EDIT. -->
### Real authoritative-metadata consensus and abstention

| Experiment | Field | Reference n | Auto-accepted | Coverage | Accepted accuracy | Review | Review recall | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P2_BGS_METADATA_CONSENSUS_ABSTENTION_001 | borehole_id | 31 | 25 | 25/31 (0.806) | 1.000 | 6 | 1.000 | formal_authoritative_metadata_method |
| P2_BGS_METADATA_CONSENSUS_ABSTENTION_001 | x_coordinate | 31 | 31 | 31/31 (1.000) | 1.000 | 0 | TBD | formal_authoritative_metadata_method |
| P2_BGS_METADATA_CONSENSUS_ABSTENTION_001 | y_coordinate | 31 | 31 | 31/31 (1.000) | 1.000 | 0 | TBD | formal_authoritative_metadata_method |
| P2_BGS_METADATA_CONSENSUS_ABSTENTION_001 | final_depth_m | 31 | 0 | 0/31 (0.000) | TBD | 31 | 1.000 | formal_authoritative_metadata_method |

The decision policy accepts only equal non-null values from two independent OCR readers. References are consulted only after decisions are frozen. This is real metadata-field evidence; interval/lithology effects remain unmeasured.

### Held-out authoritative-interval constraint-rereading result

| Experiment | Documents | Reference intervals | First-pass F1 | Reread F1 | Triggered | Accepted rereads | Needs review | Incorrect-doc trigger recall | Correct-doc trigger rate | Correction success | FCR | Eligibility |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P2_SWISSGEOL_TG_CONSTRAINT_REREAD_HELDOUT_001 | 20 | 55 | 0.855 | 0.855 | 1 | 0 | 1 | 0/3 (0.000) | 1/17 (0.059) | TBD | TBD | formal_authoritative_interval_method |

The policy was frozen on v001 records and evaluated on source-agreement records absent from development. A null FCR means no automatic correction occurred; it is not zero. The same-source, explicit-table selection remains a major limitation.

### Public ROI engineering audit (no Ground Truth)

| Experiment | Cases | VLM JSON-valid | VLM uncertain | OCR/VLM numeric-agreement cases | Accept proposals | Needs review | VLM s/ROI | Peak GiB | Eligibility |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P2_QWEN3VL4B_TESSERACT_UNIPD_ROI_AUDIT_001 | 2 | 2/2 | 0 | 2 | 0 | 2 | 3.510 | 8.413 | audit_only |

These rows report parser, candidate-path, latency, and resource behavior only. Source annotations are `auto`; accuracy, correction success, and FCR are undefined.

### Method and ablation results

<!-- AUTO-GENERATED. DO NOT EDIT. -->
| Experiment | Variant | Disabled | Calibration n | Test n | Correction success | FCR | Review recall | Review rate | Auto-accept error | Raw ECE | Calibrated ECE | Eligibility |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P2_EXECUTED_SYNTHETIC_ABLATION_001 | full | none | 30 | 97 | 54/54 (1.000) | 0/54 (0.000) | 14/14 (1.000) | 43/97 (0.443) | 0/54 (0.000) | 0.108 | 0.040 | formal_synthetic_method |
| P2_EXECUTED_SYNTHETIC_ABLATION_001 | minus_calibration | calibration | 30 | 97 | 54/54 (1.000) | 0/54 (0.000) | 14/14 (1.000) | 43/97 (0.443) | 0/54 (0.000) | 0.108 | 0.108 | formal_synthetic_method |
| P2_EXECUTED_SYNTHETIC_ABLATION_001 | minus_constraints | constraints | 30 | 97 | 0/97 (0.000) | 0/97 (0.000) | 0/14 (0.000) | 0/97 (0.000) | 14/97 (0.144) | 0.166 | 0.000 | formal_synthetic_method |
| P2_EXECUTED_SYNTHETIC_ABLATION_001 | minus_layout | layout | 30 | 97 | 54/54 (1.000) | 0/54 (0.000) | 14/14 (1.000) | 43/97 (0.443) | 0/54 (0.000) | 0.108 | 0.040 | formal_synthetic_method |
| P2_EXECUTED_SYNTHETIC_ABLATION_001 | minus_normalization | normalization | 30 | 97 | 54/54 (1.000) | 0/54 (0.000) | 14/14 (1.000) | 43/97 (0.443) | 0/54 (0.000) | 0.108 | 0.040 | formal_synthetic_method |
| P2_EXECUTED_SYNTHETIC_ABLATION_001 | minus_ocr | ocr | 30 | 97 | TBD | TBD | 14/14 (1.000) | 97/97 (1.000) | TBD | 0.310 | 0.175 | formal_synthetic_method |
| P2_EXECUTED_SYNTHETIC_ABLATION_001 | minus_rereading | rereading | 30 | 97 | TBD | TBD | 14/14 (1.000) | 97/97 (1.000) | TBD | 0.310 | 0.175 | formal_synthetic_method |
| P2_EXECUTED_SYNTHETIC_ABLATION_001 | minus_vlm | vlm | 30 | 97 | TBD | TBD | 14/14 (1.000) | 97/97 (1.000) | TBD | 0.310 | 0.175 | formal_synthetic_method |

Rows are generated from identical-case, one-module-at-a-time matrices. `formal_synthetic_method` rows are controlled Synthetic evidence and do not support human-GT claims; human-GT rows remain separately labelled.

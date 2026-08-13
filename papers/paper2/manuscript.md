# Geology-Constrained Multimodal Structured Information Extraction from Borehole Logs

## Abstract

We study whether geological and numerical constraints can improve the reliability of multimodal borehole-log extraction without rule-based overwriting. The method separates OCR, layout, VLM evidence, conservative fusion, constraint diagnosis, high-resolution ROI rereading, candidate ranking, terminology normalization, and confidence calibration. Constraints trigger review or evidence-based proposals; they never silently replace source values. The implemented system includes C1–C10, conservative candidate ranking, ROI OCR rereading, abstention, review queues, calibration primitives, and a Ground-Truth-gated batch evaluator. Main benchmark, ablation, false-correction, manual-review recall, and calibration results are `TBD`; consequently no superiority claim is made in this draft.

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

Data and splits follow Paper I without redefining the benchmark. Baselines are single-pass B1–B6. The full method is compared with one-module-at-a-time ablations: −constraints, −rereading, −layout, −OCR, −VLM, −normalization, and −calibration. The implemented ablation runner rejects case-set drift and any named variant that disables more or fewer modules than its declared single removal; all variants share exact case IDs, references, originals, review labels, GT status, and calibration/test partition. Seeds/repeats, model revisions, prompts, and compute are recorded. Exact empirical configurations are `TBD`.

Primary metrics include interval/field scores, critical numerical error rate (`TBD` field thresholds), geological component consistency and coverage, manual-review recall, review rate, auto-accept error rate, and false correction rate. Critical numerical error counts a missing prediction or absolute error above a configured field threshold among present numeric GT; threshold equality is accepted and the domain thresholds remain frozen experiment inputs rather than universal constants. Auto-accept error rate is review-required fields not sent to review divided by all auto-accepted fields. FCR is incorrect automatic corrections divided by all automatic corrections; zero corrections or zero auto-accepted fields yields undefined, not zero.

The implemented Paper II evaluator refuses `auto` labels, requires human-verified cases, and requires disjoint calibration and test partitions before fitting temperature scaling or reporting correction/review/calibration metrics. The `−calibration` ablation explicitly bypasses temperature scaling rather than merely relabelling an otherwise identical run. This prevents engineering audits and ineffective module toggles from entering the formal result table.

## 5. Results

A 127-case scripted-decision matrix exercised the metric and ablation plumbing but is retained only as failure analysis: because its variant outcomes were prescribed rather than generated by the corresponding extraction modules, its apparent differences are excluded from the method table. A replacement controlled experiment executes the actual constraint evaluator and rereading ranker on the same 127 Synthetic interval cases. On its 97-case test partition, the full ranker accepted 54 corrections, all successful, with FCR 0/54, review recall 1.000, review rate 0.443, and auto-accept error 0.000. Removing the constraint component accepted 97 proposals but corrected none of 97 accepted errors and had auto-accept error 0.144; removing rereading produced no automatic corrections and reviewed all cases. Calibration reduced full-method ECE from 0.108 to 0.040. These are controlled algorithm tests, not real-document effects.

See [generated/current_results.md](generated/current_results.md). One two-case public Padova engineering audit is indexed, but both source annotations remain `auto`; it is not a method-effect experiment. Qwen3-VL returned schema-valid numeric-token JSON for both ROIs, OCR and VLM shared at least one numeric candidate in both cases, and both decisions remained `NEEDS_REVIEW`; no proposal was accepted. Mean VLM generation time was 3.510 s/ROI and peak allocated GPU memory was 8.413 GiB. <!-- evidence:p2.roi_reread_audit --> Accuracy, false correction rate, and method benefit are undefined. Main results, ablations, constraint contribution, calibration, correction safety, and statistical tests remain `TBD`.

## 6. Failure Analysis

Planned categories are constraint false positive/negative, ambiguous ROI, OCR/VLM agreement on a wrong value, layout mislocalization, candidate omission, reread failure, normalization error, and unsafe correction. In the public audit, the narrow elevation crop contained one field and both readers found `35.22`; it remained under review because changing to the same value did not reduce a violation. The groundwater provenance bbox spanned worksite, borehole, total depth, water table, and date cells. Both readers therefore saw `15.00` and `-5.80`; the constraint score favored `15.0` because it removed a negative-depth warning even though that number belonged to total depth. The run abstained because candidates were ambiguous. This observed failure motivated a stricter post-run policy that forces review whenever one reader emits multiple distinct numbers. It demonstrates a layout-localization hazard, not an error rate, because the source annotation is not human Ground Truth.

## 7. Discussion

Constraint consistency is not correctness: a plausible but wrong continuous sequence can pass. Weak constraints must not dominate pixel evidence. Requiring violation reduction and abstention protects against some false corrections but does not establish safety without labelled trials. Thresholds and ranking weights must be selected on validation data and frozen before test.

## 8. Reproducibility, Safety, and Ethics

UI-triggered numeric runs store ROI crops and hashes, raw OCR regions, VLM generations and model revisions, prompt/configuration, candidates, component scores, before/after violations, and proposals. A recursive artifact manifest hashes each ROI and field-level result, while the result index hashes that manifest and all core outputs. Subsequent human review actions must follow the same trace. Paid APIs require explicit authorization; local models are preferred for privacy. Quarantined project data remain local. Human timing is event-based; development time is never substituted.

## 9. Conclusion

We provide an implemented non-mutating constraint and rereading architecture designed for safe geological structuring. Whether it improves extraction and lowers critical error/FCR is `TBD` pending the full Paper II experiment suite.

The repository's auto-generated [publication-readiness audit](../../docs/generated/publication_readiness.md)
currently reports zero formal Paper II runs; the indexed two-case ROI audit,
software tests, and design diagrams do not satisfy the empirical completion
gate.

## References

Shared bibliography: [../references.bib](../references.bib). Citation metadata and permitted claim scope are logged in [../../docs/literature_evidence.yaml](../../docs/literature_evidence.yaml).

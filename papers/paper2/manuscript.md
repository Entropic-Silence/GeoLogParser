# Geology-Constrained Multimodal Structured Information Extraction from Borehole Logs

## Abstract

We study whether geological and numerical constraints can improve the reliability of multimodal borehole-log extraction without rule-based overwriting. The method separates OCR, layout, VLM evidence, constraint diagnosis, high-resolution ROI rereading, candidate ranking, terminology normalization, and confidence calibration. Constraints trigger review or evidence-based proposals; they never silently replace source values. The implemented system includes C1–C10, conservative candidate ranking, ROI OCR rereading, abstention, review queues, and calibration primitives. Main benchmark, ablation, false-correction, manual-review recall, and calibration results are `TBD`; consequently no superiority claim is made in this draft.

## 1. Introduction

Critical borehole errors are often numerical: a missed decimal, swapped column, inverted boundary, or wrong coordinate can corrupt downstream geology while character accuracy remains high. Pure OCR lacks domain structure; direct VLM-to-JSON extraction can hallucinate and hide provenance. We ask whether explicit geology constraints and targeted rereading reduce critical error while retaining safe abstention.

RQ1 tests constraint benefit; RQ2 compares constraint-guided rereading to single pass; RQ3 measures each constraint family; RQ4 targets depth/thickness/coordinate/elevation error; RQ5 evaluates `needs_review` detection. The method contribution is distinct from Paper I's benchmark and Paper III's downstream workflow.

## 2. Related Work

Verified discussion of multimodal document extraction, constrained decoding, self-correction, uncertainty calibration, and geological ontologies is `TBD`. Citations will be inserted only after source verification.

## 3. Method

### 3.1 Modular extraction

Document type detection routes native PDF text or rendered-page OCR. Layout preserves panel, region, column, and bbox. OCR and VLM adapters return common evidence; structured extraction writes the v001 Schema. Every module is independently switchable.

### 3.2 Geological constraints

C1 validates bottom>top. C2 checks thickness against bottom−top with configured tolerance. C3 marks gaps/overlap; C4 detects monotonic inversions; C5 compares final depth and last bottom; C6 reviews groundwater definitions/ranges; C7 enforces configurable percentages; C8 flags coordinate/elevation OCR formats; C9 weakly reviews simple layer-code sequences; C10 detects field-type/column inconsistency. Each result returns pass, score, severity, affected fields, reason, action, evaluated count, and violations. Missing inputs do not count as passes.

### 3.3 Constraint-guided rereading

Violations locate provenance bboxes. The system pads and upscales the ROI, runs registered OCR/VLM readers, parses candidates, and stores raw evidence. Ranking combines evidence confidence, cross-model agreement, layout confidence, and change in target constraint violations. Candidates sharing a value reinforce agreement. An acceptance proposal requires reduced target violations, minimum total score, and minimum margin against the best different value. Otherwise the output is `NEEDS_REVIEW`. The source record is not mutated; proposals carry an audit warning and require subsequent policy/human handling.

### 3.4 Normalization and confidence

Raw and normalized terms are separate. Ontology coverage is data-driven and source standards/periods are recorded. Confidence fusion renormalizes available extraction, agreement, constraint, OCR, and layout components. Temperature scaling is fitted only on labelled validation observations. ECE, Brier, and reliability curves evaluate calibration.

## 4. Experimental Design

Data and splits follow Paper I without redefining the benchmark. Baselines are single-pass B1–B6. The full method is compared with one-module-at-a-time ablations: −constraints, −rereading, −layout, −OCR, −VLM, −normalization, and −calibration. Seeds/repeats, model revisions, prompts, and compute are recorded. Exact configurations are `TBD`.

Primary metrics include interval/field scores, critical numerical error rate (`TBD` field thresholds), geological component consistency and coverage, manual-review recall, review rate, auto-accept risk, and false correction rate. FCR is incorrect automatic corrections divided by all automatic corrections; zero corrections yields undefined, not zero.

## 5. Results

See [generated/current_results.md](generated/current_results.md). No Paper II experiment is yet indexed. Main results, ablations, constraint contribution, calibration, correction safety, and statistical tests are `TBD`.

## 6. Failure Analysis

Planned categories are constraint false positive/negative, ambiguous ROI, OCR/VLM agreement on a wrong value, layout mislocalization, candidate omission, reread failure, normalization error, and unsafe correction. Implemented controlled tests show the policy abstains when a candidate fails to reduce violations or competing values lack margin; these tests are software verification, not empirical performance.

## 7. Discussion

Constraint consistency is not correctness: a plausible but wrong continuous sequence can pass. Weak constraints must not dominate pixel evidence. Requiring violation reduction and abstention protects against some false corrections but does not establish safety without labelled trials. Thresholds and ranking weights must be selected on validation data and frozen before test.

## 8. Reproducibility, Safety, and Ethics

ROI crops, candidates, component scores, before/after violations, proposals, and review actions will be stored. Paid APIs require explicit authorization; local models are preferred for privacy. Quarantined project data remain local. Human timing is event-based; development time is never substituted.

## 9. Conclusion

We provide an implemented non-mutating constraint and rereading architecture designed for safe geological structuring. Whether it improves extraction and lowers critical error/FCR is `TBD` pending the full Paper II experiment suite.

## References

`[CITATIONS TO VERIFY]`

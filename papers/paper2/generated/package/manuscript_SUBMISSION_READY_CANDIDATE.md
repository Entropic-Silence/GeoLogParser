<!-- AUTO-GENERATED REVIEW BUNDLE. DO NOT EDIT. -->
> Package status: **SUBMISSION_READY_CANDIDATE**
> This bundle combines the versioned manuscript and generated results for review.

# Risk-Aware Sequence Reconstruction for Borehole-Log Extraction with Auditable Constraints and Abstention

## Abstract

We study borehole-log extraction as risk-aware reconstruction of an ordered interval sequence rather than unconstrained text generation. Positioned OCR hypotheses are filtered by field semantics, linked by document order and depth geometry, and decoded by dynamic programming; a separate addition-only policy may accept supported candidates or retain the first pass. Across five record-disjoint California cohorts, unselective sequence ranking increased interval F1 from 0.383–0.450 to 0.470–0.566, but action-level false-correction rate was 0.084–0.210. On identical archived candidate pools from two confirmatory cohorts, monotonic decoding maximized F1 at 0.579 and 0.550, whereas the complete continuity/column/semantic score increased precision to 0.953 and 0.914 at lower F1. The frozen addition-only policy accepted 82 candidates in 19 documents with no observed incorrect action or worsened document, but the primary document-level one-sided 95% upper risk bound remained 0.1459. It yielded a net gain of 41 matched intervals per 100 documents, compared with 230.5 under unselective reconstruction. A one-time unseen BGS source-family evaluation abstained on every visible page, preventing false positives but providing zero utility. The evidence supports auditable sequence reconstruction and bounded correction risk, not universal source transport or safety certification. <!-- evidence:p2.california_constraint_sequence --> <!-- evidence:p2.california_v004_candidate_risk --> <!-- evidence:p2.california_v005_candidate_risk --> <!-- evidence:p2.california_candidate_risk_certificate --> <!-- evidence:p2.california_candidate_pool_ablation --> <!-- evidence:p2.california_document_risk --> <!-- evidence:p2.bgs_v003_v028_external_failure -->

## 1. Introduction

A borehole log is not a bag of recognized numbers. Depth scale ticks, cumulative boundaries, layer thicknesses, samples, water levels, and terminal depths can all form plausible monotone sequences. Selecting the wrong column can therefore produce internally consistent but geologically irrelevant output. At the same time, a correction mechanism can improve average F1 while damaging individual documents.

This paper treats extraction as two coupled problems: reconstruct the best source-grounded interval sequence, then decide whether a proposed change is safe enough to apply automatically. The central questions are:

- RQ1: which sequence components recover intervals from a fixed candidate pool?
- RQ2: how often does automatic reconstruction harm a document or action?
- RQ3: how much recovery is sacrificed by addition-only acceptance and abstention?
- RQ4: does the method transport to a genuinely unseen page family?

The contributions are:

1. a formally specified candidate graph and dynamic-programming decoder for ordered borehole intervals;
2. same-candidate-pool ablation that separates monotonic selection from continuity, column stability, and semantic score;
3. a reference-blind addition-only policy evaluated by document-level harm, action-level false-correction rate, and net utility; and
4. explicit negative transport evidence showing that conservative abstention can avoid errors while eliminating utility.

Paper I owns the evidence hierarchy and source-shift benchmark. Paper III owns downstream spatial propagation.

## 2. Related Work

Multimodal document models combine text, layout, and pixels [@xu2020layoutlm; @xu2021layoutlmv2; @kim2022donut; @hu2024docowl2], but borehole reliability additionally requires depth order and semantic ownership. Zhang et al. study same-specification image extraction [@zhang2020boreholeimages]; Han and Suh combine page typing with spreadsheet structuring [@han2024boreholeocr]; Amini et al. separate PDF discovery, selection, and capture [@amini2023boreholepdf]; Ma et al. report weaker extraction on image-based historical well records [@ma2024historicalwell]; and Shiga evaluates direct VLM structuring on a small, single-system borehole set [@shiga2026boreholevlm]. Our target is not another image-to-JSON pipeline, but auditable sequence choice and correction harm under fixed evidence.

Garzón et al. introduce geology-informed sequence and spatial metrics for automated stratigraphic interpretations of 1,394 already structured boreholes [@garzon2026stratigraphicmetrics]. Their work motivates evaluating geological order, but our problem occurs one stage earlier: candidates must first be grounded to page regions and assigned to the correct document column. Grammar-constrained decoding can guarantee a valid output language [@geng2023grammar], yet cannot establish that a valid depth belongs to the lithologic sequence.

Selective prediction permits rejection instead of forced output [@geifman2017selective; @geifman2019selectivenet]. Calibration and conformal risk-control work clarify why raw scores are not operational probabilities and why guarantees depend on the unit and exchangeability assumptions [@guo2017calibration; @angelopoulos2024crc]. We therefore make the document the primary safety unit, treat clustered actions as secondary, and report finite-sample upper bounds rather than certification.

| Closest work | Mechanism | Difference here |
|---|---|---|
| Borehole image/VLM extraction [@zhang2020boreholeimages; @shiga2026boreholevlm] | Direct or template-specific structuring | Source-grounded candidate graph, fixed-pool ablation, and correction harm |
| Geological sequence metrics [@garzon2026stratigraphicmetrics] | Evaluate structured stratigraphic interpretations | Reconstruct page-grounded intervals before interpretation |
| Grammar-constrained generation [@geng2023grammar] | Enforce valid syntax | Enforce and audit ordered evidence relations |
| Selective prediction [@geifman2017selective; @geifman2019selectivenet] | Trade coverage for risk | Preserve raw intervals, accept only supported additions, and audit document utility |
| Calibration/risk control [@guo2017calibration; @angelopoulos2024crc] | Relate confidence to error | Frozen development threshold, clustered safety units, and explicit external abstention |

## 3. Evidence and Problem Definition

Published California manual transcription is the principal Gold evidence. Swissgeol uses source-agreement references selected from explicit page tables. BGS uses an external source-agreement panel and no-reference development artifacts. These roles are not pooled.

Let the first-pass parser return interval set \(R\) and a positioned candidate pool \(C\). Each candidate retains page, normalized geometry, OCR confidence, semantic evidence, and the original source region. The sequence decoder produces \(S\). The risk policy may add a subset \(A\subseteq S\setminus R\), retain \(R\), or abstain. Reference intervals are inaccessible to every prediction and policy decision.

The main outcomes are interval precision/recall/F1, critical numerical error rate, false-correction rate (FCR), document-F1 harm, accepted-document coverage, accepted actions per document, and correct/incorrect net additions. A worsened document has lower interval F1 after the proposed output; lost matches, new incorrect predictions, and harmful-action exposure are reported separately.

## 4. Method

### 4.1 Field-specific candidate generation

Document type detection routes native text or rendered OCR. Positioned regions are assigned to header, depth, thickness, sample, lithology, description, scale, or metadata roles when evidence supports that decision. Form fields and isolated numbers are excluded unless accompanied by geological description evidence. Each surviving top–bottom hypothesis retains its page order, normalized top and bottom column locations, vertical position, confidence, geological-term indicator, and source evidence.

### 4.2 Candidate graph

Candidate

\[
c_i=(t_i,b_i,p_i,y_i,x_i^t,x_i^b,e_i,q_i)
\]

contains top and bottom depth, page, vertical order, normalized column positions, evidence, and OCR confidence. Construction requires \(0\le t_i<b_i\le5000\) ft and a geological description. OCR confidence is normalized so that \(q_i\in[0,1]\). Its frozen raw score is

\[
r_i=1+q_i+\mathbf{1}[\text{geological term in }e_i].
\]

The shallow-start prior is applied only when a path begins:

\[
I_i=r_i-0.0005t_i.
\]

It is not part of \(r_i\), is not charged again when later nodes are visited, and is not part of the risk-policy threshold.

An edge \(i\rightarrow j\) is admissible only when document position increases, \(t_j\ge t_i\), and \(b_i-t_j\le1\) ft. Let \(g_{ij}=|b_i-t_j|\). The continuity contribution is 5 when \(g_{ij}\le0.05\), \(2-g_{ij}\) when \(0.05<g_{ij}\le1\), and \(-\min(6,\log(1+g_{ij}))\) otherwise. The complete edge score is

\[
e_{ij}=\operatorname{continuity}(g_{ij})
-4(|x_i^t-x_j^t|+|x_i^b-x_j^b|)
-0.15\max(0,p_j-p_i-1).
\]

Dynamic programming computes

\[
F(j)=\max\left(I_j,\max_{i<j:i\rightarrow j}\{F(i)+r_j+e_{ij}\}\right)
\]

and backtracks the highest-scoring path, breaking score ties by path length. Every earlier candidate is considered; the published decoder has no predecessor-window truncation. Depth conversion and thickness are deterministic after selection. A centralized implementation supplies both experiment scripts and a deterministic candidate-graph test that checks the returned path against the equations.

### 4.3 Addition-only risk policy

The unselective output is the complete path and is never treated as intrinsically safe. The risk policy preserves all first-pass intervals. It rejects automatic modification when \(R\) is non-monotone, then considers proposed additions in descending \(r_i\). Candidate \(c\) is accepted only if:

\[
r_c\ge2.999
\]

and its open depth interval has no positive overlap with any member of \(R\) or previously accepted \(A\). The output is \(R\cup A\); otherwise it remains \(R\). The threshold applies to raw score \(r_i\), not the start score \(I_i\). Since \(q_i\in[0,1]\), \(r_i\ge2.999\) requires the geological-term indicator and OCR confidence of at least 0.999.

Threshold 2.999 was selected using only v001/v002 outcomes after those cohorts had served as initial-parser evaluation and external replication data; they therefore became risk-policy development evidence and are not confirmation of that policy. The development curve at that threshold covered 17/150 documents and accepted 36/36 correct actions with no observed worsened document. v003–v005 were excluded from threshold selection. The curve is regenerated in [risk-threshold analysis](generated/figures/risk_threshold_curve.png).

The coefficient 0.0005/ft is a weak deterministic preference for paths beginning near the page origin, introduced to resolve otherwise plausible deep-start sequences rather than fitted as a physical geological parameter. A post-hoc same-pool sensitivity over 0, 0.0005, 0.001, 0.0025, and 0.005/ft left v004 F1 unchanged at 0.5662 and moved v005 only from 0.5310 to 0.5297. The archived value is retained; the sensitivity analysis does not redefine the policy or confirmation set.

### 4.4 Risk definitions

An action is harmful if it adds an unmatched prediction or removes a previously matched prediction. FCR is harmful actions divided by all automatic change actions. Document harm is defined consistently for unselective and risk-policy outputs as a decrease in document interval F1. Net utility also reports added matches and change in incorrect predictions per 100 documents.

Because actions cluster within reports, the document is primary. With \(n\) accepted documents and zero observed worsened documents, the one-sided 95% zero-event upper bound is

\[
1-0.05^{1/n}.
\]

The action-level analogue is secondary because independence is implausible when one report contributes many additions. County-group sensitivity is reported separately and is not a source-family guarantee.

### 4.5 Constraint-guided rereading and provenance

For numeric constraint violations, provenance localizes a region, registered readers rerender it at higher resolution, and candidate ranking combines reader agreement, layout, and constraint change. A proposal requires a unique candidate value, a minimum score and margin, and fewer target violations; otherwise it becomes NEEDS_REVIEW. The original record is immutable. This rereading path is evaluated on Swissgeol but is not conflated with the California fixed-pool sequence ablation.

## 5. Experimental Design

California roles depend on the claim being evaluated. v001 was the initial held-out evaluation of the parser and v002 was its external replication, but both were subsequently used to develop the 2.999 risk threshold and are development evidence for that policy. v003 prospectively tested and falsified an earlier document-selective rule. Only v004 and v005 confirm the unchanged addition-only policy. The same-pool ablation is a post-hoc explanatory analysis of archived v004/v005 positioned candidates; it uses identical documents, one matcher, and no OCR rerun, and is not represented as preregistered.

The variants are:

1. raw parser;
2. all semantically eligible candidates without sequence selection;
3. monotonic dynamic programming;
4. monotonicity plus continuity;
5. continuity plus column stability without the geological-term bonus; and
6. the complete score.

Semantic eligibility and multi-reader agreement are embedded before the archived pool and cannot be isolated; no independent effect is claimed for them. The public evidence bundle contains 200 pseudonymized documents and 2,225 candidates with normalized geometry and component scores, plus a deterministic recomputation script. Distinctive reference depth sequences remain linkable to public USGS tables, so the pool is not claimed to be anonymous and release remains subject to rights and disclosure review.

Swissgeol evaluates an independently frozen rereading policy on 35 held-out source-agreement documents and a separate 20-document replication panel. BGS development source groups were used for page-family design; the final external v003 source family remained unopened until its preregistered gate passed. No BGS v003 result was used to change routing, thresholds, aliases, prompts, or models.

## 6. Results

### 6.1 Unselective reconstruction across California

On v001, raw F1 0.390 increased to 0.514; the report-cluster gain was 0.124 [0.058, 0.186]. The ranker added 81 correct and 12 incorrect predictions, removed 10 incorrect and six correct predictions, and had FCR 18/109=0.165. Five of 50 reports were worsened by document F1. <!-- evidence:p2.california_constraint_sequence --> <!-- evidence:p2.california_replication_statistics -->

On v002, raw F1 0.450 increased to 0.564, with gain 0.114 [0.076, 0.153] and FCR 63/355=0.177. Eight of 100 reports worsened. On v003, raw F1 0.383 increased to 0.470, but FCR reached 59/281=0.210 and ten reports worsened. The earlier selective rule accepted the most severe expansion failure, prospectively falsifying net sequence growth as a sufficient safety signal. <!-- evidence:p2.california_external_constraint_sequence --> <!-- evidence:p2.california_prospective_constraint_sequence --> <!-- evidence:p2.california_prospective_selective -->

On v004 and v005, the complete sequence reached F1 0.566 and 0.530, with FCR 0.121 and 0.084. These gains confirm that reconstruction recovers many missed intervals; the non-zero FCR confirms that improvement in pooled F1 is not equivalent to safe correction. <!-- evidence:p2.california_v005_constraint --> <!-- evidence:p2.california_candidate_pool_ablation -->

### 6.2 Same-candidate-pool ablation

Without sequence selection, the eligible pool reached F1 0.554/0.516 and FCR 0.324/0.322 on v004/v005. Monotonic decoding gave the highest F1, 0.579/0.550, with precision 0.942/0.911 and FCR 0.111/0.062. Adding continuity yielded F1 0.566/0.530. Column stability without the geological-term bonus yielded 0.563/0.519. The complete score reproduced the archived system at F1 0.566/0.530 and precision 0.953/0.914. Thus monotonic path selection provides the largest recovery; continuity, column stability, and semantic score move the operating point toward fewer, higher-precision predictions but do not consistently increase F1. <!-- evidence:p2.california_candidate_pool_ablation -->

### 6.3 Addition-only risk and net utility

On v004, the frozen addition-only policy accepted 43 non-overlapping high-score additions across 8 reports; it matched 592/665 predictions (precision 0.890, recall 0.305, F1 0.454). No accepted action was incorrect and no document F1 decreased. The one-sided action-level upper bound for 0/43 was 0.067, not zero. <!-- evidence:p2.california_v004_candidate_risk --> <!-- evidence:p2.california_v004_candidate_risk_analysis -->

On v005, the unchanged policy accepted 39 additions; it matched 585/780 predictions (precision 0.750, recall 0.283, F1 0.411). Eleven reports improved, 89 were unchanged, none worsened, and no accepted addition was incorrect. <!-- evidence:p2.california_v005_candidate_risk -->

Across the confirmatory cohorts, 82 actions occurred in 19 documents. Zero worsened documents gives a primary one-sided 95% upper bound of 0.1459. The secondary iid-action bound is 0.0359. Accepted documents span 14 counties; treating counties as independent zero-event groups gives a sensitivity upper bound of 0.1926, but all documents still come from one California publication program. The number of actions per accepted document ranges from 1 to 18, making the action-independence assumption particularly weak. <!-- evidence:p2.california_candidate_risk_certificate --> <!-- evidence:p2.california_document_risk -->

The utility cost is large. The risk policy yielded a net gain of 41 matched intervals per 100 documents, compared with 230.5 under unselective reconstruction. Among 164 reports whose complete sequence differed from raw, only 19 were automatically changed and 145 were retained for review or abstention. Unselective reconstruction lowered document F1 on 6 v004 and 10 v005 reports; the risk policy lowered it on none. The [risk frontier](generated/figures/sequence_risk_frontier.png) therefore represents a safety–recovery trade-off, not a dominant policy. <!-- evidence:p2.california_document_risk -->

### 6.4 Swissgeol validation

The first frozen trigger policy changed nothing on a 20-document/55-interval panel because all three erroneous reports evaded its trigger. A subsequent content-group-held-out test on 35 documents/80 intervals improved F1 from 0.857 to 0.921 and exact documents from 25 to 29; four accepted rereads corrected four reports, while three erroneous reports still evaded triggering. Applying that same policy back to a disjoint 20-document panel again produced no change. These positive and null results show that constraint-guided rereading can help within a supported source family but does not trigger reliably on every plausible error. <!-- evidence:p2.swissgeol_heldout_constraint_reread --> <!-- evidence:p2.swissgeol_v2_heldout_constraint_reread --> <!-- evidence:p2.swissgeol_v2_external_negative -->

A development-fitted selective router accepted 15/35 reused held-out documents with observed exactness 1.000, interval precision/recall/F1 1.000/0.438/0.609, Brier score 0.0555, and five-bin ECE 0.1481. Because the split had already been consumed by an earlier alias audit, this is validation rather than untouched confirmation. <!-- evidence:p2.swissgeol_risk_router_v002 -->

### 6.5 Unseen BGS source family

The converged page-family router was authorized only after nested source-disjoint development. In the one-time BGS v003 evaluation, every one of five visible pages was classified as unsupported and abstained: boundary F1, interval F1, and coverage were all 0. No false positive or critical numerical error was emitted. The router therefore protected against unsupported output but delivered no utility. This single result is the correct external conclusion; the development version history and failed NativeMM branches are confined to the supplement. <!-- evidence:p2.bgs_v003_v028_external_failure -->

## 7. Failure Analysis

The California failures separate recovery from harm. A long monotone path can include a wrong but plausible column; document-level growth does not reveal that failure. The addition-only rule prevents removal of correct raw intervals and blocks overlap, but its high threshold sacrifices most recoverable omissions. Constraints therefore shape the operating point; they do not establish correctness.

Swissgeol exposes trigger blind spots. Plausible but incomplete sequences can satisfy monotonicity and continuity, so no violation initiates rereading. Conversely, a broad region can contain several valid numbers from different fields; reader agreement on a number does not establish semantic ownership. Unique-value and abstention checks prevent some unsafe edits but cannot recover missing field localization.

BGS exposes transport failure before sequence reasoning. Long-page compression, graphic boundaries, scale ticks, samples, water levels, and terminal metadata generate mutually plausible event sequences. Development experiments improved candidate coverage but failed to establish a source-invariant owner model. The external abstention is preferable to unsupported output, yet shows that page-family routing alone cannot solve unseen layouts.

## 8. Discussion

The same-pool ablation changes the interpretation of the method. The dominant empirical contribution is monotonic sequence selection. Continuity, column stability, and geological-term scoring improve precision in some operating points but do not consistently improve F1. They should be described as auditable regularizers, not individually proven geological reasoning modules.

The addition-only policy optimizes a different objective from the complete sequence. It substantially reduces observed harm while recovering far fewer intervals. Zero harm in 19 documents is encouraging but statistically weak; the upper bound of 0.1459 precludes a safety-certification claim. At the other extreme, BGS shows that abstention can reach zero utility. Deployment therefore requires risk–coverage reporting, not one F1 number.

The principal limitations are one publication program for confirmatory correction risk, unavailable reliable visual-template grouping, only 19 accepted documents, reused Swissgeol validation, and zero BGS external coverage. No cross-source safety certificate, universal calibration, or complete real-document multimodal factorial ablation is claimed.

## 9. Reproducibility and Safety

The core objective is centralized in one module used by experiment and public-recomputation scripts. Tests verify equation/path equivalence, threshold semantics, pseudonymized candidate-pool schema, and fixed-pool reconstruction. Every accepted or rejected action retains source geometry, scores, before/after intervals, and warnings. The publication bundle releases frozen metrics, pseudonymized document outputs, and the normalized candidate pool required to recompute the ablation without source PDFs. Direct identifiers are removed, but sequence uniqueness makes linkage possible; field removal is not treated as proof of anonymity.

## 10. Conclusion

Sequence reconstruction and safe correction are distinct objectives. Across five California cohorts, unselective reconstruction consistently recovered intervals but produced action-level FCR of 0.084–0.210. On identical confirmatory candidate pools, monotonic decoding gave the highest F1, while the complete score traded recall for precision. The addition-only policy accepted 82 additions in 19 documents, all matched under the frozen reference and matcher, with no observed worsened report; its net gain was only 41 matched intervals per 100 documents and its document-level upper risk bound remained 0.1459. Swissgeol showed both positive and null within-family effects. The one-time BGS evaluation abstained everywhere. The defensible contribution is therefore an auditable risk–coverage framework for sequence reconstruction, together with direct evidence that unseen-family transport remains unsolved. <!-- evidence:p2.california_candidate_pool_ablation --> <!-- evidence:p2.california_document_risk --> <!-- evidence:p2.california_candidate_risk_certificate --> <!-- evidence:p2.bgs_v003_v028_external_failure -->

## References

Shared bibliography: [../references.bib](../references.bib). Citation verification and permitted claim scope are recorded in [../../docs/literature_evidence.yaml](../../docs/literature_evidence.yaml).


# Linked Supplementary Material

# Supplementary Material for Paper II

## S1. Role of exploratory evidence

The main manuscript reports the California same-candidate-pool ablation, addition-only risk policy, Swissgeol validation, and the one-time BGS v003 transport failure. This supplement retains development branches that explain why the final claim is narrower. They are not pooled with confirmatory results and are not counted as independent external tests.

## S2. BGS long-page development history

The BGS v001 source groups were available for development and failure attribution. Multiscale OCR and field-specific crops increased exact boundary visibility from 20.44% on full pages to 26.43%, but most reference boundaries still had no exact numeric candidate. A continuous-depth geometry decoder reached development Boundary F1 0.3381 and Interval F1 0.1797. Its one-time v002 source-disjoint evaluation collapsed to Boundary F1 0.0286 and Interval F1 0, demonstrating that the fitted page/column assumptions did not transport.

The final routed parser combined positioned-text evidence, semantic column roles, page-family routing, deterministic geometry, and abstention. Nested source-disjoint development reached Boundary F1 0.3475 and Interval F1 0.1978. Fold Interval F1 ranged from 0 to 0.381, so even the development gain was heterogeneous. This gate authorized the single BGS v003 evaluation reported in the main paper; no later development used v003.

## S3. Native multimodal feasibility

A frozen-backbone document-VLM branch tested synthetic structural pretraining, real-reference fine-tuning, row supervision, and spatial heads. Direct generation improved output format but provided no grounded interval sequence. The strongest spatial variant reached Boundary F1 0.0789, Interval F1 0.0312, and structural-evidence coverage 0.075 on source-disjoint development. A MinerU2.5 smoke run established local LoRA trainability only. Because the predefined structural and interval gates were missed, the branch was closed without consuming BGS v003.

These results do not show that document VLMs are generally ineffective. They show that the available labels, frozen visual representation, and small source-disjoint study did not solve boundary ownership well enough to replace the positioned structural parser.

## S4. Semantic-role and event-owner diagnostics

OCR-header semantic roles improved development Boundary/Interval F1 to 0.3265/0.1458 and reached 0.4410/0.2825 on the nine explicit Graphic-Log documents. The subset result identifies column meaning as a genuine failure mode but is not a transport estimate.

Aligning candidates to description-row edges was weakly discriminative (rank AUC 0.591) and did not exceed the final routed parser. A post-candidate joint event-owner decoder reached Boundary F1 0.293, Interval F1 0.113, and Boundary CNER 0.652. Once candidates had been scored independently, owner penalties could not reconstruct the lost page context. These negative results support the main paper's decision not to claim a learned page-level ownership solution.

## S5. Swissgeol secondary analyses

Alias-only routing produced high precision at low coverage. Broadening the alias set raised family recognition but lowered accepted precision and increased CNER, so that expansion was rejected. A secondary calibration lookup and an exact cross-reader agreement rule produced useful selective subsets, but both were specified after the primary held-out method result and remain exploratory.

## S6. Shallow-start prior sensitivity

The path-start penalty was varied on the unchanged public v004/v005 candidate pools. Coefficients of 0, 0.0005, 0.001, 0.0025, and 0.005 per foot all produced v004 F1 0.5662. Corresponding v005 F1 values were 0.5310, 0.5304, 0.5297, 0.5297, and 0.5297. Candidate counts, matcher, and references were fixed. This post-hoc sensitivity shows that the reported sequence effect is not driven by the selected 0.0005 coefficient; it is not a threshold search or a new confirmatory experiment. The exact values are generated from `california_depth_start_sensitivity_v001.json`.

## S7. Synthetic and no-reference engineering checks

The executed 127-case synthetic experiment verifies that the actual constraint evaluator, rereading ranker, and calibration path are wired correctly. It does not estimate real-document effect. A two-ROI Padova audit produced schema-valid numeric candidates but both decisions remained NEEDS_REVIEW; no accuracy or FCR is defined because the annotations are not independent reference labels.

Full experiment IDs, configurations, metrics, and hashes remain in [current results](generated/current_results.md), the result index, ADRs, and the publication-evidence bundle. The public candidate pool permits independent recomputation of the main same-pool ablation without exposing OCR text or source identifiers.

# Appendix: Reproducibly Generated Current Results

<!-- AUTO-GENERATED. DO NOT EDIT. -->
# Paper II major-revision tables

## Same-candidate-pool sequence ablation

Evidence tier: **Published manual transcription Gold**. All variants use identical documents, positioned candidate pools, matcher, and tolerance; the bootstrap unit is the document.

| Variant | v004 P / R / F1 (95% CI) | v004 FCR | v005 P / R / F1 (95% CI) | v005 FCR |
|---|---:|---:|---:|---:|
| Raw parser | 0.883 / 0.282 / 0.428 [0.339, 0.515] | -- | 0.737 / 0.264 / 0.389 [0.305, 0.466] | -- |
| Eligible pool, no sequence | 0.815 / 0.419 / 0.554 [0.475, 0.625] | 0.324 | 0.718 / 0.402 / 0.516 [0.438, 0.588] | 0.322 |
| + monotonic sequence | 0.942 / 0.418 / 0.579 [0.495, 0.655] | 0.111 | 0.911 / 0.394 / 0.550 [0.471, 0.619] | 0.062 |
| + continuity / zero-origin | 0.950 / 0.403 / 0.566 [0.480, 0.644] | 0.126 | 0.914 / 0.374 / 0.530 [0.450, 0.603] | 0.086 |
| + column stability, no term bonus | 0.951 / 0.400 / 0.563 [0.476, 0.641] | 0.126 | 0.909 / 0.363 / 0.519 [0.437, 0.593] | 0.124 |
| Complete archived score | 0.953 / 0.403 / 0.566 [0.480, 0.645] | 0.121 | 0.914 / 0.374 / 0.530 [0.450, 0.603] | 0.084 |

## Document-level risk and net utility

Evidence tier: **Published manual transcription Gold**. The primary safety unit is the document; the iid-action bound is retained only as a secondary diagnostic.

| Cohort | Policy | Net additional matches / 100 documents | Net change in incorrect predictions | Worsened documents (document F1) | Accepted documents | Review/abstain documents |
|---|---|---:|---:|---:|---:|---:|
| v004 | Unselective sequence | 234.0 | -34 | 6 | 79 | 0 |
| v004 | Addition-only risk policy | 43.0 | 0 | 0 | 8 | 71 |
| v005 | Unselective sequence | 227.0 | -122 | 10 | 85 | 0 |
| v005 | Addition-only risk policy | 39.0 | 0 | 0 | 11 | 74 |

Across 200 documents, the addition-only policy accepted 82 actions in 19 documents, observed 0 worsened documents, and retained 145 changed-sequence documents for review or abstention. The one-sided 95% zero-event upper bound is 0.1459 per accepted document; the secondary iid-action bound is 0.0359.

## Post-hoc shallow-start prior sensitivity

Evidence tier: **Published manual transcription Gold**. The candidate pool, references, matcher, and tolerance are fixed; this is explanatory sensitivity, not threshold selection.

| Start penalty per foot | v004 predicted / F1 | v005 predicted / F1 |
|---:|---:|---:|
| 0.0000 | 822 / 0.5662 | 846 / 0.5310 |
| 0.0005 | 822 / 0.5662 | 846 / 0.5304 |
| 0.0010 | 822 / 0.5662 | 846 / 0.5297 |
| 0.0025 | 822 / 0.5662 | 846 / 0.5297 |
| 0.0050 | 822 / 0.5662 | 846 / 0.5297 |


# Full Indexed Result Catalogue

<!-- AUTO-GENERATED. DO NOT EDIT. -->
### Real authoritative-metadata consensus and abstention

| Experiment | Field | Reference n | Auto-accepted | Coverage | Accepted accuracy | Review | Review recall | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P2_BGS_METADATA_CONSENSUS_ABSTENTION_001 | borehole_id | 31 | 25 | 25/31 (0.806) | 1.000 | 6 | 1.000 | formal_authoritative_metadata_method |
| P2_BGS_METADATA_CONSENSUS_ABSTENTION_001 | x_coordinate | 31 | 31 | 31/31 (1.000) | 1.000 | 0 | N/A | formal_authoritative_metadata_method |
| P2_BGS_METADATA_CONSENSUS_ABSTENTION_001 | y_coordinate | 31 | 31 | 31/31 (1.000) | 1.000 | 0 | N/A | formal_authoritative_metadata_method |
| P2_BGS_METADATA_CONSENSUS_ABSTENTION_001 | final_depth_m | 31 | 0 | 0/31 (0.000) | N/A | 31 | 1.000 | formal_authoritative_metadata_method |

The decision policy accepts only equal non-null values from two independent OCR readers. References are consulted only after decisions are frozen. This is real metadata-field evidence; interval/lithology effects remain unmeasured.

### Published manual-transcription Gold sequence recovery

| Experiment | Documents | Counties | Reference intervals | Candidates | Raw P | Raw R | Raw F1 | Constrained P | Constrained R | Constrained F1 | Correct added | Incorrect added | Correct removed | FCR | Eligibility |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P2_CALIFORNIA_WCR_CONSTRAINT_TEST_FORMAL_001 | 50 | 48 | 697 | 353 | 0.892 | 0.250 | 0.390 | 0.915 | 0.357 | 0.514 | 81 | 12 | 6 | 18/109 (0.165) | formal_benchmark |
| P2_CALIFORNIA_WCR_V002_CONSTRAINT_EXTERNAL_FORMAL_002 | 100 | 23 | 1770 | 1143 | 0.817 | 0.311 | 0.450 | 0.925 | 0.406 | 0.564 | 212 | 17 | 46 | 63/355 (0.177) | formal_external_benchmark |
| P2_CALIFORNIA_WCR_V003_CONSTRAINT_PROSPECTIVE_FORMAL_001 | 100 | 31 | 1788 | 836 | 0.803 | 0.251 | 0.383 | 0.897 | 0.318 | 0.470 | 149 | 29 | 30 | 59/281 (0.210) | formal_prospective_external_benchmark |
| P2_CALIFORNIA_WCR_V004_CONSTRAINT_PROSPECTIVE_FORMAL_001 | 100 | 28 | 1944 | 1008 | 0.883 | 0.282 | 0.428 | 0.953 | 0.403 | 0.566 | 257 | 20 | 23 | 43/354 (0.121) | formal_prospective_external_method |
| P2_CALIFORNIA_WCR_V005_CONSTRAINT_EXTERNAL_FORMAL_001 | 100 | 35 | 2069 | 1217 | 0.737 | 0.264 | 0.389 | 0.914 | 0.374 | 0.530 | 251 | 10 | 25 | 35/417 (0.084) | formal_prospective_external_method |

The deterministic sequence ranker was frozen on the ten-document development partition and evaluated without reference access on the fifty-document California test. FCR counts both correct raw boundaries removed and incorrect constrained boundaries added. The result shows recovery gain and a non-negligible correction hazard rather than uniformly safe automatic repair.

### Held-out authoritative-interval constraint-rereading result

| Experiment | Documents | Reference intervals | First-pass F1 | Reread F1 | Triggered | Accepted rereads | Needs review | Incorrect-doc trigger recall | Correct-doc trigger rate | Correction success | FCR | Eligibility |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P2_SWISSGEOL_TG_CONSTRAINT_REREAD_HELDOUT_001 | 20 | 55 | 0.855 | 0.855 | 1 | 0 | 1 | 0/3 (0.000) | 1/17 (0.059) | N/A | N/A | formal_authoritative_interval_method |
| P2_SWISSGEOL_TG_CONSTRAINT_REREAD_HELDOUT_V003_001 | 35 | 80 | 0.857 | 0.921 | 9 | 4 | 5 | 7/10 (0.700) | 2/25 (0.080) | 4/4 (1.000) | 0/4 (0.000) | formal_authoritative_interval_method |
| P2_SWISSGEOL_TG_CONSTRAINT_REREAD_V2_EXTERNAL_V002_001 | 20 | 55 | 0.855 | 0.855 | 1 | 0 | 1 | 0/3 (0.000) | 1/17 (0.059) | N/A | N/A | formal_authoritative_interval_method |

Each policy was frozen on its recorded development partition before the corresponding source-agreement test was evaluated. A null FCR means no automatic correction occurred; it is not zero. The same-source, explicit-table selection remains a major limitation.

### Secondary held-out component analysis

| Experiment | Variant | Interval P | Interval R | Interval F1 | Full-document exact | Changed documents vs v2 first pass | Eligibility |
|---|---|---:|---:|---:|---:|---:|---|
| P2_SWISSGEOL_TG_V2_SECONDARY_ABLATION_001 | full_v2 | 0.972 | 0.875 | 0.921 | 29/35 | 4 | secondary_ablation_only |
| P2_SWISSGEOL_TG_V2_SECONDARY_ABLATION_001 | legacy_parser_first_pass | 0.871 | 0.762 | 0.813 | 23/35 | 4 | secondary_ablation_only |
| P2_SWISSGEOL_TG_V2_SECONDARY_ABLATION_001 | v2_first_pass | 0.892 | 0.825 | 0.857 | 25/35 | 0 | secondary_ablation_only |
| P2_SWISSGEOL_TG_V2_SECONDARY_ABLATION_001 | v2_parser_v1_acceptance | 0.893 | 0.838 | 0.865 | 26/35 | 1 | secondary_ablation_only |
| P2_SWISSGEOL_TG_V2_EXTERNAL_V002_SECONDARY_ABLATION_001 | full_v2 | 0.855 | 0.855 | 0.855 | 17/20 | 0 | secondary_ablation_only |
| P2_SWISSGEOL_TG_V2_EXTERNAL_V002_SECONDARY_ABLATION_001 | legacy_parser_first_pass | 0.855 | 0.855 | 0.855 | 17/20 | 0 | secondary_ablation_only |
| P2_SWISSGEOL_TG_V2_EXTERNAL_V002_SECONDARY_ABLATION_001 | v2_first_pass | 0.855 | 0.855 | 0.855 | 17/20 | 0 | secondary_ablation_only |
| P2_SWISSGEOL_TG_V2_EXTERNAL_V002_SECONDARY_ABLATION_001 | v2_parser_v1_acceptance | 0.855 | 0.855 | 0.855 | 17/20 | 0 | secondary_ablation_only |

This component analysis was specified and executed after the full v2 held-out result was observed. It is descriptive evidence on frozen artifacts, not an independent confirmatory experiment; change counts for the legacy parser are parser differences, not automatic corrections.

### Secondary selective-confidence and abstention analysis

| Experiment | Brier | ECE (5-bin) | Abstain review coverage | Abstain document exact | Abstain interval F1 | Peer-agreement coverage | Peer-agreement interval F1 | Eligibility |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| P2_SWISSGEOL_TG_SELECTIVE_CONFIDENCE_SECONDARY_001 | 0.126 | 0.044 | 30/35 (0.857) | 0.900 | 0.948 | 14/35 (0.400) | 1.000 | secondary_calibration_only |

The confidence lookup is fit on development-only outcomes and applied to held-out outputs. This table is a secondary post-result analysis with small denominators; it is not a confirmatory calibration estimate.

### Frozen-policy finite-sample risk certificate

| Experiment | Cohort | Accepted actions | Incorrect actions | Observed FCR | One-sided 95% FCR upper bound | One-sided 99% FCR upper bound | Accepted documents | Worsened documents | One-sided 95% document-worsening upper bound | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P2_CALIFORNIA_CANDIDATE_RISK_CERTIFICATE_001 | development | 51 | 0 | 0.000 | 0.057 | 0.086 | 21 | 0 | 0.133 | secondary_statistical_risk_analysis |
| P2_CALIFORNIA_CANDIDATE_RISK_CERTIFICATE_001 | external_v004 | 43 | 0 | 0.000 | 0.067 | 0.102 | 8 | 0 | 0.312 | secondary_statistical_risk_analysis |
| P2_CALIFORNIA_CANDIDATE_RISK_CERTIFICATE_001 | external_v005 | 39 | 0 | 0.000 | 0.074 | 0.111 | 11 | 0 | 0.238 | secondary_statistical_risk_analysis |
| P2_CALIFORNIA_CANDIDATE_RISK_CERTIFICATE_001 | external_pooled_v004_v005 | 82 | 0 | 0.000 | 0.036 | 0.055 | 19 | 0 | 0.146 | secondary_statistical_risk_analysis |

The policy was fixed before v004/v005. Exact zero-error upper bounds are conditional on independent Bernoulli action/document assumptions. The pooled 82-action California result supports a 5% action-FCR target at one-sided 95% confidence, but the 19 accepted documents do not certify a 5% document-worsening target; neither result is a cross-source guarantee.

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
| P2_EXECUTED_SYNTHETIC_ABLATION_001 | minus_ocr | ocr | 30 | 97 | N/A | N/A | 14/14 (1.000) | 97/97 (1.000) | N/A | 0.310 | 0.175 | formal_synthetic_method |
| P2_EXECUTED_SYNTHETIC_ABLATION_001 | minus_rereading | rereading | 30 | 97 | N/A | N/A | 14/14 (1.000) | 97/97 (1.000) | N/A | 0.310 | 0.175 | formal_synthetic_method |
| P2_EXECUTED_SYNTHETIC_ABLATION_001 | minus_vlm | vlm | 30 | 97 | N/A | N/A | 14/14 (1.000) | 97/97 (1.000) | N/A | 0.310 | 0.175 | formal_synthetic_method |

Rows are generated from identical-case, one-module-at-a-time matrices. `formal_synthetic_method` rows are controlled Synthetic evidence and do not support human-GT claims; human-GT rows remain separately labelled.

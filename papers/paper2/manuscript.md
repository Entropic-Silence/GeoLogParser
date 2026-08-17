# Risk-Aware Sequence Reconstruction for Borehole-Log Extraction with Auditable Constraints and Abstention

## Abstract

We study borehole-log extraction as risk-aware reconstruction and selective assurance rather than unconstrained text generation. Positioned OCR hypotheses are filtered by field semantics, linked by document order and depth geometry, and decoded by dynamic programming; a separate addition-only policy may accept supported candidates or retain the first pass. Across five record-disjoint California cohorts, unselective sequence ranking increased interval F1 from 0.383–0.450 to 0.470–0.566, but action-level false-correction rate was 0.084–0.210. The frozen addition-only policy accepted 82 candidates in 19 documents with no observed incorrect action or worsened document, but the primary document-level one-sided 95% upper risk bound remained 0.1459. A complementary assurance experiment treated a strong direct VLM as a proposal reader and accepted an interval only when an independent positioned reader agreed on both boundaries with retained bbox evidence. On held-out California v003 this increased proposal precision from 0.907 to selective precision 0.993 [0.984, 1.000] at 0.244 coverage, with 3 incorrect among 447 accepted actions and errors in 3/63 documents containing an accepted action. A one-time unseen BGS source-family evaluation abstained on every visible page, preventing false positives but providing zero utility. The evidence supports auditable risk reduction, not universal source transport or safety certification. <!-- evidence:p2.california_constraint_sequence --> <!-- evidence:p2.california_v004_candidate_risk --> <!-- evidence:p2.california_v005_candidate_risk --> <!-- evidence:p2.california_candidate_risk_certificate --> <!-- evidence:p2.california_document_risk --> <!-- evidence:p2.vlm_proposal_assurance --> <!-- evidence:p2.bgs_v003_v028_external_failure -->

## 1. Introduction

A borehole log is not a bag of recognized numbers. Depth scale ticks, cumulative boundaries, layer thicknesses, samples, water levels, and terminal depths can all form plausible monotone sequences. Selecting the wrong column can therefore produce internally consistent but geologically irrelevant output. At the same time, a correction mechanism can improve average F1 while damaging individual documents.

This paper treats extraction as two coupled problems: reconstruct the best source-grounded interval sequence, then decide whether a proposed change is safe enough to apply automatically. The central questions are:

- RQ1: which sequence components recover intervals from a fixed candidate pool?
- RQ2: how often does automatic reconstruction harm a document or action?
- RQ3: how much recovery is sacrificed by addition-only acceptance and abstention?
- RQ4: does the method transport to a genuinely unseen page family?
- RQ5: can independent positioned evidence raise the reliability of strong direct-VLM proposals without silently repairing them?

The contributions are:

1. a formally specified candidate graph and dynamic-programming decoder for ordered borehole intervals;
2. same-candidate-pool ablation that separates monotonic selection from continuity, column stability, and semantic score;
3. a reference-blind addition-only policy evaluated by document-level harm, action-level false-correction rate, and net utility; and
4. a frozen VLM-proposal assurance rule evaluated by field anchoring, selective precision, coverage, and document-cluster uncertainty; and
5. explicit negative transport evidence showing that conservative abstention can avoid errors while eliminating utility.

Paper I owns the evidence hierarchy and source-shift benchmark. Paper III owns downstream spatial propagation.

## 2. Related Work

Multimodal document models combine text, layout, and pixels [@xu2020layoutlm; @xu2021layoutlmv2; @kim2022donut; @hu2024docowl2], but borehole reliability additionally requires depth order and semantic ownership. Zhang et al. study same-specification image extraction [@zhang2020boreholeimages]; Han and Suh combine page typing with spreadsheet structuring [@han2024boreholeocr]; Amini et al. separate PDF discovery, selection, and capture [@amini2023boreholepdf]; Ma et al. report weaker extraction on image-based historical well records [@ma2024historicalwell]; and Shiga evaluates direct VLM structuring on a small, single-system borehole set [@shiga2026boreholevlm]. Our target is not another image-to-JSON pipeline, but auditable sequence choice and correction harm under fixed evidence. The modern direct-VLM comparison is deliberately complementary: a strong visual reader can propose intervals, while the present route contributes independent positioned evidence, deterministic geometry, provenance, and a risk policy.

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

### 4.6 Direct-VLM proposal assurance

A separate branch starts from the unchanged interval sequence (V=(v_1,\ldots,v_n)) emitted by a frozen Qwen3.8-27B-FP8 page-to-JSON reader. An independently frozen RapidOCR positioned parser produces candidates (C=(c_1,\ldots,c_m)) with page, bbox, text, confidence, and interval geometry. No output from either reader is supplied to the other. An order-preserving bipartite match forms

\[
M=\{(i,j): |t(v_i)-t(c_j)|\le10^{-6}\ \land\ |b(v_i)-b(c_j)|\le10^{-6}\},
\]

maximizing match cardinality and then minimizing boundary error. Proposal (v_i) is automatically accepted only if it has a matched positioned candidate with retained source regions, has non-negative top and positive thickness, and the accepted subsequence remains monotonic and non-overlapping. No value is repaired, averaged, completed, or removed from the proposal stream; non-accepted intervals receive NEEDS_REVIEW. Exact source-unit occurrences in a positioned bbox on the same page are reported as numeric-anchor candidates, but only complete interval agreement is treated as semantic ownership.

California v001 alone developed and froze this rule. v002 is validation and v003 is a record-disjoint held-out replication; v004/v005 and BGS v003 were not used. Gold is read only after decisions to estimate selective precision, false acceptance, and document-level clustering. Partial interval acceptance never establishes document completeness.

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

The VLM-proposal assurance experiment uses the same California Gold definitions and 0.05 m evaluation matcher as Paper I. The proposal model, prompt, positioned reader, (10^{-6}) m agreement tolerance, bbox requirement, and non-overlap rule are fixed before v003. Document-cluster bootstrap resamples whole reports 5,000 times. The comparison is selective: raw precision and accepted precision answer different coverage questions and are reported together.

### 5.3 Modern-VLM complementarity protocol

The open modern-VLM baseline is identified by its official checkpoint and served
ID rather than by a shorthand family name: `Qwen/Qwen3.8-27B-FP8`, served as
`qwen38-fp8-tp4-mtp4-long`, with fine-grained dynamic FP8 E4M3 weights, through
a local vLLM-compatible OpenAI server. The frozen prompt is
`vlm_interval_source_units_v002` (SHA-256
`891bc6beb7ff9cf35c55389191a208c9b09e9e2dc76909f716603f413745104a`); pages are
rendered at 200 DPI with PyMuPDF to lossless PNG, with temperature 0,
provider-default top-p, a 4,096-token ceiling, zero automatic retries, and
strict JSON parsing without repair, reordering, or deduplication. The local
server did not expose its vLLM package version; this is recorded as an unknown,
not inferred.

The comparison asks which capability is complementary rather than which model
wins universally. Qwen supplies visual semantic recall and proposal coverage;
positioned OCR supplies an independent page-coordinate witness; the routed
sequence decoder supplies monotonic geometry and column-aware selection; and the
risk layer decides whether to accept, retain, or abstain. On held-out California
v003, raw Qwen proposal precision was 0.907, while complete-boundary agreement
with the independent positioned reader yielded selective precision 0.993 at
0.244 coverage, with three incorrect accepted intervals. This is a selective
reliability improvement, not an all-output F1 improvement or evidence of
whole-document completeness.

The requested closed-model exploratory slot was recorded separately with the
served ID `gpt-5.6-sol` and requested reasoning label
`chatgpt5.6-sol-high`. Its synthetic visual preflight returned HTTP 502 before
any real page request, so it contributes no baseline or risk-layer metric.

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

### 6.6 Assurance of modern VLM proposals

On v001 development, 81.7% of critical depth fields had a same-page positioned numeric anchor. Complete independently positioned interval agreement covered 174/736 proposals (0.236); all 174 matched Gold. On v002 validation, numeric-anchor coverage was 0.849 and the fixed rule accepted 561/1,953 proposals (0.287). Selective precision was 0.979 [0.951, 0.997], compared with raw proposal precision 0.854; 12 accepted actions were incorrect and 5/72 documents with an accepted action contained at least one such error. <!-- evidence:p2.vlm_proposal_assurance -->

The frozen v003 replication retained the effect: numeric-anchor coverage 0.845, semantically owned/accepted coverage 0.244, and selective precision 444/447 = 0.993 [0.984, 1.000], compared with raw precision 0.907. Three accepted actions were incorrect, each in a different document; 63/100 documents contained at least one accepted action. The rule therefore converts roughly one quarter of high-recall proposals into highly reliable, bbox-grounded interval actions, but agreement is not independence from shared source ambiguity and does not certify whole-document completeness. The generated [assurance table](generated/vlm_proposal_assurance_v001.md) reports roles and cluster intervals without pooling them. <!-- evidence:p2.vlm_proposal_assurance -->

The practical conclusion is asymmetric. Direct modern VLMs are stronger at
recovering visually implicit intervals on the California family, while the
existing route remains necessary for numerical traceability, semantic ownership
checks, deterministic depth reconstruction, risk accounting, and review-queue
generation. The supported deployment design is therefore a hybrid assurance
stack: use the VLM as a high-recall reader, require independent positioned
evidence for automatic acceptance, and abstain when evidence or source-family
support is insufficient. The evidence does not support replacing the route with
a direct VLM, nor replacing the VLM with OCR on every template.

## 7. Failure Analysis

The California failures separate recovery from harm. A long monotone path can include a wrong but plausible column; document-level growth does not reveal that failure. The addition-only rule prevents removal of correct raw intervals and blocks overlap, but its high threshold sacrifices most recoverable omissions. Constraints therefore shape the operating point; they do not establish correctness.

Swissgeol exposes trigger blind spots. Plausible but incomplete sequences can satisfy monotonicity and continuity, so no violation initiates rereading. Conversely, a broad region can contain several valid numbers from different fields; reader agreement on a number does not establish semantic ownership. Unique-value and abstention checks prevent some unsafe edits but cannot recover missing field localization.

BGS exposes transport failure before sequence reasoning. Long-page compression, graphic boundaries, scale ticks, samples, water levels, and terminal metadata generate mutually plausible event sequences. Development experiments improved candidate coverage but failed to establish a source-invariant owner model. The external abstention is preferable to unsupported output, yet shows that page-family routing alone cannot solve unseen layouts.

## 8. Discussion

The same-pool ablation changes the interpretation of the method. The dominant empirical contribution is monotonic sequence selection. Continuity, column stability, and geological-term scoring improve precision in some operating points but do not consistently improve F1. They should be described as auditable regularizers, not individually proven geological reasoning modules.

The addition-only policy optimizes a different objective from the complete sequence. It substantially reduces observed harm while recovering far fewer intervals. Zero harm in 19 documents is encouraging but statistically weak; the upper bound of 0.1459 precludes a safety-certification claim. At the other extreme, BGS shows that abstention can reach zero utility. Deployment therefore requires risk–coverage reporting, not one F1 number.

The modern-VLM branch sharpens that conclusion. Model scale solves much of the California interval-recall problem, but not automatic database acceptance. Independent complete-boundary agreement raises selective precision substantially and attaches bbox provenance, yet its v002 errors show that two readers can share a plausible wrong interpretation. The useful system contribution is therefore an assurance layer around strong proposals, not a claim that the routed OCR parser is the best raw extractor.

The principal limitations are one publication program for confirmatory correction risk, unavailable reliable visual-template grouping, only 19 accepted documents, reused Swissgeol validation, and zero BGS external coverage. No cross-source safety certificate, universal calibration, or complete real-document multimodal factorial ablation is claimed.

## 9. Reproducibility and Safety

The core objective is centralized in one module used by experiment and public-recomputation scripts. Tests verify equation/path equivalence, threshold semantics, pseudonymized candidate-pool schema, and fixed-pool reconstruction. Every accepted or rejected action retains source geometry, scores, before/after intervals, and warnings. The publication bundle releases frozen metrics, pseudonymized document outputs, and the normalized candidate pool required to recompute the ablation without source PDFs. Direct identifiers are removed, but sequence uniqueness makes linkage possible; field removal is not treated as proof of anonymity.

## 10. Conclusion

Sequence reconstruction and safe acceptance are distinct objectives. Across five California cohorts, unselective reconstruction consistently recovered intervals but produced action-level FCR of 0.084–0.210. The addition-only policy accepted 82 additions in 19 documents, all matched under the frozen reference and matcher, while its net gain remained only 41 matched intervals per 100 documents and its document-level upper risk bound was 0.1459. For a much stronger direct VLM, independent complete-boundary agreement achieved held-out selective precision 0.993 at 0.244 proposal coverage with retained bbox evidence, but still accepted three wrong intervals and did not establish document completeness. Swissgeol showed both positive and null within-family effects; the one-time BGS evaluation abstained everywhere. The defensible contribution is an auditable risk–coverage framework that can surround either positioned candidates or modern VLM proposals, together with direct evidence that correlated errors and unseen-family transport remain unsolved. <!-- evidence:p2.california_candidate_pool_ablation --> <!-- evidence:p2.california_document_risk --> <!-- evidence:p2.california_candidate_risk_certificate --> <!-- evidence:p2.vlm_proposal_assurance --> <!-- evidence:p2.bgs_v003_v028_external_failure -->

## References

Shared bibliography: [../references.bib](../references.bib). Citation verification and permitted claim scope are recorded in [../../docs/literature_evidence.yaml](../../docs/literature_evidence.yaml).

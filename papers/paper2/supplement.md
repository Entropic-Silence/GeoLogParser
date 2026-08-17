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

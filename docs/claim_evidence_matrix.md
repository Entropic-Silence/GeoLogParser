# GeoLogParser claim--evidence matrix

This matrix is the compact audit trail for the three manuscript candidates. A
claim is allowed in an abstract or conclusion only when its evidence row points
to a frozen result, an indexed experiment, or a clearly labelled diagnostic.
The matrix does not upgrade a source's licence, annotation, or geological status.

Generated for the manuscript-closure pass on 2026-08-17.

## Paper I — multi-cohort/cross-source evaluation and failure characterization

| Claim | Evidence | Frozen result | Permitted interpretation | Boundary |
|---|---|---|---|---|
| RapidOCR and Tesseract have high conditional precision but severe omission on the California reference | `P1_CALIFORNIA_WCR_RAPIDOCR_TEST_FORMAL_001`, `P1_CALIFORNIA_WCR_TESSERACT_TEST_FORMAL_001` | RapidOCR F1 0.390 (P/R 0.892/0.250); Tesseract F1 0.325 (0.807/0.204) on 697 intervals | Real reference benchmark against published USGS manual transcription | Not a project-created human annotation; source redistribution is pending final review |
| The ordering and omission pattern replicate on disjoint California freezes | `P1_CALIFORNIA_WCR_V002_RAPIDOCR_EXTERNAL_FORMAL_002`, v003/v004/v005 indexed runs | RapidOCR F1 0.450, 0.383, 0.428, 0.389 | Prospective/content-disjoint replication | California remains one source family and one document genre |
| Document-level uncertainty exposes incomplete records | `experiments/paper1/analysis/california_replication_statistics_v001.json` | Five document-cluster F1 intervals; zero-output rates 8%–23%; boundary-exact rates 1%–6% | Multi-cohort stability and omission evidence | Pooled interval counts are descriptive, not independent observations |
| Random-record resampling did not show large F1 inflation for a fixed parser | `experiments/paper1/analysis/california_random_vs_grouped_split_v001.json` | Random F1 mean 0.394 ± 0.021; grouped F1 0.390; mean development overlap 0.1682 | Leakage-risk diagnostic | No retraining; not evidence for a trained random-split generalization estimate |
| Long-page/source transfer can collapse | `P1_BGS_OFFSHORE_V001_RAPIDOCR_CROSS_SOURCE_FORMAL_001`, `P1_BGS_OFFSHORE_V001_TESSERACT_CROSS_SOURCE_FORMAL_001` | Interval F1 0.0379/0.0405; recall 0.0205/0.0235 | Cross-source structural failure | BGS scan rights and embedded-content review remain pending |
| Metadata fields have backend-specific degradation surfaces | BGS metadata robustness indexed runs | RapidOCR clean ID/X/Y 31/31; JPEG-30 7/31; Tesseract 3° skew produced gross Y errors | Controlled first-page ID/X/Y robustness | Does not establish interval or lithology robustness |
| Page-level engine disagreement is document-specific | `P1_USGS_IDAHO_LITHOLOGIC_V001_CROSS_ENGINE_COVERAGE_001` | 49 lithology-label presence disagreements, concentrated in 3/7 documents | Failure attribution | No interval accuracy claim; image-only audit |

## Paper II — risk-aware structural extraction

| Claim | Evidence | Frozen result | Permitted interpretation | Boundary |
|---|---|---|---|---|
| Unselective sequence reasoning improves California interval recovery but can harm records | California v001--v005 constraint-sequence runs | F1 gains 0.124, 0.114, 0.087, 0.138, 0.142; FCR 0.165, 0.177, 0.210, 0.121, 0.084 | Recovery/harm trade-off | Not a universal safe-correction result |
| Candidate-level addition-only acceptance is safer but lower coverage | v004/v005 candidate-risk runs and `P2_CALIFORNIA_CANDIDATE_RISK_CERTIFICATE_001` | 82 accepted additions, 0 observed incorrect; action 95% upper bound 0.0359; document worsening upper bound 0.1459 | Finite-sample conditional risk evidence | iid-action assumption; California-only; no cross-source certificate |
| Monotonic sequence selection supplies most observed recovery | `experiments/paper2/analysis/california_candidate_pool_ablation_v001.json` | v004/v005 monotonic F1 0.579/0.550 versus complete-score F1 0.566/0.530 | Same-candidate-pool module evidence | Semantic eligibility and multi-reader agreement remain embedded upstream |
| Addition-only acceptance has measurable net utility and review cost | `experiments/paper2/analysis/california_document_risk_v001.json` | 41 correct additions per 100 documents; 145/164 changed-sequence documents retained for review/abstention | Document-level utility/risk trade-off | Low automatic coverage; no labour-time claim |
| Routed page-family/semantic-role parsing improves BGS development structure scores | `experiments/paper2/analysis/bgs_routed_moe_v028_nested_cv_summary_v002.json` | v028 overall Boundary/Interval F1 0.3475/0.1978; five-fold means 0.3333/0.1841 vs v024 0.3182/0.1688 | Nested source-disjoint development gain | Reused BGS v001 artifacts; not untouched external confirmation |
| The current route fails conservatively on an unseen BGS family | `P2_BGS_V028_ROUTED_EXTERNAL_V003_FINAL` | 1 record, 5 pages, 8 boundaries, 7 intervals; F1 0/0, coverage 0, FP 0, CNER 0 | Safety-preserving but utility-failing external result | Consumed once; never tune or rerun |
| Rereading benefit is source-conditional | Swissgeol 35-document and 20-document frozen tests | Positive F1 0.857→0.921, FCR 0/4; negative test unchanged at F1 0.855 | Triggered rereading can help or abstain | Held-out split and alias audit roles are documented separately |

## Paper III — downstream error propagation

| Claim | Evidence | Frozen result | Permitted interpretation | Boundary |
|---|---|---|---|---|
| Removing points can worsen surfaces by reducing spatial support | `P3_COAL602_CONSENSUS_QC_CONTROLLED_003` / controlled dual-channel perturbation on real structured-source records | Agreement between two synthetically perturbed channels retained ≈81.5% but surface MAE ≈0.73–0.74 m; support-preserving channel fusion reduced MAE 18.3–22.0% | Support is an independent downstream variable | Simulated reader errors; no observed two-reader comparison, CRS, or seam interpretation claim |
| Error classes have distinct downstream signatures | `P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002` | 540 seeded repetitions over six classes | Mechanism-level propagation evidence | Class prevalence and magnitudes are designed, not natural frequencies |
| Conservative page coordinate extraction is accurate when it emits, but incomplete | `P3_SWISSGEOL_EXTERNAL_SPATIAL_METADATA_002` | 53/88 emitted; 51 exact database agreements; no collar elevation accepted | Conditional spatial-field evidence | Database/collar reference is authoritative metadata, not page-derived geological truth |
| Full-support scoring favours risk selection, but matched-subset scoring does not | `experiments/paper3/analysis/swissgeol_spatial_sensitivity_v001.json` | Full-support volume error raw/reread/risk 0.1389/0.1216/0.0824; matched 15-document error 0.0326/0.0754/0.0754 | Selection/support effect separated from accepted-record value effect | Source-agreement reference, one source family, IDW diagnostic |
| Abstention changes the geometry of spatial support | `experiments/paper3/analysis/swissgeol_spatial_sensitivity_v001.json` | First-boundary hull ratio 0.636 and mean nearest-neighbour spacing 3.48 km for risk versus 1.39 km raw/reread | Spatial-support sensitivity | Does not establish geological correlation accuracy |
| Interpolation uncertainty is comparable to extraction-policy differences | `experiments/paper3/analysis/swissgeol_spatial_sensitivity_v001.json` | Reference-input LOOCV MAE about 47 m; method ordering varies across IDW settings | Model-choice and sampling baseline | IDW proxy only; no universal ranking |

## Claims explicitly not supported

- Universal cross-source safety or generalization of v028.
- Independent project-created human Ground Truth or annotator agreement.
- A measured reduction in human entry time or labour cost.
- Validated geological interpretation, GemPy production integration, or a universal 3-D model advantage.
- Accuracy for quarantined or licence-ambiguous source files.

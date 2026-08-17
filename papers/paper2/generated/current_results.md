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

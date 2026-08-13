<!-- AUTO-GENERATED. DO NOT EDIT. -->
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

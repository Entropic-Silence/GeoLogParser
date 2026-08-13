<!-- AUTO-GENERATED. DO NOT EDIT. -->
### OCR + regex audits

| Experiment | Model | Borehole ID EM | X coverage | X paired MAE | Final-depth coverage | Emitted intervals | s/page | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1_B1_BGS_AUDIT_001 | B1_tesseract_ocr_regex | 3/4 (0.750) | 4/4 (1.000) | 0.000 | 0/4 (0.000) | 1 | 6.369 | audit_only |
| P1_B1_RAPIDOCR_BGS_AUDIT_001 | B1_rapidocr_onnxruntime_ppocrv4_regex | 4/4 (1.000) | 0/4 (0.000) | TBD | 0/4 (0.000) | 0 | 3.525 | audit_only |
| P1_B1_RAPIDOCR_BGS_AUDIT_002 | B1_rapidocr_onnxruntime_ppocrv4_regex | 4/4 (1.000) | 4/4 (1.000) | 0.000 | 0/4 (0.000) | 0 | 3.506 | audit_only |
| P1_METADATA_BGS_TESSERACT_FORMAL_002 | B1_tesseract_ocr_regex | 2/4 (0.500) | 4/4 (1.000) | 0.000 | 0/4 (0.000) | 0 | 3.150 | formal_authoritative_metadata |
| P1_METADATA_BGS_TESSERACT_FORMAL_003 | B1_tesseract_ocr_regex | 29/31 (0.935) | 31/31 (1.000) | 9677.419 | 0/31 (0.000) | 1 | 2.210 | formal_authoritative_metadata |
| P1_METADATA_BGS_RAPIDOCR_FORMAL_001 | B1_rapidocr_onnxruntime_ppocrv4_regex | 31/31 (1.000) | 31/31 (1.000) | 0.000 | 1/31 (0.032) | 0 | 3.815 | formal_authoritative_metadata |
| P1_METADATA_BGS_TESSERACT_FORMAL_004 | B1_tesseract_ocr_regex | 25/31 (0.806) | 31/31 (1.000) | 0.000 | 0/31 (0.000) | 0 | 3.562 | formal_authoritative_metadata |

### Synthetic controlled OCR results (not Real Gold)

| Experiment | Model | Borehole ID EM | Final-depth coverage | Final-depth MAE (m) | Interval P | Interval R | Interval F1 | Matched top MAE (m) | s/page | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_B1_SYNTHETIC_CONTROLLED_002 | tesseract_eng_regex | 23/32 (0.719) | 32/32 (1.000) | 0.000 | 1.000 | 0.709 | 0.829 | 0.000 | 0.379 | audit_only |
| P1_B1_SYNTHETIC_CONTROLLED_001 | tesseract_eng_regex | 0/32 (0.000) | 32/32 (1.000) | 0.000 | 1.000 | 0.709 | 0.829 | 0.000 | 0.383 | failure_analysis_only |

These rows use programmatically known Synthetic labels. They validate controlled extraction and robustness paths but cannot establish performance on Real Gold borehole logs.

### Machine-adjudicated Silver agreement benchmark (not human accuracy)

| Experiment | Model | Pages | Borehole ID agreement | Final-depth MAE (Silver) | Interval P | Interval R | Interval F1 | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1_SILVER_B4_UNIPD_FIELD_002 | qwen3-vl-4b-instruct | 10 | 9/10 (0.900) | 0.000 | 0.714 | 0.663 | 0.688 | formal_silver_benchmark |
| P1_SILVER_B3_HELDOUT_UNIPD_FIELD_001 | positioned-text-layout-rules | 10 | 9/10 (0.900) | TBD | 0.677 | 0.253 | 0.368 | formal_silver_benchmark |
These metrics measure agreement with an explicitly machine-adjudicated Silver reference. They are not human/expert accuracy, and the reference construction channels are recorded in the source ledger and experiment configuration.

### Privacy-minimized OCR coverage audits (no Ground Truth)

| Experiment | Model | Completed pages | Borehole-ID presence | Final-depth presence | Pages with intervals | Emitted intervals | OCR regions | Constraint evals | Violations | s/page | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_B1_TESSERACT_SLOPES_AUDIT_001 | B1_tesseract_ocr_regex_privacy_minimized | 28/28 | 27/28 | 0/28 | 2/28 | 2 | 1528 | 14 | 4 | 1.640 | audit_only |
| P1_B1_RAPIDOCR_SLOPES_AUDIT_001 | B1_rapidocr_ppocrv4_regex_privacy_minimized | 28/28 | 28/28 | 0/28 | 0/28 | 0 | 3920 | 0 | 0 | 4.158 | audit_only |
| P1_B1_TESSERACT_TIBER_AUDIT_001 | B1_tesseract_ocr_regex_privacy_minimized | 1/1 | 0/1 | 0/1 | 0/1 | 0 | 34 | 0 | 0 | 0.948 | audit_only |
| P1_B1_RAPIDOCR_TIBER_AUDIT_001 | B1_rapidocr_ppocrv4_regex_privacy_minimized | 1/1 | 0/1 | 0/1 | 0/1 | 0 | 47 | 0 | 0 | 3.262 | audit_only |

Presence and emitted-count columns are extraction coverage diagnostics, not accuracy estimates. Records and OCR text are not serialized; source pages remain unreviewed and have no human Ground Truth.

### Privacy-minimized native-PDF coverage audits (no Ground Truth)

| Experiment | Model | Completed pages | Text regions | Regex borehole-ID presence | Regex pages with intervals | Regex intervals | Layout pages with intervals | Layout intervals | Layout constraint evals | Violations | s/page | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_NATIVE_LAYOUT_SEDLOG_AUDIT_001 | direct_native_text_regex_plus_B3_positioned_layout_privacy_minimized | 18/18 | 1279 | 0/18 | 0/18 | 0 | 0/18 | 0 | 0 | 0 | 0.087 | audit_only |

Direct-text and positioned-layout columns are extraction-path coverage diagnostics, not accuracy estimates. Persisted rows contain hashes and counts only; source text, extracted values, and source bboxes are omitted.

### B2 text-only LLM engineering audits

| Experiment | Model | Pages | Schema-valid | Emitted intervals | Constraint evals | Violations | Input tokens | s/page | Peak GiB | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_B2_QWEN3VL4B_TEXT_UNIPD_AUDIT_002 | Qwen/Qwen3-VL-4B-Instruct | 15 | 13/15 (0.867) | 74 | 538 | 8 | 11973 | 35.332 | 8.658 | audit_only |
| P1_B2_QWEN3VL4B_TEXT_UNIPD_AUDIT_003 | Qwen/Qwen3-VL-4B-Instruct | 15 | 13/15 (0.867) | 74 | 538 | 8 | 11973 | 50.102 | 8.658 | audit_only |

### B3 positioned-text layout engineering audits

| Experiment | Model | Pages | Pages with intervals | Emitted intervals | Constraint evals | Violations | s/page | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1_B3_LAYOUT_UNIPD_AUDIT_001 | B3_native_positioned_text_depth_column_rules | 15 | 5/15 | 46 | 367 | 3 | 0.039 | audit_only |
| P1_B3_LAYOUT_UNIPD_AUDIT_002 | B3_native_positioned_text_depth_column_rules | 15 | 5/15 | 46 | 367 | 3 | 0.040 | audit_only |

### VLM engineering audits

| Experiment | Model | Images | Schema-valid | Emitted intervals | Constraint evals | Violations | s/image | Peak GiB | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| P1_B4_QWEN3VL4B_SANMING_AUDIT_SMOKE_001 | Qwen/Qwen3-VL-4B-Instruct | 1 | 0/1 (0.000) | 0 | 0 | 0 | 128.382 | 8.713 | failure_analysis_only |
| P1_B4_QWEN3VL4B_SANMING_AUDIT_SMOKE_002 | Qwen/Qwen3-VL-4B-Instruct | 1 | 0/1 (0.000) | 0 | 0 | 0 | 32.553 | 8.642 | failure_analysis_only |
| P1_B4_QWEN3VL4B_SANMING_AUDIT_SMOKE_003 | Qwen/Qwen3-VL-4B-Instruct | 1 | 1/1 (1.000) | 2 | 20 | 4 | 29.820 | 8.642 | audit_only |
| P1_B4_QWEN3VL4B_SANMING_AUDIT_001 | Qwen/Qwen3-VL-4B-Instruct | 4 | 3/4 (0.750) | 8 | 82 | 20 | 50.637 | 8.654 | audit_only |
| P1_B4_QWEN3VL4B_BGS_AUDIT_001 | Qwen/Qwen3-VL-4B-Instruct | 4 | 4/4 (1.000) | 0 | 0 | 0 | 6.397 | 8.642 | audit_only |
| P1_B5_QWEN3VL4B_SANMING_AUDIT_001 | Qwen/Qwen3-VL-4B-Instruct | 4 | 1/4 (0.250) | 3 | 29 | 3 | 59.301 | 8.656 | audit_only |
| P1_B4_QWEN3VL4B_UNIPD_AUDIT_001 | Qwen/Qwen3-VL-4B-Instruct | 15 | 11/15 (0.733) | 87 | 778 | 49 | 60.987 | 8.713 | audit_only |

### B6 conservative fusion engineering audits

| Experiment | Model | Items | VLM available | Agreements | Disagreements | Visual-only review | VLM unavailable | Emitted intervals | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| P1_B6_QWEN3VL4B_UNIPD_AUDIT_001 | B6_conservative_direct_text_plus_Qwen3-VL-4B | 15 | 11/15 | 17 | 1 | 34 | 4 | 87 | audit_only |
| P1_B6_QWEN3VL4B_UNIPD_AUDIT_002 | B6_conservative_direct_text_plus_Qwen3-VL-4B | 15 | 11/15 | 17 | 1 | 34 | 4 | 87 | audit_only |

### Public native-PDF engineering audits

| Experiment | Model | Documents | Borehole-ID coverage | Final-depth coverage | Emitted intervals | Violations | s/page | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1_DIRECTPDF_UNIPD_AUDIT_001 | direct_pdf_text_conservative_regex | 11 | 0/11 | 0/11 | 0 | 0 | 0.128 | failure_analysis_only |
| P1_DIRECTPDF_UNIPD_AUDIT_002 | direct_pdf_text_conservative_regex | 11 | 11/11 | 0/11 | 0 | 10 | 0.129 | failure_analysis_only |
| P1_DIRECTPDF_UNIPD_AUDIT_003 | direct_pdf_text_conservative_regex | 11 | 11/11 | 0/11 | 0 | 10 | 0.130 | failure_analysis_only |
| P1_DIRECTPDF_UNIPD_AUDIT_004 | direct_pdf_text_conservative_regex | 11 | 11/11 | 0/11 | 0 | 1 | 0.125 | audit_only |

All rows are audit-only and not representative benchmark estimates. `TBD` paired MAE indicates zero paired predictions, not zero error. VLM audits have no human Ground Truth, so they report parse/diagnostic behavior rather than accuracy.

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

### Published manual-transcription Gold interval benchmark

| Experiment | Model | Documents | Counties | Pages | Reference intervals | Predicted intervals | Documents with predictions | Interval P | Interval R | Interval F1 | Matched lithology exact | Boundary-exact documents | s/document | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_CALIFORNIA_WCR_RAPIDOCR_TEST_FORMAL_001 | rapidocr_generic_positioned_interval_parser_v001 | 50 | 48 | 77 | 697 | 195 | 39 | 0.892 | 0.250 | 0.390 | 75/174 (0.431) | 3/50 (0.060) | 9.374 | formal_benchmark |
| P1_CALIFORNIA_WCR_TESSERACT_TEST_FORMAL_001 | tesseract_generic_positioned_interval_parser_v001 | 50 | 48 | 77 | 697 | 176 | 38 | 0.807 | 0.204 | 0.325 | 30/142 (0.211) | 1/50 (0.020) | 8.219 | formal_benchmark |
| P1_CALIFORNIA_WCR_V002_RAPIDOCR_EXTERNAL_FORMAL_002 | rapidocr_generic_positioned_interval_parser_v001 | 100 | 23 | 154 | 1770 | 673 | 92 | 0.817 | 0.311 | 0.450 | 284/550 (0.516) | 5/100 (0.050) | 9.773 | formal_external_benchmark |
| P1_CALIFORNIA_WCR_V002_TESSERACT_EXTERNAL_FORMAL_002 | tesseract_generic_positioned_interval_parser_v001 | 100 | 23 | 154 | 1770 | 497 | 79 | 0.789 | 0.221 | 0.346 | 149/392 (0.380) | 3/100 (0.030) | 9.184 | formal_external_benchmark |
| P1_CALIFORNIA_WCR_V003_RAPIDOCR_PROSPECTIVE_FORMAL_001 | rapidocr_generic_positioned_interval_parser_v001 | 100 | 31 | 154 | 1788 | 559 | 88 | 0.803 | 0.251 | 0.383 | 244/449 (0.543) | 5/100 (0.050) | 9.701 | formal_prospective_external_benchmark |
| P1_CALIFORNIA_WCR_V003_TESSERACT_PROSPECTIVE_FORMAL_001 | tesseract_generic_positioned_interval_parser_v001 | 100 | 31 | 154 | 1788 | 507 | 85 | 0.748 | 0.212 | 0.330 | 132/379 (0.348) | 4/100 (0.040) | 8.454 | formal_prospective_external_benchmark |
| P1_CALIFORNIA_WCR_V004_RAPIDOCR_PROSPECTIVE_FORMAL_001 | rapidocr_generic_positioned_interval_parser_v001 | 100 | 28 | 147 | 1944 | 622 | 77 | 0.883 | 0.282 | 0.428 | 244/549 (0.444) | 3/100 (0.030) | 9.086 | formal_prospective_external_benchmark |
| P1_CALIFORNIA_WCR_V005_RAPIDOCR_EXTERNAL_FORMAL_001 | rapidocr_generic_positioned_interval_parser_v001 | 100 | 35 | 141 | 2069 | 741 | 85 | 0.737 | 0.264 | 0.389 | 297/546 (0.544) | 4/100 (0.040) | 9.329 | formal_external_benchmark |
| P1_B4_QWEN3VL4B_CALIFORNIA_TEST_FORMAL_001R | Qwen3-VL-4B-Instruct_page_aggregate | 50 | 48 | 77 | 697 | 5 | 1 | 0.000 | 0.000 | 0.000 | TBD | 0/50 (0.000) | 0.000 | formal_external_benchmark |
The reference intervals were manually transcribed verbatim by USGS staff from California DWR well-completion-report images and received published depth-sequence and completeness checks. The project did not repeat human review of the 60-document freeze. Metrics therefore evaluate against published manual transcription, while report-image redistribution remains a separate pre-submission check.

### Held-out authoritative source-agreement interval result

| Experiment | Model | Documents | Reference intervals | Predicted intervals | Interval P | Interval R | Interval F1 | Matched top MAE (m) | Matched bottom MAE (m) | Full-document exact | s/document | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_SWISSGEOL_TG_INCREMENTAL_TESSERACT_FORMAL_003 | B1_tesseract_ocr_conservative_interval_parser | 20 | 55 | 55 | 0.855 | 0.855 | 0.855 | 0.000 | 0.000 | 17/20 (0.850) | 3.832 | formal_authoritative_interval |
| P1_SWISSGEOL_TG_CONTENT_HELDOUT_TESSERACT_FORMAL_004 | B1_tesseract_ocr_conservative_interval_parser | 35 | 80 | 74 | 0.892 | 0.825 | 0.857 | 0.000 | 0.000 | 25/35 (0.714) | 3.047 | formal_authoritative_interval |
| P1_SWISSGEOL_TG_CONTENT_HELDOUT_RAPIDOCR_FORMAL_005 | B1_rapidocr_onnx_ocr_conservative_interval_parser | 35 | 80 | 79 | 0.684 | 0.675 | 0.679 | 0.000 | 0.000 | 17/35 (0.486) | 4.117 | formal_authoritative_interval |
The reference contains only interval boundaries from official database records whose complete sequence exactly agrees with an explicit table in the paired official PDF. The reported run is incremental and disjoint from parser-development records, but the source-agreement selection is not a representative random sample and no human annotation is claimed.

### Source-disjoint official-database transfer agreement

| Experiment | Model | Records | Visual content groups | Official intervals | Predicted intervals | Records with predictions | Interval P | Interval R | Interval F1 | Content-group macro F1 | Full-record exact | s/record | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_SWISSGEOL_CROSS_CANTON_TESSERACT_TRANSFER_003 | B1_tesseract_ocr_conservative_interval_parser | 42 | 35 | 787 | 9 | 2 | 0.111 | 0.001 | 0.003 | 0.003 | 0/42 (0.000) | TBD | formal_authoritative_source_disjoint_transfer |
| P1_SWISSGEOL_CROSS_CANTON_RAPIDOCR_TRANSFER_002 | B1_rapidocr_onnx_ocr_conservative_interval_parser | 42 | 35 | 787 | 7 | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 0/42 (0.000) | TBD | formal_authoritative_source_disjoint_transfer |
| P1_SWISSGEOL_FIVE_CANTON_TESSERACT_TRANSFER_001 | B1_tesseract_ocr_conservative_interval_parser | 46 | 39 | 3332 | 9 | 2 | 0.111 | 0.000 | 0.001 | 0.003 | 0/46 (0.000) | TBD | formal_authoritative_source_disjoint_transfer |
| P1_SWISSGEOL_FIVE_CANTON_RAPIDOCR_TRANSFER_001 | B1_rapidocr_onnx_ocr_conservative_interval_parser | 46 | 39 | 3332 | 7 | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 0/46 (0.000) | TBD | formal_authoritative_source_disjoint_transfer |
These runs apply the frozen Thurgau parser without reference conditioning to all paired records in each successively frozen non-development-canton panel. Official database intervals belong to the same borehole objects, but complete page/database agreement was not established; the values therefore measure transfer agreement and combine extraction error with possible source mismatch. Content-group macro F1 prevents one repeated 21-page report from receiving eightfold weight. The indexed aggregations resumed completed OCR artifacts after earlier interrupted/metric-only runs, so end-to-end latency is not reported.

### Cross-source authoritative interval diagnostic

| Experiment | Model | Documents | Reference intervals | Predicted intervals | Interval P | Interval R | Interval F1 | Matched top MAE (m) | Matched bottom MAE (m) | Full-document exact | s/document | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_USGS142_CROSS_SOURCE_INTERVAL_FORMAL_002 | tesseract_roi_generalized_lithology_parser | 1 | 12 | 12 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 1/1 (1.000) | 3.298 | formal_authoritative_interval |
| P1_USGS144_CROSS_SOURCE_INTERVAL_FORMAL_001 | tesseract_raster_page_interval_parser | 1 | 8 | 8 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 1/1 (1.000) | 17.387 | formal_authoritative_interval |
| P1_USGS_RAFT_RIVER_TESSERACT_INTERVAL_FORMAL_001 | tesseract_raster_table_interval_parser | 2 | 62 | 56 | 0.875 | 0.790 | 0.831 | 0.000 | 0.000 | 0/2 (0.000) | 6.354 | formal_authoritative_interval |
| P1_USGS_RAFT_RIVER_RAPIDOCR_INTERVAL_FORMAL_001 | rapidocr_raster_table_interval_parser | 2 | 62 | 62 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 1/2 (0.500) | 7.736 | formal_authoritative_interval |
| P1_BGS_OFFSHORE_V001_RAPIDOCR_CROSS_SOURCE_FORMAL_001 | rapidocr_bgs_composite_interval_parser_v001 | 26 | 341 | 28 | 0.250 | 0.021 | 0.038 | 0.000 | 0.000 | TBD | 9.568 | formal_authoritative_interval |
| P1_BGS_OFFSHORE_V001_TESSERACT_CROSS_SOURCE_FORMAL_001 | tesseract_bgs_composite_interval_parser_v001 | 26 | 341 | 54 | 0.148 | 0.023 | 0.041 | 0.000 | 0.003 | TBD | 10.080 | formal_authoritative_interval |
This table adds a single official USGS Idaho PDF with an explicit generalized-lithology legend. It is a cross-source diagnostic, not evidence for a representative source-disjoint estimate; source rights remain pending manual verification.

### Reference-conditioned interval diagnostics excluded from formal claims

| Experiment | Model | Documents | Reference intervals | Predicted intervals | Interval P | Interval R | Interval F1 | Matched top MAE (m) | Matched bottom MAE (m) | Full-document exact | s/document | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_SWISSGEOL_TG_INTERVAL_TESSERACT_FORMAL_001 | B1_tesseract_ocr_conservative_interval_parser | 9 | 21 | 15 | 1.000 | 0.714 | 0.833 | 0.000 | 0.000 | 6/9 (0.667) | 3.127 | diagnostic_oracle_metadata |
These retained runs conditioned candidate filtering/ranking on an official reference field and are diagnostics only. They are excluded from formal extraction claims even when their output metrics are otherwise valid.

### Interval-parser development results excluded from held-out claims

| Experiment | Model | Documents | Reference intervals | Predicted intervals | Interval P | Interval R | Interval F1 | Matched top MAE (m) | Matched bottom MAE (m) | Full-document exact | s/document | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P1_SWISSGEOL_TG_INTERVAL_TESSERACT_FORMAL_002 | B1_tesseract_ocr_conservative_interval_parser | 9 | 21 | 16 | 1.000 | 0.762 | 0.865 | 0.000 | 0.000 | 6/9 (0.667) | 3.180 | development_authoritative_interval |
| P1_SWISSGEOL_TG_CONTENT_DEVELOPMENT_RAPIDOCR_001 | B1_rapidocr_onnx_ocr_conservative_interval_parser | 37 | 85 | 85 | 0.635 | 0.635 | 0.635 | 0.000 | 0.000 | 19/37 (0.514) | 4.150 | development_authoritative_interval |
These reference-independent runs used the v001 records on which parser/reread behavior was developed. They are retained as development evidence and excluded from the incremental held-out estimate.

### Machine-adjudicated Silver agreement benchmark (not human accuracy)

| Experiment | Model | Pages | Borehole ID agreement | Final-depth MAE (Silver) | Interval P | Interval R | Interval F1 | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1_SILVER_B4_UNIPD_FIELD_002 | qwen3-vl-4b-instruct | 10 | 9/10 (0.900) | 0.000 | 0.714 | 0.663 | 0.688 | formal_silver_benchmark |
| P1_SILVER_B3_HELDOUT_UNIPD_FIELD_001 | positioned-text-layout-rules | 10 | 9/10 (0.900) | TBD | 0.677 | 0.253 | 0.368 | formal_silver_benchmark |
These metrics measure agreement with an explicitly machine-adjudicated Silver reference. They are not human/expert accuracy, and the reference construction channels are recorded in the source ledger and experiment configuration.

### Real-source controlled-degradation robustness (metadata fields only)

| Experiment | Model | Profile | ID exact | X coverage | X MAE | Y coverage | Y MAE | Complete ID/X/Y | Field omissions | Eligibility |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| P1_BGS_METADATA_ROBUSTNESS_TESSERACT_001 | B1_tesseract_ocr_regex | blur_20 | 16 | 29 | 0.000 | 29 | 0.000 | 15 | 15 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_TESSERACT_001 | B1_tesseract_ocr_regex | clean | 24 | 31 | 0.000 | 31 | 0.000 | 24 | 1 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_TESSERACT_001 | B1_tesseract_ocr_regex | contrast_040 | 26 | 31 | 0.000 | 31 | 0.000 | 26 | 2 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_TESSERACT_001 | B1_tesseract_ocr_regex | jpeg_30 | 26 | 31 | 0.000 | 31 | 0.000 | 26 | 2 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_TESSERACT_001 | B1_tesseract_ocr_regex | noise_16 | 23 | 30 | 0.000 | 30 | 0.000 | 22 | 5 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_TESSERACT_001 | B1_tesseract_ocr_regex | resolution_050 | 29 | 30 | 0.000 | 30 | 0.000 | 29 | 4 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_TESSERACT_001 | B1_tesseract_ocr_regex | skew_30 | 17 | 15 | 0.000 | 15 | 54162.400 | 9 | 44 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_RAPIDOCR_001 | B1_rapidocr_onnxruntime_ppocrv4_regex | blur_20 | 31 | 27 | 0.000 | 27 | 0.000 | 27 | 8 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_RAPIDOCR_001 | B1_rapidocr_onnxruntime_ppocrv4_regex | clean | 31 | 31 | 0.000 | 31 | 0.000 | 31 | 0 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_RAPIDOCR_001 | B1_rapidocr_onnxruntime_ppocrv4_regex | contrast_040 | 31 | 31 | 0.000 | 31 | 0.000 | 31 | 0 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_RAPIDOCR_001 | B1_rapidocr_onnxruntime_ppocrv4_regex | jpeg_30 | 31 | 7 | 0.000 | 7 | 0.000 | 7 | 48 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_RAPIDOCR_001 | B1_rapidocr_onnxruntime_ppocrv4_regex | noise_16 | 31 | 29 | 0.000 | 29 | 0.000 | 29 | 4 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_RAPIDOCR_001 | B1_rapidocr_onnxruntime_ppocrv4_regex | resolution_050 | 31 | 28 | 0.000 | 28 | 0.000 | 28 | 6 | formal_authoritative_metadata_robustness |
| P1_BGS_METADATA_ROBUSTNESS_RAPIDOCR_001 | B1_rapidocr_onnxruntime_ppocrv4_regex | skew_30 | 31 | 31 | 0.000 | 31 | 0.000 | 31 | 0 | formal_authoritative_metadata_robustness |
These rows use first-page borehole ID/X/Y references from official BGS metadata. Profiles are synthetic transformations of real scans; final depth, intervals, and lithology are excluded because the first-page scope does not provide those references.

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

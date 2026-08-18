# Main tables for the integrated Computers & Geosciences manuscript

All interval F1 values below are **boundary-pair interval F1**: both top and
bottom depths must match under the order-preserving tolerance. Evidence tiers
are not pooled.

## Table 1. Reliability across cohorts and source families

| Cohort/source | Evidence | Documents | Reference intervals | System | Boundary-pair F1 | Boundary-exact | Zero output |
|---|---|---:|---:|---|---:|---:|---:|
| California v001 | Published manual transcription Gold | 50 | 697 | Qwen/Qwen3.8-27B-FP8 direct | 0.932 | 0.740 | 0.000 |
| California v002 | Published manual transcription Gold | 100 | 1,770 | Qwen/Qwen3.8-27B-FP8 direct | 0.896 | 0.700 | 0.000 |
| California v003 | Published manual transcription Gold | 100 | 1,788 | Qwen/Qwen3.8-27B-FP8 direct | 0.918 | 0.720 | 0.000 |
| California v004 | Published manual transcription Gold | 100 | 1,944 | Qwen/Qwen3.8-27B-FP8 direct | 0.917 | 0.740 | 0.050 |
| California v005 | Published manual transcription Gold | 100 | 2,069 | Qwen/Qwen3.8-27B-FP8 direct | 0.903 | 0.690 | 0.010 |
| Swissgeol Thurgau held-out | Source-agreement reference | 35 | 80 | Qwen/Qwen3.8-27B-FP8 direct | 0.577 | 0.000 | 0.000 |
| BGS Offshore | Source-agreement reference | 26 | 341 | RapidOCR positioned parser | 0.038 | — | — |

## Table 2. Independent evidence and selective assurance

| Cohort | Raw proposal precision | Numeric-anchor coverage | Owned/accepted coverage | Accepted intervals | Selective precision (95% CI) | Error documents |
|---|---:|---:|---:|---:|---:|---:|
| California v001 development | 0.908 | 0.817 | 0.236 | 174 | 1.000 [1.000, 1.000] | 0 |
| California v002 validation | 0.854 | 0.849 | 0.287 | 561 | 0.979 [0.951, 0.997] | 5 |
| California v003 held-out | 0.907 | 0.845 | 0.244 | 447 | 0.993 [0.984, 1.000] | 3 |

## Table 3. Risk/coverage and downstream support

| Analysis | Raw | Reread | Risk-aware |
|---|---:|---:|---:|
| California v004/v005 net matched gain per 100 documents | — | — | 41 (versus 230.5 unselective) |
| California accepted actions | — | — | 82 in 19 documents |
| California worsened documents | — | — | 0 observed; one-sided upper bound 0.1459 |
| Swissgeol full-support volume error | 0.1387 | 0.1213 | 0.0821 |
| Swissgeol matched-subset volume error | 0.0326 | 0.0754 | 0.0754 |
| Swissgeol first-boundary hull-area ratio | 1.000 | 1.000 | 0.636 |
| Swissgeol default LOO MAE (m) | 49.84 | 46.62 | 47.05 |

## Table 4. Modern VLM execution provenance

| Field | Frozen value |
|---|---|
| Official checkpoint | `Qwen/Qwen3.8-27B-FP8` |
| Served model ID | `qwen38-fp8-tp4-mtp4-long` |
| Local revision | `local_Qwen3.8-27B-FP8_qwen3_5_architecture_fp8_e4m3` |
| Precision | Fine-grained dynamic FP8 E4M3 |
| Runtime | vLLM-compatible OpenAI server; package version not exposed |
| Hardware | 4 × RTX 2080 Ti |
| Prompt | `vlm_interval_source_units_v002` |
| Prompt SHA-256 | `891bc6beb7ff9cf35c55389191a208c9b09e9e2dc76909f716603f413745104a` |
| Image input | PyMuPDF, 200-DPI lossless PNG, no crop/rotation/enhancement |
| Decoding | temperature 0; provider-default top-p; 4,096 max tokens; thinking disabled |
| Retries | 0 automatic retries |
| Parsing | strict JSON; no YAML, repair, completion, reorder, or deduplication |
| Testing date | 2026-08-17 UTC |

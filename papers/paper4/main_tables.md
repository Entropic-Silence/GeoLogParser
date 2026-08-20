# Main tables for the integrated Computers & Geosciences manuscript

All interval F1 values below are **boundary-pair interval F1**: both top and
bottom depths must match under the order-preserving tolerance. Evidence tiers
are not pooled.

## Table 1. Boundary-pair interval F1 across cohorts and source-shift panels

| Panel | Reader/interface | Evidence tier | Documents | Reference intervals | Boundary-pair interval F1 |
|---|---|---|---:|---:|---:|
| California v001 | Qwen/Qwen3.8-27B-FP8 direct | Published manual-transcription Gold | 50 | 697 | 0.932 |
| California v001 | RapidOCR positioned | Published manual-transcription Gold | 50 | 697 | 0.390 |
| California v002 | Qwen/Qwen3.8-27B-FP8 direct | Published manual-transcription Gold | 100 | 1,770 | 0.896 |
| California v002 | RapidOCR positioned | Published manual-transcription Gold | 100 | 1,770 | 0.450 |
| California v003 | Qwen/Qwen3.8-27B-FP8 direct | Published manual-transcription Gold | 100 | 1,788 | 0.918 |
| California v003 | RapidOCR positioned | Published manual-transcription Gold | 100 | 1,788 | 0.383 |
| California v004 | Qwen/Qwen3.8-27B-FP8 direct | Published manual-transcription Gold | 100 | 1,944 | 0.917 |
| California v004 | RapidOCR positioned | Published manual-transcription Gold | 100 | 1,944 | 0.428 |
| California v005 | Qwen/Qwen3.8-27B-FP8 direct | Published manual-transcription Gold | 100 | 2,069 | 0.903 |
| California v005 | RapidOCR positioned | Published manual-transcription Gold | 100 | 2,069 | 0.389 |
| Swissgeol held-out | Qwen/Qwen3.8-27B-FP8 direct | Source-agreement reference | 35 | 80 | 0.577 |
| Swissgeol held-out | RapidOCR positioned | Source-agreement reference | 35 | 80 | 0.679 |
| Swissgeol held-out | Tesseract positioned | Source-agreement reference | 35 | 80 | 0.857 |
| BGS Offshore | RapidOCR positioned | Source-agreement reference | 26 | 341 | 0.038 |
| BGS Offshore | Tesseract positioned | Source-agreement reference | 26 | 341 | 0.041 |
| Raft River | RapidOCR positioned | Source-agreement reference | 2 | 62 | 1.000 |

## Table 2. Independent evidence and selective assurance

| Cohort | Raw proposal precision | Endpoint-field anchor coverage | Both-endpoint anchor coverage | Accepted coverage | Accepted intervals (n) | Selective precision (95% CI) | Error documents |
|---|---:|---:|---:|---:|---:|---:|---:|
| California v001 development | 0.908 | 0.817 | 0.731 | 0.236 | 174 | 1.000 [1.000, 1.000] | 0 |
| California v002 validation | 0.854 | 0.849 | 0.792 | 0.287 | 561 | 0.979 [0.951, 0.997] | 5 |
| California v003 held-out | 0.907 | 0.845 | 0.791 | 0.244 | 447 | 0.993 [0.984, 1.000] | 3 |

Complete-document auto-acceptance on v003 is 4/100 (4%); it is not inferred
from interval-level coverage. Endpoint-field anchor coverage counts proposed top
and bottom fields separately; both-endpoints coverage counts intervals, and only
the final owned/accepted column represents automatically accepted intervals.

## Table 3. Risk/coverage and downstream support

| Analysis | Raw | Reread | Risk-aware |
|---|---:|---:|---:|
| California v004/v005 net matched gain per 100 documents | — | — | 41 (versus 230.5 unselective) |
| California accepted actions | — | — | 82 in 19 documents |
| California worsened documents | — | — | 0 observed; one-sided upper bound 0.1459 |
| Swissgeol full-support reference-relative volume discrepancy | 0.1387 | 0.1213 | 0.0821 |
| Swissgeol matched-subset reference-relative volume discrepancy | 0.0326 | 0.0754 | 0.0754 |
| Swissgeol first-boundary hull-area ratio | 1.000 | 1.000 | 0.636 |
| Swissgeol default LOO MAE (m) | 49.84 | 46.62 | 47.05 |

## Table 4. Modern VLM execution provenance

| Field | Frozen value |
|---|---|
| Official checkpoint | `Qwen/Qwen3.8-27B-FP8` |
| Served model ID | `qwen38-fp8-tp4-mtp4-long` |
| Local revision | `local_Qwen3.8-27B-FP8_qwen3_5_architecture_fp8_e4m3` |
| Precision | Fine-grained dynamic FP8 E4M3 |
| Runtime | vLLM 0.1.14 OpenAI server; partially reconstructable after evaluation |
| Python / ML runtime | Python 3.10.12; PyTorch 2.11.0+cu128; CUDA 12.8; Transformers 4.57.6; Triton 3.6.0 |
| Hardware | CUDA devices 1–4: 4 × RTX 2080 Ti (SM75); host driver 595.71.05 |
| Serving path | `ai@sha256:b937…22fc78d`; `runc`; `/workspace/vllm-2080ti-definitive`; TP=4 / MP backend |
| Server settings | FP8 weights; half compute dtype; KV cache auto; chunked prefill; MTP-4 speculative decoding; `flashqla_legacy` prefill |
| Prompt | `vlm_interval_source_units_v002` |
| Prompt SHA-256 | `891bc6beb7ff9cf35c55389191a208c9b09e9e2dc76909f716603f413745104a` |
| Image input | PyMuPDF, 200-DPI lossless PNG, no crop/rotation/enhancement |
| Decoding | temperature 0; provider-default top-p; 4,096 max tokens; thinking disabled |
| Retries | 0 automatic retries |
| Parsing | strict JSON; no YAML, repair, completion, reorder, or deduplication |
| Testing date | 2026-08-17 UTC |
| Unrecoverable fields | vLLM source commit, per-request trace, and immutable contemporaneous runtime lockfile |

## Table 5. Exploratory modern open-model transport panel

| Model/interface | Panel | Documents/pages | Interval output | Boundary-pair F1 | Complete-document exactness | Evidence interpretation |
|---|---|---:|---:|---:|---:|---|
| `Qwen/Qwen3.8-27B-FP8` direct JSON | Swissgeol held-out | 35/35 | 76 | 0.577 | 0/35 | source-agreement transport result |
| `Qwen/Qwen3-VL-4B-Instruct` direct JSON | California v003 page-20 exploratory | 13/20 | 273 | 0.793 | 3/13 | fixed exploratory subset |
| `Qwen/Qwen3-VL-4B-Instruct` direct JSON | Swissgeol held-out | 35/35 | 59 | 0.619 | 0/35 | source-agreement transport result |
| `PaddlePaddle/PaddleOCR-VL-1.6` official table task | Swissgeol held-out | 35/35 | 0 auditable decoded rows | 0.000* | 0/35 | task completed; fixed interval decoder coverage 0 |
| `opendatalab/MinerU2.5-Pro-2604-1.2B` official parser | Swissgeol held-out | 35/35 | 0 auditable decoded rows | 0.000* | 0/35 | task completed; fixed interval decoder coverage 0 |

\* The specialist rows are decoder/task-coverage results, not claims that the
models produced no table content. They are not pooled with direct-JSON F1.

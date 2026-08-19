# Claim–evidence map for the integrated manuscript

| Claim ID | Manuscript claim | Evidence source | Evidence tier | Reproducible artifact |
|---|---|---|---|---|
| C4-01 | Qwen/Qwen3.8-27B-FP8 reaches California boundary-pair F1 0.896–0.932 and 69–74% boundary-exact | `p1.modern_vlm_qwen38` | Published manual-transcription Gold | `experiments/paper1/modern_vlm_result_summary_v001.json`; `papers/paper1/generated/modern_vlm_results.md` |
| C4-02 | RapidOCR reaches 0.383–0.450 with 0–2% full-record exactness | Paper I California formal runs | Published manual-transcription Gold | `papers/paper1/generated/major_revision_tables.md` |
| C4-03 | Direct Qwen invalid numeric ranges occur at 0.004–0.017 | `p1.modern_vlm_qwen38` | Published manual-transcription Gold protocol diagnostic | `experiments/paper1/modern_vlm_result_summary_v001.json` |
| C4-04 | Qwen falls to F1 0.577 on Swissgeol | `p1.modern_vlm_qwen38` | Source-agreement reference | `experiments/paper1/modern_vlm_result_summary_v001.json` |
| C4-05 | Independent positioned evidence yields 0.993 precision at 0.244 coverage on v003 | `p2.vlm_proposal_assurance` | Published manual-transcription Gold | `experiments/paper2/analysis/vlm_proposal_assurance_v001.json` |
| C4-06 | Monotonic decoding is the largest same-pool recovery component | Paper II candidate-pool ablation | Published manual-transcription Gold | `experiments/paper2/analysis/california_candidate_pool_ablation_v001.json` |
| C4-07 | Unselective reconstruction has non-zero false-correction/document harm | Paper II California sequence/risk runs | Published manual-transcription Gold | `experiments/paper2/analysis/california_document_risk_v001.json` |
| C4-08 | Addition-only policy accepts 82 actions in 19 documents, zero observed worsened documents, bound 0.1459 | `p2.california_candidate_risk_certificate`; `p2.california_document_risk` | Published manual-transcription Gold | `publication_evidence/result_core/results/2026-08-17/P2_CALIFORNIA_CANDIDATE_RISK_CERTIFICATE_001/metrics.json`; `experiments/paper2/analysis/california_document_risk_v001.json` |
| C4-09 | BGS v003 abstains on every visible page | `p2.bgs_v003_v028_external_failure` | External source-shift diagnostic | `experiments/paper2/analysis/bgs_v003_v028_routed_external_final.json` |
| C4-10 | Full-support risk reference-relative volume discrepancy is 0.0821 with hull ratio 0.636 | `p3.spatial_sensitivity` | Source-agreement reference | `experiments/paper3/analysis/swissgeol_spatial_sensitivity_v001.json`; `publication_evidence/analysis_inputs/paper3/spatial_input_v001.jsonl` |
| C4-11 | Matched-subset risk and reread both have reference-relative volume discrepancy 0.0754; raw is 0.0326 | `p3.spatial_sensitivity` | Source-agreement reference | `experiments/paper3/analysis/swissgeol_spatial_sensitivity_v001.json` |
| C4-12 | Reference-input LOO MAE is 47.06 m and jackknife ranges overlap | `p3.spatial_sensitivity` | Source-agreement reference | `experiments/paper3/analysis/swissgeol_spatial_sensitivity_v001.json` |
| C4-13 | Support-preserving fusion improves 26–29 of 30 synthetic perturbation repetitions | `p3.coal602_consensus_qc` | Controlled synthetic error injection | `publication_evidence/result_core/results/2026-08-13/P3_COAL602_CONSENSUS_QC_CONTROLLED_002/metrics.json` |
| C4-14 | Model, prompt, rendering, precision, runtime and parsing provenance | Qwen config and execution ledger | Protocol metadata | `configs/models/qwen38_fp8_modern_vlm_v002.json`; `papers/paper1/generated/modern_vlm_execution_ledger.md` |
| C4-15 | Exploratory transport evidence across Qwen3-VL-4B, PaddleOCR-VL-1.6 and MinerU2.5-Pro on the independent Swissgeol panel | Modern open-model transport roster | Source-agreement reference; decoder/task-coverage diagnostics | `experiments/paper1/analysis/modern_vlm_transport_comparison_v001.json`; `configs/experiments/paper1_modern_vlm_transport_v001.json`; `papers/paper4/supplement.md` |

## Evidence boundary

No claim in the integrated manuscript promotes source-agreement, Silver,
synthetic, or audit-only evidence to published manual-transcription Gold. The
claim map is intended to be checked automatically against the existing claim
registry before submission.

# Modern VLM Baseline Roster

This registry separates executable baseline definitions from scientific
results. A registered model is not a completed experiment.

| Group | Model | Interface | Status | Evidence source |
| --- | --- | --- | --- | --- |
| Open | Qwen3.8-27B-FP8 | Local OpenAI-compatible server | `COMPLETED_CALIFORNIA_V001_TO_V005` | `configs/models/qwen38_fp8_modern_vlm_v002.json` |
| Open | Qwen3-VL-4B-Instruct | Local Transformers direct page-to-JSON | `COMPLETED_TRANSPORT_SWISSGEOL_F1_0.619_CALIFORNIA_PAGE20_F1_0.793` | `configs/models/qwen3vl4b_modern_vlm_v001.json` |
| Open | MinerU2.5-Pro-2604-1.2B | Local official two-step parser | `COMPLETED_INTERFACE_COVERAGE_35_PAGES_ZERO_AUDITABLE_INTERVAL_ROWS` | `configs/models/mineru25_pro_modern_vlm_v001.json` |
| Open | PaddleOCR-VL-1.6 | Local Transformers official table-recognition interface | `COMPLETED_INTERFACE_COVERAGE_35_PAGES_ZERO_AUDITABLE_INTERVAL_ROWS` | `configs/models/paddleocr_vl_1_6_modern_vlm_v001.json` |
| Closed | OpenAI GPT-5.6-Sol (`gpt-5.6-sol`, Codex internal visual, xhigh) | Codex host-managed visual runtime | `COMPLETED_STRATIFIED_5_PAGE_PILOT_F1_1.000_NOT_FULL_COHORT` | `configs/models/gpt56_sol_codex_internal_visual_v001.json` |
| Closed | requested `chatgpt5.6-sol-high`, served `gpt-5.6-sol` | User-provided OpenAI-compatible Responses endpoint | `NO_GO_SYNTHETIC_VISUAL_PREFLIGHT_UPSTREAM_502_NO_GOLD_REQUEST` | [Preflight record](modern_vlm_closed_endpoint_preflight.md) |
| Closed | Claude Opus 4.6 | Anthropic official Messages API | `NOT_RUN_REQUIRES_VALID_OFFICIAL_API_CREDENTIAL` | [Anthropic model overview](https://docs.anthropic.com/en/docs/about-claude/models/overview) |

The closed group is registered in the post-hoc exploratory extension
`configs/experiments/paper1_modern_vlm_closed_extension_v003.json`. It is not
folded into the frozen v002 open-model roster, and it will not be represented
as an evaluated group unless the exact official calls, provider-returned model
IDs, page-level responses, and metrics are all archived.

The endpoint's own `/v1/models` response is the authoritative identity evidence
for this exploratory slot. No account identity, interactive product session,
proxy label, or inferred upstream model name is treated as an experimental model
identity. Because the visual preflight failed, this slot is not included in any
accuracy comparison or risk-layer claim. The Codex internal-visual pilot is a
separate closed baseline: it is included in Paper II as a five-page stratified
Gold pilot, but not pooled with the full-cohort Qwen results because its host
runtime does not expose a checkpoint, revision, decoding trace, or independent
reproduction path.

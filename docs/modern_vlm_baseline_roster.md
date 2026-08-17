# Modern VLM Baseline Roster

This registry separates executable baseline definitions from scientific
results. A registered model is not a completed experiment.

| Group | Model | Interface | Status | Evidence source |
| --- | --- | --- | --- | --- |
| Open | Qwen3.8-27B-FP8 | Local OpenAI-compatible server | `RUNNING` | `configs/models/qwen38_fp8_modern_vlm_v002.json` |
| Open | MinerU2.5-Pro-2604-1.2B | Local official two-step parser | `RUNNING` | `configs/models/mineru25_pro_modern_vlm_v001.json` |
| Open | PaddleOCR-VL-1.6 | Official-compatible local runtime pending | `NOT_RUN` | `docs/modern_vlm_baseline_protocol.md` |
| Closed | GPT-5.6 Sol | OpenAI official Chat Completions API | `NOT_RUN_REQUIRES_VALID_OFFICIAL_API_CREDENTIAL` | [OpenAI Docs](https://developers.openai.com/api/docs/models/gpt-5.6-sol) |
| Closed | Claude Opus 4.6 | Anthropic official Messages API | `NOT_RUN_REQUIRES_VALID_OFFICIAL_API_CREDENTIAL` | [Anthropic model overview](https://docs.anthropic.com/en/docs/about-claude/models/overview) |

The closed group is registered in the post-hoc exploratory extension
`configs/experiments/paper1_modern_vlm_closed_extension_v003.json`. It is not
folded into the frozen v002 open-model roster, and it will not be represented
as an evaluated group unless the exact official calls, provider-returned model
IDs, page-level responses, and metrics are all archived.

OpenAI's model documentation retrieved on 2026-08-17 identifies
`gpt-5.6-sol` as accepting image input through both Responses and Chat
Completions APIs. The configuration uses the latter because it shares the
repository's frozen JSON transport. The model identifier and documentation URL
are retained in its configuration file. Anthropic's model overview was checked
on the same date before registering the Messages API slot. No account identity,
interactive product session, proxy label, or inferred upstream model name is
treated as an experimental model identity.

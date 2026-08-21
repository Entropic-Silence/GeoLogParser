# Closed VLM Endpoint Preflight

Date: 2026-08-17 (UTC)

## Scope and identity

This is a synthetic visual transport preflight, not a model evaluation. The
user-provided OpenAI-compatible endpoint was queried through both `/v1/models`
and the multimodal `/v1/responses` interface. The model list returned only
`gpt-5.6-sol`; it did not expose a distinct `chatgpt5.6-sol-high` model ID.
The auditable identity is therefore:

| Field | Recorded value |
| --- | --- |
| requested deployment label | `chatgpt5.6-sol-high` |
| served model ID | `gpt-5.6-sol` |
| reasoning effort | `high` |
| checkpoint/API snapshot | not exposed by endpoint; response IDs retained when returned |
| revision/hash | model-list observation `2026-08-17:gpt-5.6-sol` |
| precision | provider undisclosed |
| serving framework/version | provider undisclosed |
| transport | OpenAI-compatible Responses `/v1/responses` |
| prompt | `vlm_interval_source_units_v002`, SHA-256 `891bc6beb7ff9cf35c55389191a208c9b09e9e2dc76909f716603f413745104a` |
| image preprocessing | 200-DPI PyMuPDF PNG, no crop/rotation/enhancement |
| temperature/top-p | temperature omitted; provider default top-p |
| max output tokens | 4096 |
| retries | zero automatic page retries |
| parsing | strict JSON object; no YAML, repair, completion, reorder, or deduplication |
| test date | 2026-08-17 |

The credential is stored only in `/root/.geologparser_closed_vlm.env` with mode
600 and is not part of the repository or any artifact.

## Outcome

The synthetic image request reached the visual endpoint but returned HTTP 502
`upstream_error` twice. A minimal Responses request also returned a visual
validation error before generation. No California, Swissgeol, BGS, Raft River,
or other real-source page was sent. Consequently there is no closed-model Gold
baseline, no closed-model risk-layer result, and no accuracy claim. The
registered status is:

`NO_GO_SYNTHETIC_VISUAL_PREFLIGHT_UPSTREAM_502_NO_GOLD_REQUEST`

This is an endpoint availability/protocol failure, not evidence about the
capability of the named model. The extension remains registered but excluded
from confirmatory tables. It may be rerun only after a successful synthetic
visual preflight, with the exact request/response metadata archived first.

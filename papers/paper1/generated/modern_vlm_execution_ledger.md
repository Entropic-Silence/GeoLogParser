# Modern VLM Execution Ledger

This ledger separates completed experiments from registered or failed slots.

| Group | Official model / served ID | Revision or checkpoint | Precision | Runtime | Prompt hash | DPI / preprocessing | Decode | Date | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Open | `Qwen/Qwen3.8-27B-FP8` / `qwen38-fp8-tp4-mtp4-long` | local file hashes recorded in `configs/models/qwen38_fp8_modern_vlm_v002.json` | fine-grained dynamic FP8 E4M3 | vLLM-compatible OpenAI server; package version not exposed | `891bc6beb7ff9cf35c55389191a208c9b09e9e2dc76909f716603f413745104a` | 200-DPI PyMuPDF lossless PNG; no crop/rotation/enhancement | temperature 0; provider-default top-p; 4096 tokens; no retries; strict JSON only | 2026-08-17 | California v001–v005 and Swissgeol completed |
| Closed exploratory | requested `chatgpt5.6-sol-high` / `gpt-5.6-sol` | endpoint model-list observation `2026-08-17:gpt-5.6-sol`; no checkpoint/API snapshot exposed | provider undisclosed | user-provided OpenAI-compatible Responses endpoint; framework/version undisclosed | `891bc6beb7ff9cf35c55389191a208c9b09e9e2dc76909f716603f413745104a` | 200-DPI PyMuPDF lossless PNG; no crop/rotation/enhancement | reasoning effort high; temperature omitted; provider-default top-p; 4096 tokens; no retries; strict JSON only | 2026-08-17 | NO-GO: synthetic visual preflight HTTP 502; no real page sent |

For every completed run, the immutable run directory also stores page hashes,
provider response IDs when available, parser version, and metrics. The closed
credential is never stored in this repository.

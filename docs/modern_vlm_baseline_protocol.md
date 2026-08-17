# Modern VLM Baseline Protocol

This protocol adds a deliberately narrow direct-VLM comparison to Paper I. It
does not retune GeoLogParser and it does not alter the five California Gold
cohorts, BGS v003, or any frozen parser configuration.

## Question

Can current generalist and document-specialist VLMs reconstruct visible
lithological intervals directly from a rendered borehole-log page, and which
reliability properties remain unique to an evidence-aware routed parser?

## Frozen Common Protocol

Every direct-JSON model receives the same 200-DPI rendered page, the same
`vlm_interval_source_units_v002` prompt, greedy decoding and a 4,096-token
limit. It returns source-unit interval JSON. Document-specialist models retain
their published task prompt and produce table markup, so they are a separate
interface rather than an artificially prompt-matched variant. All interfaces
use the same source-unit conversion, explicit-header decoder, document-order
aggregation and frozen order-preserving boundary matcher at 0.05 m tolerance.
Neither decoder completes, repairs, reorders, or deduplicates intervals.

Prompt writing and endpoint-format smoke tests are restricted to synthetic
pages. No California Gold page is used to revise the prompt, output schema,
decoder, threshold, model roster or selection decision. BGS v003 is excluded.

## Model Families

The open group consists of the locally served Qwen3.8-27B-FP8 generalist VLM,
MinerU2.5-Pro-2604-1.2B through its official two-step document parser, and
PaddleOCR-VL-1.6 through its published table-recognition task. For MinerU and
PaddleOCR-VL, the common decoder reads only explicitly labelled top/bottom HTML
table cells. These document-specialist interfaces are reported separately from
the common-prompt generalist comparison because their published task prompts
are part of the models' intended operating mode. The prior Qwen3-VL-4B result
remains a historical reproducible reference, not an upper bound.

The initial open-model roster is frozen under `paper1_modern_vlm_v002`.
After that protocol began, a user-directed closed-model extension was added as
`paper1_modern_vlm_closed_extension_v003`. It fixes the same inputs, prompt,
decoder, matcher, and budget for `gpt-5.6-sol` and `claude-opus-4-6`, but is a
post-hoc exploratory comparison rather than a confirmatory roster member. The
user-provided GPT slot was tested on a synthetic visual page on 2026-08-17;
the endpoint returned HTTP 502 upstream errors, so it is now explicitly
`NO_GO_SYNTHETIC_VISUAL_PREFLIGHT_UPSTREAM_502_NO_GOLD_REQUEST`. No real page
was sent and no accuracy or risk-layer number is reported. ChatGPT/Codex session
identity and opaque model proxies are not valid experimental backends.

## Protocol History

`paper1_modern_vlm_v001` was a resource-feasibility preflight. It used a
1,024-token completion ceiling and revealed that long, otherwise valid direct
JSON sequences can be cut off before the closing brace. It is retained as a
negative deployment observation and is not a formal accuracy result. Revision
`v002` changes only the common maximum completion budget to 4,096 tokens. The
prompt, models, rendered pages, normalizer, matcher and evaluation cohorts are
unchanged. This post-hoc transport correction is recorded explicitly and uses
no Gold label or model-error-driven logic.

## Metrics

Primary outcomes are interval precision, recall and F1, document-boundary exact
rate and zero-output-document rate. Reliability outcomes are JSON-valid page
rate, critical numeric invalidity rate (invalid emitted depth ranges divided by
all emitted interval objects), raw emitted interval count, and latency per page.
The comparative analysis also records whether a system offers grounded source
evidence, deterministic numeric conversion, constraint violations, calibrated
risk decisions, selective acceptance, and database-ready provenance.

## Interpretation

The baseline tests direct page-to-JSON extraction, not the best possible use of
each foundation model. A VLM win on semantic recall is evidence for a visual
understanding advantage. GeoLogParser can claim an advantage only where the
logged measurements establish it, especially in numerical validity,
traceability, acceptance risk and predictable local deployment cost.

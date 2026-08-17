# ADR-043: Closed VLM visual preflight remains NO-GO

Date: 2026-08-17
Status: Accepted

## Decision

Keep the user-provided closed-model slot registered as an exploratory baseline,
but do not send any real-source page until a synthetic visual request succeeds.
The endpoint returned `gpt-5.6-sol` from `/v1/models`, while the requested label
was `chatgpt5.6-sol-high`; the label is not treated as a model identity. The
Responses visual request returned HTTP 502 `upstream_error` twice. No Gold,
source-agreement, BGS, or other real page was transmitted.

## Rationale

A closed VLM baseline is scientifically useful only when the exact served model,
image transport, response metadata, and page-level outputs are archived. A
transport failure cannot support accuracy, risk-layer, or model-comparison
claims. Treating the failure as a score would break the evidence hierarchy.

## Consequences

- Qwen3.8-27B-FP8 remains the completed modern open VLM baseline.
- Paper II may compare the routed parser with the completed Qwen proposal-
  assurance result and explain complementarity, but must not invent a closed
  model result.
- The closed slot is marked
  `NO_GO_SYNTHETIC_VISUAL_PREFLIGHT_UPSTREAM_502_NO_GOLD_REQUEST`.
- Re-execution is permitted only after a successful synthetic visual preflight,
  using the frozen prompt and California manifest without retuning.

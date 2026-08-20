# ADR-039: Modern VLM Comparative Boundary

Date: 2026-08-17

## Decision

Evaluate current VLMs as direct page-to-interval extractors under one frozen
schema and matcher, but do not present their aggregate F1 as the sole measure
of deployability. The comparison records interval recovery, JSON delivery,
numeric invalidity, latency, raw output volume, source grounding, deterministic
validation, abstention, acceptance risk, and database provenance separately.

Qwen3.8-27B-FP8, Qwen3-VL-4B-Instruct, MinerU2.5-Pro, and PaddleOCR-VL-1.6
form the open-model group. GPT-5.6
Sol and Claude Opus 4.6 are registered as a user-directed, post-hoc exploratory
closed-model extension. They require a direct official credential; neither the
interactive Codex model nor an opaque API proxy may be substituted.

## Rationale

The first completed Qwen run on California v001 demonstrates that a modern
generalist VLM can read the source template extremely well. The project must
therefore not claim generic VLM incapacity. The research question becomes which
properties direct model output still fails to provide: field-level evidence,
deterministic numeric checks, a reasoned acceptance policy, error containment,
and versioned database provenance. Those are testable system properties, not
assumed advantages.

## Consequences

- A direct VLM accuracy win is reported as a real visual-understanding result.
- GeoLogParser may claim an advantage only for measurements it logs, including
  risk, coverage, numerical validity, review routing, provenance, or resource
  cost.
- The closed-model extension remains explicitly exploratory and `NOT RUN`
  without provider-auditable output.
- Cross-source tests use an independently declared source-agreement reference;
  BGS v003 remains excluded from this modern baseline protocol.

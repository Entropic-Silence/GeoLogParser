# ADR-044: Record Codex internal visual as a closed baseline pilot

Date: 2026-08-18
Status: Accepted

## Decision

Record the Codex internal visual component as a closed-source, host-managed
`OpenAI GPT-5.6-Sol` (`gpt-5.6-sol`, reasoning effort `xhigh`) baseline pilot.
Use one pre-registered geology-bearing page from each of the five California
cohorts, freeze the visual interval outputs, and score them against the
published manual-transcription Gold. Report this result in Paper II as a
stratified pilot, not as a full-cohort estimate.

## Result

Five pages and 91 Gold intervals were read. The frozen visual outputs matched
91/91 intervals with precision 1.000, recall 1.000, F1 1.000, and matched
boundary MAE 0.000 m. These are page-level pilot results, not a claim that the
host model reaches F1 1.0 on the California corpus.

## Reproducibility boundary

The host runtime does not expose a checkpoint/API snapshot, revision hash,
weight precision, inference-framework version, provider response IDs, or
sampling defaults. The prompt, image hashes, page manifest identities, output
JSONL, and evaluation code are archived, but the model invocation cannot be
reproduced outside the Codex host. Consequently the pilot is never pooled with
the reproducible Qwen3.8-27B-FP8 cohort benchmark and cannot support a general
closed-model superiority claim.

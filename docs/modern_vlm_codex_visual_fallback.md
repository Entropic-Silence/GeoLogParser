# Codex internal-vision fallback audit

Date: 2026-08-18 (UTC)

## Scope

The user-provided closed visual endpoint remained unavailable for image
generation requests, although its text/model-list interface responded. A small
fallback audit was therefore performed with the local Codex visual inspection
component. This is an exploratory audit only; it is not a formal VLM baseline
because the component does not expose a stable public model ID, checkpoint,
revision hash, precision, inference framework, prompt hash, or provider response
metadata.

## Inputs

| Record | Page image SHA-256 | Evidence tier |
| --- | --- | --- |
| `WCR2013-007608` | `eaaf506bb91c7d1b8b9e7a9201a4691e945e3eced08eb5e1e02b815897ac0886` | published manual-transcription Gold |
| `WCR2004-001217` | `629303e6a7933dd2dda109eb00fb7d45b4dd953f768efb643017bf616a20622b` | published manual-transcription Gold |

The first page contains seven visible geological-log intervals and was read
exactly. The second page contains a visible `0–450` well-deepening row in the
form, but the authoritative Gold interval sequence begins at 450 ft; the
fallback therefore omitted the non-lithology row. This is a semantic ownership
decision, not evidence that vision alone resolves every table row.

## Result

Using the frozen 0.05 m boundary matcher, the two-document exploratory output
matched 12/12 Gold intervals: precision 1.000, recall 1.000, F1 1.000, and
matched-boundary MAE 0.000 m. The sample is intentionally too small for a
benchmark claim and was not added to Paper I/II metrics or used to tune any
parser, prompt, threshold, or risk policy.

## Interpretation

Codex visual inspection can provide a useful emergency qualitative reader, but
it is not scientifically equivalent to the closed endpoint or the completed
Qwen3.8-27B-FP8 baseline. It lacks reproducible model identity and structured
bbox/provider traces. The formal comparison therefore remains Qwen direct VLM
versus GeoLogParser risk assurance; this fallback is retained only as an
explicitly labelled exploratory audit.

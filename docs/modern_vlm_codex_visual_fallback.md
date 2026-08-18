# Codex internal-vision fallback audit

Date: 2026-08-18 (UTC)

## Scope

The user-provided closed visual endpoint remained unavailable for image
generation requests, although its text/model-list interface responded. A small
fallback audit was therefore performed with the local Codex visual inspection
component. This two-page audit remains exploratory. A separate five-page
stratified Gold pilot was subsequently registered as
`P2_CODEX_INTERNAL_VISUAL_CALIFORNIA_STRATIFIED_PILOT_001` and is reported in
Paper II. That pilot is a formal closed-baseline pilot, but not a full-cohort
benchmark: the host component does not expose a checkpoint, revision hash,
precision, inference-framework version, or provider response metadata.

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
parser, prompt, threshold, or risk policy. The later five-page pilot is archived
at `experiments/paper2/analysis/codex_internal_visual_baseline_v001.json` with
frozen predictions in the adjacent JSONL file.

## Interpretation

Codex visual inspection can provide a useful emergency qualitative reader, but
it is not scientifically equivalent to the closed endpoint or the completed
Qwen3.8-27B-FP8 baseline. It lacks reproducible model identity and structured
bbox/provider traces. The reproducible full-cohort comparison therefore
remains Qwen direct VLM versus GeoLogParser risk assurance. The five-page Codex
pilot is retained as a separately labelled closed baseline because it
demonstrates page-level visual recovery without supporting a general transport
or reproducibility claim.

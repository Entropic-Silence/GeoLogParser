# ADR-003: First local VLM baseline

- Status: accepted for engineering audit
- Date: 2026-08-12

## Context

The first B4/B5 implementation needs Chinese OCR, document/layout perception,
structured output, local deployment, a fixed revision, and a licence compatible
with reproducible research software. The available GPUs are one RTX 5090 32 GB
and four modified RTX 2080 Ti 22 GB cards; every card normally runs one named
mining container.

## Decision

Use `Qwen/Qwen3-VL-4B-Instruct` at immutable Hugging Face revision
`ebb281ec70b05090aa6165b016eac8ec08e71b17` through the local Transformers
adapter. The model repository declares Apache-2.0 and is not gated. Weights and
cache belong under `/data/GeoLogParser`; the already isolated runtime at
`/root/venvs/ai` is captured by `requirements-vlm.txt`.

Prompts are versioned separately for B4 zero-shot and B5 few-shot. Generation
is greedy. Raw response, parse status, schema-normalized record, constraints,
latency, and peak allocated VRAM are saved for every image. Whole-image VLM
fields receive `VLM_UNGROUNDED` and `needs_review`, because the baseline does not
claim source bboxes.

## Alternatives and consequences

`Qwen2.5-VL-3B-Instruct` was screened but not selected: its fixed repository
revision carries the Qwen Research License with non-commercial restrictions.
The 4B Qwen3 model is somewhat larger but remains suitable for the 32 GB card.
Selection is not a performance conclusion; B4/B5 accuracy is `TBD` until a
human-validated, rights-cleared test set exists.

Mining is paused only through the card-specific Docker container and restored
with `docker start`; direct process termination is prohibited by this workflow.

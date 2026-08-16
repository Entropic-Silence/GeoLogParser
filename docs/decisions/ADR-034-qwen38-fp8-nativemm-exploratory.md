# ADR-034: Qwen3.8-27B FP8 NativeMM exploratory branch

Date: 2026-08-16  
Status: Accepted exploratory / `NO_GO_PRIMARY` at current feasibility gate

## Context

Paper II needs a structural reasoning branch that predicts visual regions,
column roles, structural events, semantic owners and depth-scale evidence
before deterministic geometry reconstruction. The local Qwen3.8-27B-FP8
checkpoint is available and is already served for inference. BGS v003 is a
frozen external set and is not opened by this branch.

## Evidence

- The FP8 checkpoint produced a valid intermediate structural graph on 3/4
  BGS v001 development pages in the first four-page audit; after tightening
  the coordinate-space contract, the second four-page audit was schema-valid
  on 3/3 parseable outputs (one output remained non-JSON).
- A three-page BGS v001 development structural audit produced schema-valid
  graphs on 3/3 pages. The deterministic graph-to-depth decoder selected
  structural events and reconstructed boundary depths, but micro Boundary F1
  at ±0.05 m was `0.0526` (1 TP, 7 FP, 29 FN).
- The current routed v028 development reference is Boundary F1 `0.3475`,
  Interval F1 `0.1978`, and Boundary CNER `0.3281`. The exploratory Qwen
  branch therefore does not meet the promotion gate.
- The official visual tensors load exactly when the `model.visual.` prefix is
  stripped into `Qwen3_5VisionModel`; 333 visual tensors had zero missing or
  unexpected keys.
- PEFT LoRA targets (`qkv`, `proj`, `linear_fc1`, `linear_fc2`) were attached
  to the visual module. One synthetic forward/backward pass on RTX 5090 had
  finite loss `0.4867213`, 111 non-zero gradient tensors, and peak allocated
  memory `0.9043 GiB`.

## Decision

Keep Qwen3.8-27B-FP8 as an inference baseline/teacher and structural-audit
branch. Do not expand training or promote it to the Paper II primary method.
The visual-submodule smoke test does not establish full FP8 language-stack
training or multimodal SFT. The local environment has no importable ms-swift,
Unsloth, bitsandbytes, or local BF16 Qwen3.8 checkpoint; full multimodal SFT is
therefore `NOT_COMPLETED`.

## Follow-up

Retain the structural graph schema and deterministic decoder for future
training with an explicitly supported BF16/Megatron runtime. Any future model
must exceed v028 on an independent development source before a frozen external
run is considered. BGS v003 remains unopened.

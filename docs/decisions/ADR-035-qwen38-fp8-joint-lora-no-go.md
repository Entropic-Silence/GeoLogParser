# ADR-035: Qwen3.8 FP8 joint-LoRA staged feasibility gate

Date: 2026-08-16  
Status: Accepted — `NO_GO_PRIMARY`

## Context

The exploratory Qwen3.8-27B-FP8 branch was extended to test a controlled
low-bit multimodal training route with a frozen FP8 backbone and BF16 residual
adapters. The intended stages were visual encoder LoRA, visual encoder plus
multimodal projector, and those modules plus a small selective language LoRA.
The target was a compact intermediate structural graph rather than Image→JSON.

## Evidence

1. On a single RTX 5090 with CPU offload, the complete multimodal backward
   path reached 29.776 GiB allocated and failed with CUDA OOM in the first
   visual-LoRA stage. Offloaded frozen layers still have to be retained or
   recomputed for the gradient path.
2. A five-GPU device map loaded the checkpoint, but the first forward failed
   in Triton because `fp8e4nv` is unsupported on the RTX 2080 Ti SM75 devices.
3. Forcing Transformers to dequantize the local FP8 checkpoint to BF16 in host
   RAM avoided the FP8 kernel issue without downloading BF16 weights, but the
   first complete CPU language forward/backward remained CPU-bound for more
   than 33 minutes. It was terminated before any gradient metric was claimed.
4. The visual-only BF16 LoRA path remains verified in ADR-034; that result does
   not establish a complete multimodal gradient chain.

## Decision

Do not expand Qwen3.8 joint LoRA training, do not start NVFP4/4-bit training,
and do not promote this branch to the Paper II main method. The current
hardware/runtime does not provide a stable, reproducible complete FP8
multimodal training route. Retain the checkpoint for inference, structural
auditing and possible future teacher use.

## Consequences

- No BGS v003 data was opened or consumed.
- No Boundary/Interval/CNER/FCR claim is produced from this branch because no
  staged gradient chain completed.
- Paper II returns to the validated routed structural parser and its existing
  source-disjoint development evidence.
- A future revisit requires a supported Blackwell-only FP8 training stack or a
  distributed training environment with compatible FP8 kernels on every rank;
  it must pass the same staged gradient gate before any real-data SFT.

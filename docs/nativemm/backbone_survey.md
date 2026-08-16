# PaperII-NativeMM Backbone Survey

Date: 2026-08-15

## Decision-relevant requirements

The first training stage needs a compact local Document-VLM with Chinese and
English document support, high-resolution inputs, an available parameter-efficient
training route, and a license compatible with reproducible research and a later
deployable implementation. The model is supervised for visual structure; final
critical depths are decoded by deterministic geometry and constraints.

## PaddleOCR-VL-1.6

- Official model: `PaddlePaddle/PaddleOCR-VL-1.6`
- Verified revision: `c5630abae1d940eafe0697512a0325494b02ab42`
- License: Apache-2.0, verified from the official model card and bundled license.
- Scale: 0.9B; the official BF16 safetensors file is 1,917,255,968 bytes.
- Language/domain: official card declares Chinese, English, multilingual document
  parsing, layout, table, formula, chart, seal, and text spotting support.
- Visual budget: official processor defaults to 1,003,520 pixels; model text
  configuration exposes 131,072 maximum positions, although usable training
  length is bounded more conservatively in this project.
- Training route: ms-swift v4.5.0 registers the model and ships an official LoRA
  SFT example using BF16, frozen vision/alignment modules, and `all-linear`
  adapters. The project starts with narrower language q/v adapters for the smoke
  audit before testing broader adapters.
- Risk: the official Transformers example is element-level; page-level parsing
  is officially recommended through the PaddleOCR pipeline. NativeMM therefore
  requires direct long-page and task-format verification.

Official evidence:

- https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.6
- https://github.com/PaddlePaddle/PaddleOCR
- https://github.com/modelscope/ms-swift/tree/v4.5.0/examples/models/paddle_ocr

## MinerU2.5-Pro-2604-1.2B

- Official model: `opendatalab/MinerU2.5-Pro-2604-1.2B`
- Verified revision: `d3f5e08d073c21466bbabe21c71bb1e9c2e595da`
- License: Apache-2.0 on the official model card. This is materially preferable
  to the older `MinerU2.5-2509-1.2B` checkpoint, whose official card is AGPL-3.0.
- Scale: 1.2B; BF16 safetensors file is 2,312,126,640 bytes.
- Architecture: Qwen2-VL-compatible, 32,768 top-level visual/text positions and
  official two-stage coarse-to-fine document parsing utilities.
- Visual budget: official processor allows up to 1,605,632 pixels.
- Training route: ms-swift v4.5.0 registers the Pro checkpoint under Qwen2-VL,
  supporting LoRA through the established Qwen2-VL training path.
- Risk: the released model is optimized for document-to-markdown/content-list
  parsing rather than domain-specific boundary grounding. It is retained as an
  architectural comparison and fallback backbone.

Official evidence:

- https://huggingface.co/opendatalab/MinerU2.5-Pro-2604-1.2B
- https://github.com/opendatalab/MinerU
- https://github.com/modelscope/ms-swift/tree/v4.5.0

## DocOwl2

- Official model: `mPLUG/DocOwl2`, Apache-2.0.
- Strength: explicit high-resolution compressor; each page is represented by
  324 visual tokens and the official example accepts multiple pages.
- Cost: released safetensors are 17,127,218,408 bytes and the decoder is a
  7B-class Llama configuration. ms-swift lists inference support but no Megatron
  support and provides no current dedicated training recipe.
- Decision: architecture reference only in the first stage. It does not justify
  the substantially higher memory and adaptation risk before the compact models
  pass the development go/no-go gate.

Official evidence:

- https://huggingface.co/mPLUG/DocOwl2
- https://github.com/X-PLUG/mPLUG-DocOwl

## Selected order

1. PaddleOCR-VL-1.6: primary compact backbone.
2. MinerU2.5-Pro-2604-1.2B: independent Qwen2-VL-compatible comparison.
3. DocOwl2: no first-stage training.

No external frozen GeoLogParser test source was used in this survey or in the
training corpus construction.

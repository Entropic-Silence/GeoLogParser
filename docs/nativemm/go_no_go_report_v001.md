# PaperII-NativeMM go/no-go report v001

Date: 2026-08-16

## Decision

`NO-GO` for scaling the current PaddleOCR-VL-1.6 NativeMM route. BGS v002 and
California v004/v005 remain unopened. The v018 modular layout/semantic-role
pipeline remains the strongest BGS development method.

This decision applies to the tested recipe: generative LoRA, frozen-backbone
dense row classification, and frozen-backbone column-aware spatial heads. It
does not rule out native multimodal structure learning after substantially more
independent real spatial supervision becomes available.

## Source-disjoint evidence

| Route | Boundary F1 @ 0.05 m | Boundary recall | Interval F1 @ 0.05 m | CNER | Structural evidence coverage |
|---|---:|---:|---:|---:|---:|
| Current v018 modular pipeline | 0.3103 | 0.2262 | 0.1116 | 0.5060 | 0.2262 |
| Generative NativeMM real-SFT, California development | 0.0015 | 0.0008 | 0.0000 | 0.8750 | 0.0000 |
| Dense row head | 0.0667 | 0.0500 | 0.0000 | 0.9000 | 0.0500 |
| Spatial pixel-only | 0.0789 | 0.0750 | 0.0312 | 0.9167 | 0.0750 |
| Spatial visual-only | 0.0488 | 0.0250 | 0.0000 | 0.0000 | 0.0250 |
| Spatial fused | 0.0364 | 0.0250 | 0.0000 | 0.9333 | 0.0250 |

The dense/spatial heads were evaluated on six BGS v001 source-group-disjoint
pages containing 40 scale-projectable reference boundaries. Their denominator
is therefore smaller than the full 367-boundary v018 benchmark. The comparison
is directional rather than a claim of identical test support; every NativeMM
variant nevertheless missed its predeclared absolute gate by a wide margin.

## Failure attribution

1. The first BGS spatial corpus incorrectly used the bounding boxes of printed
   depth numbers as graphical boundary targets. Correcting this label definition
   improved supervision validity but did not recover cross-source performance.
2. Generative SFT improved JSON validity but not structure recovery. On BGS
   bundle development, JSON validity rose from 0 to 0.2857 while direct
   structural evidence coverage remained 0.
3. Frozen document-VLM row embeddings did not transfer boundary semantics.
   Pixel-only exceeded fused and visual-only on boundary F1, showing that the
   added pretrained visual representation was not useful under the available
   real supervision.
4. Calibration-fold precision did not transfer. Fused and visual-only heads
   found high-precision, very-low-coverage operating points on three calibration
   pages, but their recall fell to 0.025 on unseen source groups.
5. Official database intervals can encode recovery or interpretation changes
   expressed in narrow columns rather than full-width horizontal rules. A page
   label at y alone is insufficient to teach which local column event supports
   each boundary across heterogeneous templates.

## Gate audit

| Gate | Required | Observed best NativeMM | Result |
|---|---:|---:|---|
| Interval F1 @ 0.05 m | >= 0.15 | 0.0312 | fail |
| Boundary precision @ 0.10 m | >= 0.70 | NOT RUN as release metric | fail / not eligible |
| Boundary recall @ 0.10 m | >= 0.20 | NOT RUN as release metric | fail / not eligible |
| Selective precision | >= 0.90 | calibration-only points did not transfer | fail |
| CNER | <= 0.10 | 0.9000--0.9333 for nontrivial-coverage heads | fail |
| External frozen evaluation | one-time after all gates | not executed | preserved |

## Consequence

No additional epochs, model size, hard-case mining from frozen sources, or BGS
v002 evaluation are authorized for this branch. Further method work must first
increase independent real column/event supervision and explicitly associate
each boundary with its supporting field region. The negative result is retained
for Paper I failure attribution and for Paper II architecture selection; it is
not promoted as the proposed method.

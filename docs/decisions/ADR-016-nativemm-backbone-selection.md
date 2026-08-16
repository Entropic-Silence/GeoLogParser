# ADR-016: Native Multimodal Backbone and Development Gate

Date: 2026-08-15

Status: `CLOSED_NO_GO` on 2026-08-16. See
`docs/nativemm/go_no_go_report_v001.md`.

## Context

The strongest BGS v018 development pipeline reaches boundary precision/recall/F1
of 0.4940/0.2262/0.3103 at +/-0.05 m and interval F1 0.1116. Its selective point
is reliable (precision 0.9302, coverage 0.1172), but the visual candidate recall
ceiling prevents sequence recovery. Additional correlated OCR evidence and
depth-alignment features failed to improve this result.

## Decision

Create an independent `PaperII-NativeMM` route. Use PaddleOCR-VL-1.6 as the
primary compact backbone and MinerU2.5-Pro-2604-1.2B as the independent
Qwen2-VL-compatible comparison. Both official checkpoints are Apache-2.0 and
have current local LoRA routes. DocOwl2 remains an architecture reference.

Training proceeds in four versioned stages:

1. synthetic structural pretraining;
2. real Gold sequence and derived-spatial SFT;
3. hard-case fine-tuning mined only from declared development sources;
4. geological constraint alignment and selective acceptance.

The model predicts column roles, graphical boundary locations, visible scale
anchors, field semantics, and sequence topology. Final depth values are produced
by a deterministic geometry decoder and then validated. A generated depth with
no visual/scale support is never a final critical value.

The first language-only adapter was retained as a baseline.  The NativeMM v002
route adds LoRA to the two visual-to-language projector matrices while keeping
the vision tower frozen.  This is the smallest trainable change that can alter
structural visual evidence without turning the experiment into full vision
fine-tuning.  A single-sample v002 overfit check produced valid JSON and exact
boundary recovery; this is a trainability diagnostic, not a quality claim.

The forbidden development sources are BGS v002 and California v004/v005. The
corpus builder rejects those identifiers at runtime.

## Predeclared go/no-go gate

Before any one-time BGS v002 evaluation, a source-disjoint development run must:

1. raise structural evidence coverage above the v018 29.97% candidate-union
   ceiling with directly grounded correct evidence;
2. achieve interval F1 >= 0.15 at +/-0.05 m;
3. achieve boundary precision >= 0.70 and recall >= 0.20 at +/-0.10 m;
4. expose a selective operating point with precision >= 0.90, CNER <= 0.10,
   and reference-relative coverage >= 0.10;
5. retain page/bbox provenance for every accepted boundary;
6. serialize model, geometry, calibration, prompt, and threshold revisions
   before external execution.

If the NativeMM route does not materially improve structural coverage and
interval F1 on independent development sources, training scale will not be
expanded. The negative result will be retained as method evidence.

## Outcome

The predeclared gate was not met. Generative real-Gold SFT produced interval F1
0 and sequence-boundary F1 0.0015 on California source-disjoint development.
Corrected dense spatial supervision and three column-aware ablations also
failed: the best interval F1 was 0.0312 and the best boundary F1 was 0.0789 on
six BGS source-group-disjoint pages. BGS v002 was not opened. The current
NativeMM route is closed rather than scaled.

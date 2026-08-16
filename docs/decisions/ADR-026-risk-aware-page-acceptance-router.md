# ADR-026: Learned risk-aware acceptance for routed structural extraction

Date: 2026-08-16  
Status: `ACCEPT_VALIDATION_ONLY`

## Decision

Add a document-level probabilistic risk router after the existing Swissgeol
RapidOCR interval expert. The router uses only page/OCR/sequence evidence:
page-family support, OCR confidence and density, sequence monotonicity and
contiguity, zero-origin evidence, boundary OCR support, predicted sequence
length, and German structural headers. It is trained on development-document
exactness labels with five-fold out-of-fold probabilities. The acceptance
threshold is selected on development OOF predictions to require at least 95%
accepted-document exactness, then frozen before held-out scoring.

## Results

On Swissgeol Thurgau development (37 documents), the fixed threshold was
`0.7581`, accepting 16/37 documents (`43.24%`) with document exactness
`1.0000`. On the content-group-held-out split (35 documents), it accepted
15/35 (`42.86%`) with exactness `1.0000`.

Held-out routed interval metrics were precision `1.0000`, recall `0.4375`, and
F1 `0.6087`, compared with the unchanged baseline precision/recall/F1
`0.5714/0.6000/0.5854`. Routed boundary precision was `1.0000`, recall
`0.4348`, F1 `0.6061`, and critical numerical error rate `0.0000`.

## Limitations

The held-out Swissgeol split had already been consumed by the multilingual
alias coverage audit, so this is validation evidence rather than untouched
external confirmation. The router changes acceptance, not extraction recall;
it cannot recover intervals omitted by the baseline. The accepted denominator
is 15 documents, and calibration remains imperfect (held-out Brier `0.0555`,
ECE `0.1481`).

The router is not yet promoted to the BGS primary method. BGS v003 remains
frozen and unopened. Promotion requires an independent, pre-registered source
where the same fixed router improves selective precision/coverage without
increasing critical numerical error.


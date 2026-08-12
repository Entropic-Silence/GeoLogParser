# ADR-002: Optional document backend adapters

- Status: accepted
- Date: 2026-08-12

## Decision

Keep domain logic free of model-runtime dependencies. Direct PDF extraction and
OCR engines implement small adapter protocols and return common text-region
objects. Backend/model names and revisions belong in configuration and run
metadata, not in pipeline conditionals.

## Consequences

Schema, constraints, and evaluation run on CPU with no AI stack. PaddleOCR,
Tesseract, local VLMs, or API models can be compared without rewriting the
extractor. Backend absence produces an explicit error, never a fabricated
empty success.


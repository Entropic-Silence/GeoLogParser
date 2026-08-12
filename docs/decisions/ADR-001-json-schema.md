# ADR-001: Field-level provenance envelopes

- Status: accepted
- Date: 2026-08-12

## Decision

Represent extractable scalar fields as an envelope containing `value` and its
provenance/validation metadata. Keep raw and normalized geological terms in
separate fields. Preserve source numeric text and raw units even when the
internal value is SI.

## Consequences

Values remain traceable and can be calibrated or reviewed independently. The
JSON is more verbose, but downstream flat exports can project `value` while
retaining a separate provenance table.


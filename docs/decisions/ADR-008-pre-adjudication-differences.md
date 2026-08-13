# ADR-008: Freeze field differences before adjudication

- Status: accepted
- Date: 2026-08-13

## Context

Aggregate exact match and boundary MAE cannot tell an adjudicator which page,
interval, or field differs. If reviewer files remain mutable after metrics are
computed, the adjudication evidence can also drift away from the reported
agreement. Automatically selecting one review track would erase disagreement
and make the final GT provenance misleading.

## Decision

Pre-adjudication agreement includes a deterministic list of every v001
borehole/interval value disagreement, interval count/ID mismatch, and both
record hashes. The agreement artifact freezes each source annotation file hash.

An adjudication-pack builder accepts only that agreement schema, verifies both
roots and all file hashes, and copies the two records plus their discrepancy
list into an immutable case directory. It creates no final record. Cases with
differences are `adjudication_pending`; equal records remain
`confirmation_pending` because agreement does not prove source correctness.

## Consequences

Agreement results remain auditable after reconciliation begins, and no review
track wins automatically. A separate human adjudicator must inspect the source,
resolve or confirm each case, and generate a final record with ordinary
record-bound attestations. Adjudicator identity, qualifications, resolution
reasons, and time remain real study data and cannot be synthesized by this
builder.

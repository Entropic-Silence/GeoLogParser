# ADR-006: Record-bound verification attestations

- Status: accepted
- Date: 2026-08-13

## Context

An annotation status string alone cannot establish independent double review or
expert verification. A reviewer could select `double_verified` after one pass,
or select `expert_verified` without an authorized expert identity. Revision
history proves that edits occurred, but does not prove which exact final record
each reviewer approved.

## Decision

Every human verification save appends an attestation containing an anonymized
annotator ID, reviewer/expert role, revision, timestamp, and SHA256 of the exact
canonical record JSON. Only attestations whose hash matches the current record
are effective.

`double_verified` requires effective attestations from at least two distinct
annotator IDs. If either reviewer changes the record, prior attestations for the
old hash no longer count. `expert_verified` requires an effective expert-role
attestation, and the server grants that role only to IDs in
`GEOLOGPARSER_EXPERT_ANNOTATOR_IDS`. The default allowlist is empty.

Agreement calculations additionally reject two collections whose annotator ID
sets overlap. This validates identity separation, not professional credentials
or organizational independence; those study controls remain protocol metadata.

## Consequences

GT exports can trace who approved the exact final bytes and cannot infer double
or expert review from a dropdown value. Legacy auto proposals without the new
optional attestation list remain readable. Existing human-status records made
before this decision fail the strengthened GT gate until they are re-attested;
they are not silently grandfathered as Ground Truth.

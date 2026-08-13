# ADR-007: Blinded duplicate-annotation tracks

- Status: accepted
- Date: 2026-08-13

## Context

Double-review status on a shared evolving record does not measure independent
annotation agreement: a second reviewer can see and anchor on the first answer.
Paper I needs a defensible pre-adjudication agreement sample, while final GT
needs a separate reconciliation and attestation process.

## Decision

Create immutable full-overlap task assignments from one frozen `auto` proposal
collection before review begins. Each track receives byte-identical seed JSON
in a separate annotation directory, a distinct anonymized reviewer ID, and a
service process whose actor ID is fixed server-side and whose write allowlist
contains only that ID. Source annotation,
record, and rendered-panel hashes are frozen in an assignment manifest.

The comparison command runs only after every item in both tracks independently
passes the single-review GT gate. It rejects overlapping annotator IDs, freezes
all input file hashes, writes once, and labels the result pre-adjudication rather
than final GT. Adjudication occurs only after this output is frozen.

## Consequences

Agreement is not inflated by direct answer sharing through the application.
Track services do not expose peer results, and browser payloads cannot select a
peer actor. The fixed actor identifies a track service, not the human at the
keyboard; human authentication remains a deployment/study control.
However, separate directories on the same Unix account are not a security
boundary. Review protocol or OS permissions must prevent direct filesystem
inspection. Anonymous assignment IDs do not prove that a real human was
assigned; human assignment, qualifications, consent, and independence remain
study records and cannot be inferred from generated files.

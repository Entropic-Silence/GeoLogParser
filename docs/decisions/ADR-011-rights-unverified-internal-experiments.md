# ADR-011: Permit rights-unverified sources for internal experiments

- Status: Accepted
- Date: 2026-08-13

## Context

The project has useful borehole pages and structured records whose repository
access is available but whose exact item licence, embedded third-party rights,
privacy, or sensitive-location status has not yet been checked by a person.
Making that check a prerequisite for every internal parser and constraint
experiment would unnecessarily stop method development. Conversely, treating
an automated access observation as publication clearance would create a legal
and scientific provenance failure.

## Decision

Rights verification is a **pre-submission and pre-redistribution gate**, not an
experiment-execution gate. A source may be downloaded and processed for
internal or provisional experiments when:

- the acquisition path is recorded;
- the source URL/DOI, claimed licence or terms, retrieval date, local path, and
  SHA256 are frozen in `datasets/source_verification_ledger.yaml`;
- unresolved terms, privacy, sensitive locations, or embedded content are
  explicitly marked; and
- outputs are kept local and are not represented as rights-cleared releases.

Sources with contradictory access metadata (for example `embargoedAccess` plus
an open-licence claim) remain quarantined and are never silently upgraded.
Synthetic data may be used for controlled experiments, but its generated
labels are known programmatic labels, not human or expert Ground Truth.

The final manuscript and release gate must use the separate ledger to verify
each source. Until then, results are internal/provisional and any benchmark
claim must state the reference tier accurately. Machine outputs remain
`Silver`, `pseudo-label`, or `machine-adjudicated`; the project must not call
them human/expert labels to improve apparent publication readiness.

## Consequences

- OCR, VLM, layout, constraint, Silver-adjudication, and downstream protocol
  work can continue while source rights are being checked.
- Every source used by an experiment has a traceable local inventory and a
  human-check queue in a separate document.
- Publication, data release, and redistribution remain blocked for records
  whose item-level rights or privacy decision is unresolved.
- A later rights decision does not retroactively change an experiment's
  provenance; reruns must create a new dataset/experiment version.

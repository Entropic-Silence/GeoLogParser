# ADR-021: Demote consumed BGS v002 to validation for the next method cycle

Date: 2026-08-16

Status: `ACCEPT`.

## Context

The frozen v023 evaluation on BGS v002 failed and is permanently reported as
the external result for that method. Continuing method development without
using the only observed unseen-source failure would preserve nominal blinding
but prevent diagnosis of the transport failure. ADR-020 froze BGS v003 before
any such diagnosis.

## Decision

For methods after v023, BGS v002 is validation and failure-attribution data.
Its v023 result remains an external no-go for v023, but no revised method may
describe performance on v002 as external confirmation. BGS v003 is the sole
remaining BGS external freeze and must remain unopened until a replacement
method and thresholds are committed.

## Consequences

- v001 and v002 may support layout/error diagnosis and development after this
  ADR; all such experiments must label v002 as validation.
- v003 record, page images, intervals, and errors are forbidden for method,
  prompt, threshold, or feature development.
- Because v003 has only one source and seven intervals, a future positive
  result is limited confirmation and must be supplemented by another domain.

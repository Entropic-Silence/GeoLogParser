# ADR-027: BGS safe-sequence risk gate is a no-go for deployment promotion

Date: 2026-08-16  
Status: `NO_GO`

## Decision

Evaluate a nested source-disjoint document risk gate over the fixed v028 routed
BGS predictions. The gate labels a document safe only when every emitted
boundary is supported by an authoritative reference boundary within 0.05 m;
incomplete recall is allowed, but unsupported emitted boundaries are unsafe.
The gate is fitted and thresholded without using the target fold labels.

## Results

On the 26-document BGS v001 development panel, the gate selected threshold
`0.968716` and accepted 1/26 documents (`3.85%` coverage). Accepted document
safety was `1.0000`, but selective boundary F1 was `0.0054` and selective
interval F1 was `0.0000`; the accepted document contributed one supported
boundary and omitted the remaining reference boundaries. The unfiltered v028
predictions remain boundary F1 `0.3475` and interval F1 `0.1978`.

## Interpretation

The safe-sequence label is useful as a diagnostic for unsupported emissions,
but it is too conservative and does not recover the structural recall ceiling.
It therefore cannot promote the BGS routed mixture to an industrial selective
operating point. This result is a genuine no-go, not a threshold-tuning
invitation: the gate changes acceptance only and cannot recover omitted
boundaries.

## Scope and limitations

This is nested development evidence over previously generated v024/v025/v028
artifacts. BGS v003 remains frozen and unopened. The result must not be called
untouched external confirmation. The Swissgeol router remains validation-only
because its held-out split was already consumed by the multilingual audit.


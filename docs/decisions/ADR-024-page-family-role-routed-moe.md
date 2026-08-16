# ADR-024: Page-family and semantic-role routed structural mixture

Date: 2026-08-16  
Status: `ACCEPT_DEVELOPMENT_ONLY`

## Decision

Integrate the conservative v024 page-family/risk route with the v025 semantic
column-role reader as a routed structural parser. The parser keeps separate
experts for:

1. explicit depth-range tables (`explicit_range_expert`);
2. scaled composite or graphical-contact pages with sufficient semantic-role
   evidence (`semantic_role_expert`); and
3. the conservative v024 route (`v024_baseline_expert`).

Unsupported or structurally unsafe pages abstain. The routing decision uses
reference-blind page evidence. For v028, the family-to-expert choice is fitted
inside each source-disjoint fold using only the other folds' interval F1; the
target fold is not used to choose its expert.

## Evidence

On the 26-document/34-page BGS v001 development manifest (manifest SHA256
`d85f6c862b81d80c793887f73ca8b70658d42de358f25230dc4a15104520c99c`), the
fixed v027 route reached boundary F1 `0.3327` and interval F1 `0.1806`, compared
with v024 boundary/interval F1 `0.3313/0.1801`. The nested v028 route reached
overall boundary F1 `0.3475` and interval F1 `0.1978`.

The five-fold source-disjoint nested summary gives:

| Method | Boundary F1 mean | Boundary F1 population SD | Interval F1 mean | Interval F1 population SD |
|---|---:|---:|---:|---:|
| v024 baseline | 0.3182 | not re-estimated in this artifact | 0.1688 | not re-estimated in this artifact |
| semantic-role only | 0.3103 | not re-estimated in this artifact | 0.1276 | not re-estimated in this artifact |
| nested routed v028 | 0.3333 | 0.1323 | 0.1841 | 0.1294 |

The routed mean gain over v024 is approximately `+0.0150` boundary F1 and
`+0.0153` interval F1. Fold-level routed interval F1 was `0.0943, 0.0000,
0.2174, 0.2278, 0.3810` across the five folds, showing substantial source
heterogeneity. The semantic-role-only branch is therefore retained as an
expert, not promoted as a standalone method.

## Scope and limitations

These are nested source-disjoint development results, not untouched external
confirmation. The underlying v024/v025 candidate artifacts were produced on
the BGS v001 development corpus before this routing evaluation. BGS v002 and
v002r2 are consumed validation artifacts and cannot be used as external
confirmation for this route. BGS v003 remains frozen and unopened; no v003
score may influence routing, thresholds, prompts, or error-driven development.

The current route is a deterministic family-level mixture rather than a
learned probabilistic gate. It also inherits the structural-recall ceiling of
the underlying experts. Promotion to the Paper II primary method requires a
new independent development source or a formally frozen external evaluation,
with family-level coverage, selective risk, critical numerical error, and
resource cost reported separately.

## Consequence

Paper II will describe routed v028 as an integrated development branch and
report its fold variance and evidence limitations. It will not claim that the
small overall gain establishes cross-source generalization. Future work may
replace the fixed gate with a learned risk-aware router, but no additional
complexity is justified until an independent source shows a reproducible
benefit.


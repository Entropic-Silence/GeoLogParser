# ADR-023: Semantic column-role grounding for composite BGS logs

Date: 2026-08-16

Status: Accepted for diagnostic branch; not promoted as the Paper II primary method

## Context

The v023/v024 development parser used texture-bearing vertical intervals as
graphic evidence. On long composite logs this conflated Stratigraphy, Depth
Drilled, Graphic Log, Core, and auxiliary electrical-log columns. The corrected
BGS v002r2 page `BGS_OFFSHORE_1983444_page-2` is a representative failure: the
candidate generator produced 2,021 candidates, although the page exposes a
single semantically labelled Graphic Log column.

## Decision

Add a reference-blind OCR-header role layer. It detects composite header words,
groups split words such as `Graphic` + `Log`, assigns roles to detected
vertical-rule intervals by x proximity and confidence, and generates graphical
transitions only from a `graphic_log` (or narrowly supported `core`) role. If a
page has no recoverable Graphic Log header, the route may use the legacy
multi-column generator as an explicitly marked low-semantic-evidence fallback;
if a Graphic Log header exists but cannot be geometrically matched, the route
abstains.

The route is exposed separately as `graphic_mode=role_multi`, preserving the
reproducibility of earlier `single` and `multi` modes.

## Development evidence

Using the source-disjoint BGS v001 development panel only:

| Route | Boundary F1 @ ±0.05 m | Interval F1 | Notes |
|---|---:|---:|---|
| v021 multi-column sequence | 0.2944 | 0.1213 | prior reference-blind route |
| v025 role-gated, no fallback | 0.3265 | 0.1458 | 10/34 pages had an explicit Graphic Log anchor |
| v026 role-gated + no-anchor fallback | 0.3094 | 0.1179 | fallback restored coverage but diluted precision |

On the subset of pages with a recoverable Graphic Log role, v025 achieved
boundary F1 `0.4410` and interval F1 `0.2825`. These subset numbers are
diagnostic, not a claim of source-disjoint generalization by themselves.

## Consequence

Semantic column grounding is retained as a page-family evidence module and a
failure-analysis result. It does not satisfy the pre-declared Paper II primary
promotion gate because it does not exceed the v024 development interval F1
(`0.1801`) or boundary F1 (`0.3313`) on the full development panel. BGS v003
remains frozen and unopened. No v002/v002r2 evidence was used for tuning.

Artifacts:

- `experiments/paper2/analysis/bgs_layout_method_development_v025_role_multi.json`
- `experiments/paper2/analysis/bgs_layout_method_development_v026_role_fallback.json`
- `experiments/paper2/models/bgs_layout_field_aware_moe_v025_role_multi.json`
- `experiments/paper2/models/bgs_layout_field_aware_moe_v026_role_fallback.json`

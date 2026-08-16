# ADR-025: Multilingual page-family coverage before expert expansion

Date: 2026-08-16  
Status: `ACCEPT_SELECTIVE_COVERAGE_ONLY`

## Context

The v028 routed parser improved nested BGS v001 development means but reused
BGS-specific English page-family and column-role semantics. An untouched
application to the independent Swissgeol Thurgau development source classified
all 38 pages as unsupported, so no cross-language expert gain could be tested.

## Decision

Add a minimal set of reference-blind German structural aliases to the family
detector: `Tiefe`, `bis`, `Beschreibung des Bohrguts`, and
`Schichtenverzeichnis`. Do not change BGS expert weights, numerical thresholds,
candidate generation, or the BGS v003 freeze. Recognized Swiss pages route to
the existing conservative baseline expert; other pages abstain.

## Evidence

Before the aliases, routed page-family support was `0/38` on 37 Swissgeol
development documents. After the aliases, support was `8/38` pages. The
accepted subset had interval precision `1.0000`, recall `0.2353`, and F1
`0.3810`; the unselective baseline F1 was `0.5714`.

The aliases were then evaluated on the content-group-held-out Swissgeol split:
`7/35` pages were supported. Accepted interval precision remained `1.0000`,
recall was `0.2250`, and F1 was `0.3673`; the unselective baseline F1 was
`0.5854`.

## Consequence

The alias branch is evidence that page-family routing can expose a conservative
high-precision operating point on an independent language/source, but it is
not an extraction improvement and it leaves approximately 80% of pages
unsupported. Paper II must report both the precision and the coverage loss.
Future work requires a real multilingual structural expert, not further alias
accumulation. BGS v003 remains frozen and unopened.


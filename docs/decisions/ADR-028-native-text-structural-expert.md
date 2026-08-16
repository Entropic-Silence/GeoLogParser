# ADR-028: Native-text structural expert and identity-routed page selection

Date: 2026-08-16  
Status: `ACCEPT_DEVELOPMENT_ONLY`

## Decision

Add a native-PDF structural expert to the Paper II routed parser. When a PDF
retains positioned text, the expert extracts word boxes, recognizes cumulative
depth headers (`Depth interval`, `Teufenintervall`, and equivalent roles),
clusters numeric words by normalized x position, and reconstructs a monotonic
boundary sequence. A document-level route selects this expert before the
RapidOCR numeric-column expert when semantic anchoring and risk checks pass;
otherwise it uses the existing OCR expert or abstains.

For multi-borehole reports, page selection is performed from the borehole
identity suffix visible in the document title (for example `KB3` or `BS6`).
The paired authoritative record supplies the identity used for evaluation
alignment; interval values, lithology, and reference boundaries are never
used for page selection or candidate scoring. This avoids parsing the same
21-page report as if it were eight independent single-borehole pages.

The high-resolution ROI rereading branch is closed. It did not recover the
missing column evidence on Aargau long pages: Boundary F1 fell from `0.0361`
to `0.0285` and Interval F1 remained `0.0031` at 300 DPI.

## Development evidence

The fixed, already-inspected 46-record/five-canton Swissgeol transfer panel
was used for development diagnosis, not as an untouched external test. The
official database intervals are authoritative structured references, but
page/database completeness has not been independently verified.

| Route | Boundary precision | Boundary recall | Boundary F1 | Interval F1 | Critical numerical error rate |
|---|---:|---:|---:|---:|---:|
| RapidOCR field-aware identity-routed baseline | 0.6015 | 0.0947 | 0.1637 | 0.1000 | 0.3985 |
| Native text expert only | 0.7208 | 0.0933 | 0.1651 | 0.0922 | 0.2792 |
| Native-text/OCR routed MoE | 0.7735 | 0.1607 | 0.2662 | 0.1722 | 0.2265 |

The routed branch improved interval F1 for all five source families and
improved boundary F1 for four of five. St. Gallen improved from `0.5337` to
`0.7182` Boundary F1 and from `0.3949` to `0.5997` Interval F1 after report
page identity routing. Aargau reached boundary precision `0.9581`, while its
recall remained limited by page/database scope mismatch and sparse semantic
columns.

## Scope and limitations

These values are exploratory development evidence. The five-canton panel was
visually inspected while designing the field-aware branch, and it cannot
serve as untouched confirmation. The official interval database is not a
page-visible gold annotation. The route currently addresses structural depth
evidence only; lithology and description extraction remain outside this
experiment.

BGS v003 remains `FROZEN_UNOPENED`. No BGS external result was used in this
decision, and no claim of cross-source generalization is promoted from this
panel alone.

## Consequence

Paper II will treat positioned native text as a first-class modality in the
page-family-aware mixture-of-experts method. The next promotion gate requires
an independently frozen source with page-visible or independently verified
boundary ground truth, plus source-disjoint ablation of native text, OCR,
identity routing, and abstention. The native branch is not yet the final
primary method.

# ADR-031: Corrected NativeMM supervision does not remove the structural bottleneck

Date: 2026-08-16  
Status: `NO_GO_PRIMARY`

## Context

The first NativeMM real SFT used `paper2_nativemm_v001`, whose boundary labels
were tied to printed-number boxes. The corrected v002r2 corpus projects
authoritative interval endpoints through page scale into graphical boundary
positions. The first result could therefore not distinguish model failure from
supervision mismatch.

## Recheck

PaddleOCR-VL 1.6 was resumed from the synthetic multitask adapter and trained
for two epochs on 255 real Gold/derived-spatial samples from v002r2, adapting
the visual projector and language q/v blocks. The run used GPU 0 (RTX 5090),
with mean/final loss `0.5508/0.2295` and peak allocated memory `9.02 GiB`.

On the 12 BGS v001 development bundles available in the corrected evaluation
manifest, JSON-valid rate was `0.2143`, structural-evidence coverage `0.0000`,
direct Boundary F1 `0.0000`, and geometry-decoded Boundary F1 `0.0000` at
0.05 m. No frozen external source was opened.

## Decision

The NativeMM branch remains `NO_GO_PRIMARY`; corrected supervision does not
recover the missing structural evidence. Do not enlarge NativeMM training or
use it for BGS v003 external evaluation. Preserve the checkpoints and metrics
as a negative result showing that generic document-VLM generation is not a
substitute for explicit layout/geometry evidence on these long scans.

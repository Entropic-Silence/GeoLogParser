# ADR-042: PaddleOCR-VL page-level table-task feasibility gate

Date: 2026-08-17

## Observation

The official Transformers table-recognition prompt was evaluated on the first
frozen California v001 page.  The documented 512-token generation ceiling and
OTSL-to-HTML conversion completed in 46.16 s on the RTX 5090.  The output
contained one syntactically convertible OTSL table but no declared top/bottom
interval pair: the fixed decoder recovered zero of 22 reference intervals.

An earlier 4,096-token smoke took 367.57 s and likewise emitted no table
markup or intervals.  The lower, documented ceiling is therefore the valid
page-level smoke; neither run is a formal benchmark.

## Decision

The page-level official table task is not a viable California interval baseline
under the fixed full-page protocol.  Do not expand it to the 77-page Gold
cohort or report a performance score.  A future study could test a separately
registered ROI detector and official element-level recognition interface, but
that would be a different layout-dependent system rather than this baseline.

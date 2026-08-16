# ADR-030: Generic raster contact grounding is not a primary expert

Date: 2026-08-16  
Status: `NO_GO_PRIMARY_RETAIN_DIAGNOSTIC`

## Question

Can a reference-blind raster expert recover BGS layer boundaries by fitting a
numeric page depth axis and detecting horizontal contact lines across the
depth/description fields, thereby closing the v028 structural-recall gap?

## Evidence

On the 26-document/34-page BGS v001 development panel, a depth axis and at
least one contact event were recovered on 17/34 pages (`0.5000` page
coverage). At ±0.05 m, the raw deterministic candidate set reached Boundary
Recall/F1 `0.1090/0.1057`; its selected sequence reached Boundary F1 `0.0923`,
Interval F1 `0.0334`, and CNER `0.8431`.

Adding the contact-line, transition, y-proximity, depth-agreement, and axis
quality features to the existing v025 candidate pool under nested
source-disjoint folds produced Boundary F1 `0.2578`, Interval F1 `0.0866`, and
CNER `0.5448`. This is below routed v028 (`0.3475/0.1978` Boundary/Interval F1,
CNER `0.3281`) on the same development panel.

Failure inspection shows that horizontal raster evidence is not semantically
unique: regular stratigraphy grids, sample-recovery lines, description rules,
table borders, and true geological contacts share the same low-level line
signature. A generic line detector therefore adds candidate coverage but
degrades precision and sequence reconstruction.

## Decision

Do not promote generic horizontal contact grounding or its learned fusion as a
Paper II primary branch. Retain the reference-blind axis reconstruction and
contact events as diagnostic provenance, local ROI evidence, and hard-case
features for a future column-role-conditioned detector. Do not tune this branch
on BGS v002 or open BGS v003.

The next method change must model the semantic owner of a boundary event
(description contact, interpreted lithology, core/recovery, or scale grid), not
only its horizontal appearance. Any learned detector must use source-disjoint
column-role supervision and beat v028 on development before external use.

## Reproducibility

- Grounding: `scripts/run_bgs_graphical_grounding_development.py`
- Nested fusion: `scripts/run_bgs_graphical_fusion_nested.py`
- Outputs: `experiments/paper2/analysis/bgs_graphical_grounding_development_v001.json`
  and `experiments/paper2/analysis/bgs_graphical_fusion_nested_v001.json`
- Frozen external status: BGS v003 remained unopened.

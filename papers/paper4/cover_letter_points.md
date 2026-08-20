# Cover-letter points for Computers & Geosciences

## Proposed title

**Trustworthy Borehole Database Ingestion from VLM Proposals: Provenance and Spatial Support**

## Why this manuscript fits

- It addresses a geoscience-computing problem at the boundary of document AI,
  geological data management, and reproducible spatial analysis.
- It evaluates a modern open VLM under record-disjoint cohort and source-shift
  conditions rather than presenting a single-template demonstration.
- It contributes an auditable assurance architecture: page-grounded evidence,
  field semantics, deterministic depth geometry, selective accept/review,
  abstention, and review-queue provenance.
- It tests whether an apparently improved extraction policy changes the spatial
  support and volume diagnostics used by downstream geoscience workflows.

## Three claims to emphasize

1. High boundary-pair interval F1 from a modern VLM is a capability result, not
   a database-reliability result. On California the Qwen checkpoint reaches
   0.896–0.932 F1, but transport and provenance fail without an assurance layer.
2. Independent positioned evidence converts high-recall proposals into a
   selective, auditable subset: 0.993 precision at 0.244 coverage on a held-out
   cohort, with every unaccepted proposal retained for review.
3. Abstention has a spatial cost. The full-support risk-aware volume result is
   largely a selection/support effect and does not survive the matched-subset
   comparison as an additional correction benefit.

## What is intentionally not claimed

- No comprehensive multilingual benchmark is claimed.
- No universal or certified safety guarantee is claimed.
- No validated production geological model or geological interpretation accuracy
  is claimed.
- The 602-record dual-channel experiment is synthetic error injection on real
  structured records, not a comparison of two observed readers.
- The small host-managed closed visual pilot is not pooled with the formal VLM
  baseline.

## Related manuscripts and disclosure

The associated Paper I, Paper II, and Paper III analyses should be disclosed to
the editor if they are submitted simultaneously or subsequently. This
manuscript is independently structured around one problem statement, three
research questions, one provenance-grounded assurance method, and one
downstream consequence analysis; it is not a concatenation of those studies.

## Suggested reviewer expertise

- geological data systems and borehole stratigraphy;
- document intelligence, layout-aware extraction, or vision-language models;
- selective prediction, uncertainty calibration, and risk-aware automation;
- geostatistical interpolation and spatial-support sensitivity.

## Submission checklist

- Author, CRediT, funding, competing-interest, and corresponding-author
  statements are fixed in the final package.
- Confirm the exact C&G reference style and artwork requirements at submission.
- Rights, attribution, and linkage review is signed off in
  `submission/cageo/RIGHTS_LINKAGE_SIGNOFF.md`.
- Attach the release manifest and exact model/prompt provenance table as data/code
  availability material.

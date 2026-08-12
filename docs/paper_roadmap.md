# Three-paper roadmap

All empirical values are `TBD` until generated from versioned runs.

## Paper I — Chinese heterogeneous borehole-log benchmark

- **Hypothesis:** random page splitting materially overestimates field and
  interval extraction generalization compared with project- and
  template-disjoint evaluation. Effect magnitude: `TBD`.
- **Research questions:** current OCR/VLM/hybrid capability; split leakage;
  degradation sensitivity; dominant error modes.
- **Required data:** rights-audited Chinese pages spanning projects, sources,
  templates, formats, and quality; provenance-rich verified annotations;
  international transfer samples.
- **Required experiments:** B1–B6 on random, project-, template-, and if possible
  source-disjoint splits; real/synthetic degradation curves; repeated stochastic
  inference; error taxonomy and cost reporting.
- **Main contribution:** problem/schema definition, benchmark, leakage-resistant
  protocol, systematic baselines, robustness and failure analysis.
- **Largest risk:** obtaining diverse Chinese records with publication and
  redistribution rights; secondary risk is expert annotation capacity.
- **Minimum publishable result:** a quality-controlled, legally distributable or
  controlled-access multi-template benchmark with reproducible baselines and a
  convincing split-leakage analysis.
- **Ideal result:** multi-source public release, expert agreement study, broad
  model coverage, robust transfer/degradation findings, and maintained toolkit.

## Paper II — geology-constrained multimodal extraction

- **Hypothesis:** evidence-localized re-reading guided by soft/hard geological
  constraints reduces critical numerical errors while calibrated abstention
  limits false corrections. Effect magnitude: `TBD`.
- **Research questions:** constraint benefit; re-reading versus single pass;
  per-constraint contribution; critical numeric reliability; review detection.
- **Required data:** Paper I training/validation split plus constraint-trigger
  cases, candidate evidence, correction outcomes, and confidence labels.
- **Required experiments:** full system and one-module-at-a-time ablations;
  constraint-type contribution; candidate-ranking study; calibration diagrams,
  ECE/Brier; false correction and review precision/recall; latency/cost.
- **Main contribution:** modular geological constraint engine, localized
  multimodal re-reading/ranking, and reliability-aware acceptance.
- **Largest risk:** constraints may improve internal consistency without
  improving truth, or may introduce harmful false corrections.
- **Minimum publishable result:** statistically defensible reduction in critical
  errors with measured false-correction risk on disjoint tests.
- **Ideal result:** consistent gains across templates/sources, calibrated review
  decisions, interpretable constraint attribution, and reproducible local stack.

## Paper III — legacy logs to geological models

- **Hypothesis:** constraint-validated extraction and targeted human review yield
  measurably more stable downstream geological products at lower human effort
  than raw extraction. Effect magnitude: `TBD`.
- **Research questions:** error propagation; QC effect; real time saving; most
  consequential extraction error types.
- **Required data:** spatially coherent boreholes with permitted coordinates and
  stratigraphy, ground truth, timed correction sessions, and controlled depth/
  class perturbations.
- **Required experiments:** raw AI versus constraint-validated versus human GT;
  controlled 0.01–1.00 m perturbations; database/export validation; model surface
  displacement/uncertainty; measured human-in-loop workflow.
- **Main contribution:** end-to-end usable data workflow and causal error-
  propagation/human-efficiency evidence.
- **Largest risk:** lack of a legally usable spatially coherent case study and
  ambiguity in defining geologically meaningful downstream stability.
- **Minimum publishable result:** one real controlled case study with traceable
  database, downstream sensitivity analysis, and recorded human time.
- **Ideal result:** multiple geology/settings, calibrated review policy, QGIS/
  GeoParquet/3D reproducibility bundle, and actionable error budgets.

## Non-overlap controls

Paper I owns data/benchmark findings; Paper II owns the proposed method and
ablation; Paper III owns downstream sensitivity and human workflow. Shared data,
software, and upstream predictions are disclosed and versioned. No central
table, figure, analysis, or prose is counted as a novel result twice.


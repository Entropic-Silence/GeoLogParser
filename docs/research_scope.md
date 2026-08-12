# Research scope

## What we do

The first stage accepts a **single borehole column/log** as PDF, JPG, or PNG and
produces validated JSON and CSV. The MVP fields are borehole identifier, collar
elevation, final depth, groundwater depth, and interval top, bottom, thickness,
lithology, and description. Missing evidence remains null and is never guessed.

Every extracted value should retain its page, bounding box when available,
source text, extraction method, confidence, validation status, and warning
codes. Modules remain independently switchable so that attribution and ablation
experiments are possible.

## What we do not do

- Whole geotechnical-report understanding in stage one.
- Silent rule-based correction or geological-value completion.
- Training a large foundation model before baselines expose a specific need.
- Treating random page splits as the primary generalization result.
- Publishing private engineering records, locations, or unclear-license data.
- Claiming dataset sizes, accuracy, significance, or conclusions before runs.
- Making RQD, SPT, sample tables, core imagery, maps, or cross-sections MVP
  requirements.

## Paper I boundary — data and benchmark

Core question: how well do reproducible OCR, VLM, and hybrid systems structure
heterogeneous Chinese borehole logs under leakage-resistant and degraded-data
evaluation?

Unique contribution: benchmark definition, annotation/schema, project/template/
source-disjoint splits, robustness suite, baseline comparison, and error
taxonomy. Paper I may use simple constraints as diagnostic metrics, but it will
not claim the proposed constraint-guided correction method.

## Paper II boundary — method

Core question: can geological constraints, evidence-localized re-reading,
candidate ranking, and calibrated abstention improve reliable extraction while
avoiding false corrections?

Unique contribution: constraint API, multimodal fusion, constraint-guided
re-reading, confidence calibration, review decisions, module-level ablation,
critical numerical error and false-correction analysis. Dataset construction is
referenced from Paper I rather than republished as a new contribution.

## Paper III boundary — downstream workflow

Core question: how do extraction errors and human review policies affect a
usable borehole database and geological model?

Unique contribution: database/export workflow, error propagation, QC impact,
and measured human efficiency. It does not re-run Paper I as a new benchmark or
re-present Paper II's method ablations as a new method contribution.

## Shared-assets policy

The three papers may use the same versioned data and software, with explicit
disclosure. Text, tables, figures, central analyses, and claimed contributions
must remain paper-specific. Shared upstream metrics are referenced, not copied
as independent findings.


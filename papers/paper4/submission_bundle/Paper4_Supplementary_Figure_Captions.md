# Supplementary figure and table captions

These captions are the standalone caption file for the Paper 4
Computers & Geosciences supplementary upload. The supplementary methods
remain in `supplement.md`; the files listed here are the corresponding
figure/table captions and do not introduce additional evidence.

## Supplementary figures

### Supplementary Figure S1. Legacy sequence-reconstruction risk frontier

Interval F1 is plotted against action-level false-correction rate for the
v004 and v005 California cohorts using the same positioned candidate pools.
“All candidates” is the eligible pool without sequence selection;
“Monotonic” applies the monotonic dynamic-programming path; “+ continuity”
adds the continuity term; “Complete” is the complete candidate score; and
“Addition-only” is the conservative policy that accepts only additions above
the frozen threshold. The figure is a diagnostic ablation of the legacy
sequence-reconstruction branch, not the executed end-to-end VLM assurance
path. The clustered action-level points are shown to expose the
recovery–correction-harm trade-off; document-level risk and coverage are the
primary safety quantities in the main text.

### Supplementary Figure S2. Development-only threshold selection

The addition-only threshold grid is evaluated on v001/v002 development
evidence. The left panel shows document coverage and interval F1 as a function
of the raw node-score threshold; the right panel shows observed action-level
false-correction rate and worsened-document rate. The dashed line marks the
frozen threshold of 2.999, selected before the v004/v005 confirmation cohorts
were interpreted. No v004/v005 result is used to select or retune this
threshold.

### Supplementary Figure S3. Controlled error mechanisms and spatial response

Each small panel reports a within-error-class dose response from the controlled
error-injection study on authoritative spatial records. The blue curve is
surface mean absolute error, the red dashed curve is support loss, and the
green dotted curve is topology mismatch. The six panels represent boundary
displacement, coordinate displacement, missing boundary, merged layer, split
layer, and duplicate boundary conditions. Horizontal axes have different
units and are intentionally not comparable across panels; the figure supports
mechanism interpretation within each class rather than a cross-class severity
ranking. The perturbations are synthetic and are not observations from two
independent readers.

## Supplementary tables

### Supplementary Table S1. California cohort selection and roles

Record-disjoint California cohorts used in the integrated analysis, with
report, page, and reference-interval counts and the development, replication,
held-out, or confirmation role assigned before analysis. Pooled interval totals
are descriptive; confidence intervals in the main manuscript resample whole
documents.

### Supplementary Table S2. Full execution provenance and unresolved fields

Frozen checkpoint, serving identifier, software environment, hardware,
prompt, image-rendering, decoding, parsing, and component-hash records for the
direct VLM evaluation. The table also identifies runtime fields that could not
be reconstructed after evaluation; the missing fields are limitations on
bitwise replay, not hidden tuning inputs.

### Supplementary Table S3. Exploratory modern-model transport roster

Source-disjoint Swissgeol Thurgau transport diagnostics for the listed model or
interface. “Boundary-pair F1” is computed only when an auditable compatible
interval decoder output is available. A zero in the two specialist parser rows
means that the official task completed but did not yield an interval structure
compatible with the study matcher; it is not interpreted as a universal model
accuracy estimate. This table is exploratory and is not pooled with the
California Gold headline results.

### Supplementary Table S4. Assurance components and evidence coverage

Operational components of the provenance-grounded assurance layer, the
evidence represented by each component, and the corresponding observed
coverage or validity check. Endpoint-field anchor coverage, both-endpoint
interval coverage, semantic ownership, deterministic geometry, and selective
risk acceptance are distinct quantities and must not be substituted for one
another.

# From Legacy Borehole Logs to Structured Geological Models: An Automated AI-Assisted Workflow

## Abstract

This paper studies the downstream consequences of automatically structured legacy borehole logs. The workflow exports provenance-bearing extraction into SQLite and GeoJSON, performs quality control, correlates stratigraphic boundaries, and evaluates how controlled extraction errors propagate to geological surfaces and human review effort. A traceable database exporter and transparent IDW error-propagation baseline are implemented. One synthetic four-borehole smoke experiment validates the protocol but is not real-world evidence. Spatially coherent human Ground Truth, raw-versus-validated-versus-human comparisons, 3D modelling, and timed human studies are `TBD`.

## 1. Introduction

Document extraction is useful only if its output supports defensible engineering workflows. A small boundary error may be negligible in one setting and distort a thin layer in another; a wrong coordinate may be catastrophic. We ask: (RQ1) how extraction-depth errors affect model surfaces; (RQ2) whether constraint QC stabilizes downstream models; (RQ3) how much human time is saved; and (RQ4) which error classes dominate downstream impact.

This contribution boundary is workflow and error propagation. It reuses extraction/data definitions with disclosure but does not repeat Paper I benchmark or Paper II method contributions.

## 2. Related Work

Verified literature on borehole databases, stratigraphic correlation, spatial interpolation, implicit 3D modelling, uncertainty propagation, and human-AI data entry is `TBD`.

## 3. Workflow

Legacy PDF/JPG/PNG enters GeoLogParser and produces validated records with provenance. SQLite separates boreholes, intervals, and field provenance. GeoJSON exports coordinates without implicit CRS transformation. CSV, JSON, XLSX, and Parquet are supported with separate borehole, interval, and provenance tables. QGIS/GemPy/PyVista integration is `TBD`.

Human review is triggered by missing MVP fields, low confidence, field warnings, unknown terminology, and constraint violations. Start/completion events record real duration and corrected-field count. No human timing result exists yet.

## 4. Error-Propagation Method

For a selected correlated boundary, depth is converted to elevation as collar elevation minus depth. A transparent IDW baseline interpolates the surface. Controlled perturbations of 0.01, 0.05, 0.10, 0.50, and 1.00 m are applied with recorded seeds; shared interval boundaries remain continuous and thickness is recomputed. Surface MAE, RMSE, and maximum absolute error are evaluated on a fixed grid. Formal experiments require multiple seeds and confidence intervals.

The main comparison will be raw AI extraction versus constraint-validated extraction versus human GT using identical correlation/interpolation settings. Error types will also be injected separately: depth, missing interval, wrong lithology correlation, coordinate, and elevation. Exact site, grid, model, and repetitions are `TBD`.

## 5. Database and Interoperability

The database preserves source hash, raw/normalized values, page/bbox/text, method, confidence, validation, warnings, and units. Upserts replace a document's interval projection transactionally. GeoJSON skips missing coordinates and reports encountered CRS labels; it never guesses or transforms an unknown CRS. A quarantine-only internal run built four auto boreholes, 12 intervals, and 224 provenance rows; because data are not human-validated or release-cleared, this is connectivity evidence only.

## 6. Results

See [generated/current_results.md](generated/current_results.md). The tables contain synthetic protocol results only. A 30-seed extension now exercises mean/std and explicitly named normal-approximation confidence intervals for perturbations 0.01–1.00 m. At 1.00 m, synthetic surface MAE was 0.662470 ± 0.110565 m across seeds. This four-artificial-borehole fixture is not a real geological sensitivity estimate. Real-site sensitivity, raw/QC/GT comparison, 3D figures, uncertainty, human time, and statistical analysis remain `TBD`.

## 7. Human-in-the-Loop Evaluation

Planned measures are manual-entry time, AI inference time, AI+correction time, auto-accept rate, review rate, post-review error, and fields corrected/minute. Sessions must use anonymized annotator IDs, fixed instructions, counterbalanced task order where feasible, and real event timestamps. Sample size and analysis are `TBD`.

## 8. Discussion and Threats to Validity

The synthetic smoke shows that the code responds to controlled perturbations, not that real geology has the same response. IDW is a transparent baseline rather than a universal geological model. Correlation errors, anisotropy, structural geology, spatial sampling, and model choice may dominate boundary noise. Rights-cleared spatial coherence is the largest current data risk.

## 9. Reproducibility and Ethics

Database and surface artifacts will be linked to extraction experiment IDs and hashes. Spatially sensitive project information will be anonymized or withheld. Automated output is not an engineering sign-off; provenance and review status travel into downstream exports.

## 10. Conclusion

We define and partially implement a traceable path from legacy logs to geological surfaces and human review measurements. The central claim—whether constraint QC improves real downstream stability and efficiency—remains `TBD` until the full real-data study is complete.

## References

`[CITATIONS TO VERIFY]`

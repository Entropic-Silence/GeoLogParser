# Supplementary Material for Paper I

## S1. Scope

The main paper reports only the California manual-transcription cohorts and the Swissgeol, BGS, and Raft River source-shift panels. This supplement retains acquisition, eligibility, degradation, CAD conversion, Machine-Silver, metadata-only, and no-reference material. These tracks are useful for reproducibility and failure discovery but do not support the same claims as published manual transcription Gold.

## S2. Candidate-source audits

The Padova acquisition contains 11 PDFs/15 pages under a recorded CC BY 4.0 release. Slopes/Tiber contributes 29 rendered candidates, and SedLog contributes 18 tall native-PDF lithology pages. None has independent human interval reference in this project. Their results are therefore limited to coverage, candidate counts, schema validity, runtime, and failure types.

A Chinese CAD acquisition contains 33 DWGs. Renderer audits identified incomplete graphical-entity coverage, empty rasters, and invalid geometry on some files. Structural handle/text agreement on three priority derivatives did not establish pixel fidelity. These records remain conversion-incomplete and rights-unverified and do not enter any accuracy table.

The annotation service supports distinct tracks, record-hash attestations, and adjudication, but the Padova tasks remain auto proposals. There are zero effective human attestations and no project-created Gold result.

## S3. Secondary source diagnostics

USGS-142 and USGS-144 are tailored single-document checks whose explicit interval lists were recovered after source-specific crop/parser choices. They show software transfer, not representative source generalization. A seven-document Idaho scan audit compares label and numeric-range detection between OCR engines without an independent interval reference; it reports agreement events, not accuracy.

A five-canton Swiss transfer panel contains authoritative database intervals but lacks complete explicit page/database agreement. The frozen Thurgau parser produced candidates on only 2/46 records. Because low agreement may reflect extraction failure, page coverage, or page/database mismatch, this remains an authoritative-metadata stress test rather than Gold accuracy.

BGS first-page metadata and controlled degradation runs evaluate borehole ID and coordinate fields only. They show backend-specific omission and degradation sensitivity but do not establish interval or lithology robustness.

## S4. Machine-Silver and no-GT experiments

The Padova A/B adjudication track produces Machine Silver. Agreement to that reference is not human accuracy, and one participating model contributes to reference construction. Slopes, Tiber, SedLog, Padova, BGS-VLM, and quarantined Chinese runs report only their eligible evidence types. Accuracy metrics are null when no independent reference exists.

## S5. Fixed-prediction resampling

A 100-seed calculation resamples already frozen California predictions. Random-record F1 averaged 0.394±0.021 versus 0.390 on the grouped test. Because neither training nor tuning is rerun, the result means only that this frozen prediction set showed no large resampling difference. It is not evidence for or against the general causal claim that random train/test splits inflate document-model performance.

All exact experiment IDs, evidence tiers, hashes, and outputs remain in [current results](generated/current_results.md), the claim registry, source ledger, and publication-evidence bundle.

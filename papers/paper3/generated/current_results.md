<!-- AUTO-GENERATED. DO NOT EDIT. -->
### Synthetic error-propagation protocol

| Experiment | Perturbation (m) | Seed | Repetitions/grid points | Surface MAE (m) | RMSE (m) | Max abs. error (m) | Eligibility |
|---|---:|---:|---:|---:|---:|---:|---|
| P3_SYNTHETIC_ERROR_PROPAGATION_SMOKE_001 | 0.01 | 20260812 | 36 | 0.006136 | 0.006702 | 0.010000 | protocol_only |
| P3_SYNTHETIC_ERROR_PROPAGATION_SMOKE_001 | 0.05 | 20260813 | 36 | 0.024720 | 0.029174 | 0.050000 | protocol_only |
| P3_SYNTHETIC_ERROR_PROPAGATION_SMOKE_001 | 0.10 | 20260814 | 36 | 0.061361 | 0.067018 | 0.100000 | protocol_only |
| P3_SYNTHETIC_ERROR_PROPAGATION_SMOKE_001 | 0.50 | 20260815 | 36 | 0.306805 | 0.335092 | 0.500000 | protocol_only |
| P3_SYNTHETIC_ERROR_PROPAGATION_SMOKE_001 | 1.00 | 20260816 | 36 | 1.000000 | 1.000000 | 1.000000 | protocol_only |
| P3_SYNTHETIC_ERROR_PROPAGATION_MULTISEED_001 | 0.01 | multiple | 30 | 0.006780 ± 0.001256 | 0.007309 ± 0.001056 | 0.010000 ± 0.000000 | protocol_only |
| P3_SYNTHETIC_ERROR_PROPAGATION_MULTISEED_001 | 0.05 | multiple | 30 | 0.035460 ± 0.007308 | 0.037903 ± 0.006103 | 0.050000 ± 0.000000 | protocol_only |
| P3_SYNTHETIC_ERROR_PROPAGATION_MULTISEED_001 | 0.10 | multiple | 30 | 0.070823 ± 0.012221 | 0.075573 ± 0.010385 | 0.100000 ± 0.000000 | protocol_only |
| P3_SYNTHETIC_ERROR_PROPAGATION_MULTISEED_001 | 0.50 | multiple | 30 | 0.359916 ± 0.067800 | 0.383214 ± 0.056993 | 0.500000 ± 0.000000 | protocol_only |
| P3_SYNTHETIC_ERROR_PROPAGATION_MULTISEED_001 | 1.00 | multiple | 30 | 0.662470 ± 0.110565 | 0.717275 ± 0.093319 | 1.000000 ± 0.000000 | protocol_only |

These rows are synthetic protocol results only; they are not evidence of real geological-model sensitivity. Multi-seed rows show mean ± sample standard deviation across seeds.

### Executed Synthetic raw/constrained/reference comparison

| Experiment | Injected boundary error (m) | Raw surface MAE (m) | Constrained surface MAE (m) | Accepted corrections | Abstentions | Eligibility |
|---|---:|---:|---:|---:|---:|---|
| P3_EXECUTED_SYNTHETIC_RAW_QC_REFERENCE_001 | 0.01 | 0.006741 | 0.006741 | 0 | 120 | formal_synthetic_downstream |
| P3_EXECUTED_SYNTHETIC_RAW_QC_REFERENCE_001 | 0.05 | 0.035126 | 0.035126 | 0 | 120 | formal_synthetic_downstream |
| P3_EXECUTED_SYNTHETIC_RAW_QC_REFERENCE_001 | 0.10 | 0.069805 | 0.000000 | 120 | 0 | formal_synthetic_downstream |
| P3_EXECUTED_SYNTHETIC_RAW_QC_REFERENCE_001 | 0.50 | 0.356582 | 0.000000 | 120 | 0 | formal_synthetic_downstream |
| P3_EXECUTED_SYNTHETIC_RAW_QC_REFERENCE_001 | 1.00 | 0.665164 | 0.000000 | 120 | 0 | formal_synthetic_downstream |

This table executes the production constraint/rereading ranker and the same IDW surface for all inputs. It is controlled Synthetic algorithm evidence, not a real-site sensitivity estimate.

### Real structured-source controlled raw/QC/reference comparison

| Experiment | Injected error (m) | Raw MAE (m) | Consensus-drop MAE (m) | Mean-fusion MAE (m) | Relative reduction | Fusion better | Sign-test p | Retained coverage | False accepted | Eligibility |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P3_COAL602_CONSENSUS_QC_CONTROLLED_001 | 0.01 | 0.000575 ± 0.000147 | 0.731944 ± 0.111704 | N/A | N/A | N/A | N/A | 0.813 | 93 | failure_analysis_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_001 | 0.05 | 0.002874 ± 0.000689 | 0.729222 ± 0.166501 | N/A | N/A | N/A | N/A | 0.816 | 73 | failure_analysis_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_001 | 0.10 | 0.005539 ± 0.001343 | 0.736137 ± 0.128284 | N/A | N/A | N/A | N/A | 0.817 | 74 | failure_analysis_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_001 | 0.50 | 0.029294 ± 0.006825 | 0.743434 ± 0.135452 | N/A | N/A | N/A | N/A | 0.815 | 90 | failure_analysis_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_001 | 1.00 | 0.054885 ± 0.010986 | 0.737065 ± 0.104432 | N/A | N/A | N/A | N/A | 0.817 | 85 | failure_analysis_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_002 | 0.01 | 0.000575 ± 0.000147 | 0.731944 ± 0.111704 | 0.000453 ± 0.000093 | N/A | N/A | N/A | 0.813 | 93 | audit_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_002 | 0.05 | 0.002874 ± 0.000689 | 0.729222 ± 0.166501 | 0.002291 ± 0.000496 | N/A | N/A | N/A | 0.816 | 73 | audit_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_002 | 0.10 | 0.005539 ± 0.001343 | 0.736137 ± 0.128284 | 0.004334 ± 0.000899 | N/A | N/A | N/A | 0.817 | 74 | audit_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_002 | 0.50 | 0.029294 ± 0.006825 | 0.743434 ± 0.135452 | 0.022854 ± 0.004454 | N/A | N/A | N/A | 0.815 | 90 | audit_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_002 | 1.00 | 0.054885 ± 0.010986 | 0.737065 ± 0.104432 | 0.044844 ± 0.005753 | N/A | N/A | N/A | 0.817 | 85 | audit_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_003 | 0.01 | 0.000575 ± 0.000147 | 0.731944 ± 0.111704 | 0.000453 ± 0.000093 | 0.212 | 29/30 | 5.77e-08 | 0.813 | 93 | formal_source_controlled_downstream |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_003 | 0.05 | 0.002874 ± 0.000689 | 0.729222 ± 0.166501 | 0.002291 ± 0.000496 | 0.203 | 29/30 | 5.77e-08 | 0.816 | 73 | formal_source_controlled_downstream |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_003 | 0.10 | 0.005539 ± 0.001343 | 0.736137 ± 0.128284 | 0.004334 ± 0.000899 | 0.218 | 27/30 | 8.43e-06 | 0.817 | 74 | formal_source_controlled_downstream |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_003 | 0.50 | 0.029294 ± 0.006825 | 0.743434 ± 0.135452 | 0.022854 ± 0.004454 | 0.220 | 26/30 | 5.95e-05 | 0.815 | 90 | formal_source_controlled_downstream |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_003 | 1.00 | 0.054885 ± 0.010986 | 0.737065 ± 0.104432 | 0.044844 ± 0.005753 | 0.183 | 28/30 | 8.68e-07 | 0.817 | 85 | formal_source_controlled_downstream |

This controlled experiment uses 602 real source records and post-decision source-reference scoring. It is not image-extraction accuracy or human Ground Truth. Consensus deletion changes interpolation support and can worsen the surface; support-preserving fusion is reported separately.

### Real image-derived boundary to surface diagnostic

| Experiment | Documents | Reference points | Query points | Raw boundary MAE (m) | Reread boundary MAE (m) | Raw surface MAE (m) | Reread surface MAE (m) | Accepted rereads | Needs review | Eligibility |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P3_SWISSGEOL_TG_BOUNDARY_SURFACE_FROM_FROZEN_REREAD_002 | 35 | 35 | 423 | 1.471 | 0.941 | 3.402 | 3.050 | 4 | 5 | formal_authoritative_boundary_downstream |
| P3_SWISSGEOL_TG_MULTIBOUNDARY_SURFACE_FROM_FROZEN_REREAD_001 | 35 | 80 | 1265 | 11.171 | 2.789 | 21.397 | 20.615 | 4 | 5 | formal_authoritative_boundary_downstream |

This diagnostic inherits frozen reference-blinded image boundaries from the Paper II held-out run. Coordinates and collar elevations are taken from the authoritative structured record; image extraction of spatial metadata is not evaluated, so this is not a complete end-to-end spatial workflow.

### Real stratigraphic layer-volume diagnostic

| Experiment | Variant | Documents | Layers | Mean layer-thickness MAE (m) | Relative absolute volume error | Mean top support | Mean bottom support | Layers with negative thickness | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| P3_SWISSGEOL_STRATIGRAPHIC_LAYER_MODEL_002 | final | 35 | 3 | 45.679 | 0.122 | 0.7841 | 0.7079 | 1 | formal_real_stratigraphic_model |
| P3_SWISSGEOL_STRATIGRAPHIC_LAYER_MODEL_002 | raw | 35 | 3 | 45.952 | 0.139 | 0.7841 | 0.6984 | 1 | formal_real_stratigraphic_model |
| P3_SWISSGEOL_STRATIGRAPHIC_LAYER_MODEL_RISK_AWARE_002 | final | 35 | 3 | 45.679 | 0.122 | 0.7841 | 0.7079 | 1 | formal_real_stratigraphic_model_risk_aware |
| P3_SWISSGEOL_STRATIGRAPHIC_LAYER_MODEL_RISK_AWARE_002 | raw | 35 | 3 | 45.952 | 0.139 | 0.7841 | 0.6984 | 1 | formal_real_stratigraphic_model_risk_aware |
| P3_SWISSGEOL_STRATIGRAPHIC_LAYER_MODEL_RISK_AWARE_002 | risk_aware | 35 | 3 | 34.808 | 0.082 | 0.3873 | 0.3778 | 0 | formal_real_stratigraphic_model_risk_aware |

These rows convert adjacent IDW contact surfaces into layer-thickness and volume estimates. They are real downstream diagnostics, not validated geological interpretations; sparse deep-layer support and authoritative collars/coordinates remain explicit limitations.

### Authoritative controlled error-class propagation

| Experiment | Error type | Severity | Parameter | Unit | Boundary MAE (m) | Surface MAE (m) | Support | Topology mismatch | Eligibility |
|---|---|---:|---:|---|---:|---:|---:|---:|---|
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | boundary_shift | 1 | 0.10 | m | 0.025000 ± 0.000000 | 0.015834 ± 0.004640 | 1.0000 | 0.0000 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | boundary_shift | 2 | 0.50 | m | 0.125000 ± 0.000000 | 0.081641 ± 0.020818 | 1.0000 | 0.0000 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | boundary_shift | 3 | 1.00 | m | 0.250000 ± 0.000000 | 0.168353 ± 0.042179 | 1.0000 | 0.0000 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | coordinate_shift | 1 | 25.00 | m | 0.000000 ± 0.000000 | 0.071537 ± 0.030763 | 1.0000 | 0.0000 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | coordinate_shift | 2 | 100.00 | m | 0.000000 ± 0.000000 | 0.280400 ± 0.106989 | 1.0000 | 0.0000 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | coordinate_shift | 3 | 500.00 | m | 0.000000 ± 0.000000 | 1.564117 ± 0.624882 | 1.0000 | 0.0000 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | missing_boundary | 1 | 0.10 | affected_document_fraction | 0.000000 ± 0.000000 | 2.473709 ± 1.946654 | 0.9500 | 0.1143 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | missing_boundary | 2 | 0.25 | affected_document_fraction | 0.000000 ± 0.000000 | 4.284154 ± 2.022886 | 0.8875 | 0.2571 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | missing_boundary | 3 | 0.50 | affected_document_fraction | 0.000000 ± 0.000000 | 8.620714 ± 2.456667 | 0.7750 | 0.5143 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | merged_layer | 1 | 0.10 | affected_document_fraction | 9.230263 ± 1.415854 | 9.849802 ± 2.763770 | 0.9500 | 0.1143 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | merged_layer | 2 | 0.25 | affected_document_fraction | 22.610798 ± 2.207236 | 20.851922 ± 4.236661 | 0.8875 | 0.2571 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | merged_layer | 3 | 0.50 | affected_document_fraction | 51.441398 ± 2.594455 | 40.956927 ± 4.477924 | 0.7750 | 0.5143 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | split_layer | 1 | 0.10 | affected_document_fraction | 7.134167 ± 1.499206 | 6.912026 ± 2.963111 | 1.0000 | 0.1143 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | split_layer | 2 | 0.25 | affected_document_fraction | 15.457500 ± 1.974436 | 14.205055 ± 3.021957 | 1.0000 | 0.2571 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | split_layer | 3 | 0.50 | affected_document_fraction | 31.817500 ± 2.717759 | 30.747222 ± 5.952748 | 1.0000 | 0.5143 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | duplicate_boundary | 1 | 0.10 | affected_document_fraction | 4.442083 ± 2.467289 | 5.066429 ± 3.591368 | 1.0000 | 0.1143 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | duplicate_boundary | 2 | 0.25 | affected_document_fraction | 9.656667 ± 2.854705 | 8.806453 ± 4.141115 | 1.0000 | 0.2571 | formal_authoritative_controlled_error_downstream |
| P3_SWISSGEOL_ERROR_CLASS_PROPAGATION_002 | duplicate_boundary | 3 | 0.50 | affected_document_fraction | 20.734167 ± 5.084878 | 20.663361 ± 6.530423 | 1.0000 | 0.5143 | formal_authoritative_controlled_error_downstream |

Each row aggregates 30 seeded injections on 35 held-out authoritative records and a fixed 1,265-query reference domain. Parameters are error-class specific and are not directly comparable across units. Coordinates and collar elevations are authoritative structured fields rather than image-derived predictions; no human Ground Truth is claimed.

### External page spatial-metadata extraction

| Experiment | Documents | Coordinate predictions | Coordinate coverage | Pair exact/all | Pair exact/predicted | X MAE (m) | Y MAE (m) | Page/database disagreements | Collar predictions | Eligibility |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| P3_SWISSGEOL_EXTERNAL_SPATIAL_METADATA_002 | 88 | 53 | 53/88 (0.602) | 51/88 (0.580) | 51/53 (0.962) | 94.453 | 132.075 | 2 | 0 | formal_authoritative_spatial_extraction |

The frozen conservative parser was evaluated on every paired record outside the interval-v003 split. Database disagreement is not automatically attributed to recognition because the page and database can contain different values. Zero collar predictions is a measured abstention result, not missing evaluation output.

### Page-coordinate downstream surface diagnostic

| Experiment | Variant | Points | Coverage | Boundary MAE (m) | Surface MAE (m) | Surface RMSE (m) | Max error (m) | Eligibility |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P3_SWISSGEOL_PAGE_SPATIAL_SURFACE_001 | authoritative_coordinate_reread_boundary | 34 | 0.9714 | 0.941 | 3.050 | 5.014 | 29.590 | formal_partial_page_spatial_downstream |
| P3_SWISSGEOL_PAGE_SPATIAL_SURFACE_001 | page_coordinate_raw_boundary | 17 | 0.4857 | 0.000 | 9.514 | 13.751 | 69.821 | formal_partial_page_spatial_downstream |
| P3_SWISSGEOL_PAGE_SPATIAL_SURFACE_001 | page_coordinate_reference_boundary | 17 | 0.4857 | 0.000 | 9.514 | 13.751 | 69.821 | formal_partial_page_spatial_downstream |
| P3_SWISSGEOL_PAGE_SPATIAL_SURFACE_001 | page_coordinate_reread_boundary | 17 | 0.4857 | 0.000 | 9.514 | 13.751 | 69.821 | formal_partial_page_spatial_downstream |

Page coordinates and frozen image-boundary predictions are reference-free, but every collar elevation remains supplied by the authoritative record because page extraction coverage was zero. The comparison is therefore a partial spatial workflow, not complete end-to-end extraction.

### Licensed structured-source field proxy protocol

| Experiment | Perturbation (m) | Seed | Repetitions/grid points | Proxy-surface MAE (m) | RMSE (m) | Max abs. error (m) | Eligibility |
|---|---:|---:|---:|---:|---:|---:|---|
| P3_COAL602_SOURCE_ROOF_PROXY_PROTOCOL_001 | 0.01 | multiple | 30 | 0.002636 ± 0.000244 | 0.003600 ± 0.000234 | 0.009927 ± 0.000038 | protocol_only |
| P3_COAL602_SOURCE_ROOF_PROXY_PROTOCOL_001 | 0.05 | multiple | 30 | 0.012762 ± 0.000883 | 0.017592 ± 0.000913 | 0.049641 ± 0.000187 | protocol_only |
| P3_COAL602_SOURCE_ROOF_PROXY_PROTOCOL_001 | 0.10 | multiple | 30 | 0.025873 ± 0.001824 | 0.035878 ± 0.001331 | 0.099203 ± 0.000258 | protocol_only |
| P3_COAL602_SOURCE_ROOF_PROXY_PROTOCOL_001 | 0.50 | multiple | 30 | 0.131606 ± 0.013952 | 0.181193 ± 0.012088 | 0.496435 ± 0.001052 | protocol_only |
| P3_COAL602_SOURCE_ROOF_PROXY_PROTOCOL_001 | 1.00 | multiple | 30 | 0.260428 ± 0.018737 | 0.361223 ± 0.020639 | 0.992077 ± 0.003371 | protocol_only |

These rows use source-reported tabular values with origin-suppressed local coordinates. They are protocol-development evidence only, not image-derived automated extraction, a geological reference, constraint-QC, a true geological surface, absolute-location evidence, or formal downstream evidence. Multi-seed rows show mean ± sample standard deviation across seeds.

### Synthetic 3D interoperability protocol

| Experiment | Points | Triangle cells | Bounds (x0, x1, y0, y1, z0, z1) | VTP SHA256 | PNG SHA256 | Eligibility |
|---|---:|---:|---|---|---|---|
| P3_SYNTHETIC_PYVISTA_INTEROP_001 | 121 | 200 | 0.000, 10.000, 0.000, 10.000, 96.800, 100.800 | 283830930242804c7fa378972153c93a0da317c10a099739b8e13604fa62478b | ade2507596b32db5ab15e9898c8007b948f9536d68ce226eea640c6b249c98b5 | protocol_only |

Interoperability rows establish reproducible artifact generation only; they do not establish geological validity or real-site performance.

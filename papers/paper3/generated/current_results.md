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
| P3_COAL602_CONSENSUS_QC_CONTROLLED_001 | 0.01 | 0.000575 ± 0.000147 | 0.731944 ± 0.111704 | TBD | TBD | TBD | TBD | 0.813 | 93 | failure_analysis_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_001 | 0.05 | 0.002874 ± 0.000689 | 0.729222 ± 0.166501 | TBD | TBD | TBD | TBD | 0.816 | 73 | failure_analysis_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_001 | 0.10 | 0.005539 ± 0.001343 | 0.736137 ± 0.128284 | TBD | TBD | TBD | TBD | 0.817 | 74 | failure_analysis_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_001 | 0.50 | 0.029294 ± 0.006825 | 0.743434 ± 0.135452 | TBD | TBD | TBD | TBD | 0.815 | 90 | failure_analysis_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_001 | 1.00 | 0.054885 ± 0.010986 | 0.737065 ± 0.104432 | TBD | TBD | TBD | TBD | 0.817 | 85 | failure_analysis_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_002 | 0.01 | 0.000575 ± 0.000147 | 0.731944 ± 0.111704 | 0.000453 ± 0.000093 | TBD | TBD | TBD | 0.813 | 93 | audit_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_002 | 0.05 | 0.002874 ± 0.000689 | 0.729222 ± 0.166501 | 0.002291 ± 0.000496 | TBD | TBD | TBD | 0.816 | 73 | audit_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_002 | 0.10 | 0.005539 ± 0.001343 | 0.736137 ± 0.128284 | 0.004334 ± 0.000899 | TBD | TBD | TBD | 0.817 | 74 | audit_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_002 | 0.50 | 0.029294 ± 0.006825 | 0.743434 ± 0.135452 | 0.022854 ± 0.004454 | TBD | TBD | TBD | 0.815 | 90 | audit_only |
| P3_COAL602_CONSENSUS_QC_CONTROLLED_002 | 1.00 | 0.054885 ± 0.010986 | 0.737065 ± 0.104432 | 0.044844 ± 0.005753 | TBD | TBD | TBD | 0.817 | 85 | audit_only |
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

This diagnostic inherits frozen reference-blinded image boundaries from the Paper II held-out run. Coordinates and collar elevations are taken from the authoritative structured record; image extraction of spatial metadata is not evaluated, so this is not a complete end-to-end spatial workflow.

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

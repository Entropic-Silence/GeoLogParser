<!-- AUTO-GENERATED. DO NOT EDIT. -->
# Paper III major-revision tables

## Full-support and strict matched-subset diagnostics

Evidence tier: **Source-agreement reference**. These are surface and volume diagnostics, not validated geological models.

| Estimand | Variant | Documents | Mean thickness MAE (m) | Relative absolute volume error | Mean top support | Mean bottom support | Negative-thickness layers |
|---|---|---:|---:|---:|---:|---:|---:|
| Full support | raw | 35 | 45.623 | 0.1387 | 0.784 | 0.698 | 1 |
| Full support | reread | 35 | 45.350 | 0.1213 | 0.784 | 0.708 | 1 |
| Full support | risk | 35 | 34.899 | 0.0821 | 0.387 | 0.378 | 0 |
| Matched accepted subset | raw | 15 | 35.128 | 0.0326 | 0.894 | 0.850 | 0 |
| Matched accepted subset | reread | 15 | 34.670 | 0.0754 | 0.894 | 0.872 | 0 |
| Matched accepted subset | risk | 15 | 34.670 | 0.0754 | 0.894 | 0.872 | 0 |

## First-boundary spatial support

| Variant | Effective points | Point coverage | Hull-area ratio | Mean nearest-neighbour distance (m) | Mean grid-to-observation distance (m) |
|---|---:|---:|---:|---:|---:|
| raw | 34/35 | 0.971 | 1.000 | 1387.5 | 2745.0 |
| reread | 34/35 | 0.971 | 1.000 | 1387.5 | 2745.0 |
| risk | 14/35 | 0.400 | 0.636 | 3479.5 | 4618.6 |

## Accepted versus rejected document diagnostics

| Risk-router group | Documents | Reference boundaries | Raw available | Raw missing | Raw aligned MAE (m) | Raw exact documents | Hull-area ratio | Mean nearest-neighbour distance (m) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| accepted | 15 | 35 | 30 | 5 | 0.000 | 12/15 | 0.636 | 3080.7 |
| rejected | 20 | 45 | 44 | 5 | 19.550 | 13/20 | 0.946 | 2313.6 |

## IDW and leave-one-borehole-out sensitivity

| Domain | Variant | Relative volume-error range across IDW settings | Default LOO n | Default LOO MAE (m) |
|---|---|---:|---:|---:|
| Full reference | reference | -- | 80 | 47.06 |
| Full reference | raw | 0.122–0.153 | 80 | 49.84 |
| Full reference | reread | 0.092–0.132 | 80 | 46.62 |
| Full reference | risk | 0.033–0.124 | 79 | 47.05 |
| Matched accepted | reference | -- | 34 | 52.99 |
| Matched accepted | raw | 0.021–0.065 | 34 | 48.85 |
| Matched accepted | reread | 0.061–0.098 | 34 | 48.76 |
| Matched accepted | risk | 0.061–0.098 | 34 | 48.76 |

## Default LOO by ordered boundary

| Domain | Variant | B1 n / MAE (m) | B2 n / MAE (m) | B3 n / MAE (m) | B4 n / MAE (m) |
|---|---|---:|---:|---:|---:|
| Full reference | reference | 35 / 23.72 | 35 / 57.56 | 7 / 103.22 | 3 / 65.75 |
| Full reference | raw | 35 / 24.16 | 35 / 64.32 | 7 / 82.43 | 3 / 104.35 |
| Full reference | reread | 35 / 24.27 | 35 / 56.86 | 7 / 82.43 | 3 / 104.35 |
| Full reference | risk | 35 / 30.73 | 35 / 53.52 | 7 / 81.93 | 2 / 97.60 |
| Matched accepted | reference | 15 / 25.51 | 15 / 58.21 | 4 / 136.46 | 0 / -- |
| Matched accepted | raw | 15 / 27.00 | 15 / 59.03 | 4 / 92.60 | 0 / -- |
| Matched accepted | reread | 15 / 27.00 | 15 / 58.84 | 4 / 92.60 | 0 / -- |
| Matched accepted | risk | 15 / 27.00 | 15 / 58.84 | 4 / 92.60 | 0 / -- |

## Leave-one-borehole-out volume jackknife

| Domain | Variant | Replicates | Relative volume error, mean [min, max] | Thickness MAE, mean [min, max] (m) |
|---|---|---:|---:|---:|
| Full support | raw | 35 | 0.1348 [0.0884, 0.1659] | 45.06 [24.12, 54.80] |
| Full support | reread | 35 | 0.1177 [0.0489, 0.1699] | 44.78 [23.95, 54.75] |
| Full support | risk | 35 | 0.0849 [0.0274, 0.1365] | 35.27 [30.51, 44.03] |
| Matched accepted | raw | 15 | 0.0426 [0.0265, 0.0965] | 34.51 [2.67, 53.93] |
| Matched accepted | reread | 15 | 0.0780 [0.0165, 0.1108] | 33.96 [0.76, 53.37] |
| Matched accepted | risk | 15 | 0.0780 [0.0165, 0.1108] | 33.96 [0.76, 53.37] |

The full-support and matched-subset estimands answer different questions. The matched subset shows that risk-aware and reread inputs are identical after acceptance; the apparent full-support risk advantage is therefore a selection/support effect.

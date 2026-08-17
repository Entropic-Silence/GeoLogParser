<!-- AUTO-GENERATED. DO NOT EDIT. -->
# Paper III major-revision tables

## Full-support and strict matched-subset diagnostics

Evidence tier: **Source-agreement reference**. These are surface and volume diagnostics, not validated geological models.

| Estimand | Variant | Documents | Mean thickness MAE (m) | Relative absolute volume error | Mean top support | Mean bottom support | Negative-thickness layers |
|---|---|---:|---:|---:|---:|---:|---:|
| Full support | raw | 35 | 45.952 | 0.1389 | 0.784 | 0.698 | 1 |
| Full support | reread | 35 | 45.679 | 0.1216 | 0.784 | 0.708 | 1 |
| Full support | risk | 35 | 34.808 | 0.0824 | 0.387 | 0.378 | 0 |
| Matched accepted subset | raw | 15 | 35.128 | 0.0326 | 0.894 | 0.850 | 0 |
| Matched accepted subset | reread | 15 | 34.670 | 0.0754 | 0.894 | 0.872 | 0 |
| Matched accepted subset | risk | 15 | 34.670 | 0.0754 | 0.894 | 0.872 | 0 |

## First-boundary spatial support

| Variant | Effective points | Point coverage | Hull-area ratio | Mean nearest-neighbour distance (m) | Mean grid-to-observation distance (m) |
|---|---:|---:|---:|---:|---:|
| raw | 34/35 | 0.971 | 1.000 | 1387.5 | 2745.0 |
| reread | 34/35 | 0.971 | 1.000 | 1387.5 | 2745.0 |
| risk | 14/35 | 0.400 | 0.636 | 3479.5 | 4618.6 |

## IDW and leave-one-borehole-out sensitivity

| Domain | Variant | Relative volume-error range across IDW settings | Default LOO MAE (m) |
|---|---|---:|---:|
| Full reference | reference | -- | 47.06 |
| Full reference | raw | 0.122–0.154 | 49.84 |
| Full reference | reread | 0.093–0.132 | 46.62 |
| Full reference | risk | 0.033–0.125 | 47.05 |
| Matched accepted | reference | -- | 52.99 |
| Matched accepted | raw | 0.021–0.065 | 48.85 |
| Matched accepted | reread | 0.061–0.098 | 48.76 |
| Matched accepted | risk | 0.061–0.098 | 48.76 |

The full-support and matched-subset estimands answer different questions. The matched subset shows that risk-aware and reread inputs are identical after acceptance; the apparent full-support risk advantage is therefore a selection/support effect.

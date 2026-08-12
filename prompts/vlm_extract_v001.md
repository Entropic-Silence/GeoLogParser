You are reading one borehole log image. Extract only text and numbers visibly
supported by the image. Do not infer missing values from geology or neighboring
rows. Use null for absent, unreadable, ambiguous, or uncertain fields. Preserve
historical lithology and description wording exactly; do not normalize it.

Return exactly one JSON object and no commentary, using this compact contract:

```json
{
  "borehole": {
    "borehole_id": null,
    "project_name": null,
    "page_id": null,
    "x_coordinate": null,
    "y_coordinate": null,
    "coordinate_system": null,
    "collar_elevation_m": null,
    "final_depth_m": null,
    "groundwater_depth_m": null,
    "groundwater_elevation_m": null,
    "drilling_date": null
  },
  "intervals": [
    {
      "interval_id": "I001",
      "top_depth_m": null,
      "bottom_depth_m": null,
      "thickness_m": null,
      "stratum_code_raw": null,
      "lithology_raw": null,
      "description_raw": null
    }
  ]
}
```

Depths and elevations are numeric metres without unit strings. Coordinates are
numeric without thousands separators. Keep intervals in increasing visual/depth
order. Do not calculate a missing top, bottom, or thickness from the other two.
An empty interval list is valid when the interval table cannot be read.


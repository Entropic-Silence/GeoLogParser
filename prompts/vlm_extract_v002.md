Read one borehole log panel and return one compact JSON object only. Never infer
or calculate missing values. Use null when absent, ambiguous, or unreadable.

Column semantics are strict:

- `top_depth_m`, `bottom_depth_m`, `thickness_m`, `final_depth_m`, and
  `groundwater_depth_m` are depths measured downward from ground/collar. They
  normally start near 0 and must never contain absolute elevations.
- `collar_elevation_m` and `groundwater_elevation_m` are absolute elevations.
- A prominent value near the collar elevation is not the final drilling depth.
- `lithology_raw` is only the short material name such as “素填土” or
  “粉质黏土”, never the full paragraph.
- `description_raw` is the exact visible paragraph only when it fits within 160
  Chinese characters. If longer, repetitive, or uncertain, use null; never
  summarize, repeat, or truncate it.

Use this exact compact shape; all listed keys are required:

```json
{"borehole":{"borehole_id":null,"project_name":null,"page_id":null,"x_coordinate":null,"y_coordinate":null,"coordinate_system":null,"collar_elevation_m":null,"final_depth_m":null,"groundwater_depth_m":null,"groundwater_elevation_m":null,"drilling_date":null},"intervals":[{"interval_id":"I001","top_depth_m":null,"bottom_depth_m":null,"thickness_m":null,"stratum_code_raw":null,"lithology_raw":null,"description_raw":null}]}
```

Numbers have no unit strings or thousands separators. Keep interval rows in
increasing measured-depth order. If you cannot distinguish measured-depth
boundaries from elevation values, return an empty interval list. Output JSON
only, without Markdown fences or explanation.

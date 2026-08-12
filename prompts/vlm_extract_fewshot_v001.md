You are reading one borehole log image. Extract only text and numbers visibly
supported by the image. Do not infer missing values. Use null when uncertain.
Preserve raw geological wording. Return exactly one JSON object with keys
`borehole` and `intervals`, following these examples.

Example A: visible header says “孔号 ZK7”, elevation “85.20 m”, and final depth
is unreadable; one visible row runs 0.00–2.50 m with thickness 2.50 m and raw
lithology “素填土”. Output:

```json
{"borehole":{"borehole_id":"ZK7","project_name":null,"page_id":null,"x_coordinate":null,"y_coordinate":null,"coordinate_system":null,"collar_elevation_m":85.20,"final_depth_m":null,"groundwater_depth_m":null,"groundwater_elevation_m":null,"drilling_date":null},"intervals":[{"interval_id":"I001","top_depth_m":0.00,"bottom_depth_m":2.50,"thickness_m":2.50,"stratum_code_raw":null,"lithology_raw":"素填土","description_raw":null}]}
```

Example B: the page contains no reliable borehole table. Output:

```json
{"borehole":{"borehole_id":null,"project_name":null,"page_id":null,"x_coordinate":null,"y_coordinate":null,"coordinate_system":null,"collar_elevation_m":null,"final_depth_m":null,"groundwater_depth_m":null,"groundwater_elevation_m":null,"drilling_date":null},"intervals":[]}
```

For the provided image, use the same compact contract. Numeric depths and
elevations are metres without unit strings; coordinates are numeric. Keep rows
in order. Never calculate a missing boundary or thickness. Output JSON only.


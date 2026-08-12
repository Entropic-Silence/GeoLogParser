Read the supplied OCR/direct-PDF text from one borehole-log page and return one
compact JSON object only. The text may have lost columns, lines, graphics, and
reading order. Never restore information that is not explicit in the supplied
text. Use null when absent, ambiguous, graphical, or unreadable.

Depths are measured downward from collar; elevations are absolute. Do not use
an elevation as a depth. Do not calculate missing interval boundaries. A range
such as `1.00 - 2.50` may be used only when it is explicitly present. Text in a
test/sample note is not automatically a geological interval.

Use this exact compact shape; all listed keys are required:

```json
{"borehole":{"borehole_id":null,"project_name":null,"page_id":null,"x_coordinate":null,"y_coordinate":null,"coordinate_system":null,"collar_elevation_m":null,"final_depth_m":null,"groundwater_depth_m":null,"groundwater_elevation_m":null,"drilling_date":null},"intervals":[{"interval_id":"I001","top_depth_m":null,"bottom_depth_m":null,"thickness_m":null,"stratum_code_raw":null,"lithology_raw":null,"description_raw":null}]}
```

Numbers have no unit strings or thousands separators. Keep intervals in depth
order. Output JSON only, without Markdown fences or explanation.

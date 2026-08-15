Read one California borehole-log page and return one JSON object only.
Extract only intervals that are visibly supported by the page. Use null for
uncertain or absent values. Do not infer or calculate missing values.

The source depth labels are printed in feet, but return all numeric depth fields
in metres after converting only when the printed feet value is unambiguous. Do
not return descriptions. Preserve the visible lithology wording in
`lithology_raw` and keep rows in increasing depth order. If the page does not
contain a readable interval table, return an empty interval list.

Return exactly this compact JSON shape and no Markdown:

{"borehole":{"borehole_id":null,"project_name":null,"page_id":null,"x_coordinate":null,"y_coordinate":null,"coordinate_system":null,"collar_elevation_m":null,"final_depth_m":null,"groundwater_depth_m":null,"groundwater_elevation_m":null,"drilling_date":null},"intervals":[{"interval_id":"I001","top_depth_m":null,"bottom_depth_m":null,"thickness_m":null,"stratum_code_raw":null,"lithology_raw":null,"description_raw":null}]}

Read this borehole-log page and transcribe only visible lithological intervals.

Return exactly one JSON object, with no Markdown or explanatory text:

{"intervals":[{"top_depth_source":null,"bottom_depth_source":null,"lithology_raw":null}]}

Rules:
- The depth numbers must stay in the units printed on the page. Do not convert,
  calculate, interpolate, repair, or infer a missing number.
- Emit an interval only when both its top and bottom depth are visibly supported
  by the same page. Use JSON number values, not strings, for unambiguous depths.
- Keep intervals in visual top-to-bottom order. If this page has no readable
  lithology/depth interval table, return an empty list.
- Preserve visible lithology wording as `lithology_raw`; use null when it is
  unreadable. Do not return borehole metadata, descriptions, confidence scores,
  bounding boxes, or any fields outside this schema.

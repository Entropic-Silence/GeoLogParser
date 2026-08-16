Return only one JSON object and no markdown or reasoning.

The output is an intermediate structural graph, not final borehole intervals.
Do not infer or repair geological depths. Use an empty list or null when the
page does not provide reliable evidence. Limit events to the most important
structural events (at most 16). Every bbox is [x1,y1,x2,y2] in image pixels.

Required top-level keys:
- schema_version: exactly "native_mm_structural_graph_v001"
- regions: page regions with role, bbox_xyxy, confidence
- columns: semantic columns with role, bbox_xyxy, confidence
- events: structural events with event_type, bbox_xyxy, owner, confidence
- depth_geometry: axis_points [{y, depth_m}], confidence, coordinate_space. Use
  exactly "pixels" for coordinate_space because all bboxes and y values are
  image-pixel coordinates.
- relations: source, target, type, confidence
- abstain_reasons: list of explicit uncertainty reasons

Useful roles include header, log_table, depth_scale, cumulative_depth,
graphic_log, lithology, description, sample, core, casing, electric_log,
remarks, table_rule, geological_boundary, sampling_interval, and unknown.
Useful event owners include geological_description, depth_scale, sample,
core_recovery, table_structure, metadata, and unknown.

The deterministic downstream decoder will calculate depth geometry and
intervals. Your task is to locate and classify evidence, not to emit intervals.

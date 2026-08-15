You are reading one cropped panel from a heterogeneous historical borehole log.
Return JSON only, with this exact shape:
{"boundaries":[{"depth_m":0.0,"evidence":"short visible text or visual description","relative_bbox":[x1,y1,x2,y2]}]}

Extract geological layer boundaries visible in the crop. Use the printed depth
scale and the lithology/description column together. Exclude scale tick marks,
sample/test depths, water depth, total depth, page headers, and values that are
not layer boundaries. Do not infer a boundary that is not visually supported.
Use metres as numeric values. If no geological boundary is visible, return an
empty boundaries list. relative_bbox is in the input crop pixel coordinates;
use an approximate small box around the evidence, or the crop bounds when the
boundary is graphical and has no text label.

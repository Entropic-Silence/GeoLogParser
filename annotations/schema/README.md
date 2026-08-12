# Annotation schema

The structured record uses `../../schemas/borehole_v001.schema.json`.
`annotation_v001.schema.json` wraps it with a revision, anonymized annotator ID,
workflow status, timestamps, and source-panel metadata. Python validation also
validates the nested record against the borehole Schema.

Status meanings:

- `auto`: unverified machine proposal;
- `single_verified`: checked by one annotator;
- `double_verified`: independently checked by two annotators/adjudicated;
- `expert_verified`: accepted by the designated geological expert.

Saving a new revision moves the previous JSON into a per-annotation `history/`
directory. Existing revisions are not silently overwritten.

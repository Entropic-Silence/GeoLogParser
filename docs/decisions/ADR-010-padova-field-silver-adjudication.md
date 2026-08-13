# ADR-010: Padova field-level machine-adjudicated Silver reference

## Decision

Construct a Padova reference at field level from three frozen extraction
channels. Extractor A is the native-text Qwen3-VL channel (`P1_B2`), extractor
B is the rendered-page Qwen3-VL channel (`P1_B4`), and the positioned-text
layout channel (`P1_B3`) is corroborating evidence. A/B predictions are never
silently overwritten. Equal values are retained with an agreement decision;
values supported by one channel and the layout channel are retained as
corroborated; unresolved disagreements are set to `null` and sent to the hard
case stream.

The resulting tier is explicitly `SILVER_HIGH_CONFIDENCE` or
`SILVER_UNCERTAIN`, with `reference_type:
machine_adjudicated_silver_reference`. It is not human-verified or expert
ground truth, and its metrics are not accuracy against an authoritative label.

## Provenance

The builder freezes SHA-256 hashes for the three prediction files, the public
dataset manifest, and the rendered panel manifest. Each row also stores source
PDF/image paths and hashes, the claimed CC-BY-4.0 status, and a
`recorded_for_pre_submission_human_check` license-verification status. The
source-rights decision remains a separate pre-submission gate.

## Artifact

The immutable run is generated with:

```text
python scripts/build_padova_silver_reference.py \
  --output /data/GeoLogParser/artifacts/silver/unipd_field_silver_v003
```

The output is write-once. `silver_labels.jsonl` contains complete field
decisions and constraint results; `silver_reference.jsonl` is the compact
evaluation projection; `hard_cases.jsonl` contains unresolved or violated
records; and `artifact_manifest.json` hashes the generated JSON artifacts.


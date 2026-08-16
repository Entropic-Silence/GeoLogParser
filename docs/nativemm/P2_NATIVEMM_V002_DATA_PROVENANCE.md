# PaperII-NativeMM v002 development data provenance

This file records the inputs used by the NativeMM v002 development branch. It
is an internal provenance record, not a claim that every source is suitable for
redistribution. Frozen external evaluation sources are intentionally absent.

| Source tier | Dataset / manifest | Use | Label origin | Frozen external use |
|---|---|---|---|---|
| SYNTHETIC | `/data/GeoLogParser/datasets/synthetic_borehole_logs_v002/manifest.jsonl` | structural pretraining and controlled development | programmatic exact labels | no |
| GOLD | `datasets/manifests/bgs_offshore_gold_v001.jsonl` | source-disjoint development | authoritative source-aligned references | no |
| GOLD | `datasets/manifests/california_wcr_gold_v001.jsonl` | source-disjoint development | published paired/manual transcription | no |
| GOLD | `datasets/manifests/california_wcr_gold_v002.jsonl` | source-disjoint development | published paired/manual transcription | no |
| GOLD | `datasets/manifests/california_wcr_gold_v003.jsonl` | source-disjoint development | published paired/manual transcription | no |

The generated corpus is:

```text
/data/GeoLogParser/datasets/paper2_nativemm_v002r2
```

Its manifest summary and SHA256 hashes are stored in `summary.json`. The corpus
builder rejects BGS v002, BGS paired v002, and California v004/v005 identifiers.
The synthetic source is explicitly marked `SYNTHETIC`; its labels are never
reported as human or expert annotations.

The external BGS v002 and California v004/v005 sets remain reserved for the
predeclared one-time confirmation gate and were not used for prompt tuning,
threshold selection, hard-case mining, or training.

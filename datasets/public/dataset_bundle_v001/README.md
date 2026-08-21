# GeoLogParser public data bundle v001

This bundle contains the source files required to reproduce the principal
California, BGS, Swissgeol, Raft River, Paper III spatial, and synthetic
experiments. The archive is published as a GitHub Release asset rather than
committed into the git history so a normal clone remains lightweight.

## Download and extract

From a fresh checkout:

```bash
gh release download data-v001 --repo Entropic-Silence/GeoLogParser \
  --pattern 'GeoLogParser-public-data-v001.tar.zst' --dir /tmp/geologparser-data
tar --zstd -xf /tmp/geologparser-data/GeoLogParser-public-data-v001.tar.zst -C .
```

The archive preserves repository-relative paths. Its `manifest.json` records
every file size and SHA-256 digest. Verify the archive contents before running
any experiment.

## Included datasets

- California WCR Gold v001–v005: published USGS manual-transcription reference
  cohorts and source PDFs.
- BGS offshore paired v001, validation v002r2, paired v003, and the small BGS
  metadata v001 benchmark.
- Swissgeol Thurgau paired v003: development/held-out PDF/database pairing.
- USGS Raft River interval source material.
- Mendeley Coal 602 structured spatial records used by Paper III.
- Synthetic borehole logs v002 with programmatic labels and degradation fields.

## Evidence and rights

The manifest is a publication-data inventory, not a claim that every source
term has completed final legal review. California and synthetic files are the
most permissive. BGS files retain the required acknowledgement and the legacy
scan-footer caveat. Swissgeol publication authorization was supplied by the
project owner for this release, while the source-term field remains explicitly
flagged for final author verification before manuscript submission. The
authoritative source ledger in `datasets/data_registry.yaml` remains the
canonical provenance record.

Do not describe source-agreement or database-derived references as new human
annotations. The evidence tier for every record remains in the manifests.

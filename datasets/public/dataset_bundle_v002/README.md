# GeoLogParser public data companion v002

This GitHub Release asset is the portable data companion for GeoLogParser
Paper 4. It contains the selected source and structured data used by the
reported experiments. The complete manuscript, code, evidence projections,
claim audits, figures, and submission bundle are fixed separately by the
`paper4-cageo-v1.0.1` tag.

`data-v001` is retained only as a historical prerelease. It is superseded by
`data-v002` and should not receive a DOI.

## Download, verify, and extract

From a checkout of `paper4-cageo-v1.0.1`:

```bash
gh release download data-v002 --repo Entropic-Silence/GeoLogParser \
  --pattern 'GeoLogParser-public-data-v002.tar.zst*' --dir /tmp/geologparser-data
cd /tmp/geologparser-data
sha256sum --check GeoLogParser-public-data-v002.tar.zst.sha256
tar --zstd -xf GeoLogParser-public-data-v002.tar.zst -C /path/to/GeoLogParser
```

The archive uses repository-relative paths. It does not require a checkout at
`/data/GeoLogParser` or `/root/GeoLogParser`. The committed and in-archive
`manifest.json` records each payload file's byte size and SHA-256 digest;
`SHA256SUMS` provides a standard checksum list.

## Included data

- California WCR Gold v001-v005: published USGS manual-transcription reference
  cohorts and selected public source reports.
- BGS offshore paired v001, validation v002r2, paired v003, and BGS v001.
- Swissgeol Thurgau paired v003.
- USGS Raft River interval source material.
- Mendeley Coal 602 structured spatial records.
- Synthetic borehole logs v002 with programmatic labels and degradation fields.

The v002 release normalizes the synthetic identity to
`synthetic_borehole_logs_v002` / `SYNTHETIC_V002`. This is a metadata correction;
the 512 images, labels, scientific values, seed, and evidence tier are unchanged.

## Rights and evidence

Yifan Du manually reviewed the selected release contents, source terms, item
scope, privacy, sensitive locations, embedded third-party content, attribution,
and linkage, and approved this exact bundle for public research distribution on
2026-08-20. That approval is item-scoped and does not authorize unrelated
quarantined repository sources. It also does not replace source-specific terms.

See `DATA_LICENSES.md` for the obligations that travel with each source family.
No source-agreement or database-derived reference is represented as a new human
annotation, and no evidence tier changes because of public release.

## Citation and relationship to Paper 4

Use `CITATION.cff` for this data companion. Until the author registers an
archive DOI, cite the `data-v002` GitHub Release URL and version. Cite
`paper4-cageo-v1.0.1` separately when referring to the article's full
reproducibility package.

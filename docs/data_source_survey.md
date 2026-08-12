# Public data source survey — first pass

Verified on 2026-08-12. The structured facts and URLs live in
`datasets/data_registry.yaml`; this document summarizes operational status.

## Directly accessible now

- **University of Padova levee geotechnical dataset:** DOI
  `10.25430/researchdata.cab.unipd.it.00001663`. Repository JSON records public
  file 14335 under CC BY 4.0 with a 15,986,769-byte size and MD5. The downloaded
  ZIP matched that MD5 and contains 11 borehole-log PDFs (15 native-PDF pages),
  plus CPT/laboratory files. This is directly usable, with attribution, as an
  international pipeline/transfer source. It is not a Chinese benchmark and is
  not yet manually annotated.
- **BGS borehole records:** OGL terms and a fixed four-document/20-page audit
  sample are acquired and hashed. BGS source acknowledgement and item terms
  must accompany any redistribution.
- **Dutch BRO product environment:** official technical environment responded
  and is useful for database/schema interoperability. Its value as a legacy
  scanned-log image source and exact dataset licence are `TBD`.

## Accessible licence, dataset inspection incomplete

- **Ontario water well records:** the Open Government Licence – Ontario page was
  accessible and permits broad reuse with conditions. The dataset page returned
  HTTP 429 from this host, so format, resource inventory, and image-log fitness
  are not verified.

## Requires manual access/verification

- **USGS GeoLog Locator:** official pages returned HTTP 403 to automated access.
  USGS-authored material may be public domain, but item-level authorship and
  third-party content must be verified manually.
- **New Zealand Geotechnical Database:** landing page responded, while auditable
  access/licence conditions were not available in the command-line response.
  Account/terms review is required before download.

## Chinese candidates quarantined — not rights-cleared

- **Chinese benchmark sources:** `NOT COMPLETED`. Three public-web PDFs were
  frozen in
  `/data/GeoLogParser/datasets/candidates_quarantine/chinese_public_web_20260812`
  for internal technical and rights review only. One is a blank borehole-log
  form; one 58-page procurement attachment contains four modern Chinese logs on
  pages 44–45; one specifies delivery content rather than containing logs.
- The four visible log panels include project name, borehole ID, coordinates,
  elevation, final depth, groundwater depth, interval boundaries/thickness, and
  descriptions. The two PDF pages also contain stamps and precise public
  project details. Exact item URLs/licence terms, redistribution authorization,
  privacy treatment, and sensitive-location review are not yet documented.
  Therefore the actual rights-cleared benchmark page and interval counts remain
  zero, and no metric from these pages is a Paper I benchmark result.

No quarantined candidate is eligible for redistribution until its rights record
and privacy decision are complete.

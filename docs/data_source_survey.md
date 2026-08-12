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
- **Mendeley Borehole log Collection:** DOI `10.17632/vcpz47r3sv.2` is public
  under CC BY 4.0. The anonymous repository API exposed one 26,720,387-byte ZIP
  with SHA256 `c262d83a...1a16`; the acquired file matched. It contains 33 DWG
  drawings in eight folders (AutoCAD AC1014/AC1018/AC1021). This is a promising
  Chinese CAD-log candidate. A pinned LibreDWG 0.14 conversion of one drawing
  confirmed Chinese geological descriptions and a comprehensive borehole
  column, but also exposed a named company and named mining-area/project title.
  LibreDWG reported ignored MTEXT, so the rendering is incomplete. The sample
  and remaining 32 drawings stay quarantined pending complete conversion,
  privacy/sensitive-location review, third-party-content screening, and a
  deliberate PDF/PNG derivative policy. They are not eligible benchmark pages.
  An automatic `dwgread` text pre-screen subsequently found Chinese text in all
  33 and conservatively risk-flagged 30; this prioritizes human review but does
  not clear the other three. Review-only DXF/PNG derivatives were produced for
  those three with a recorded CJK font substitution, but all three conversion
  logs contain completeness warnings. Human review and benchmark eligibility
  therefore remain at zero.

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

## CGS/DataCite Chinese candidates — metadata only

Four China Geological Survey records were checked through DataCite on
2026-08-12: `10.35080/data.A.2020.P12`, `10.35080/data.H.2020.P19`,
`10.35080/data.H.2020.P20`, and `10.35080/data.C.2021.P25`. Their descriptions
are relevant: they respectively mention five borehole histograms, a 20-hole XLS
database, a 2.99 GB database/JPG atlas, and two lithological borehole columns.
The first three expose `http://dcc.ngac.org.cn/` in DataCite `rightsList`; this
is an institutional URL, not an identifiable licence. The fourth has no rights
entry. DOI targets redirected to the CGS HTTP site and timed out from this host.

Consequently all four remain `metadata_only`: none was downloaded, none is
counted toward dataset size, and none may be redistributed. Exact item terms,
authentication/application requirements, file inventory, and sensitive
geolocation review must be established before acquisition.

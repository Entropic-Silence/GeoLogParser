# Public data source survey — first pass

First-pass sources were verified on 2026-08-12. A frozen follow-up survey was
completed on 2026-08-13. The structured facts and URLs live in
`datasets/data_registry.yaml`; this document summarizes operational status.

## Reproducible metadata survey — 2026-08-13

The canonical run `chinese_borehole_open_metadata_20260813_v004` froze five
DataCite queries, 15 exact DOI reads, seven anonymous Mendeley file inventories,
and five repository reachability probes. It issued 32 read-only requests: 27
returned HTTP 200 and five failed. The recursive artifact manifest verified 69
files and has SHA256
`48a4b19577d8e1e61040cbe78caba99ffa187f862c4254692fa108c443d6b540`.
The complete evidence is under
`/data/GeoLogParser/artifacts/source_surveys/chinese_borehole_open_metadata_20260813_v004`.

The five DataCite searches reported 187, 92, 36, 16, and 15 source-side hits
for `China AND borehole`, Mendeley+borehole, Chinese engineering geology,
Chinese borehole+column, and Figshare+China+borehole respectively. Only the
first page of up to 100 records was requested per query; overlap is substantial.
After DOI deduplication, 226 metadata records were frozen. These are search
records, not acquired datasets, pages, intervals, or Benchmark samples.

Fifteen candidates were curated by the automated project agent from the frozen
metadata; this is not real human source review. Seven
Mendeley file inventories were accessible. Exactly one item had both a verified
open licence and a PDF/JPG/PNG inventory: the international SedLog PDF described
below. No newly found Chinese item passed both gates, and the survey itself is
not authorized to declare any item Benchmark eligible. The new eligible Chinese
Benchmark page count therefore remains zero.

Failed probes were retained as evidence: Figshare search and the SAGE Figshare
collection returned HTTP 403; Mendeley search returned HTTP 401 while known
public item-level file inventories remained accessible; the Zenodo record API
refused the connection; and the CGS item page returned HTTP 504. DataCite
metadata remained accessible for those DOI-bearing candidates.

## Directly accessible now

- **University of Padova levee geotechnical dataset:** DOI
  `10.25430/researchdata.cab.unipd.it.00001663`. Repository JSON records public
  file 14335 under CC BY 4.0 with a 15,986,769-byte size and MD5. The downloaded
  ZIP matched that MD5 and contains 11 borehole-log PDFs (15 native-PDF pages),
  plus CPT/laboratory files. This is directly usable, with attribution, as an
  international pipeline/transfer source. It is not a Chinese benchmark and is
  not yet manually annotated. Its KMZ supplies WGS84 locations for all 11 PDF
  identifiers and three site groups, making it a Paper III candidate; the
  coordinates remain source-provided/unverified, and the known TS5 filename vs
  TS2 page-header conflict is explicitly retained.
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
  those three with a recorded CJK font substitution. An automated v002
  source-DWG/derivative-DXF reconciliation found exact modelspace entity-handle
  and ordered-text inventory matches for all three: 1,244 entities/363 text,
  1,905/537, and 7,173/611. This is stronger conversion evidence than warning
  parsing alone, but it does not verify fonts, pixel appearance, privacy,
  rights of embedded content, or geological correctness. Human review and
  benchmark eligibility therefore remain at zero.
- **Mendeley SedLog drilling cores:** DOI `10.17632/v6k9s36pbm.1`, CC BY 4.0.
  The public file is a 10,549,922-byte, 18-page native PDF; the download matched
  repository SHA256 `007d26b...e6dd02`. Visual and programmatic review confirmed
  one long-form SedLog lithology column per page. It is English/non-Chinese and
  lacks most MVP header and text-description fields, so it is retained only for
  international transfer and unusual-layout testing. Human GT and
  Benchmark-eligible page counts are both zero.

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

## Additional CC BY Chinese metadata candidate

- **China shear-wave velocity profiles:** Zenodo DOI
  `10.5281/zenodo.15400683` has CC BY 4.0 metadata and an abstract reporting
  measurements from 9,715 Chinese boreholes. DataCite exposes no file format,
  size, or content URL, and the Zenodo records API was unreachable from this
  host during verification. The headline count is therefore only a source
  claim, not project data inventory. The record is potentially useful for a
  Paper III spatial/velocity study, but legacy images, interval fields,
  coordinates, privacy, embedded-data rights, and file accessibility all remain
  `TBD`; nothing was downloaded or counted.

## Additional metadata triage — no new phase-1 pages

- **SAGE/Figshare China site-classification collection:** DOI
  `10.25384/sage.c.6961823.v1` is CC BY 4.0 at collection level. Its abstract
  describes statistics from thousands of engineering boreholes, but DataCite
  exposes no members, file formats, sizes, or content URL; the Figshare API
  returned HTTP 403. This is not evidence of legacy log images and no headline
  count enters project inventory.
- **Dryad Gonghe core-stress data:** DOI `10.5061/dryad.9kd51c5sp` is CC0 and
  DataCite reports 6,710,118 bytes, but the record concerns stress measurements
  from 16 granite cores rather than borehole-column documents. It is explicitly
  out of scope and was not downloaded.
- **Xiong'an records:** DOI `10.35080/data.D.2019.P23` has no rights statement,
  size, format, or content URL and appears to be an article/case record. The
  distinct DOI `10.23650/data.D.2019.P23` describes a 16.5 MB OBJ/ArcGIS 3D
  model, but its rights field only says to consult the website. Neither is a
  licensed phase-1 image source, and neither was acquired.

## Newly registered structured-data leads — not Paper I page images

- **Binhai BH-CPTU/10-44** (`10.17632/vkjwwb8zsh.2`) exposes 44 XLSX files
  under CC BY 4.0. It is a Paper III structured-data lead, not PDF/JPG/PNG.
- **Wuhan karst-collapse data** (`10.17632/g7gzd8jfyn.1`) describes CSV
  lithology/location data but exposes `embargoedAccess` alongside CC BY 4.0.
  The access conflict must be resolved before acquisition.
- **PRD-CLAY** (`10.17632/jr8gcyhsff.1`), the 602-coal-borehole minimum dataset
  (`10.17632/33z3d5r6xk.1`), and the Songliao geophysical logs
  (`10.17632/fgn2chjdnz.2`) expose DOCX/XLSX/code rather than legacy page images.
- **CGS Pingluo, Luhuatai, Doumen, and Huangling records** describe engineering
  boreholes, tests, field photos, databases, or 3D outputs. None exposes both a
  reusable licence and an inspectable Phase-1 file inventory. Abstract quantities
  remain source claims and are not project data counts.
- **Wudalianchi borehole modeling data** (`10.5281/zenodo.14696781`) has CC BY
  metadata but no verified file inventory because Zenodo was unreachable from
  this host. Its current fit is Paper III metadata only.

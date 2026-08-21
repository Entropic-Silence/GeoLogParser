# Verified modern-VLM and borehole-document related work (2026-08-17)

This note records the directly relevant literature used to revise Paper II. It
does not transfer vendor or paper benchmark numbers into GeoLogParser claims.
Verification levels and permitted claim scopes are maintained in
`docs/literature_evidence.yaml`.

| Work | Evidence verified | Relevance to GeoLogParser | Boundary of comparison |
| --- | --- | --- | --- |
| Zhang et al. (2020), DOI `10.3390/app10165520` | publisher metadata/abstract | same-specification borehole-log image extraction | template-specific image extraction; not a source-disjoint modern-VLM benchmark |
| Amini et al. (2023), DOI `10.4095/332258` | Geological Survey of Canada record/abstract | separates PDF identification, selection, and capture | operational PDF workflow; does not provide our page-grounded interval evidence |
| Han & Suh (2024), DOI `10.9719/EEG.2024.57.5.473` | publisher PDF reviewed | page typing plus structured abandoned-mine borehole records | one Korean report family and Type-1 structuring; not cross-source interval Gold |
| Ma et al. (2024), DOI `10.1038/s41598-024-81846-5` | Scientific Reports metadata/abstract | LLM extraction from historical well records | image-based records remain a distinct difficulty; no transferred score |
| Hu et al. (DocOwl2, 2025), DOI `10.18653/v1/2025.acl-long.291` | ACL/arXiv metadata | high-resolution multi-page document understanding | general document capability; no borehole-specific structural guarantee |
| Shiga (2026), DOI `10.11532/jsceiii.7.1_133` | J-STAGE metadata/open article | direct VLM schema-selection and YAML extraction from borehole logs | 10 boreholes/12 pages in one Japanese system; no cross-source claim |
| Garzón et al. (2026), DOI `10.1016/j.cageo.2025.106043` | open-access article and repository PDF reviewed | geology-informed sequence/spatial metrics for 1,394 structured boreholes | starts after structuring; motivates downstream and topology diagnostics rather than image extraction |
| Qwen Team (2026), `Qwen/Qwen3.8-27B-FP8` | official model card and license archived locally | strong open native-VLM baseline used in our California Gold comparison | model-card identity only; no vendor score reused |

## Position of the present work

Existing borehole studies demonstrate template extraction, page classification,
PDF capture, LLM assistance, or direct VLM structuring. The unresolved issue is
not whether a modern VLM can emit plausible intervals on a familiar page family;
it is whether those intervals can be assigned to the correct semantic column,
reconstructed into a monotone sequence, traced to page regions, and selectively
accepted under source shift. Paper II therefore treats the VLM as a high-recall
proposal reader and evaluates an independent positioned-evidence/risk layer.
The completed California v003 result (raw Qwen precision 0.907 versus selective
precision 0.993 at 0.244 coverage) is reported as a selective assurance result,
not as evidence that the route dominates modern VLM extraction in every metric.

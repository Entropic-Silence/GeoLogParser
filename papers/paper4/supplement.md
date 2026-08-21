# Supplementary material

## S1. Scope and evidence labels

The integrated manuscript uses three evidence classes. Published manual-
transcription Gold is the primary extraction evidence; it originates from the
USGS release and is not a project-created annotation. Source-agreement
references are explicit page/database pairings and support source-specific
transfer or downstream diagnostics. Machine Silver and audit/no-reference
results are retained for agreement, coverage, and failure analysis only. The
synthetic class has programmatically known labels and is never substituted for
real Gold.

Other model branches, alternative OCR/VLM experiments, no-reference audits, and
source-acquisition diagnostics are not used as main evidence here. They are
excluded because they have a different evidence tier, consumed a development
role, or do not change the three research questions. This supplement retains
only details needed to reproduce or interpret the combined claims.

## S2. California selection and split audit

The initial deterministic join contained 12,732 reports and 225,150 exact-
deduplicated intervals. The selection gates were: a public report link; 5–60
intervals; empty source comments; adjacent continuity at least 0.99; and county-
diverse acquisition. The final formal cohorts are record-disjoint. v001 has a
10-report development partition and a 50-report test partition. v002, v003,
v004, and v005 each contain 100 reports, and each freeze excludes every earlier
record. The v004/v005 risk-policy confirmation labels were not used to change
the direct-VLM prompt, positioned parser, candidate matcher, or threshold.

The formal interval counts are summarized in Supplementary Table S1.

### Supplementary Table S1. California cohort selection and roles

| Cohort | Reports | Pages | Reference intervals | Role |
|---|---:|---:|---:|---|
| v001 test | 50 | 77 | 697 | initial parser evaluation; assurance development |
| v002 | 100 | 154 | 1,770 | external replication; assurance validation; threshold development |
| v003 | 100 | 154 | 1,788 | held-out assurance replication |
| v004 | 100 | 147 | 1,944 | risk-policy confirmation |
| v005 | 100 | 141 | 2,069 | risk-policy confirmation |

The five cohorts contain 450 reports and 8,268 intervals. Pooled interval totals
are descriptive; all confidence intervals in the main text resample whole
documents.

## S3. Matching, exactness, and semantic fields

For each reference/prediction pair, both top and bottom depths are converted to
metres and compared with tolerance 0.05 m. The order-preserving matcher first
maximizes match cardinality and then minimizes the sum of top and bottom errors.
One prediction cannot match twice, and crossing matches are forbidden. Boundary-
pair interval F1 is computed from the resulting matched count. Boundary MAE is
conditional on matched pairs and is always reported with unmatched counts.

Boundary-exact is a document-level property: every ordered boundary must match,
with no extra or missing boundary. Full-record exact adds the evaluated semantic
fields. Matched lithology exact is available for positioned OCR references; the
direct Qwen archive does not contain a validated lithology/full-record adjudication
for every proposal. Its 0.896–0.932 values must therefore not be relabelled as
semantic or full-record accuracy.

The RapidOCR matched-lithology exact rates in the five California cohorts are
0.431, 0.516, 0.543, 0.444, and 0.544. The corresponding full-record exact
counts are 0/50, 2/100, 0/100, 1/100, and 1/100. These complementary values
show why a high boundary-pair score is not a substitute for field-level semantic
correctness.

## S4. Direct-VLM execution record

The open baseline is the official `Qwen/Qwen3.8-27B-FP8` model. The exact
served ID is `qwen38-fp8-tp4-mtp4-long`; local revision is
`local_Qwen3.8-27B-FP8_qwen3_5_architecture_fp8_e4m3`; precision is fine-grained
dynamic FP8 E4M3. The runtime record is **partially reconstructable** rather
than a complete immutable per-request log: the continuously running server was
inspected on 2026-08-18 UTC after starting on 2026-08-17 15:25:16 UTC. It was
vLLM 0.1.14, Python 3.10.12, PyTorch 2.11.0+cu128, CUDA 12.8, Transformers
4.57.6, and Triton 3.6.0. The server ran in image
`ai@sha256:b937a8fa086d1ab30d5ac5843f04503bc5fc2be9152a0ee44bec7eb3b22fc78d`
under `runc`, working directory `/workspace/vllm-2080ti-definitive`, with
`CUDA_VISIBLE_DEVICES=1,2,3,4`, tensor parallelism 4, MP distributed execution,
FP8 weights, half compute dtype, automatic KV-cache dtype, chunked prefill,
prefix caching, MTP-4 speculative decoding, and `flashqla_legacy` prefill. The
selected devices were four RTX 2080 Ti GPUs (SM75); the host driver observed
during reconstruction was 595.71.05. The source commit, build recipe,
per-request scheduler trace, and immutable contemporaneous runtime lockfile are
unavailable and are not guessed. The frozen prompt is `vlm_interval_source_units_v002`, hash
`891bc6beb7ff9cf35c55389191a208c9b09e9e2dc76909f716603f413745104a`. Pages
were rendered at 200 DPI with PyMuPDF as lossless PNGs without crop, rotation,
or enhancement. Temperature was 0, top-p was not sent and therefore remained
provider default, maximum completion length was 4,096 tokens, thinking was
disabled, retries were 0, and parsing was strict JSON with no repair, YAML,
completion, reorder, or deduplication. Test date was 2026-08-17 UTC.

The component hashes are recorded here and in the release configuration:
`config.json` `74227dd615bf1ea975aa676bdf355a0379858c12f394b5365cd9dfa5fc2c70bc`,
`preprocessor_config.json`
`27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516`, and
`model.safetensors.index.json`
`f0838c766951bdfe76d6afbdb2771a8f67aaa2231dedb3d33cebd817729843a2`.

**Supplementary Table S2. Full execution provenance and unresolved fields.**

| Field | Frozen record |
|---|---|
| Official checkpoint | `Qwen/Qwen3.8-27B-FP8` |
| Served model ID | `qwen38-fp8-tp4-mtp4-long` |
| Local revision | `local_Qwen3.8-27B-FP8_qwen3_5_architecture_fp8_e4m3` |
| Precision | Fine-grained dynamic FP8 E4M3 |
| Runtime | vLLM 0.1.14 OpenAI server; partially reconstructable after evaluation |
| Python / ML runtime | Python 3.10.12; PyTorch 2.11.0+cu128; CUDA 12.8; Transformers 4.57.6; Triton 3.6.0 |
| Hardware | 4 x RTX 2080 Ti (SM75); tensor parallelism over four devices |
| Prompt | `vlm_interval_source_units_v002`; SHA-256 recorded above |
| Image input | PyMuPDF, 200-DPI lossless PNG, no crop/rotation/enhancement |
| Decoding | temperature 0; provider-default top-p; 4,096 max tokens; thinking disabled |
| Parsing | strict JSON; no YAML, repair, completion, reorder, or deduplication |
| Component hashes | `config.json`, `preprocessor_config.json`, and `model.safetensors.index.json` hashes recorded above |
| Unrecoverable fields | vLLM source commit, per-request trace, and immutable contemporaneous runtime lockfile |

The user-requested closed endpoint was recorded separately as a transport
failure: synthetic visual preflight returned HTTP 502 and no Gold page was
sent. A host-managed internal visual pilot is also retained as an operational
record, not a headline baseline. It used `OpenAI GPT-5.6-Sol` / `gpt-5.6-sol`,
one page from each California cohort, and returned 91/91 matched intervals on
five pages. Because checkpoint/API snapshot, revision, precision, runtime
version, provider decode settings, field bboxes, and confidence traces were not
exposed, the pilot is not pooled with Qwen and cannot support a general closed-
model claim.

### S4.1 Exploratory open-model transport roster

To test whether the source-shift risk was specific to the 27B Qwen serving path,
we ran a post-hoc, source-disjoint exploratory roster on the complete 35-page
Swissgeol Thurgau held-out panel. The panel was not used to change the Paper 4
prompt, thresholds, parser, or acceptance policy, and BGS v003 was not accessed.
The direct generalist comparison used the official
`Qwen/Qwen3-VL-4B-Instruct` checkpoint at revision
`ebb281ec70b05090aa6165b016eac8ec08e71b17`, local Transformers 5.14.1 and
PyTorch 2.11.0+cu128 on an RTX 5090. Its local checkpoint config records
`torch_dtype=null`, so the effective per-weight runtime dtype is marked
partially reconstructable rather than guessed. It used the same frozen prompt
`vlm_interval_source_units_v002` (SHA-256
`891bc6beb7ff9cf35c55389191a208c9b09e9e2dc76909f716603f413745104a`), 200-DPI
lossless page PNGs, greedy decoding (temperature 0, 4,096 maximum new tokens,
zero retries), strict JSON parsing, and metre units for Swissgeol. On the fixed
20-page California v003 exploratory panel it reached boundary-pair interval F1
0.793 (207/249 matched intervals; 3/13 complete documents); on Swissgeol it
reached 0.619 (43/80 matched; 0/35 complete documents). The California subset is
not a replacement for the full-cohort Qwen result and is reported only to make
the transport comparison explicit.

Two document-specialist open models were evaluated through their published task
interfaces rather than forced into a direct JSON prompt. `PaddlePaddle/PaddleOCR-VL-1.6`
(local revision `c5630abae1d940eafe0697512a0325494b02ab42`, Transformers 5.14.1,
PyTorch 2.11.0+cu128, checkpoint `torch_dtype=bfloat16`, RTX 5090) used its
official `Table Recognition:` task.
`opendatalab/MinerU2.5-Pro-2604-1.2B` (local snapshot
`local_snapshot_MinerU2.5-Pro-2604-1.2B`, Transformers 4.57.6,
`mineru-vl-utils` 1.2.1, PyTorch 2.11.0+cu128, RTX 5090; checkpoint
`torch_dtype=null`, effective runtime dtype partially reconstructable) used its
official two-step document parser. Both completed page inference on all 35
pages, but the fixed auditable decoder found no explicit top/bottom interval
rows (decoder output rate 0.0 and interval F1 0.0 for both). This is a
**task/interface coverage result**, not evidence that either model visually
recognized no table content; the specialist outputs were intentionally not
converted through an unregistered heuristic decoder.

### Supplementary Table S3. Exploratory modern-model transport roster

| Model/interface | Swissgeol pages | Interval output | Boundary-pair F1 | Complete documents | Interpretation |
|---|---:|---:|---:|---:|---|
| Qwen/Qwen3.8-27B-FP8, direct JSON | 35 | 76 intervals | 0.577 | 0/35 | source-shift degradation |
| Qwen/Qwen3-VL-4B-Instruct, direct JSON | 35 | 59 intervals | 0.619 | 0/35 | recurring source sensitivity; not monotonic with size |
| PaddleOCR-VL-1.6, official table task | 35 | 0 auditable decoded intervals | 0.000 | 0/35 | complete page-task execution but no compatible interval decoder output |
| MinerU2.5-Pro-2604-1.2B, official parser | 35 | 0 auditable decoded intervals | 0.000 | 0/35 | complete page-task execution but no compatible interval decoder output |

The comparison supports a bounded conclusion: transport degradation or loss of
usable, auditable interval output recurred across multiple open-model families
and interfaces. It does not estimate universal model capability, and specialist
decoder coverage must not be pooled with direct-JSON F1. The practical advantage
of the Paper 4 route is therefore not a claim that one VLM dominates all
others; it is the explicit separation of proposal quality, evidence ownership,
decoder coverage, and accept/review state.

## S5. Assurance ablation details

The VLM proposal assurance experiment uses the same frozen Qwen output and a
separate positioned candidate pool. The two readers are not allowed to read one
another's output. **Endpoint-field numeric-anchor coverage** is the proportion
of proposed top and bottom fields that occur in a positioned bbox on the same
page. **Both-endpoints anchored proposal coverage** is the fraction of VLM
interval proposals whose top and bottom fields are both anchored; it is a
different, interval-level quantity. Owned/accepted coverage is stricter: both
boundaries must agree with one positioned interval in the same semantic column
and retain source regions. Acceptance additionally requires positive thickness,
monotonic order, and no overlap. All unaccepted proposals remain review items.

### Supplementary Table S4. Assurance components and evidence coverage

| Component | Effect represented | Main evidence |
|---|---|---|
| VLM proposal | visual recall and implicit layout semantics | California v001–v005 F1 |
| Endpoint-field numeric anchor | page-local numerical evidence | 0.817–0.849 endpoint-field coverage |
| Both endpoints anchored | interval-level numerical evidence | 0.731–0.792 proposal coverage |
| Complete top-bottom ownership | semantic column evidence | 0.236–0.287 development/validation coverage; 0.244 held-out |
| Deterministic geometry | unit conversion, positive thickness, order | zero non-finite accepted values |
| Selective risk policy | acceptance versus review/abstention | 0.993 held-out selective precision |

The 2.999 threshold belongs only to this legacy addition-only sequence-risk
policy; it is not a threshold in the main VLM assurance path. It was developed
using v001/v002 outcomes. The accepted actions in v004/v005 are confirmation
evidence for the unchanged legacy policy, not a new threshold search. The
document-level upper bound of 0.1459 follows from 19
accepted documents and zero observed worsened documents. The 82 actions are
clustered within those documents; the iid action bound is reported only as a
secondary sensitivity quantity.

Complete-document auto-acceptance is 2/50 (4%) in v001, 4/100 (4%) in v002,
and 4/100 (4%) in held-out v003. This is distinct from interval-level proposal
coverage and is reported as deployment utility, not as a replacement for
interval precision.

## S6. Candidate-graph and sequence ablation

The legacy candidate graph operates on semantically eligible positioned OCR
hypotheses. Candidate

$$
c_i=(t_i,b_i,p_i,y_i,x_i^t,x_i^b,e_i,q_i)
$$

retains top and bottom depth, page, vertical order, normalized top and bottom
column positions, source evidence, and normalized OCR confidence. Construction
requires $0\leq t_i<b_i\leq5000$ ft and a geological description. The frozen
raw node score is

$$
r_i=1+q_i+\mathbf{1}[\text{geological term in }e_i].
$$

The shallow-start preference is applied only when a path begins,
$I_i=r_i-0.0005t_i$; it is not included in the later risk threshold. An edge
$i\rightarrow j$ is admissible only when document position increases,
$t_j\geq t_i$, and $b_i-t_j\leq1$ ft. With $g_{ij}=|b_i-t_j|$, the complete
edge score is

$$
e_{ij}=\operatorname{continuity}(g_{ij})
-4(|x_i^t-x_j^t|+|x_i^b-x_j^b|)
-0.15\max(0,p_j-p_i-1),
$$

where the continuity contribution is 5 for $g_{ij}\leq0.05$,
$2-g_{ij}$ for $0.05<g_{ij}\leq1$, and
$-\min(6,\log(1+g_{ij}))$ otherwise. Dynamic programming computes

$$
F(j)=\max\left(I_j,\max_{i<j:i\rightarrow j}\{F(i)+r_j+e_{ij}\}\right)
$$

and backtracks the highest-scoring path, breaking score ties by path length.
Every earlier admissible candidate is considered; the published decoder has no
predecessor-window truncation.

The addition-only risk policy preserves the first-pass interval set $R$ and
considers non-overlapping proposed additions in descending $r_i$. If $R$ is
non-monotone, automatic modification is rejected before any addition is
considered. Candidate
$c$ is accepted only when $r_c\geq2.999$ and its open depth interval has no
positive overlap with $R$ or an earlier accepted addition. The development
grid used only v001/v002 and comprised every archived candidate score in
$[1,3]$ together with 1.0, 2.0, 2.5, 2.9, 2.95, 2.975, 2.99, 2.995, 2.999,
and 3.0. The threshold 2.999 was frozen before v004/v005 confirmation; the
development-only curve is shown in Supplementary Figure S2.

The same candidate pool, documents, source matcher, and interval tolerance are
used for every v004/v005 variant. The eligible pool without sequence selection
has F1 0.554/0.516 and FCR 0.324/0.322. Monotonic dynamic programming reaches
0.579/0.550 and FCR 0.111/0.062. Adding continuity gives 0.566/0.530; column
stability without the geological-term bonus gives 0.563/0.519; the complete
score gives 0.566/0.530 with precision 0.953/0.914. The conclusion is not that
every constraint adds F1: monotonic path selection provides the largest recovery,
while additional terms change the precision/risk operating point.
The full same-pool risk frontier is shown in Supplementary Figure S1.

The shallow-start coefficient is a weak deterministic tie preference, not a
fitted geological constant. A post-hoc sensitivity over 0, 0.0005, 0.001,
0.0025, and 0.005 per foot leaves v004 F1 unchanged at 0.5662 and changes v005
from 0.5310 to 0.5297. This sensitivity is explanatory and does not change the
confirmation labels.

## S7. Spatial-support and interpolation details

The full-support analysis uses the available points for each variant over a
common reference hull. The matched-subset analysis restricts all variants to the
same 15 accepted documents. The first-boundary risk point coverage is 14/35,
with hull-area ratio 0.636, mean nearest-neighbour distance 3,479.5 m, and mean
grid-to-nearest-observation distance 4,618.6 m. Raw and reread use 34/35 points,
retain hull-area ratio 1.000, and have mean distances 1,387.5 m and 2,745.0 m.

The IDW sweep varies power 1–3, all points versus four/eight nearest neighbours,
and grid sizes 15, 25, and 41. Full-support reference-relative volume-discrepancy ranges are 0.122–0.153
(raw), 0.092–0.132 (reread), and 0.033–0.124 (risk). Matched-subset ranges are
0.021–0.065 (raw) and 0.061–0.098 for both reread and risk. Reference-input
leave-one-borehole-out MAE is 47.06 m for 80 ordered boundary targets; risk has
79 evaluable targets in full support and 34 in the matched subset. The volume
jackknife removes one borehole at a time and reports 35 full-support replicates;
its overlapping ranges are a principal reason the main text avoids a universal
downstream ranking.

The 602-record protocol injects synthetic boundary/value errors into two channels
on real structured-source coordinates. Agreement-based deletion retains 0.813–
0.817 of points, while support-preserving mean fusion improves 26–29 of 30
perturbation repetitions at each magnitude. The seed repetitions measure
mechanism repeatability, not independent site-level inference. Supplementary
Figure S3 shows the within-error-class spatial responses.

## S8. Additional source-shift and excluded experiments

The one-time BGS v003 external gate contains a single five-page record. Four
pages were classified as explicit depth-range tables but produced no accepted
ranges, one page was classified as unsupported, and the record abstained
completely with zero false positives and zero utility.

The broader project contains five-canton Swissgeol transfer, BGS metadata-only
scans, Raft River tabular diagnostics, USGS Idaho cross-engine checks, synthetic
degradation, NativeMM feasibility branches, and no-reference Chinese/CAD audits.
They are excluded from the integrated headline tables because they either have a
different evidence tier, no interval reference, a consumed development role, or
do not change the three research questions. The original paper supplements and
claim registry preserve their exact status and hashes.

## S9. Reproducibility and release contents

The Paper 4 public reproducibility package provides the manuscript, supplement,
figures, structured or reanalysis assets, transformed inputs, aggregate metrics,
manifests, checksums, model configurations, prompt hashes, generated tables,
and scripts that recompute the public analyses. Source PDFs, rendered pages,
page crops, raw OCR regions/text, model weights, and private credentials are
not redistributed where third-party terms apply. The sole author has reviewed
and screened the GitHub release materials for public dissemination, confirmed
the source attribution and linkage records, and confirms that the released
materials are sufficient to reproduce the reported result-level analyses. The
released transformed inputs may remain linkable and are not claimed to be
anonymous. The published software archive is version `paper4-cageo-v1.0.9`,
https://doi.org/10.5281/zenodo.22043933; the published GitHub release is
`paper4-cageo-v1.0.9`. The separate published data companion is `data-v002`,
https://doi.org/10.5281/zenodo.22031703. The first identifier is a software DOI,
not a journal-article DOI. The data record has mixed source-specific rights and
no blanket licence.

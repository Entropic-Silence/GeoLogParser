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

The formal interval counts are:

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
dynamic FP8 E4M3; runtime is a vLLM-compatible OpenAI server whose package
version was not exposed. The run used four RTX 2080 Ti GPUs. The frozen prompt
is `vlm_interval_source_units_v002`, hash
`891bc6beb7ff9cf35c55389191a208c9b09e9e2dc76909f716603f413745104a`. Pages
were rendered at 200 DPI with PyMuPDF as lossless PNGs without crop, rotation,
or enhancement. Temperature was 0, top-p was not sent and therefore remained
provider default, maximum completion length was 4,096 tokens, thinking was
disabled, retries were 0, and parsing was strict JSON with no repair, YAML,
completion, reorder, or deduplication. Test date was 2026-08-17 UTC.

The component hashes are recorded in the main paper and release configuration:
`config.json` `74227dd615bf1ea975aa676bdf355a0379858c12f394b5365cd9dfa5fc2c70bc`,
`preprocessor_config.json`
`27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516`, and
`model.safetensors.index.json`
`f0838c766951bdfe76d6afbdb2771a8f67aaa2231dedb3d33cebd817729843a2`.

The user-requested closed endpoint was recorded separately as a transport
failure: synthetic visual preflight returned HTTP 502 and no Gold page was
sent. A host-managed internal visual pilot is also retained as an operational
record, not a headline baseline. It used `OpenAI GPT-5.6-Sol` / `gpt-5.6-sol`,
one page from each California cohort, and returned 91/91 matched intervals on
five pages. Because checkpoint/API snapshot, revision, precision, runtime
version, provider decode settings, field bboxes, and confidence traces were not
exposed, the pilot is not pooled with Qwen and cannot support a general closed-
model claim.

## S5. Assurance ablation details

The VLM proposal assurance experiment uses the same frozen Qwen output and a
separate positioned candidate pool. The two readers are not allowed to read one
another's output. Numeric-anchor coverage is the proportion of proposal values
that occur in a positioned bbox on the same page. Owned/accepted coverage is
stricter: both boundaries must agree with one positioned interval and retain
source regions. Acceptance additionally requires positive thickness, monotonic
order, and no overlap. All unaccepted proposals remain review items.

| Component | Effect represented | Main evidence |
|---|---|---|
| VLM proposal | visual recall and implicit layout semantics | California v001–v005 F1 |
| Positioned numeric anchor | page-local numerical evidence | 0.817–0.849 coverage |
| Complete top-bottom ownership | semantic column evidence | 0.236–0.287 development/validation coverage; 0.244 held-out |
| Deterministic geometry | unit conversion, positive thickness, order | zero non-finite accepted values |
| Selective risk policy | acceptance versus review/abstention | 0.993 held-out selective precision |

The 2.999 threshold was developed using v001/v002 outcomes. The accepted
actions in v004/v005 are confirmation evidence for the unchanged policy, not a
new threshold search. The document-level upper bound of 0.1459 follows from 19
accepted documents and zero observed worsened documents. The 82 actions are
clustered within those documents; the iid action bound is reported only as a
secondary sensitivity quantity.

Complete-document auto-acceptance is 2/50 (4%) in v001, 4/100 (4%) in v002,
and 4/100 (4%) in held-out v003. This is distinct from interval-level proposal
coverage and is reported as deployment utility, not as a replacement for
interval precision.

## S6. Candidate-graph and sequence ablation

The same candidate pool, documents, source matcher, and interval tolerance are
used for every v004/v005 variant. The eligible pool without sequence selection
has F1 0.554/0.516 and FCR 0.324/0.322. Monotonic dynamic programming reaches
0.579/0.550 and FCR 0.111/0.062. Adding continuity gives 0.566/0.530; column
stability without the geological-term bonus gives 0.563/0.519; the complete
score gives 0.566/0.530 with precision 0.953/0.914. The conclusion is not that
every constraint adds F1: monotonic path selection provides the largest recovery,
while additional terms change the precision/risk operating point.

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
and grid sizes 15, 25, and 41. Full-support volume-error ranges are 0.122–0.153
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
mechanism repeatability, not independent site-level inference.

## S8. Additional source-shift and excluded experiments

The broader project contains five-canton Swissgeol transfer, BGS metadata-only
scans, Raft River tabular diagnostics, USGS Idaho cross-engine checks, synthetic
degradation, NativeMM feasibility branches, and no-reference Chinese/CAD audits.
They are excluded from the integrated headline tables because they either have a
different evidence tier, no interval reference, a consumed development role, or
do not change the three research questions. The original paper supplements and
claim registry preserve their exact status and hashes.

## S9. Reproducibility and release contents

The public `data-v001` release contains California WCR Gold v001–v005, BGS
offshore paired/validation inputs, Swissgeol Thurgau v003, Raft River, the
structured Coal-602 source, and Synthetic v002. The archive contains 1,951
files and is checked by a per-file manifest. The repository additionally stores
the candidate-pool reanalysis inputs, transformed spatial inputs, model configs,
prompt hashes, generated tables, and the scripts that recompute public analyses.
All source-specific rights, attribution, and linkage notes remain in the data
registry and source-verification ledger.

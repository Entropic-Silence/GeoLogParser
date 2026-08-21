#!/usr/bin/env python3
"""Regenerate the compact autonomous-research status dashboard."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path("/data/GeoLogParser/datasets")


def _count_manifest(path: Path, tier: str | None = None) -> int:
    if not path.is_file():
        return 0
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if tier is None or row.get("ground_truth_tier") == tier:
            count += 1
    return count


def main() -> None:
    registry = yaml.safe_load((ROOT / "datasets/data_registry.yaml").read_text(encoding="utf-8"))
    compliance_path = Path("/data/GeoLogParser/artifacts/compliance/automated_compliance_v002.json")
    compliance = json.loads(compliance_path.read_text(encoding="utf-8")) if compliance_path.is_file() else {"decision_counts": {}}
    synthetic_summary_path = DATA_ROOT / "synthetic_borehole_logs_v001/summary.json"
    synthetic = json.loads(synthetic_summary_path.read_text(encoding="utf-8")) if synthetic_summary_path.is_file() else {}
    silver_summary_path = Path("/data/GeoLogParser/artifacts/silver/synthetic_ocr_ab_v001/summary.json")
    silver = json.loads(silver_summary_path.read_text(encoding="utf-8")) if silver_summary_path.is_file() else {}
    padova_silver_summary = Path("/data/GeoLogParser/artifacts/silver/unipd_field_silver_v003/summary.json")
    padova_silver = json.loads(padova_silver_summary.read_text(encoding="utf-8")) if padova_silver_summary.is_file() else {}
    swissgeol_gold_manifests = [
        Path("/data/GeoLogParser/datasets/public/swissgeol_thurgau_paired_v002/gold_interval_manifest_v002.jsonl"),
        Path("/data/GeoLogParser/datasets/public/swissgeol_thurgau_paired_v003/gold_interval_manifest_v003.jsonl"),
        ROOT / "datasets/manifests/usgs142_interval_gold_v001.jsonl",
        ROOT / "datasets/manifests/usgs144_interval_gold_v001.jsonl",
        ROOT / "datasets/manifests/usgs_raft_river_interval_gold_v001.jsonl",
        ROOT / "datasets/manifests/bgs_offshore_gold_v001.jsonl",
    ]
    swissgeol_gold_rows = [
        json.loads(line)
        for manifest in swissgeol_gold_manifests if manifest.is_file()
        for line in manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    authoritative_gold_documents = len(swissgeol_gold_rows)
    authoritative_gold_intervals = sum(
        int(row.get("interval_count", len(row.get("intervals", []))))
        for row in swissgeol_gold_rows
    )
    california_manifest = ROOT / "datasets/manifests/california_wcr_gold_v001.jsonl"
    california_rows = [
        json.loads(line) for line in california_manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ] if california_manifest.is_file() else []
    california_split_path = ROOT / "datasets/splits/california_wcr_gold_split_v001.json"
    california_split = (
        json.loads(california_split_path.read_text(encoding="utf-8"))
        if california_split_path.is_file() else {"test": []}
    )
    california_test_ids = set(california_split.get("test", []))
    california_test_rows = [row for row in california_rows if row.get("record_id") in california_test_ids]
    california_intervals = sum(int(row.get("interval_count", 0)) for row in california_rows)
    california_test_intervals = sum(int(row.get("interval_count", 0)) for row in california_test_rows)
    california_test_pages = sum(int(row.get("pdf_pages", 0)) for row in california_test_rows)
    california_test_counties = len({row.get("county") for row in california_test_rows if row.get("county")})
    california_external_manifest = ROOT / "datasets/manifests/california_wcr_gold_v002.jsonl"
    california_external_rows = [
        json.loads(line)
        for line in california_external_manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ] if california_external_manifest.is_file() else []
    california_external_intervals = sum(int(row.get("interval_count", 0)) for row in california_external_rows)
    california_external_pages = sum(int(row.get("pdf_pages", 0)) for row in california_external_rows)
    california_external_counties = len({row.get("county") for row in california_external_rows if row.get("county")})
    california_prospective_manifest = ROOT / "datasets/manifests/california_wcr_gold_v003.jsonl"
    california_prospective_rows = [
        json.loads(line)
        for line in california_prospective_manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ] if california_prospective_manifest.is_file() else []
    california_prospective_intervals = sum(int(row.get("interval_count", 0)) for row in california_prospective_rows)
    california_prospective_pages = sum(int(row.get("pdf_pages", 0)) for row in california_prospective_rows)
    california_prospective_counties = len({row.get("county") for row in california_prospective_rows if row.get("county")})
    california_v004_manifest = ROOT / "datasets/manifests/california_wcr_gold_v004.jsonl"
    california_v004_rows = [
        json.loads(line)
        for line in california_v004_manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ] if california_v004_manifest.is_file() else []
    california_v004_intervals = sum(int(row.get("interval_count", 0)) for row in california_v004_rows)
    california_v004_pages = sum(int(row.get("pdf_pages", 0)) for row in california_v004_rows)
    california_v004_counties = len({row.get("county") for row in california_v004_rows if row.get("county")})
    california_v005_manifest = ROOT / "datasets/manifests/california_wcr_gold_v005.jsonl"
    california_v005_rows = [
        json.loads(line)
        for line in california_v005_manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ] if california_v005_manifest.is_file() else []
    california_v005_intervals = sum(int(row.get("interval_count", 0)) for row in california_v005_rows)
    california_v005_pages = sum(int(row.get("pdf_pages", 0)) for row in california_v005_rows)
    california_v005_counties = len({row.get("county") for row in california_v005_rows if row.get("county")})
    transfer_summary_path = DATA_ROOT / "public/swissgeol_cross_canton_transfer_v002/dataset.json"
    transfer_summary = (
        json.loads(transfer_summary_path.read_text(encoding="utf-8"))
        if transfer_summary_path.is_file() else {}
    )
    readiness = json.loads((ROOT / "docs/generated/publication_readiness.json").read_text(encoding="utf-8"))
    publication_evidence_path = ROOT / "publication_evidence/manifest.json"
    publication_evidence = (
        json.loads(publication_evidence_path.read_text(encoding="utf-8"))
        if publication_evidence_path.is_file() else {}
    )
    linkage_path = ROOT / "docs/generated/publication_linkage_risk.json"
    linkage = json.loads(linkage_path.read_text(encoding="utf-8")) if linkage_path.is_file() else {}
    paper1_revision = json.loads((ROOT / "experiments/paper1/analysis/california_replication_statistics_v001.json").read_text(encoding="utf-8"))
    paper2_ablation = json.loads((ROOT / "experiments/paper2/analysis/california_candidate_pool_ablation_v001.json").read_text(encoding="utf-8"))
    paper2_risk = json.loads((ROOT / "experiments/paper2/analysis/california_document_risk_v001.json").read_text(encoding="utf-8"))
    modern_vlm = json.loads((ROOT / "experiments/paper1/analysis/modern_vlm_statistics_v001.json").read_text(encoding="utf-8"))
    vlm_assurance = json.loads((ROOT / "experiments/paper2/analysis/vlm_proposal_assurance_v001.json").read_text(encoding="utf-8"))
    paper3_spatial = json.loads((ROOT / "experiments/paper3/analysis/swissgeol_spatial_sensitivity_v001.json").read_text(encoding="utf-8"))
    rows = []
    for paper, value in sorted(readiness.get("paper_indexes", {}).items()):
        rows.append((paper, value.get("controlled_formal_experiment_count", 0), value.get("real_formal_experiment_count", 0), value.get("indexed_experiment_count", 0)))
    lines = [
        "<!-- AUTO-GENERATED by scripts/update_status.py; evidence dashboard, not a paper result. -->",
        "# GeoLogParser Status",
        "",
        "Status basis: current version-controlled working tree; experiment-level commits remain in each run record.",
        "",
        "## Data tiers",
        "",
        "| Tier | Count | Meaning |",
        "|---|---:|---|",
        "| Human-verified Gold | 0 | No project annotation has yet passed the independent human Ground-Truth gate |",
        f"| Published manual-transcription Gold | v001: {len(california_rows)} documents / {california_intervals} intervals with {len(california_test_rows)} documents / {california_test_intervals} intervals held out; v002: {len(california_external_rows)} / {california_external_intervals}; v003: {len(california_prospective_rows)} / {california_prospective_intervals}; v004: {len(california_v004_rows)} / {california_v004_intervals}; v005: {len(california_v005_rows)} / {california_v005_intervals} | USGS staff manually transcribed the paired WCR images and applied published depth-logic/completeness QC; project_human_reviewed=false |",
        f"| Authoritative interval Gold | {authoritative_gold_documents} documents / {authoritative_gold_intervals} intervals | Official source-agreement or explicit source-description interval references; interval boundaries only; no human annotation claimed |",
        f"| Authoritative transfer reference | {transfer_summary.get('frozen_documents', 0)} records / {transfer_summary.get('frozen_intervals', 0)} intervals | Same-object official database sequences from {transfer_summary.get('source_count', 0)} non-development cantons; complete page/database agreement unverified |",
        f"| Authoritative metadata | {readiness.get('paper_indexes', {}).get('paper1', {}).get('eligibility_counts', {}).get('formal_authoritative_metadata', 0)} runs | Official metadata paired with scans; no interval/lithology labels |",
        f"| Silver | {silver.get('source_item_count', 0) + padova_silver.get('source_item_count', 0)} | Machine-adjudicated candidate labels; not Gold |",
        f"| Synthetic | {synthetic.get('count', 0)} | Known programmatic labels; controlled experiments only |",
        f"| Registry entries | {len(registry.get('datasets', []))} | Candidate sources, not page/interval counts |",
        "",
        "## Automated compliance",
        "",
        "`review_type=automated_compliance_review`; `human_reviewed=false`.",
        "",
        "| Decision | Count |",
        "|---|---:|",
    ]
    for decision in ("ELIGIBLE", "ELIGIBLE_INTERNAL_ONLY", "AMBIGUOUS", "EXCLUDE"):
        lines.append(f"| {decision} | {compliance.get('decision_counts', {}).get(decision, 0)} |")
    lines.extend([
        "",
        "## Formal experiments",
        "",
        "| Paper | Controlled formal | Real formal | Indexed runs |",
        "|---|---:|---:|---:|",
    ])
    lines.extend(f"| {paper} | {controlled} | {real} | {indexed} |" for paper, controlled, real, indexed in rows)
    lines.extend([
        "",
        "## Publication evidence",
        "",
        f"- Exact indexed run/metrics files: {publication_evidence.get('result_core_file_count', 0)}.",
        f"- External aggregate/source-audit summaries: {publication_evidence.get('external_summary_file_count', 0)}.",
        f"- Public reanalysis input files: {publication_evidence.get('analysis_input_file_count', 0)}.",
        "- Source pages, model weights, record-level predictions/errors, logs, ROI artifacts, and complete databases remain outside the repository.",
        "- Fresh-clone paper audits verify the publication core; full immutable-run verification requires the controlled local evidence store.",
        "",
        "## Paper status",
        "",
        f"- Paper I: `SUBMISSION_READY_CANDIDATE` for five mutually record-disjoint published-manual-transcription California evaluations: v001 {len(california_test_rows)} documents/{california_test_intervals} intervals, v002 {len(california_external_rows)}/{california_external_intervals}, v003 {len(california_prospective_rows)}/{california_prospective_intervals}, v004 {len(california_v004_rows)} documents/{california_v004_counties} counties/{california_v004_pages} pages/{california_v004_intervals} intervals, and independent v005 {len(california_v005_rows)} documents/{california_v005_counties} counties/{california_v005_pages} pages/{california_v005_intervals} intervals. RapidOCR F1 was 0.390, 0.450, 0.383, 0.428, and 0.389; matched Tesseract comparisons exist for v001-v003. Additional real evidence includes a 26-source-group BGS historical-scan benchmark, a seven-document/608-page USGS Idaho source-scan disagreement audit, a 35-document/80-interval PDF-content-group held-out benchmark, a 46-record/3,332-interval source-disjoint official-database transfer panel, and a two-document/62-interval Raft River benchmark. The manuscript is scientifically closed; source-item rights and redistribution remain a separate pre-submission gate.",
        "- Paper II: `SUBMISSION_READY_CANDIDATE`. Five mutually disjoint California evaluations show unselective F1 gains with FCR 0.084–0.210, while the frozen addition-only policy accepted 43/43 and 39/39 correct additions on v004/v005. On BGS v001 development, v018 reached interval F1 0.1116, v021 reached 0.1213, v022 reached 0.1475, and the nested source-disjoint v023 continuous-depth refiner reached boundary F1 0.3381 and interval F1 0.1797 at ±0.05 m. The v024 page-family/risk route reached boundary F1 0.3313 and interval F1 0.1801 on the same development panel. The standalone semantic column-role diagnostic reached boundary/interval F1 0.3265/0.1458, with 0.4410/0.2825 on its 9-document explicit-Graphic-Log subset. Integrating these branches with nested source-disjoint family gating produced v028 overall boundary/interval F1 0.3475/0.1978 and five-fold means 0.3333/0.1841, versus v024 means 0.3182/0.1688; fold interval F1 ranged from 0 to 0.3810. The preregistered convergence gate passed, but the one-time BGS v003 external evaluation returned Boundary/Interval F1 0.0000/0.0000 and coverage 0.0000 because the unseen page family was routed to `abstain_unsupported_family`; no false positive or critical numerical error was emitted and no post-result tuning was performed. The BGS v003 result is a consumed external failure/abstention case, not evidence of generalization. An independent Swissgeol audit first showed 0/38 page-family coverage; conservative German aliases restored 8/38 development pages and 7/35 held-out pages. A development-fitted risk router then accepted 16/37 development and 15/35 held-out documents with observed exactness 1.0000; held-out interval precision/recall/F1 were 1.0000/0.4375/0.6087 and CNER was 0.0000. The held-out split was already consumed by the alias audit, so this is validation rather than untouched confirmation. Native positioned-text structural routing on the inspected 46-record Swissgeol panel reached routed boundary/interval F1 0.2662/0.1722 versus the identity-routed OCR baseline 0.1637/0.1000, reducing CNER from 0.3985 to 0.2265; this development-only branch is recorded in ADR-028. NativeMM direct and spatial heads remain `NO_GO` on BGS development (structural-evidence coverage 0.0–0.05 at the fixed operating points). The manuscript is scientifically closed; finite-sample risk bounds and the BGS failure prevent universal safety claims.",
        "- Paper II latest method gate: the native explicit-range expert remains auxiliary (Thurgau held-out Boundary/Interval F1 0.4943/0.3833 versus frozen OCR+constraint 0.9502/0.9211). Generic scanned-page contact grounding covered 17/34 BGS v001 pages but nested fusion reached only Boundary/Interval F1 0.2578/0.0866 with CNER 0.5448, below v028. Corrected NativeMM real-Gold SFT on v002r2 still yielded BGS development structural-evidence coverage 0.0000 and Boundary F1 0.0000. Description-row edge alignment was weakly discriminative (candidate AUC 0.5912); its nested route reached Boundary/Interval F1 0.3333/0.1786, below v028, and is also `NO_GO`. ADR-029/030/032 and the corrected SFT artifact retain all branches; the NativeMM branches did not consume BGS v003, which was later consumed once by v028.",
        "- Paper II finite-sample risk certificate: the frozen candidate-risk policy accepted 82 additions across the two prospective California v004/v005 cohorts with zero observed incorrect actions. The exact one-sided 95% upper action-FCR bound is 0.0359 (0.0546 at 99%), but the same actions occur in only 19 accepted documents, whose one-sided 95% upper worsening-rate bound is 0.1459. Thus a conditional 5% action-risk target is supported only under an iid-action assumption; a 5% document-level target and any cross-source safety guarantee remain `NO_GO`.",
        "- Paper II Qwen3.8-27B-FP8 NativeMM exploratory branch: visual-submodule LoRA forward/backward is verified on RTX 5090, but full multimodal FP8 SFT is `NOT_COMPLETED` because the active runtime lacks ms-swift/Unsloth and no local BF16 checkpoint is available. On three BGS v001 development pages, schema-valid structural graphs reached deterministic decoded Boundary F1 0.0526 at ±0.05 m (1 TP, 7 FP, 29 FN), below v028 0.3475; decision `NO_GO_PRIMARY`, retain as inference baseline/teacher. This branch did not consume BGS v003. See ADR-034.",
        "- Paper II Qwen3.8 FP8 staged joint-LoRA gate: single-5090 full-chain backward OOM at 29.776 GiB, five-GPU mixed 5090/2080 execution failed because fp8e4nv is unsupported on RTX 2080 Ti SM75, and CPU dequantized-from-FP8 execution exceeded 33 minutes before a gradient metric could be claimed. Decision `NO_GO_PRIMARY`; NVFP4/4bit not started. This branch did not consume BGS v003. See ADR-035 and `P2_QWEN38_FP8_JOINT_LORA_FEASIBILITY_GATE_001.json`.",
        "- Paper III: `SUBMISSION_READY_CANDIDATE` with a real structured-source controlled comparison, 35-document first/four-boundary surfaces, a real three-layer risk-aware volume diagnostic, 540 seeded repetitions across six error classes, an external 88-document page-coordinate evaluation, and a partial 35-document page-coordinate surface workflow. Risk-aware abstention reduced relative volume error from 0.1389 (raw) to 0.0824 and mean thickness MAE from 45.952 m to 34.808 m while accepting 15/35 documents and eliminating negative-thickness layers. Human time savings and page-derived collar accuracy are outside the quantitative claims; validated geological interpretation remains out of scope.",
        "",
        "## Boundary",
        "",
        "Synthetic and Silver outputs are never promoted to human Gold. The authoritative",
        "interval tier is limited to source-agreed numeric boundaries and is not described",
        "as human annotation. The California Gold tier is explicitly a published USGS manual",
        "transcription with published QC, not a new project annotation. Automated compliance is limited to captured licence/source",
        "evidence and text metadata; visual privacy, sensitive-location absence, and geological correctness remain",
        "unestablished without the corresponding evidence.",
        "",
    ])
    # Replace the accumulated project-log status section with the review-focused
    # scientific estimands.  Historical branch details remain in ADRs and the
    # result index rather than on the primary dashboard.
    publication_line = next(
        index for index, line in enumerate(lines)
        if line.startswith("- Source pages, model weights")
    )
    document_output_count = len(publication_evidence.get("document_outputs", []))
    lines[publication_line] = (
        f"- Pseudonymized document-level prediction/error files: {document_output_count}; "
        "source pages, model weights, raw OCR text/regions, and sensitive fields remain outside the repository."
    )
    if linkage:
        p2_linkage = linkage["paper2_candidate_pool"]
        p3_linkage = linkage["paper3_spatial_input"]
        lines.insert(
            publication_line + 1,
            f"- Linkage diagnostic: Paper II uniquely matched {p2_linkage['records_with_unique_exact_source_match']}/{p2_linkage['public_record_count']} depth signatures; "
            f"Paper III uniquely matched {p3_linkage['records_with_unique_exact_distance_fingerprint_match']}/{p3_linkage['public_record_count']} distance fingerprints. "
            "The inputs are linkable and are not claimed to be anonymous.",
        )
    start = lines.index("## Paper status")
    end = lines.index("## Boundary")
    p1_f1 = [
        paper1_revision["freezes"][key]["rapidocr_document_cluster_metrics"]["f1"]
        for key in ("v001", "v002_external", "v003_prospective", "v004_prospective", "v005_external")
    ]
    p1_zero = [
        paper1_revision["freezes"][key]["rapidocr_document_diagnostics"]["zero_output_document_rate"]
        for key in ("v001", "v002_external", "v003_prospective", "v004_prospective", "v005_external")
    ]
    qwen_runs = list(modern_vlm["analyses"].values())
    qwen_california = [row for row in qwen_runs if row["cohort"].startswith("California")]
    qwen_f1 = [row["document_cluster_metrics"]["f1"] for row in qwen_california]
    qwen_delta = [
        row["paired_against_frozen_rapidocr"]["delta_left_minus_right"]["f1"]["observed"]
        for row in qwen_california
    ]
    qwen_swiss = next(row for row in qwen_runs if row["cohort"] == "Swissgeol held-out")
    qwen_swiss_f1 = qwen_swiss["document_cluster_metrics"]["f1"]
    assurance_v003 = next(
        row for row in vlm_assurance["analyses"]
        if row["role"] == "held-out replication"
    )["point_estimates"]
    combined_risk = paper2_risk["combined_confirmatory"]
    full = paper3_spatial["full_support_comparison"]
    matched = paper3_spatial["matched_subset_comparison"]
    replacement = [
        "## Paper status", "",
        "- Paper I: `SUBMISSION_READY_CANDIDATE` as a provenance-aware multi-cohort/cross-source evaluation, not a comprehensive multilingual benchmark. "
        f"California RapidOCR F1 is {', '.join(f'{value:.3f}' for value in p1_f1)}; zero-output rates span "
        f"{min(p1_zero):.0%}–{max(p1_zero):.0%}. Frozen Qwen3.8 direct-VLM F1 spans {min(qwen_f1):.3f}–{max(qwen_f1):.3f} "
        f"with paired Qwen-minus-RapidOCR gains of {min(qwen_delta):.3f}–{max(qwen_delta):.3f}; its separately tiered Swissgeol source-agreement F1 is {qwen_swiss_f1:.3f}. "
        "Source-agreement, authoritative-metadata, Silver, and no-GT results remain visually and inferentially separate. The Qwen run identity is `Qwen/Qwen3.8-27B-FP8` served as `qwen38-fp8-tp4-mtp4-long` in fine-grained dynamic FP8 E4M3; the user-provided closed slot served `gpt-5.6-sol` but remained NO-GO after synthetic visual HTTP 502. A two-document Codex internal-vision audit matched 12/12 intervals but is exploratory and excluded from formal metrics.",
        "- Paper II: `SUBMISSION_READY_CANDIDATE` centered on same-candidate-pool sequence reconstruction and document-level correction risk. "
        f"Monotonic decoding gives v004/v005 F1 {paper2_ablation['freezes']['v004']['document_cluster_f1']['monotonic_sequence']['f1']:.3f}/"
        f"{paper2_ablation['freezes']['v005']['document_cluster_f1']['monotonic_sequence']['f1']:.3f}; the addition-only policy accepted "
        f"{combined_risk['accepted_action_count']} additions in {combined_risk['accepted_document_count']} documents, observed zero worsened documents, "
        f"and has a one-sided 95% document-level upper bound {combined_risk['document_level_one_sided_95_upper_bound']:.4f}. "
        f"The held-out VLM-proposal assurance rule reached selective precision {assurance_v003['accepted_precision']:.3f} at "
        f"coverage {assurance_v003['accepted_coverage']:.3f}, with {assurance_v003['accepted_count'] - assurance_v003['accepted_correct_count']} wrong accepted intervals; "
        "the BGS external zero-coverage result remains a concise transport failure. The Qwen proposal-assurance branch is complementary: it contributes visual recall, while positioned evidence and the risk layer contribute provenance, deterministic geometry, and abstention.",
        "- Paper III: `SUBMISSION_READY_CANDIDATE` as a sensitivity diagnostic, not a complete geological-model workflow. "
        f"Full-support relative volume error is raw/reread/risk {full['raw']['aggregate']['relative_absolute_volume_error']:.4f}/"
        f"{full['reread']['aggregate']['relative_absolute_volume_error']:.4f}/{full['risk']['aggregate']['relative_absolute_volume_error']:.4f}; "
        f"on the identical 15-document subset it is {matched['raw']['aggregate']['relative_absolute_volume_error']:.4f}/"
        f"{matched['reread']['aggregate']['relative_absolute_volume_error']:.4f}/{matched['risk']['aggregate']['relative_absolute_volume_error']:.4f}, "
        "showing that the apparent full-support risk gain is principally a selection/spatial-support effect.",
        "- Paper IV (C&G integrated): `SUBMISSION_READY_CANDIDATE` with a 5,843-word single narrative, 243-word structured abstract, four integrated main figures, and exactly three RQs. It foregrounds Qwen3.8-27B-FP8 California boundary-pair F1 0.896–0.932, held-out selective precision 0.993 at coverage 0.244, complete-document auto-acceptance 4/100, and the full-support versus matched-support spatial consequence. Paper 4 numeric bindings, claim-evidence audit, and C&G submission gate are green; rights, linkage, authorship, and final journal-format checks remain external gates.",
        "", "## Boundary", "",
    ]
    lines = lines[:start] + replacement + lines[end + 2:]
    output = ROOT / "docs/status.md"
    # Status is a committed generated Markdown artifact; avoid CRLF drift.
    output.write_bytes("\n".join(lines).encode("utf-8"))
    print(output)


if __name__ == "__main__":
    main()

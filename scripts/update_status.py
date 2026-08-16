#!/usr/bin/env python3
"""Regenerate the compact autonomous-research status dashboard."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import subprocess

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
    rows = []
    for paper, value in sorted(readiness.get("paper_indexes", {}).items()):
        rows.append((paper, value.get("controlled_formal_experiment_count", 0), value.get("real_formal_experiment_count", 0), value.get("indexed_experiment_count", 0)))
    git_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    lines = [
        "<!-- AUTO-GENERATED by scripts/update_status.py; evidence dashboard, not a paper result. -->",
        "# GeoLogParser Status",
        "",
        f"Git commit: `{git_commit or 'UNCOMMITTED'}`",
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
        "## Paper status",
        "",
        f"- Paper I: `RESULTS_AVAILABLE` for five mutually record-disjoint published-manual-transcription California evaluations: v001 {len(california_test_rows)} documents/{california_test_intervals} intervals, v002 {len(california_external_rows)}/{california_external_intervals}, v003 {len(california_prospective_rows)}/{california_prospective_intervals}, v004 {len(california_v004_rows)} documents/{california_v004_counties} counties/{california_v004_pages} pages/{california_v004_intervals} intervals, and independent v005 {len(california_v005_rows)} documents/{california_v005_counties} counties/{california_v005_pages} pages/{california_v005_intervals} intervals. RapidOCR F1 was 0.390, 0.450, 0.383, 0.428, and 0.389; matched Tesseract comparisons exist for v001-v003. Additional real evidence includes a 26-source-group BGS historical-scan benchmark, a seven-document/608-page USGS Idaho source-scan disagreement audit, a 35-document/80-interval PDF-content-group held-out benchmark, a 46-record/3,332-interval source-disjoint official-database transfer panel, and a two-document/62-interval Raft River benchmark. Representative multilingual source-disjoint manually transcribed Gold remains `NOT COMPLETED`.",
        "- Paper II: `EXPERIMENTING`. Five mutually disjoint California evaluations show unselective F1 gains with FCR 0.084–0.210, while the frozen addition-only policy accepted 43/43 and 39/39 correct additions on v004/v005. On BGS v001, v018 reached boundary precision/recall/F1 0.4940/0.2262/0.3103 and interval F1 0.1116 at ±0.05 m; its selective point accepted 43 boundaries with precision 0.9302, coverage 0.1172 and CNER 0.0698. The v021 multi-column event ablation raised interval F1 to 0.1213 but reduced boundary F1 to 0.2944; its selective precision/coverage/CNER were 0.9268/0.1117/0.0732. A pairwise interval ranker was rejected at interval F1 0.0445. The independent NativeMM branch was closed `NO_GO`: its best boundary F1 was 0.0789 and best interval F1 0.0312. BGS v002 remains unspent because no route met the 0.15 interval-F1 gate. External confirmation remains `NOT COMPLETED`.",
        "- Paper III: `MANUSCRIPT_IN_PROGRESS` with a real structured-source controlled comparison, 35-document first/four-boundary surfaces, a three-layer real stratigraphic volume diagnostic, 540 seeded repetitions across six error classes, an external 88-document page-coordinate evaluation, and a partial 35-document page-coordinate surface workflow; page-derived collar extraction, validated geological interpretation, and timed human study remain `NOT COMPLETED`.",
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
    output = ROOT / "docs/status.md"
    output.write_text("\n".join(lines), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()

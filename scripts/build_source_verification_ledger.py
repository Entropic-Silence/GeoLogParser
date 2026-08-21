#!/usr/bin/env python3
"""Build the source, licence, and public-release verification ledger.

The ledger is deliberately separate from ``data_registry.yaml``.  The registry
describes discovery/acquisition; this ledger records every source that can
appear in an experiment, including sources whose rights or content review is
still unresolved.  It binds local material to immutable manifest hashes so a
    human can repeat or audit the item-scoped rights check.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path("/data/GeoLogParser")


LOCAL_DIRS = {
    "mendeley_sedlog_drilling_cores_v002": DATA_ROOT / "datasets/public/mendeley_sedlog_drilling_cores_v002",
    "mendeley_subsurface_slopes_logs_v001": DATA_ROOT / "datasets/public/mendeley_subsurface_slopes_logs_v001",
    "mendeley_tiber_borehole_pdf_v001": DATA_ROOT / "datasets/public/mendeley_tiber_borehole_pdf_v001",
    "mendeley_guaiba_cores_pdf_v001": DATA_ROOT / "datasets/public/mendeley_guaiba_cores_pdf_v001",
    "unipd_levee_geotechnical_logs_v001": DATA_ROOT / "datasets/public/unipd_levee_geotech_v001",
    "unipd_levee_geotech_v001": DATA_ROOT / "datasets/public/unipd_levee_geotech_v001",
    "mendeley_borehole_log_collection_v002": DATA_ROOT / "datasets/public/mendeley_borehole_logs_v002",
    "bgs_onshore_borehole_records": DATA_ROOT / "datasets/public/bgs_authoritative_metadata_v001",
    "swissgeol_thurgau_paired_v001": DATA_ROOT / "datasets/public/swissgeol_thurgau_paired_v002",
    "swissgeol_thurgau_paired_v003": DATA_ROOT / "datasets/public/swissgeol_thurgau_paired_v003",
    "swissgeol_stgallen_paired_v001": DATA_ROOT / "datasets/public/swissgeol_stgallen_paired_v001",
    "swissgeol_bern_paired_v001": DATA_ROOT / "datasets/public/swissgeol_bern_paired_v001",
    "swissgeol_solothurn_paired_v001": DATA_ROOT / "datasets/public/swissgeol_solothurn_paired_v001",
    "swissgeol_vaud_paired_v001": DATA_ROOT / "datasets/public/swissgeol_vaud_paired_v001",
    "mendeley_binhai_cptu_borehole_v002": DATA_ROOT / "datasets/public/mendeley_binhai_cptu_borehole_v002",
    "mendeley_coal_boreholes_602_v001": DATA_ROOT / "datasets/public/mendeley_coal_boreholes_602_v001",
    "usgs_california_lithology_manual_v3_2025": DATA_ROOT / "datasets/public/usgs_california_lithology_v3_2025",
    "usgs_california_wcr_links_v6_2025": DATA_ROOT / "datasets/public/usgs_california_wcr_v6_2025",
}

LOCAL_DIRS["synthetic_borehole_logs_v002"] = DATA_ROOT / "datasets/synthetic_borehole_logs_v002"
LOCAL_DIRS["chinese_engineering_borehole_logs"] = DATA_ROOT / "datasets/candidates_quarantine/chinese_public_web_20260812"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inventory(path: Path) -> tuple[list[str], str | None, list[dict[str, Any]]]:
    """Return relative files, aggregate inventory hash, and selected file rows."""
    if not path.exists():
        return [], None, []
    files = sorted(p for p in path.rglob("*") if p.is_file())
    rows: list[dict[str, Any]] = []
    for item in files:
        rel = item.relative_to(path).as_posix()
        # Do not hash very large model/tool directories in this provenance
        # ledger; source datasets and their manifests are always hashed.
        if "/models/" in item.as_posix() or "/tools/" in item.as_posix():
            continue
        rows.append({"relative_path": rel, "size_bytes": item.stat().st_size, "sha256": sha256(item)})
    if not rows:
        return [], None, []
    canonical = "\n".join(f"{r['relative_path']}\t{r['size_bytes']}\t{r['sha256']}" for r in rows)
    return [r["relative_path"] for r in rows], hashlib.sha256(canonical.encode()).hexdigest(), rows


def evidence_paths(source_id: str, local_dir: Path | None) -> list[str]:
    paths: list[str] = ["datasets/data_registry.yaml"]
    if local_dir and local_dir.exists():
        for candidate in ("metadata/acquisition.json", "metadata/manifest.jsonl", "metadata/content_manifest.jsonl", "metadata/content_summary.json"):
            p = local_dir / candidate
            if p.exists():
                paths.append(str(p))
        if source_id == "bgs_onshore_borehole_records":
            paths.extend(str(p) for p in sorted((local_dir / "license").glob("*")) if p.is_file())
    if source_id == "chinese_engineering_borehole_logs":
        paths.extend([
            "configs/datasets/sanming_quarantine_panels_v001.jsonl",
            "docs/data_source_survey.md",
        ])
    if source_id == "swissgeol_boreholes_dataextraction_examples_v001":
        paths.append("/data/GeoLogParser/artifacts/source_surveys/swissgeol_example_groundtruth_audit_v001.json")
    if source_id in {
        "usgs_california_lithology_manual_v3_2025",
        "usgs_california_wcr_links_v6_2025",
    }:
        paths.extend([
            "/data/GeoLogParser/datasets/public/california_wcr_gold_v001/metadata/acquisition.json",
            "datasets/manifests/california_wcr_gold_v001.jsonl",
            "datasets/splits/california_wcr_gold_split_v001.json",
            "/data/GeoLogParser/datasets/public/california_wcr_gold_v002/metadata/acquisition.json",
            "datasets/manifests/california_wcr_gold_v002.jsonl",
            "datasets/splits/california_wcr_gold_split_v002.json",
            "/data/GeoLogParser/datasets/public/california_wcr_gold_v003/metadata/acquisition.json",
            "datasets/manifests/california_wcr_gold_v003.jsonl",
            "datasets/splits/california_wcr_gold_split_v003.json",
        ])
    if source_id in {
        "swissgeol_thurgau_paired_v001", "swissgeol_thurgau_paired_v003",
        "swissgeol_stgallen_paired_v001", "swissgeol_bern_paired_v001",
        "swissgeol_solothurn_paired_v001", "swissgeol_vaud_paired_v001",
    } and local_dir and local_dir.exists():
        paths.extend(str(local_dir / name) for name in ("dataset.json", "manifest.jsonl") if (local_dir / name).is_file())
        paths.extend(
            str(path) for pattern in ("pairing_audit_*.jsonl", "pairing_audit_summary_*.json", "gold_interval_manifest_*.jsonl")
            for path in sorted(local_dir.glob(pattern))
        )
    if source_id == "bgs_onshore_borehole_records" and local_dir and local_dir.exists():
        legacy = DATA_ROOT / "datasets/public/bgs_v001/license"
        paths.extend(str(p) for p in sorted(legacy.glob("*")) if p.is_file())
    return paths


def status_for(record: dict[str, Any], local_dir: Path | None) -> tuple[str, str, list[str]]:
    source_id = record["id"]
    status = str(record.get("status", "")).lower()
    signoff = record.get("public_release_signoff") or {}
    if signoff.get("status") == "verified_for_public_release":
        return (
            "HUMAN_VERIFIED_FOR_PUBLIC_RELEASE",
            "PUBLIC_RELEASE_APPROVED",
            ["retain the source-specific attribution, licence statement, and caveats recorded in the registry"],
        )
    if source_id == "chinese_engineering_borehole_logs":
        return "UNVERIFIED_SOURCE", "QUARANTINE_INTERNAL_ONLY", ["source URLs and item-level terms not captured", "project names/stamps/precise locations may be present"]
    if "conflict" in status or "embargo" in str(record.get("license", "")).lower():
        return "RIGHTS_CONFLICT", "QUARANTINE_INTERNAL_ONLY", ["repository metadata contains conflicting access/licence signals"]
    if "metadata_only" in status or "unverified" in status or "unclear" in status or "needs_manual" in status or "ambiguous" in status:
        return "UNVERIFIED_SOURCE", "USE_WITH_CAUTION" if local_dir and local_dir.exists() else "QUARANTINE_INTERNAL_ONLY", ["file-level rights or content scope are incomplete"]
    if "out_of_scope" in status:
        return "CLAIM_CAPTURED", "USE_WITH_CAUTION", ["format/content is outside the Phase-I page-image contract"]
    return "CLAIM_CAPTURED", "USE_WITH_CAUTION", ["licence claim is recorded from repository metadata; final item/content review remains required"]


def submission_decision(verification_status: str, local_dir: Path | None) -> str:
    """Map internal evidence states to the four-value pre-submission vocabulary."""
    if verification_status == "HUMAN_VERIFIED_FOR_PUBLIC_RELEASE":
        return "ELIGIBLE_PUBLIC_RELEASE"
    if verification_status == "SYNTHETIC_KNOWN_GT":
        return "ELIGIBLE_INTERNAL_ONLY"
    if verification_status == "CLAIM_CAPTURED" and local_dir and local_dir.exists():
        return "ELIGIBLE_INTERNAL_ONLY"
    return "AMBIGUOUS"


def build() -> dict[str, Any]:
    registry = yaml.safe_load((ROOT / "datasets/data_registry.yaml").read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = []
    for source in registry.get("datasets", []):
        sid = source["id"]
        local_dir = LOCAL_DIRS.get(sid)
        files, aggregate, rows = inventory(local_dir) if local_dir else ([], None, [])
        verification_status, decision, risks = status_for(source, local_dir)
        signoff = source.get("public_release_signoff")
        manifest_rows = [r for r in rows if "manifest" in r["relative_path"] or "acquisition" in r["relative_path"]]
        records.append({
            "source_id": sid,
            "source_name": source.get("name"),
            "url": source.get("url"),
            "source_url": source.get("url"),
            "doi": source.get("doi"),
            "publisher": source.get("source_organization"),
            "citation": source.get("name") + (f"; DOI: {source['doi']}" if source.get("doi") else ""),
            "retrieval_date": source.get("access_date"),
            "local_paths": [str(local_dir)] if local_dir and local_dir.exists() else [],
            "file_count_in_local_snapshot": len(files),
            "local_snapshot_inventory_sha256": aggregate,
            "manifest_evidence": manifest_rows,
            "access_method": source.get("access_status"),
            "terms_of_use": source.get("license_url"),
            "claimed_license": source.get("license"),
            "license_url": source.get("license_url"),
            "commercial_use": "reviewed_for_selected_release_scope" if signoff else "not_verified",
            "personal_information_risk": "human_review_complete_for_selected_release_scope" if signoff else "not_assessed",
            "sensitive_location_risk": "human_review_complete_for_selected_release_scope" if signoff else "not_assessed",
            "verification_status": verification_status,
            "internal_decision": decision,
            "decision": submission_decision(verification_status, local_dir),
            "risks": risks,
            "experiments_or_papers": source.get("paper_fit", []),
            "requires_human_check_before_submission": not bool(signoff),
            "author_public_release_signoff": signoff,
            "evidence": evidence_paths(sid, local_dir),
            "registry_status": source.get("status"),
            "registry_verification_notes": source.get("verification_notes"),
        })

    return {
        "ledger_version": "v002",
        "generated_utc": date.today().isoformat(),
        "purpose": "Item-scoped source, licence, attribution, and public-release verification for experiment and submission materials.",
        "policy": {
            "rights_unverified_experiment_use": "permitted for internal/provisional work under quarantine and explicit disclosure",
            "public_release_or_submission": "allowed only for records carrying an explicit verified_for_public_release author sign-off for the named release scope; all other records remain blocked",
            "machine_labels": "must be called Silver, pseudo-label, or machine-adjudicated; never human/expert Ground Truth without independent evidence",
            "ledger_is_not_a_licence": "recording a source does not grant permission to download, redistribute, or publish it",
        },
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "datasets/source_verification_ledger.yaml")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(build(), sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()

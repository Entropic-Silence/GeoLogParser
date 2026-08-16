#!/usr/bin/env python3
"""Evaluate a native-text structural expert and a reference-blind MoE route."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from geologparser.layout import locate_named_log_pages, predict_native_pdf_boundaries
from scripts.run_bgs_layout_method_development import boundary_metrics, interval_metrics


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit() -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
        capture_output=True, check=False,
    )
    return completed.stdout.strip() or None


def references(row: dict) -> list[float]:
    intervals = json.loads(Path(row["reference_path"]).read_text(encoding="utf-8"))["stratigraphy"]["intervals"]
    return sorted({float(value) for item in intervals for value in (item["top_depth_m"], item["bottom_depth_m"])})


def metrics(predictions: dict[str, list[float]], gold: dict[str, list[float]]) -> dict:
    return {
        "boundary": boundary_metrics(predictions, gold, 0.05),
        "interval": interval_metrics(predictions, gold, 0.05),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--ocr-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--maximum-native-risk", type=float, default=0.55)
    parser.add_argument("--minimum-ocr-count", type=int, default=3)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)

    manifest = load_jsonl(args.manifest)
    ocr_report = json.loads(args.ocr_report.read_text(encoding="utf-8"))
    ocr_predictions = {key: list(map(float, value)) for key, value in ocr_report["predictions"].items()}
    ocr_diagnostics = {row["record_id"]: row for row in ocr_report["diagnostics"]}
    native_predictions: dict[str, list[float]] = {}
    routed_predictions: dict[str, list[float]] = {}
    diagnostics = []
    route_counts: Counter[str] = Counter()
    started = time.perf_counter()

    for index, row in enumerate(manifest, 1):
        record_id = row["record_id"]
        reference_record = json.loads(Path(row["reference_path"]).read_text(encoding="utf-8"))
        target_name = str(reference_record.get("borehole", {}).get("name") or "")
        selected_pages = locate_named_log_pages(Path(row["pdf_path"]), target_name) if target_name else ()
        prediction = predict_native_pdf_boundaries(
            Path(row["pdf_path"]), pages=set(selected_pages) if selected_pages else None,
        )
        native = list(prediction.boundaries)
        native_predictions[record_id] = native
        ocr = ocr_predictions.get(record_id, [])
        ocr_pages = ocr_diagnostics.get(record_id, {}).get("page_reports", [])
        ocr_supported = any(
            page.get("selected") and int(page["selected"].get("count", 0)) >= args.minimum_ocr_count
            for page in ocr_pages
        )
        if prediction.status == "selected" and prediction.risk_score <= args.maximum_native_risk:
            route = "native_semantic_depth_expert"
            routed = native
        elif ocr_supported:
            route = "ocr_numeric_column_expert"
            routed = ocr
        else:
            route = "abstain"
            routed = []
        route_counts[route] += 1
        routed_predictions[record_id] = routed
        diagnostics.append({
            "record_id": record_id,
            "source_family": row["source_family"],
            "route": route,
            "target_name_for_page_alignment": target_name or None,
            "identity_aligned_pages": list(selected_pages),
            "native": prediction.to_dict(),
            "native_boundary_count": len(native),
            "ocr_boundary_count": len(ocr),
            "routed_boundary_count": len(routed),
        })
        print(f"[{index}/{len(manifest)}] {record_id} route={route} native={len(native)} ocr={len(ocr)}", flush=True)

    gold = {row["record_id"]: references(row) for row in manifest}
    by_source = {}
    for source in sorted({row["source_family"] for row in manifest}):
        ids = [row["record_id"] for row in manifest if row["source_family"] == source]
        source_gold = {key: gold[key] for key in ids}
        by_source[source] = {
            "document_count": len(ids),
            "native": metrics({key: native_predictions[key] for key in ids}, source_gold),
            "ocr": metrics({key: ocr_predictions[key] for key in ids}, source_gold),
            "routed": metrics({key: routed_predictions[key] for key in ids}, source_gold),
            "routes": dict(Counter(item["route"] for item in diagnostics if item["record_id"] in ids)),
        }

    report = {
        "experiment_id": args.experiment_id,
        "status": "completed_native_text_structural_moe_exploration",
        "method_version": "swissgeol_native_text_semantic_moe_v001",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit(),
        "platform": platform.platform(),
        "manifest": str(args.manifest),
        "manifest_sha256": sha256(args.manifest),
        "ocr_report": str(args.ocr_report),
        "ocr_report_sha256": sha256(args.ocr_report),
        "document_count": len(manifest),
        "page_count": sum(int(row["page_count"]) for row in manifest),
        "reference_ground_truth_tier": "AUTHORITATIVE_STRUCTURED_SOURCE",
        "page_database_interval_agreement_verified": False,
        "prediction_reference_conditioning": "borehole_identity_only_for_multi_page_alignment; interval values never used",
        "route_policy": {
            "maximum_native_risk": args.maximum_native_risk,
            "minimum_ocr_column_count": args.minimum_ocr_count,
            "priority": ["native_semantic_depth_expert", "ocr_numeric_column_expert", "abstain"],
        },
        "routes": dict(route_counts),
        "ocr": metrics(ocr_predictions, gold),
        "native": metrics(native_predictions, gold),
        "routed": metrics(routed_predictions, gold),
        "by_source": by_source,
        "diagnostics": diagnostics,
        "wall_time_seconds": time.perf_counter() - started,
        "limitations": [
            "Exploratory development evidence; the official database intervals are not verified as complete page-visible Ground Truth.",
            "The five-canton panel has already been inspected and is not an untouched external test.",
            "The native expert applies only to PDFs with positioned text and a localized cumulative-depth header.",
            "Authoritative borehole names are used only to align a target record to pages in multi-borehole reports; this is identity metadata, not interval supervision.",
            "Lithology and description extraction are outside this structural experiment.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "routes": report["routes"], "ocr": report["ocr"], "native": report["native"],
        "routed": report["routed"], "wall_time_seconds": report["wall_time_seconds"],
    }, indent=2))


if __name__ == "__main__":
    main()

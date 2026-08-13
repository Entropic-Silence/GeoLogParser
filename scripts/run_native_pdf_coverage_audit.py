#!/usr/bin/env python3
"""Run privacy-minimized regex and B3 layout coverage on native PDF pages."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
from importlib.metadata import version
from pathlib import Path

from geologparser.constraints import load_engine_config
from geologparser.native_pdf_coverage_audit import run_native_pdf_coverage_audit
from geologparser.pdf import PyMuPDFPanelTextAdapter
from geologparser.result_index import file_sha256


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = Path(
    "/data/GeoLogParser/datasets/public/mendeley_sedlog_drilling_cores_v002/metadata/content_manifest.jsonl"
)
DEFAULT_CONSTRAINTS = ROOT / "configs/constraints/default_v001.yaml"
REGEX_IMPLEMENTATION = ROOT / "src/geologparser/extraction/regex.py"
LAYOUT_IMPLEMENTATION = ROOT / "src/geologparser/layout/columns.py"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--content-summary", type=Path,
        help="frozen content summary that independently binds the manifest SHA256",
    )
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--dataset-id")
    parser.add_argument("--content-class")
    parser.add_argument("--phase1-scope", default="international_candidate")
    parser.add_argument("--x-bin-points", type=float, default=12.0)
    parser.add_argument("--minimum-unique-ranges", type=int, default=3)
    parser.add_argument("--constraint-config", type=Path, default=DEFAULT_CONSTRAINTS)
    arguments = parser.parse_args()
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
        capture_output=True, check=True,
    ).stdout.strip()
    content_summary_path = (
        arguments.content_summary
        if arguments.content_summary is not None
        else arguments.manifest.with_name("content_summary.json")
    )
    content_summary = json.loads(content_summary_path.read_text(encoding="utf-8"))
    manifest_sha256 = content_summary.get("content_manifest_sha256")
    if not isinstance(manifest_sha256, str) or len(manifest_sha256) != 64:
        raise ValueError("content summary lacks a valid content_manifest_sha256")
    if file_sha256(arguments.manifest) != manifest_sha256:
        raise ValueError("content manifest differs from frozen content summary")
    regex_sha256 = file_sha256(REGEX_IMPLEMENTATION)
    layout_sha256 = file_sha256(LAYOUT_IMPLEMENTATION)
    metadata = {
        "experiment_id": arguments.experiment_id,
        "git_commit": commit,
        "date": "2026-08-13",
        "dataset_version": "native_pdf_content_manifest_v001",
        "split_version": "audit_selection_no_training_no_ground_truth",
        "model": "direct_native_text_regex_plus_B3_positioned_layout_privacy_minimized",
        "model_revision": f"regex:{regex_sha256};layout:{layout_sha256}",
        "prompt_version": "not_applicable",
        "seed": None,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version(), "PyMuPDF": version("PyMuPDF")},
        "config": {
            "manifest_path": str(arguments.manifest.resolve()),
            "manifest_sha256": manifest_sha256,
            "content_summary_path": str(content_summary_path.resolve()),
            "content_summary_sha256": file_sha256(content_summary_path),
            "dataset_id_filter": arguments.dataset_id,
            "content_class_filter": arguments.content_class,
            "phase1_scope_filter": arguments.phase1_scope,
            "x_bin_points": arguments.x_bin_points,
            "minimum_unique_ranges": arguments.minimum_unique_ranges,
            "regex_implementation_sha256": regex_sha256,
            "layout_implementation_sha256": layout_sha256,
            "source_content_review_status": "unreviewed",
            "record_output_policy": "hash_and_presence_only",
            "constraint_config_path": str(arguments.constraint_config.resolve()),
            "constraint_config_sha256": file_sha256(arguments.constraint_config),
        },
    }
    run, metrics = run_native_pdf_coverage_audit(
        manifest_path=arguments.manifest,
        expected_manifest_sha256=manifest_sha256,
        results_root=arguments.results_root,
        run_metadata=metadata,
        adapter=PyMuPDFPanelTextAdapter(),
        constraint_engine=load_engine_config(arguments.constraint_config),
        dataset_id=arguments.dataset_id,
        content_class=arguments.content_class,
        phase1_scope=arguments.phase1_scope,
        x_bin_points=arguments.x_bin_points,
        minimum_unique_ranges=arguments.minimum_unique_ranges,
    )
    print(json.dumps({"result_path": str(run), "metrics": metrics}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

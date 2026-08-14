#!/usr/bin/env python3
"""Run the raster OCR interval baseline on the frozen Swissgeol Gold subset.

The reference is intentionally narrow: interval top, bottom, and thickness
values from official database records whose complete interval sequence agrees
with an explicit table visible in the paired official PDF.  Selection used
native PDF text, while this benchmark renders every page and uses only raster
OCR output for prediction.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
import platform
import re
import resource
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from geologparser.datasets.swissgeol import choose_interval_section
from geologparser.evaluation import (
    boundary_matched_interval_metrics,
    match_intervals_by_boundaries,
)
from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256, write_artifact_manifest


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = Path(
    "/data/GeoLogParser/datasets/public/swissgeol_thurgau_paired_v001"
)


def command_version(command: list[str]) -> str:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    output = (completed.stdout + "\n" + completed.stderr).strip()
    return output.splitlines()[0] if output else f"exit={completed.returncode}"


def natural_page_key(path: Path) -> tuple[int, str]:
    match = re.search(r"-(\d+)\.png$", path.name)
    return (int(match.group(1)) if match else 0, path.name)


def render_pdf(pdf: Path, output_root: Path, dpi: int) -> list[Path]:
    renderer = shutil.which("pdftoppm")
    if renderer is None:
        raise RuntimeError("pdftoppm is required")
    prefix = output_root / "page"
    completed = subprocess.run(
        [renderer, "-png", "-r", str(dpi), str(pdf), str(prefix)],
        text=True,
        capture_output=True,
        check=False,
    )
    pages = sorted(output_root.glob("page-*.png"), key=natural_page_key)
    if completed.returncode != 0 or not pages:
        raise RuntimeError(
            f"pdftoppm failed for {pdf} ({completed.returncode}): "
            f"{completed.stderr.strip()}"
        )
    return pages


def tesseract_text(image: Path, language: str, psm: int) -> str:
    executable = shutil.which("tesseract")
    if executable is None:
        raise RuntimeError("tesseract is required")
    completed = subprocess.run(
        [executable, str(image), "stdout", "-l", language, "--psm", str(psm)],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"tesseract failed for {image} ({completed.returncode}): "
            f"{completed.stderr.strip()}"
        )
    return completed.stdout


def interval_dict(top: float, bottom: float) -> dict:
    return {
        "top_depth_m": float(top),
        "bottom_depth_m": float(bottom),
        "thickness_m": float(bottom - top),
    }


def load_and_verify_reference(row: dict) -> tuple[float, list[dict]]:
    pdf = Path(row["pdf_path"])
    reference_path = Path(row["reference_path"])
    if file_sha256(pdf) != row["pdf_sha256"]:
        raise ValueError(f"source PDF hash mismatch: {pdf}")
    if file_sha256(reference_path) != row["reference_sha256"]:
        raise ValueError(f"reference hash mismatch: {reference_path}")
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    final_depth = float(reference["borehole"]["final_depth_m"])
    intervals = sorted(
        (
            interval_dict(item["top_depth_m"], item["bottom_depth_m"])
            for item in reference["stratigraphy"]["intervals"]
        ),
        key=lambda item: (item["top_depth_m"], item["bottom_depth_m"]),
    )
    expected_pairs = [
        [item["top_depth_m"], item["bottom_depth_m"]] for item in intervals
    ]
    if expected_pairs != row["source_interval_evidence"]:
        raise ValueError(
            f"frozen source-agreement evidence mismatch: {row['record_id']}"
        )
    if len(intervals) != row["interval_count"]:
        raise ValueError(f"interval count mismatch: {row['record_id']}")
    return final_depth, intervals


def metric_dicts(reference_documents: list[list[dict]], prediction_documents: list[list[dict]]) -> dict:
    return {
        name: result.to_dict()
        for name, result in boundary_matched_interval_metrics(
            reference_documents, prediction_documents, tolerance_m=0.05,
        ).items()
    }


def manifest_count_keys(name: str) -> tuple[str, str, str]:
    if "heldout" in name:
        return "heldout_documents", "heldout_intervals", "content_group_heldout"
    if "development" in name:
        return "development_documents", "development_intervals", "content_group_development"
    if "incremental" in name:
        return "incremental_gold_documents", "incremental_gold_intervals", "incremental_heldout"
    return "exact_full_interval_agreement_documents", "exact_full_interval_agreement_intervals", "source_agreement_all"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--gold-manifest", type=Path)
    parser.add_argument("--audit-summary", type=Path)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--render-dpi", type=int, default=250)
    parser.add_argument("--ocr-language", default="eng")
    parser.add_argument("--psm", type=int, default=3)
    parser.add_argument("--parser-version", default="choose_interval_section_v2")
    parser.add_argument("--split-version")
    arguments = parser.parse_args()
    if arguments.render_dpi <= 0:
        raise ValueError("render DPI must be positive")

    gold_manifest = arguments.gold_manifest or (
        arguments.dataset_root / "gold_interval_manifest_v001.jsonl"
    )
    audit_summary_path = arguments.audit_summary or (
        arguments.dataset_root / "pairing_audit_summary_v001.json"
    )
    dataset_summary_path = arguments.dataset_root / "dataset.json"
    rows = [
        json.loads(line)
        for line in gold_manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    audit_summary = json.loads(audit_summary_path.read_text(encoding="utf-8"))
    dataset_summary = json.loads(dataset_summary_path.read_text(encoding="utf-8"))
    expected_documents_key, expected_intervals_key, inferred_split = manifest_count_keys(
        gold_manifest.name,
    )
    if len(rows) != audit_summary[expected_documents_key]:
        raise ValueError("Gold manifest/document count does not match frozen audit summary")
    if sum(row["interval_count"] for row in rows) != audit_summary[expected_intervals_key]:
        raise ValueError("Gold manifest/interval count does not match frozen audit summary")
    if any(row.get("human_reviewed") is not False for row in rows):
        raise ValueError("benchmark requires explicit human_reviewed=false provenance")

    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout.strip()
    tesseract_revision = command_version(["tesseract", "--version"])
    poppler_revision = command_version(["pdftoppm", "-v"])
    started_utc = datetime.now(timezone.utc)
    run = create_run_directory(arguments.results_root, {
        "experiment_id": arguments.experiment_id,
        "git_commit": git_commit,
        "date": date.today().isoformat(),
        "dataset_version": dataset_summary["dataset_version"] + "__interval_gold",
        "split_version": arguments.split_version or inferred_split,
        "model": "B1_tesseract_ocr_conservative_interval_parser",
        "model_revision": tesseract_revision,
        "prompt_version": "not_applicable",
        "seed": 0,
        "hardware": {
            "device": "cpu",
            "processor": platform.processor(),
            "gpu_used": False,
        },
        "software": {
            "python": platform.python_version(),
            "tesseract": tesseract_revision,
            "poppler_pdftoppm": poppler_revision,
        },
        "config": {
            "render_dpi": arguments.render_dpi,
            "ocr_language": arguments.ocr_language,
            "tesseract_psm": arguments.psm,
            "parser": arguments.parser_version,
            "interval_match_tolerance_m": 0.05,
            "ground_truth_sha256": file_sha256(gold_manifest),
            "ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT",
            "prediction_reference_conditioning": "none",
            "pairing_audit_summary_sha256": file_sha256(audit_summary_path),
            "dataset_summary_sha256": file_sha256(dataset_summary_path),
            "evaluated_fields": [
                "interval.top_depth_m",
                "interval.bottom_depth_m",
                "interval.thickness_m",
            ],
            "excluded_fields": [
                "lithology",
                "description",
                "material_semantics",
                "source_bbox",
            ],
            "selection_limitation": (
                "source-agreement explicit-table pilot; documents were selected because the "
                "complete visible interval table agreed with the official database and are not "
                "a representative random sample"
            ),
            "prediction_input": "250-DPI page raster OCR only; native PDF text not used for prediction",
            "rights_review": dataset_summary["rights_review"],
        },
        "started_utc": started_utc.isoformat(),
    })
    ocr_text_root = run / "ocr_text"
    ocr_text_root.mkdir()
    prediction_rows: list[dict] = []
    reference_documents: list[list[dict]] = []
    prediction_documents: list[list[dict]] = []
    total_started = time.perf_counter()

    for row in rows:
        record_started = time.perf_counter()
        final_depth, references = load_and_verify_reference(row)
        with tempfile.TemporaryDirectory(prefix="geologparser-swissgeol-render-") as temporary:
            pages = render_pdf(Path(row["pdf_path"]), Path(temporary), arguments.render_dpi)
            page_texts = [
                tesseract_text(page, arguments.ocr_language, arguments.psm)
                for page in pages
            ]
        combined_text = "\n\n".join(
            f"===== PAGE {index:03d} =====\n{text}"
            for index, text in enumerate(page_texts, 1)
        )
        text_path = ocr_text_root / f"{row['record_id']}.txt"
        text_path.write_text(combined_text, encoding="utf-8")
        # The reference final depth is loaded only to validate the frozen
        # reference record. Prediction must remain independent of all reference
        # values; interval candidates are derived from raster OCR text alone.
        pairs = choose_interval_section(combined_text)
        predictions = [interval_dict(top, bottom) for top, bottom in pairs]
        matches, unmatched_references, unmatched_predictions = match_intervals_by_boundaries(
            references, predictions, tolerance_m=0.05,
        )
        exact = len(matches) == len(references) == len(predictions)
        prediction_rows.append({
            "record_id": row["record_id"],
            "borehole_id": row["borehole_id"],
            "pdf_path": row["pdf_path"],
            "pdf_sha256": row["pdf_sha256"],
            "reference_sha256": row["reference_sha256"],
            "ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT",
            "human_reviewed": False,
            "page_count": len(pages),
            "ocr_text_path": str(text_path.relative_to(run)),
            "ocr_text_sha256": file_sha256(text_path),
            "reference_intervals": references,
            "predicted_intervals": predictions,
            "matched_interval_count": len(matches),
            "unmatched_reference_indices": unmatched_references,
            "unmatched_prediction_indices": unmatched_predictions,
            "document_full_exact": exact,
            "latency_seconds": time.perf_counter() - record_started,
        })
        reference_documents.append(references)
        prediction_documents.append(predictions)

    wall_seconds = time.perf_counter() - total_started
    (run / "predictions.jsonl").write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in prediction_rows
        ),
        encoding="utf-8",
    )
    interval_metrics = metric_dicts(reference_documents, prediction_documents)
    document_exact_count = sum(row["document_full_exact"] for row in prediction_rows)
    documents_with_predictions = sum(bool(row["predicted_intervals"]) for row in prediction_rows)
    metrics = {
        "scope": "authoritative-interval benchmark evaluation",
        "reference_ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT",
        "prediction_reference_conditioning": "none",
        "reference_definition": (
            "official database interval boundaries with exact complete agreement to an explicit "
            "interval table in the paired official PDF"
        ),
        "human_reviewed": False,
        "document_count": len(rows),
        "page_count": sum(row["page_count"] for row in prediction_rows),
        "reference_interval_count": sum(len(items) for items in reference_documents),
        "predicted_interval_count": sum(len(items) for items in prediction_documents),
        "documents_with_predictions": documents_with_predictions,
        "document_full_exact": {
            "value": document_exact_count / len(rows) if rows else None,
            "numerator": document_exact_count,
            "denominator": len(rows),
        },
        "interval_metrics": interval_metrics,
        "evaluated_fields": [
            "interval.top_depth_m",
            "interval.bottom_depth_m",
            "interval.thickness_m",
        ],
        "excluded_reference_fields": [
            "lithology",
            "description",
            "material_semantics",
            "source_bbox",
        ],
        "selection_limitation": (
            "source-agreement explicit-table pilot; not a representative random sample of the "
            "Swissgeol candidate pool"
        ),
        "wall_time_seconds": wall_seconds,
        "latency_seconds_per_document_wall": wall_seconds / len(rows) if rows else None,
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (run / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    error_rows = []
    for row in prediction_rows:
        for index in row["unmatched_reference_indices"]:
            error_rows.append({
                "record_id": row["record_id"],
                "error_type": "missing_interval",
                "reference_index": index,
                "reference_interval": row["reference_intervals"][index],
            })
        for index in row["unmatched_prediction_indices"]:
            error_rows.append({
                "record_id": row["record_id"],
                "error_type": "spurious_interval",
                "prediction_index": index,
                "predicted_interval": row["predicted_intervals"][index],
            })
        if not row["predicted_intervals"]:
            error_rows.append({
                "record_id": row["record_id"],
                "error_type": "interval_section_not_detected",
            })
    (run / "errors.jsonl").write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in error_rows
        ),
        encoding="utf-8",
    )
    ended_utc = datetime.now(timezone.utc)
    (run / "run.log").write_text(
        "\n".join([
            f"started_utc={started_utc.isoformat()}",
            f"ended_utc={ended_utc.isoformat()}",
            f"documents={len(rows)}",
            f"pages={metrics['page_count']}",
            f"reference_intervals={metrics['reference_interval_count']}",
            f"predicted_intervals={metrics['predicted_interval_count']}",
            f"wall_seconds={wall_seconds:.6f}",
            "status=completed",
            "",
        ]),
        encoding="utf-8",
    )
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()

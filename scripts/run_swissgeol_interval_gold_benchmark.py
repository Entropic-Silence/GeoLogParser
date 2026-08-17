#!/usr/bin/env python3
"""Run the raster OCR interval baseline on frozen Swissgeol references.

The source-agreement mode uses official database intervals whose complete
sequence agrees with an explicit table in the paired PDF. The transfer mode
uses all acquired paired records from non-development cantons and therefore
measures agreement with the official database, not verified page Ground Truth.
Both modes render every page and use only raster OCR output for prediction.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from importlib.metadata import PackageNotFoundError, version as package_version
import json
import platform
import re
from geologparser.runtime_resources import peak_process_rss_kib
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
from geologparser.ocr import RapidOCROnnxAdapter


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = Path(
    "/data/GeoLogParser/datasets/public/swissgeol_thurgau_paired_v001"
)
DEFAULT_RAPIDOCR_MODELS = Path("/data/GeoLogParser/models/rapidocr")


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


def rapidocr_text(image: Path, adapter: RapidOCROnnxAdapter) -> str:
    """Serialize detected regions in approximate reading order.

    RapidOCR supplies polygons rather than page text.  The stable top/left
    ordering is deliberately simple and does not use reference values.
    """
    regions = sorted(
        adapter.extract(image),
        key=lambda region: (
            round(region.bbox[1] / 8.0),
            region.bbox[0],
            region.bbox[1],
        ),
    )
    return "\n".join(region.text for region in regions if region.text.strip())


def installed_version(package: str) -> str:
    try:
        return package_version(package)
    except PackageNotFoundError:
        return "unknown"


def interval_dict(top: float, bottom: float) -> dict:
    return {
        "top_depth_m": float(top),
        "bottom_depth_m": float(bottom),
        "thickness_m": float(bottom - top),
    }


def load_and_verify_reference(
    row: dict, require_source_agreement: bool = True,
) -> tuple[float | None, list[dict]]:
    pdf = Path(row["pdf_path"])
    reference_path = Path(row["reference_path"])
    if file_sha256(pdf) != row["pdf_sha256"]:
        raise ValueError(f"source PDF hash mismatch: {pdf}")
    if file_sha256(reference_path) != row["reference_sha256"]:
        raise ValueError(f"reference hash mismatch: {reference_path}")
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    final_depth_raw = reference["borehole"].get("final_depth_m")
    final_depth = float(final_depth_raw) if final_depth_raw is not None else None
    intervals = sorted(
        (
            interval_dict(item["top_depth_m"], item["bottom_depth_m"])
            for item in reference["stratigraphy"]["intervals"]
        ),
        key=lambda item: (item["top_depth_m"], item["bottom_depth_m"]),
    )
    if require_source_agreement:
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


def interval_f1(row: dict) -> float:
    matched = int(row["matched_interval_count"])
    denominator = len(row["reference_intervals"]) + len(row["predicted_intervals"])
    return (2.0 * matched / denominator) if denominator else 1.0


def content_group_summary(rows: list[dict]) -> dict:
    groups: dict[str, list[dict]] = {}
    for row in rows:
        groups.setdefault(row["content_group_id"], []).append(row)
    group_f1 = [
        sum(interval_f1(row) for row in group_rows) / len(group_rows)
        for group_rows in groups.values()
    ]
    exact_groups = sum(
        all(row["document_full_exact"] for row in group_rows)
        for group_rows in groups.values()
    )
    return {
        "content_group_count": len(groups),
        "duplicate_record_count": len(rows) - len(groups),
        "maximum_records_per_content_group": max(map(len, groups.values()), default=0),
        "groups_with_predictions": sum(
            any(row["predicted_intervals"] for row in group_rows)
            for group_rows in groups.values()
        ),
        "content_group_macro_interval_f1": (
            sum(group_f1) / len(group_f1) if group_f1 else None
        ),
        "content_group_full_exact": {
            "value": exact_groups / len(groups) if groups else None,
            "numerator": exact_groups,
            "denominator": len(groups),
        },
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
    parser.add_argument(
        "--ocr-backend", choices=("tesseract", "rapidocr"), default="tesseract",
    )
    parser.add_argument("--ocr-language", default="eng")
    parser.add_argument("--psm", type=int, default=3)
    parser.add_argument("--rapidocr-model-dir", type=Path, default=DEFAULT_RAPIDOCR_MODELS)
    parser.add_argument("--rapidocr-threads", type=int, default=4)
    parser.add_argument("--parser-version", default="choose_interval_section_v2")
    parser.add_argument("--split-version")
    parser.add_argument("--resume-ocr-run", type=Path)
    parser.add_argument(
        "--reference-mode",
        choices=("source_agreement_gold", "official_database_transfer"),
        default="source_agreement_gold",
    )
    arguments = parser.parse_args()
    if arguments.render_dpi <= 0:
        raise ValueError("render DPI must be positive")

    gold_manifest = arguments.gold_manifest or (
        arguments.dataset_root / (
            "manifest.jsonl" if arguments.reference_mode == "official_database_transfer"
            else "gold_interval_manifest_v001.jsonl"
        )
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
    audit_summary = (
        json.loads(audit_summary_path.read_text(encoding="utf-8"))
        if arguments.reference_mode == "source_agreement_gold" else None
    )
    dataset_summary = json.loads(dataset_summary_path.read_text(encoding="utf-8"))
    expected_documents_key, expected_intervals_key, inferred_split = manifest_count_keys(gold_manifest.name)
    if arguments.reference_mode == "source_agreement_gold":
        assert audit_summary is not None
        if len(rows) != audit_summary[expected_documents_key]:
            raise ValueError("Gold manifest/document count does not match frozen audit summary")
        if sum(row["interval_count"] for row in rows) != audit_summary[expected_intervals_key]:
            raise ValueError("Gold manifest/interval count does not match frozen audit summary")
    else:
        inferred_split = (
            f"non_thurgau_{dataset_summary.get('source_count', 0)}_source_"
            f"disjoint_transfer_{dataset_summary.get('dataset_version', 'unknown')}"
        )
        if dataset_summary.get("source_count", 0) < 2 or dataset_summary.get("development_source") != "Thurgau":
            raise ValueError("transfer dataset must contain multiple non-development sources")
    if any(row.get("human_reviewed") is not False for row in rows):
        raise ValueError("benchmark requires explicit human_reviewed=false provenance")

    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout.strip()
    poppler_revision = command_version(["pdftoppm", "-v"])
    rapidocr_adapter = None
    if arguments.ocr_backend == "tesseract":
        backend_model = "B1_tesseract_ocr_conservative_interval_parser"
        backend_revision = command_version(["tesseract", "--version"])
        backend_software = {"tesseract": backend_revision}
        backend_config = {
            "ocr_language": arguments.ocr_language,
            "tesseract_psm": arguments.psm,
        }
    else:
        rapidocr_adapter = RapidOCROnnxAdapter(
            model_dir=arguments.rapidocr_model_dir,
            intra_op_num_threads=arguments.rapidocr_threads,
        )
        model_hashes = {
            path.name: file_sha256(path)
            for path in sorted(arguments.rapidocr_model_dir.glob("*.onnx"))
        }
        if len(model_hashes) != 3:
            raise ValueError(
                f"expected three frozen RapidOCR ONNX models, found {len(model_hashes)}"
            )
        backend_model = "B1_rapidocr_onnx_ocr_conservative_interval_parser"
        backend_revision = (
            f"rapidocr_onnxruntime={installed_version('rapidocr-onnxruntime')};"
            f"onnxruntime={installed_version('onnxruntime')}"
        )
        backend_software = {
            "rapidocr_onnxruntime": installed_version("rapidocr-onnxruntime"),
            "onnxruntime": installed_version("onnxruntime"),
        }
        backend_config = {
            "rapidocr_model_dir": str(arguments.rapidocr_model_dir),
            "rapidocr_model_sha256": model_hashes,
            "rapidocr_threads": arguments.rapidocr_threads,
            "region_serialization": "stable_approximate_top_left_v001",
        }
    resume_run_config = None
    if arguments.resume_ocr_run is not None:
        resume_run_config = json.loads(
            (arguments.resume_ocr_run / "run.json").read_text(encoding="utf-8")
        )["config"]
        required_resume_config = {
            "render_dpi": arguments.render_dpi,
            "ocr_backend": arguments.ocr_backend,
            **backend_config,
        }
        mismatches = [
            key for key, value in required_resume_config.items()
            if resume_run_config.get(key) != value
        ]
        if mismatches:
            raise ValueError(
                "resume OCR configuration mismatch: " + ", ".join(mismatches)
            )
    started_utc = datetime.now(timezone.utc)
    run = create_run_directory(arguments.results_root, {
        "experiment_id": arguments.experiment_id,
        "git_commit": git_commit,
        "date": date.today().isoformat(),
        "dataset_version": dataset_summary["dataset_version"] + (
            "__interval_gold"
            if arguments.reference_mode == "source_agreement_gold"
            else "__interval_transfer"
        ),
        "split_version": arguments.split_version or inferred_split,
        "model": backend_model,
        "model_revision": backend_revision,
        "prompt_version": "not_applicable",
        "seed": 0,
        "hardware": {
            "device": "cpu",
            "processor": platform.processor(),
            "gpu_used": False,
        },
        "software": {
            "python": platform.python_version(),
            "poppler_pdftoppm": poppler_revision,
            **backend_software,
        },
        "config": {
            "render_dpi": arguments.render_dpi,
            "ocr_backend": arguments.ocr_backend,
            **backend_config,
            "parser": arguments.parser_version,
            "interval_match_tolerance_m": 0.05,
            "ground_truth_sha256": file_sha256(gold_manifest),
            "ground_truth_tier": (
                "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT"
                if arguments.reference_mode == "source_agreement_gold"
                else "AUTHORITATIVE_STRUCTURED_SOURCE"
            ),
            "prediction_reference_conditioning": "none",
            "pairing_audit_summary_sha256": (
                file_sha256(audit_summary_path)
                if arguments.reference_mode == "source_agreement_gold" else None
            ),
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
                "source-agreement explicit-table pilot; documents were selected because the complete visible interval table agreed with the official database and are not a representative random sample"
                if arguments.reference_mode == "source_agreement_gold"
                else f"all acquired paired documents from {dataset_summary.get('source_count', 0)} non-Thurgau cantons; official database intervals are not verified as complete page-visible Ground Truth"
            ),
            "reference_mode": arguments.reference_mode,
            "ocr_cache_key": (
                "visual_content_sha256_36dpi_grayscale"
                if arguments.reference_mode == "official_database_transfer"
                else "pdf_sha256"
            ),
            "prediction_input": (
                f"{arguments.render_dpi}-DPI page raster {arguments.ocr_backend} OCR only; "
                "native PDF text not used for prediction"
            ),
            "rights_review": dataset_summary["rights_review"],
            "resume_ocr_run": (
                str(arguments.resume_ocr_run) if arguments.resume_ocr_run else None
            ),
            "resume_ocr_run_json_sha256": (
                file_sha256(arguments.resume_ocr_run / "run.json")
                if arguments.resume_ocr_run else None
            ),
        },
        "started_utc": started_utc.isoformat(),
    })
    ocr_text_root = run / "ocr_text"
    ocr_text_root.mkdir()
    prediction_rows: list[dict] = []
    reference_documents: list[list[dict]] = []
    prediction_documents: list[list[dict]] = []
    ocr_cache: dict[str, tuple[str, int]] = {}
    total_started = time.perf_counter()

    for record_number, row in enumerate(rows, 1):
        record_started = time.perf_counter()
        final_depth, references = load_and_verify_reference(
            row, require_source_agreement=arguments.reference_mode == "source_agreement_gold",
        )
        content_group_id = row.get("visual_content_sha256", row["pdf_sha256"])
        cache_hit = content_group_id in ocr_cache
        resume_hit = False
        if cache_hit:
            combined_text, page_count = ocr_cache[content_group_id]
        elif (
            arguments.resume_ocr_run is not None
            and (arguments.resume_ocr_run / "ocr_text" / f"{row['record_id']}.txt").is_file()
        ):
            prior_text_path = (
                arguments.resume_ocr_run / "ocr_text" / f"{row['record_id']}.txt"
            )
            combined_text = prior_text_path.read_text(encoding="utf-8")
            page_count = int(row.get("page_count", combined_text.count("===== PAGE ")))
            ocr_cache[content_group_id] = (combined_text, page_count)
            resume_hit = True
        else:
            with tempfile.TemporaryDirectory(prefix="geologparser-swissgeol-render-") as temporary:
                pages = render_pdf(Path(row["pdf_path"]), Path(temporary), arguments.render_dpi)
                if arguments.ocr_backend == "tesseract":
                    page_texts = [
                        tesseract_text(page, arguments.ocr_language, arguments.psm)
                        for page in pages
                    ]
                else:
                    assert rapidocr_adapter is not None
                    page_texts = [rapidocr_text(page, rapidocr_adapter) for page in pages]
            page_count = len(page_texts)
            combined_text = "\n\n".join(
                f"===== PAGE {index:03d} =====\n{text}"
                for index, text in enumerate(page_texts, 1)
            )
            ocr_cache[content_group_id] = (combined_text, page_count)
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
            "ground_truth_tier": (
                "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT"
                if arguments.reference_mode == "source_agreement_gold"
                else "AUTHORITATIVE_STRUCTURED_SOURCE"
            ),
            "source_family": row.get("source_family"),
            "canton": row.get("canton"),
            "human_reviewed": False,
            "content_group_id": content_group_id,
            "ocr_cache_hit": cache_hit,
            "ocr_resume_hit": resume_hit,
            "page_count": page_count,
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
        print(
            f"[{record_number}/{len(rows)}] {row['record_id']} pages={page_count} "
            f"predictions={len(predictions)} cache_hit={cache_hit} resume_hit={resume_hit}",
            flush=True,
        )

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
        "scope": (
            "authoritative-interval benchmark evaluation"
            if arguments.reference_mode == "source_agreement_gold"
            else "source-disjoint authoritative-database interval transfer evaluation"
        ),
        "reference_ground_truth_tier": (
            "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT"
            if arguments.reference_mode == "source_agreement_gold"
            else "AUTHORITATIVE_STRUCTURED_SOURCE"
        ),
        "prediction_reference_conditioning": "none",
        "reference_definition": (
            "official database interval boundaries with exact complete agreement to an explicit interval table in the paired official PDF"
            if arguments.reference_mode == "source_agreement_gold"
            else "official database interval sequence paired to the same borehole object; page/database completeness agreement is unverified"
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
            "source-agreement explicit-table pilot; not a representative random sample of the Swissgeol candidate pool"
            if arguments.reference_mode == "source_agreement_gold"
            else f"{dataset_summary.get('source_count', 0)} acquired non-Thurgau canton collections; agreement includes document extraction error plus possible page/database source mismatch"
        ),
        "wall_time_seconds": wall_seconds,
        "pipeline_recompute_wall_time_seconds": wall_seconds,
        "latency_seconds_per_document_wall": (
            wall_seconds / len(rows)
            if rows and not any(row["ocr_resume_hit"] for row in prediction_rows)
            else None
        ),
        "latency_exclusion_reason": (
            "OCR artifacts resumed from a prior run; recompute wall time is not end-to-end latency"
            if any(row["ocr_resume_hit"] for row in prediction_rows) else None
        ),
        "peak_process_rss_kib": peak_process_rss_kib(),
        "ocr_unique_execution_count": len(ocr_cache),
        "ocr_cache_hit_count": sum(row["ocr_cache_hit"] for row in prediction_rows),
        "ocr_resume_hit_count": sum(row["ocr_resume_hit"] for row in prediction_rows),
    }
    if arguments.reference_mode == "official_database_transfer":
        metrics.update(content_group_summary(prediction_rows))
        source_metrics = {}
        for source_family in sorted({row["source_family"] for row in prediction_rows}):
            indexes = [
                index for index, row in enumerate(prediction_rows)
                if row["source_family"] == source_family
            ]
            source_references = [reference_documents[index] for index in indexes]
            source_predictions = [prediction_documents[index] for index in indexes]
            exact_count = sum(prediction_rows[index]["document_full_exact"] for index in indexes)
            source_metrics[source_family] = {
                "document_count": len(indexes),
                "reference_interval_count": sum(len(row) for row in source_references),
                "predicted_interval_count": sum(len(row) for row in source_predictions),
                "documents_with_predictions": sum(bool(row) for row in source_predictions),
                "document_full_exact": {
                    "value": exact_count / len(indexes),
                    "numerator": exact_count,
                    "denominator": len(indexes),
                },
                "interval_metrics": metric_dicts(source_references, source_predictions),
                **content_group_summary([prediction_rows[index] for index in indexes]),
            }
        metrics.update({
            "source_count": len(source_metrics),
            "source_metrics": source_metrics,
            "development_source": "Thurgau",
            "development_evaluation_overlap_count": 0,
            "page_database_interval_agreement_verified": False,
            "human_ground_truth_evidence": False,
        })
    (run / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    error_rows = []
    for row in prediction_rows:
        for index in row["unmatched_reference_indices"]:
            error_rows.append({
                "record_id": row["record_id"],
                "source_family": row.get("source_family"),
                "error_type": "missing_interval",
                "reference_index": index,
                "reference_interval": row["reference_intervals"][index],
            })
        for index in row["unmatched_prediction_indices"]:
            error_rows.append({
                "record_id": row["record_id"],
                "source_family": row.get("source_family"),
                "error_type": "spurious_interval",
                "prediction_index": index,
                "predicted_interval": row["predicted_intervals"][index],
            })
        if not row["predicted_intervals"]:
            error_rows.append({
                "record_id": row["record_id"],
                "source_family": row.get("source_family"),
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

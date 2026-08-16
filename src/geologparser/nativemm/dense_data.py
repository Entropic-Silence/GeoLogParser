"""Dense structural supervision for the NativeMM boundary detector.

The first generative NativeMM corpus grounded BGS labels on the bounding box of
the *printed number*.  That is useful provenance for a numeric candidate, but
it is not the graphical position of the geological boundary.  This module
instead projects authoritative depths through a reference-blind page scale and
stores the resulting page/crop geometry explicitly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image

from .data import load_jsonl, sha256_file, stable_fold, validate_training_source


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _crop_image(source: Path, output: Path, box: tuple[int, int, int, int]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as opened:
        opened.convert("RGB").crop(box).save(output, format="JPEG", quality=92, optimize=True)


def _synthetic_dense_rows(corpus_root: Path, output_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split in ("train", "development"):
        source_path = corpus_root / f"{split}.jsonl"
        for source in load_jsonl(source_path):
            if source["task_family"] != "boundary_grounding" or source["source_tier"] != "SYNTHETIC":
                continue
            target = json.loads(source["messages"][1]["content"])
            boundaries = target.get("boundaries", [])
            if len(boundaries) < 2:
                continue
            image_path = Path(source["images"][0])
            validate_training_source(image_path)
            with Image.open(image_path) as opened:
                width, height = opened.size
            boxes = [row["bbox"] for row in boundaries]
            x1 = max(0, int((min(box[0] for box in boxes) - 0.02) * width))
            x2 = min(width, int((max(box[2] for box in boxes) + 0.02) * width))
            y_values = [float(row["y"]) * height for row in boundaries]
            margin = max(24, round((max(y_values) - min(y_values)) * 0.035))
            y1 = max(0, round(min(y_values) - margin))
            y2 = min(height, round(max(y_values) + margin))
            if x2 - x1 < 64 or y2 - y1 < 64:
                continue
            crop_path = output_root / "images" / "synthetic" / f"{source['sample_id'].replace('::', '__')}.jpg"
            _crop_image(image_path, crop_path, (x1, y1, x2, y2))
            crop_height = y2 - y1
            dense_boundaries = [
                {
                    "y": round((float(row["y"]) * height - y1) / crop_height, 8),
                    "depth_m": float(row["depth"]),
                    "evidence_type": row.get("evidence_type", "synthetic_boundary"),
                }
                for row in boundaries
                if y1 <= float(row["y"]) * height <= y2
            ]
            rows.append({
                "sample_id": source["sample_id"],
                "image": str(crop_path.resolve()),
                "source_tier": "SYNTHETIC",
                "source_dataset": source["source_dataset"],
                "source_group": source["source_group"],
                "fold": stable_fold(source["source_group"]),
                "split": split,
                "boundaries": dense_boundaries,
                "geometry": {
                    "crop_bbox_page": [x1, y1, x2, y2],
                    "page_size": [width, height],
                    "depth_per_pixel": None,
                    "intercept_m": None,
                    "scale_rmse_m": 0.0,
                },
                "supervision": "programmatic_exact_graphical_boundary",
                "provenance": source["provenance"],
            })
    return rows


def _reference_depths(source: dict[str, Any]) -> list[float]:
    return sorted({
        float(value)
        for interval in source["intervals"]
        for value in (interval["top_depth_m"], interval["bottom_depth_m"])
    })


def _bgs_dense_rows(
    manifest_path: Path,
    analysis_path: Path,
    output_root: Path,
    *,
    minimum_normalized_y: float = 0.18,
    maximum_normalized_y: float = 0.98,
) -> list[dict[str, Any]]:
    sources = {row["record_id"]: row for row in load_jsonl(manifest_path)}
    validate_training_source(analysis_path)
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    source_run = Path(analysis["source_run"])
    predictions = {row["record_id"]: row for row in analysis["predictions"]}
    output: list[dict[str, Any]] = []
    for record_id, source in sources.items():
        prediction = predictions.get(record_id)
        if not prediction:
            continue
        pages = list(source["evaluation_pages"])
        calibrations = list(prediction.get("scale_calibrations", []))
        if len(pages) != len(calibrations):
            continue
        source_group = str(source.get("source_title") or record_id)
        fold = stable_fold(source_group)
        split = "development" if fold == 0 else "train"
        depths = _reference_depths(source)
        for page, calibration in zip(pages, calibrations):
            page_path = source_run / f"{record_id}_page-{page}.png"
            if not page_path.exists():
                continue
            with Image.open(page_path) as opened:
                width, height = opened.size
            slope = float(calibration["depth_per_pixel"])
            intercept = float(calibration["intercept_m"])
            if slope <= 0:
                continue
            projected = [
                (depth, (depth - intercept) / slope)
                for depth in depths
            ]
            projected = [
                (depth, y) for depth, y in projected
                if minimum_normalized_y * height <= y <= maximum_normalized_y * height
            ]
            if len(projected) < 2:
                continue
            top = min(y for _, y in projected)
            bottom = max(y for _, y in projected)
            margin = max(36, round((bottom - top) * 0.035))
            y1 = max(0, round(top - margin))
            y2 = min(height, round(bottom + margin))
            # Preserve the complete log panel.  The vertical crop removes title,
            # map and footer regions while retaining lithology and description.
            x1 = max(0, round(width * 0.025))
            x2 = min(width, round(width * 0.965))
            crop_path = output_root / "images" / "bgs" / f"{record_id}_page-{page}.jpg"
            _crop_image(page_path, crop_path, (x1, y1, x2, y2))
            crop_height = y2 - y1
            boundaries = [
                {
                    "y": round((y - y1) / crop_height, 8),
                    "depth_m": depth,
                    "evidence_type": "official_depth_projected_through_page_scale",
                }
                for depth, y in projected
            ]
            output.append({
                "sample_id": f"{record_id}::page-{page}::dense_boundary",
                "image": str(crop_path.resolve()),
                "source_tier": "GOLD_DERIVED_SPATIAL",
                "source_dataset": "bgs_offshore_gold_v001",
                "source_group": source_group,
                "fold": fold,
                "split": split,
                "boundaries": boundaries,
                "geometry": {
                    "crop_bbox_page": [x1, y1, x2, y2],
                    "page_size": [width, height],
                    "depth_per_pixel": slope,
                    "intercept_m": intercept,
                    "scale_rmse_m": float(calibration["rmse_m"]),
                    "source_page": page,
                },
                "supervision": "official_depth_scale_projected_graphical_position",
                "provenance": {
                    "source_hash": source["pdf_sha256"],
                    "source_page": page,
                    "calibration_route": calibration["route"],
                    "calibration_inliers": calibration["inlier_count"],
                    "reference_type": source["reference_type"],
                },
            })
    return output


def build_dense_boundary_corpus(
    output_root: Path,
    *,
    nativemm_corpus_root: Path,
    bgs_manifest: Path,
    bgs_analysis: Path,
) -> dict[str, Any]:
    """Build immutable dense-boundary train/development manifests."""
    output_root = output_root.resolve()
    if output_root.exists():
        raise FileExistsError(f"dense NativeMM corpus already exists: {output_root}")
    output_root.mkdir(parents=True)
    rows = _synthetic_dense_rows(nativemm_corpus_root, output_root)
    rows.extend(_bgs_dense_rows(bgs_manifest, bgs_analysis, output_root))
    rows.sort(key=lambda row: row["sample_id"])
    for split in ("train", "development"):
        _write_jsonl(output_root / f"{split}.jsonl", [row for row in rows if row["split"] == split])
    source_counts: dict[str, int] = {}
    split_counts: dict[str, int] = {}
    boundary_counts: dict[str, int] = {}
    for row in rows:
        source_counts[row["source_dataset"]] = source_counts.get(row["source_dataset"], 0) + 1
        split_counts[row["split"]] = split_counts.get(row["split"], 0) + 1
        boundary_counts[row["source_dataset"]] = boundary_counts.get(row["source_dataset"], 0) + len(row["boundaries"])
    summary = {
        "dataset_version": output_root.name,
        "sample_count": len(rows),
        "source_counts": source_counts,
        "boundary_counts": boundary_counts,
        "split_counts": split_counts,
        "label_definition": "official/programmatic boundary y, never numeric-text bbox",
        "bgs_manifest": str(bgs_manifest),
        "bgs_analysis": str(bgs_analysis),
        "nativemm_corpus_root": str(nativemm_corpus_root),
    }
    for split in ("train", "development"):
        path = output_root / f"{split}.jsonl"
        summary[f"{split}_sha256"] = sha256_file(path)
    (output_root / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary

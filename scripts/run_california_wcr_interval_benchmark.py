#!/usr/bin/env python3
"""Run frozen California WCR interval extraction baselines."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
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

from PIL import Image

from geologparser.evaluation import boundary_matched_interval_metrics, match_intervals_by_boundaries
from geologparser.experiment import create_run_directory
from geologparser.ocr import RapidOCROnnxAdapter
from geologparser.ocr.rapidocr import DEFAULT_MODEL_DIR, MODEL_FILENAMES
from geologparser.result_index import file_sha256, write_artifact_manifest


ROOT = Path(__file__).resolve().parents[1]
FT_TO_M = 0.3048
SINGLE_NUMBER = re.compile(r"^[\s|_]*(\d{1,4}(?:[.,]\d{1,2})?)[\s|_.,]*$")
PAIR_NUMBER = re.compile(
    r"^[\s|_]*(\d{1,4}(?:[.,]\d{1,2})?)\s*[-:/]\s*(\d{1,4}(?:[.,]\d{1,2})?)(.*)$"
)
GEOLOGY_TERMS = re.compile(
    r"(?:soil|clay|sand|gravel|granite|rock|shale|silt|stone|lava|fracture|boulder|cobble|caliche|limestone|basalt|formation|loam|mud)",
    re.I,
)


@dataclass(frozen=True)
class Region:
    text: str
    confidence: float
    bbox: tuple[float, float, float, float]

    @property
    def center_x(self) -> float:
        return (self.bbox[0] + self.bbox[2]) / 2

    @property
    def center_y(self) -> float:
        return (self.bbox[1] + self.bbox[3]) / 2

    @property
    def height(self) -> float:
        return self.bbox[3] - self.bbox[1]


def normalize_lithology(value: str) -> str:
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_number(text: str) -> float | None:
    match = SINGLE_NUMBER.fullmatch(text)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", "."))
    except ValueError:
        return None


def reference_intervals(row: dict) -> list[dict]:
    return [
        {
            "top_depth_m": float(item["top_depth_ft"]) * FT_TO_M,
            "bottom_depth_m": float(item["bottom_depth_ft"]) * FT_TO_M,
            "thickness_m": float(item["thickness_ft"]) * FT_TO_M,
            "lithology_raw": item["lithology_raw"],
            "lithology_normalized": normalize_lithology(item["lithology_raw"]),
        }
        for item in row["intervals"]
    ]


def render_pdf(pdf: Path, output: Path, dpi: int) -> list[tuple[int, Path]]:
    prefix = output / "page"
    completed = subprocess.run(
        ["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(prefix)],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(f"pdftoppm failed: {completed.stderr.strip()}")
    pages = []
    for path in sorted(output.glob("page-*.png")):
        match = re.search(r"-(\d+)\.png$", path.name)
        if match:
            pages.append((int(match.group(1)), path))
    if not pages:
        raise RuntimeError(f"no rendered pages for {pdf}")
    return pages


def rapidocr_regions(adapter: RapidOCROnnxAdapter, image: Path) -> list[Region]:
    return [
        Region(item.text, float(item.confidence or 0.0), tuple(item.bbox))
        for item in adapter.extract(image)
        if item.bbox is not None and item.text.strip()
    ]


def tesseract_regions(image: Path, psm: int) -> tuple[list[Region], str]:
    completed = subprocess.run(
        ["tesseract", str(image), "stdout", "-l", "eng", "--psm", str(psm), "tsv"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip())
    rows = completed.stdout.splitlines()
    if not rows:
        return [], completed.stdout
    header = rows[0].split("\t")
    output: list[Region] = []
    for raw in rows[1:]:
        values = raw.split("\t")
        if len(values) != len(header):
            continue
        row = dict(zip(header, values))
        text = row.get("text", "").strip()
        if not text:
            continue
        try:
            left, top = float(row["left"]), float(row["top"])
            width, height = float(row["width"]), float(row["height"])
            confidence = max(0.0, float(row["conf"]) / 100.0)
        except ValueError:
            continue
        output.append(Region(text, confidence, (left, top, left + width, top + height)))
    return output, completed.stdout


def anchor(regions: list[Region], width: int, height: int) -> tuple[float, float] | None:
    normalized = [(re.sub(r"[^a-z]", "", item.text.lower()), item) for item in regions]
    direct = [item for text, item in normalized if "geologiclog" in text or "welllog" in text]
    if direct:
        item = min(direct, key=lambda value: value.center_y)
        return item.center_x / width, item.bbox[3] / height
    log_regions = [item for text, item in normalized if text in {"log", "geologic", "formation"}]
    if log_regions:
        item = min(log_regions, key=lambda value: value.center_y)
        return item.center_x / width, item.bbox[3] / height
    return None


def row_candidates(regions: list[Region], width: int, height: int) -> list[dict]:
    page_anchor = anchor(regions, width, height)
    if page_anchor is not None:
        anchor_x, anchor_y = page_anchor
        if anchor_x < 0.45:
            x_min, x_max = 0.015, 0.49
        else:
            x_min, x_max = 0.45, 0.995
        y_min = max(0.08, anchor_y + 0.005)
    else:
        x_min, x_max, y_min = 0.05, 0.85, 0.18
    usable = [
        item for item in regions
        if x_min <= item.center_x / width <= x_max and y_min <= item.center_y / height <= 0.88
    ]
    numeric = [(item, parse_number(item.text)) for item in usable]
    numeric = [(item, value) for item, value in numeric if value is not None]
    candidates: list[dict] = []

    # Regions that contain both depths, such as "15-31" or "166-184F Sand".
    for item in usable:
        match = PAIR_NUMBER.fullmatch(item.text)
        if not match:
            continue
        top, bottom = float(match.group(1).replace(",", ".")), float(match.group(2).replace(",", "."))
        if not 0 <= top < bottom <= 5000:
            continue
        trailing = match.group(3).strip(" |_:;.,")
        candidates.append({
            "top": top, "bottom": bottom, "y": item.center_y / height,
            "x_top": item.bbox[0] / width, "x_bottom": item.bbox[0] / width,
            "description_x": item.bbox[2] / width, "description_seed": trailing,
            "confidence": item.confidence, "evidence_regions": [item],
        })

    # More common case: independent From and To regions on the same visual row.
    for left, top in numeric:
        same_row = [
            (right, bottom) for right, bottom in numeric
            if right.center_x > left.center_x
            and 0.012 * width <= right.center_x - left.center_x <= 0.14 * width
            and abs(right.center_y - left.center_y) <= max(8.0, 0.50 * max(left.height, right.height))
            and top < bottom <= 5000
        ]
        if not same_row:
            continue
        right, bottom = min(same_row, key=lambda pair: pair[0].center_x)
        candidates.append({
            "top": top, "bottom": bottom, "y": (left.center_y + right.center_y) / (2 * height),
            "x_top": left.bbox[0] / width, "x_bottom": right.bbox[0] / width,
            "description_x": right.bbox[2] / width, "description_seed": "",
            "confidence": min(left.confidence, right.confidence), "evidence_regions": [left, right],
        })

    # Deduplicate pair hypotheses before selecting the dominant table columns.
    unique: dict[tuple, dict] = {}
    for item in candidates:
        key = (round(item["top"], 3), round(item["bottom"], 3), round(item["y"], 3))
        if key not in unique or item["confidence"] > unique[key]["confidence"]:
            unique[key] = item
    candidates = list(unique.values())
    if not candidates:
        return []

    # Select a stable From/To column pair. This rejects most construction tables.
    clusters: dict[tuple[int, int], list[dict]] = {}
    for item in candidates:
        key = (round(item["x_top"] / 0.035), round(item["x_bottom"] / 0.035))
        clusters.setdefault(key, []).append(item)
    # A page can contain a later casing table with similar columns. Split every
    # column hypothesis into vertical runs before ranking; the first dense run
    # after a detected log heading is preferred over a longer construction table.
    runs: list[list[dict]] = []
    for cluster in clusters.values():
        ordered = sorted(cluster, key=lambda item: item["y"])
        cluster_runs: list[list[dict]] = []
        for item in ordered:
            if not cluster_runs or item["y"] - cluster_runs[-1][-1]["y"] > 0.055:
                cluster_runs.append([item])
            else:
                cluster_runs[-1].append(item)
        runs.extend(cluster_runs)
    eligible_runs = [run for run in runs if len(run) >= 2]
    if not eligible_runs:
        eligible_runs = runs
    if page_anchor is not None:
        selected = min(
            eligible_runs,
            key=lambda run: (
                max(0.0, run[0]["y"] - page_anchor[1]),
                -len(run),
                -sum(bool(GEOLOGY_TERMS.search(item["description_seed"])) for item in run),
            ),
        )
    else:
        selected = max(eligible_runs, key=len)

    description_cutoff = x_max * width
    selected = sorted(selected, key=lambda item: item["y"])
    for index, item in enumerate(selected):
        next_y = selected[index + 1]["y"] * height if index + 1 < len(selected) else item["y"] * height + 2.8 * max(r.height for r in regions)
        y_center = item["y"] * height
        x_start = item["description_x"] * width
        description_regions = [
            region for region in usable
            if region.bbox[0] >= x_start - 5
            and region.bbox[0] <= description_cutoff
            and region.center_y >= y_center - max(8.0, 0.55 * region.height)
            and region.center_y < next_y - max(1.0, 0.25 * region.height)
            and re.search(r"[A-Za-z]", region.text)
            and region not in item["evidence_regions"]
        ]
        description_regions.sort(key=lambda region: (region.center_y, region.bbox[0]))
        description = " ".join([item["description_seed"], *(region.text for region in description_regions)]).strip()
        description = re.sub(r"\s+", " ", description).strip(" |_:;.,-")
        item["description"] = description
        item["description_regions"] = description_regions
    return [item for item in selected if item.get("description") and re.search(r"[A-Za-z]", item["description"])]


def parse_regions(regions: list[Region], width: int, height: int, page: int, backend: str) -> list[dict]:
    output = []
    for item in row_candidates(regions, width, height):
        evidence = [*item["evidence_regions"], *item.get("description_regions", [])]
        output.append({
            "top_depth_m": item["top"] * FT_TO_M,
            "bottom_depth_m": item["bottom"] * FT_TO_M,
            "thickness_m": (item["bottom"] - item["top"]) * FT_TO_M,
            "lithology_raw": item["description"],
            "lithology_normalized": normalize_lithology(item["description"]),
            "source_page": page,
            "source_unit": "ft_bls",
            "evidence": {
                "backend": backend,
                "confidence": min(region.confidence for region in evidence),
                "regions": [
                    {"text": region.text, "confidence": region.confidence, "bbox": list(region.bbox)}
                    for region in evidence
                ],
            },
        })
    return output


def deduplicate(rows: list[dict]) -> list[dict]:
    output, seen = [], set()
    for row in sorted(rows, key=lambda item: (item["source_page"], item["top_depth_m"], item["bottom_depth_m"])):
        key = (round(row["top_depth_m"], 5), round(row["bottom_depth_m"], 5))
        if key not in seen:
            output.append(row)
            seen.add(key)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--backend", choices=("tesseract", "rapidocr"), required=True)
    parser.add_argument("--partition", choices=("development", "test"), required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "datasets/manifests/california_wcr_gold_v001.jsonl")
    parser.add_argument("--split", type=Path, default=ROOT / "datasets/splits/california_wcr_gold_split_v001.json")
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--psm", type=int, default=11)
    args = parser.parse_args()

    all_rows = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    split = json.loads(args.split.read_text(encoding="utf-8"))
    selected_ids = set(split[args.partition])
    manifest = [row for row in all_rows if row["record_id"] in selected_ids]
    if len(manifest) != len(selected_ids) or any(row["ground_truth_tier"] != "GOLD_PUBLISHED_MANUAL_TRANSCRIPTION" for row in manifest):
        raise ValueError("unexpected California WCR Gold manifest or split")
    for row in manifest:
        if file_sha256(Path(row["pdf_path"])) != row["pdf_sha256"]:
            raise ValueError(f"source PDF hash mismatch: {row['record_id']}")

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    tesseract_revision = subprocess.run(["tesseract", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    model_hashes = {name: file_sha256(DEFAULT_MODEL_DIR / filename) for name, filename in MODEL_FILENAMES.items()}
    model_revision = tesseract_revision if args.backend == "tesseract" else json.dumps(model_hashes, sort_keys=True)
    started = datetime.now(timezone.utc)
    run = create_run_directory(args.results_root, {
        "experiment_id": args.experiment_id,
        "git_commit": commit,
        "date": date.today().isoformat(),
        "dataset_version": "california_wcr_gold_v001",
        "split_version": split["split_version"] + f"_{args.partition}",
        "model": f"{args.backend}_generic_positioned_interval_parser_v001",
        "model_revision": model_revision,
        "prompt_version": "not_applicable",
        "seed": 0,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version(), "tesseract": tesseract_revision},
        "config": {
            "ground_truth_sha256": file_sha256(args.manifest),
            "split_sha256": file_sha256(args.split),
            "partition": args.partition,
            "prediction_reference_conditioning": "none",
            "ground_truth_tier": "GOLD_PUBLISHED_MANUAL_TRANSCRIPTION",
            "render_dpi": args.dpi,
            "tesseract_psm": args.psm,
            "unit_conversion": "feet_bls_to_meters_multiply_0.3048",
            "evaluated_fields": ["interval.top_depth_m", "interval.bottom_depth_m", "interval.thickness_m", "interval.lithology_normalized"],
            "reference_scope": "USGS-published verbatim manual transcriptions from DWR WCR images",
            "reference_doi": "10.5066/P9M85U0T",
            "rights": "CC0-1.0 transcriptions; publicly released redacted DWR report images retained locally",
        },
        "started_utc": started.isoformat(),
    })
    wall_started = time.perf_counter()
    adapter = RapidOCROnnxAdapter(intra_op_num_threads=4) if args.backend == "rapidocr" else None
    refs_by_doc, preds_by_doc, prediction_rows, errors = [], [], [], []
    for doc_index, row in enumerate(manifest, start=1):
        refs = reference_intervals(row)
        predictions = []
        evidence_rows = []
        with tempfile.TemporaryDirectory(prefix="geologparser-california-wcr-") as temporary:
            pages = render_pdf(Path(row["pdf_path"]), Path(temporary), args.dpi)
            for page_number, page_path in pages:
                with Image.open(page_path) as image:
                    width, height = image.size
                if args.backend == "rapidocr":
                    regions = rapidocr_regions(adapter, page_path)
                    raw_tsv = None
                else:
                    regions, raw_tsv = tesseract_regions(page_path, args.psm)
                parsed = parse_regions(regions, width, height, page_number, args.backend)
                predictions.extend(parsed)
                region_path = run / f"{row['record_id']}_page-{page_number}_regions.jsonl"
                region_path.write_text(
                    "".join(json.dumps({"bbox": list(item.bbox), "text": item.text, "confidence": item.confidence}, sort_keys=True) + "\n" for item in regions),
                    encoding="utf-8",
                )
                evidence = {"page": page_number, "ocr_regions_path": region_path.name, "ocr_regions_sha256": file_sha256(region_path)}
                if raw_tsv is not None:
                    tsv_path = run / f"{row['record_id']}_page-{page_number}.tsv"
                    tsv_path.write_text(raw_tsv, encoding="utf-8")
                    evidence.update({"ocr_tsv_path": tsv_path.name, "ocr_tsv_sha256": file_sha256(tsv_path)})
                evidence_rows.append(evidence)
        predictions = deduplicate(predictions)
        matches, missing, extra = match_intervals_by_boundaries(refs, predictions, tolerance_m=0.05)
        lith_correct = sum(
            refs[item.reference_index]["lithology_normalized"] == predictions[item.prediction_index]["lithology_normalized"]
            for item in matches
        )
        refs_by_doc.append(refs)
        preds_by_doc.append(predictions)
        prediction_rows.append({
            "record_id": row["record_id"],
            "county": row["county"],
            "pdf_sha256": row["pdf_sha256"],
            "ground_truth_tier": row["ground_truth_tier"],
            "source_human_transcribed": True,
            "project_human_reviewed": False,
            "reference_intervals": refs,
            "predicted_intervals": predictions,
            "matched_interval_count": len(matches),
            "matched_lithology_exact_count": lith_correct,
            "unmatched_reference_indices": missing,
            "unmatched_prediction_indices": extra,
            "document_boundary_exact": len(matches) == len(refs) == len(predictions),
            "document_full_exact": len(matches) == len(refs) == len(predictions) and lith_correct == len(matches),
            "evidence": evidence_rows,
        })
        errors.extend({"record_id": row["record_id"], "error_type": "missing_interval", "reference_index": index} for index in missing)
        errors.extend({"record_id": row["record_id"], "error_type": "spurious_interval", "prediction_index": index} for index in extra)
        errors.extend(
            {"record_id": row["record_id"], "error_type": "lithology_semantic_error", "reference_index": item.reference_index, "prediction_index": item.prediction_index}
            for item in matches
            if refs[item.reference_index]["lithology_normalized"] != predictions[item.prediction_index]["lithology_normalized"]
        )
        print(f"[{doc_index}/{len(manifest)}] {row['record_id']} refs={len(refs)} preds={len(predictions)} matches={len(matches)}")

    interval_metrics = boundary_matched_interval_metrics(refs_by_doc, preds_by_doc, tolerance_m=0.05)
    total_matches = sum(row["matched_interval_count"] for row in prediction_rows)
    total_lith_correct = sum(row["matched_lithology_exact_count"] for row in prediction_rows)
    metrics = {
        "scope": "human-GT benchmark evaluation",
        "reference_ground_truth_tier": "GOLD_PUBLISHED_MANUAL_TRANSCRIPTION",
        "reference_production": "USGS staff manually transcribed WCR images and applied published depth-logic and completeness QC",
        "prediction_reference_conditioning": "none",
        "project_human_reviewed": False,
        "partition": args.partition,
        "document_count": len(manifest),
        "county_count": len({row["county"] for row in manifest}),
        "page_count": sum(row["pdf_pages"] for row in manifest),
        "reference_interval_count": sum(len(rows) for rows in refs_by_doc),
        "predicted_interval_count": sum(len(rows) for rows in preds_by_doc),
        "documents_with_predictions": sum(bool(rows) for rows in preds_by_doc),
        "document_boundary_exact": {
            "value": sum(row["document_boundary_exact"] for row in prediction_rows) / len(prediction_rows),
            "numerator": sum(row["document_boundary_exact"] for row in prediction_rows),
            "denominator": len(prediction_rows),
        },
        "document_full_exact": {
            "value": sum(row["document_full_exact"] for row in prediction_rows) / len(prediction_rows),
            "numerator": sum(row["document_full_exact"] for row in prediction_rows),
            "denominator": len(prediction_rows),
        },
        "interval_metrics": {name: result.to_dict() for name, result in interval_metrics.items()},
        "matched_lithology_exact": {
            "value": total_lith_correct / total_matches if total_matches else None,
            "numerator": total_lith_correct,
            "denominator": total_matches,
        },
        "source_domain": "California DWR Well Completion Reports / USGS published manual lithology transcriptions",
        "selection_limitation": "County-diverse fixed sample restricted to continuous 5-60 interval records without source comments; development and test partitions are disjoint",
        "wall_time_seconds": time.perf_counter() - wall_started,
        "latency_seconds_per_document_wall": (time.perf_counter() - wall_started) / len(manifest),
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (run / "predictions.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in prediction_rows), encoding="utf-8")
    (run / "errors.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in errors), encoding="utf-8")
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run / "run.log").write_text(
        f"started_utc={started.isoformat()}\nbackend={args.backend}\npartition={args.partition}\ndocuments={len(manifest)}\nreference_intervals={metrics['reference_interval_count']}\npredicted_intervals={metrics['predicted_interval_count']}\nstatus=completed\n",
        encoding="utf-8",
    )
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()

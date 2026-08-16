"""Versioned multi-task corpus builder for PaperII-NativeMM."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_FROZEN_PATTERNS = (
    "bgs_offshore_gold_v002",
    "bgs_offshore_paired_v002",
    "california_wcr_gold_v004",
    "california_wcr_gold_v005",
    "P1_CALIFORNIA_WCR_V004",
    "P1_CALIFORNIA_WCR_V005",
)


class LeakageError(RuntimeError):
    """Raised when a frozen external source is requested for model development."""


@dataclass(frozen=True)
class NativeMMSample:
    sample_id: str
    image: str
    task_family: str
    source_tier: str
    source_dataset: str
    source_group: str
    split: str
    prompt_version: str
    supervision: str
    messages: list[dict[str, str]]
    provenance: dict[str, Any]

    def to_swift(self) -> dict[str, Any]:
        row = asdict(self)
        row["images"] = [row.pop("image")]
        return row


PROMPTS = {
    "column_roles": (
        "Identify only the semantic column or field regions that are visually supported. "
        "Use normalized [x1,y1,x2,y2] boxes and the controlled roles cumulative_depth, "
        "layer_thickness, sampling_depth, lithology, description, and depth_scale. Return JSON only."
    ),
    "boundary_grounding": (
        "Ground geological interval boundaries in the image. Return normalized boundary y positions "
        "and thin bounding boxes. Do not infer a depth that is not printed or scale-supported. Return JSON only."
    ),
    "depth_scale": (
        "Reconstruct visual depth-scale anchor points as normalized page y and printed depth pairs. "
        "Do not extrapolate missing labels. Return JSON only."
    ),
    "field_semantics": (
        "Classify visible borehole-log fields by semantic role and ground each field with a normalized box. "
        "Return only evidence present in the image as JSON."
    ),
    "interval_sequence": (
        "Reconstruct the ordered geological interval sequence. Preserve the source unit and original text. "
        "Use UNKNOWN rather than guessing. Return JSON only."
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_fold(value: str, folds: int = 5) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:8], 16) % folds


def validate_training_source(path: str | Path, frozen_patterns: Iterable[str] = DEFAULT_FROZEN_PATTERNS) -> None:
    normalized = str(Path(path).resolve()).lower()
    conflicts = [pattern for pattern in frozen_patterns if pattern.lower() in normalized]
    if conflicts:
        raise LeakageError(f"frozen external source is forbidden for NativeMM development: {path} ({conflicts})")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    validate_training_source(path)
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _field_value(field: dict[str, Any] | None) -> Any:
    return field.get("value") if isinstance(field, dict) else None


def _norm_bbox(box: Iterable[float], width: int, height: int) -> list[float]:
    x1, y1, x2, y2 = (float(value) for value in box)
    return [
        round(max(0.0, min(1.0, x1 / width)), 6),
        round(max(0.0, min(1.0, y1 / height)), 6),
        round(max(0.0, min(1.0, x2 / width)), 6),
        round(max(0.0, min(1.0, y2 / height)), 6),
    ]


def _messages(task_family: str, target: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"role": "user", "content": f"<image>\n{PROMPTS[task_family]}"},
        {"role": "assistant", "content": json.dumps(target, ensure_ascii=False, sort_keys=True)},
    ]


def _make_sample(
    *, sample_id: str, image: Path, task_family: str, source_tier: str,
    source_dataset: str, source_group: str, split: str, target: dict[str, Any],
    supervision: str, provenance: dict[str, Any],
) -> NativeMMSample:
    validate_training_source(image)
    return NativeMMSample(
        sample_id=sample_id,
        image=str(image.resolve()),
        task_family=task_family,
        source_tier=source_tier,
        source_dataset=source_dataset,
        source_group=source_group,
        split=split,
        prompt_version=f"nativemm_{task_family}_v001",
        supervision=supervision,
        messages=_messages(task_family, target),
        provenance=provenance,
    )


def _synthetic_targets(record: dict[str, Any], image: Path, degradation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    from PIL import Image

    with Image.open(image) as opened:
        width, height = opened.size
    count = len(record["intervals"])
    template = record["document"]["metadata"]["template_id"]
    base_width = 1400 if template.endswith("A") else 1200
    left, table_top, right = 60, 220, base_width - 60
    columns = [left, left + 170, left + 370, left + 570, right]
    body_top = table_top + 65
    body_bottom = body_top + count * 150
    rotation = float(degradation.get("rotation_angle_degrees") or 0.0)
    spatial_exact = abs(rotation) < 1e-9 and width == base_width
    intervals = []
    depths = []
    for item in record["intervals"]:
        top = float(_field_value(item["top_depth_m"]))
        bottom = float(_field_value(item["bottom_depth_m"]))
        depths.append(top)
        intervals.append({
            "top": top,
            "bottom": bottom,
            "thickness": float(_field_value(item["thickness_m"])),
            "unit": "m",
            "lithology": _field_value(item["lithology_raw"]),
            "description": _field_value(item["description_raw"]),
        })
    depths.append(float(_field_value(record["intervals"][-1]["bottom_depth_m"])))
    targets: dict[str, dict[str, Any]] = {
        "interval_sequence": {
            "task": "interval_sequence",
            "borehole_id": _field_value(record["borehole"]["borehole_id"]),
            "intervals": intervals,
        }
    }
    if spatial_exact:
        targets["column_roles"] = {
            "task": "column_roles",
            "regions": [
                {"role": "cumulative_depth", "bbox": _norm_bbox([columns[0], table_top, columns[1], body_bottom], width, height)},
                {"role": "cumulative_depth", "bbox": _norm_bbox([columns[1], table_top, columns[2], body_bottom], width, height)},
                {"role": "layer_thickness", "bbox": _norm_bbox([columns[2], table_top, columns[3], body_bottom], width, height)},
                {"role": "lithology", "bbox": _norm_bbox([columns[3], table_top, columns[4], body_bottom], width, height)},
                {"role": "description", "bbox": _norm_bbox([columns[3], body_top, columns[4], body_bottom], width, height)},
            ],
            "absent_roles": ["sampling_depth", "depth_scale"],
        }
        boundaries = []
        for index, depth in enumerate(depths):
            y = body_top + index * 150
            boundaries.append({
                "y": round(y / height, 6),
                "bbox": _norm_bbox([left, y - 4, right, y + 4], width, height),
                "depth": depth,
                "unit": "m",
                "evidence_type": "table_row_boundary",
            })
        targets["boundary_grounding"] = {"task": "boundary_grounding", "boundaries": boundaries}
        targets["depth_scale"] = {
            "task": "depth_scale",
            "scale_points": [{"y": row["y"], "depth": row["depth"], "unit": "m"} for row in boundaries],
        }
        fields = []
        for index, interval in enumerate(intervals):
            y1 = body_top + index * 150
            y2 = y1 + 150
            roles = (
                ("top_depth", columns[0], columns[1]),
                ("bottom_depth", columns[1], columns[2]),
                ("layer_thickness", columns[2], columns[3]),
                ("lithology_description", columns[3], columns[4]),
            )
            for role, x1, x2 in roles:
                fields.append({"role": role, "bbox": _norm_bbox([x1, y1, x2, y2], width, height), "row": index})
        targets["field_semantics"] = {"task": "field_semantics", "fields": fields}
    return targets


def build_synthetic_samples(manifest_path: Path) -> list[NativeMMSample]:
    rows = load_jsonl(manifest_path)
    dataset_name = manifest_path.parent.name
    # Keep the manifest version in provenance; never label a v002 render as v001.
    source_dataset = dataset_name
    output: list[NativeMMSample] = []
    for row in rows:
        image = Path(row["image_path"])
        label = Path(row["label_path"])
        validate_training_source(label)
        record = json.loads(label.read_text(encoding="utf-8"))
        template = str(row["template_id"])
        split = "development" if stable_fold(template) == 0 else "train"
        provenance = {
            "source_page": 1,
            "source_hash": row["image_sha256"],
            "label_hash": row["label_sha256"],
            "geometry_status": "exact_unrotated" if not row["degradation"].get("rotation_angle_degrees") else "sequence_only_rotated",
        }
        for task_family, target in _synthetic_targets(record, image, row["degradation"]).items():
            output.append(_make_sample(
                sample_id=f"{row['record_id']}::{task_family}", image=image, task_family=task_family,
                source_tier="SYNTHETIC", source_dataset=source_dataset,
                source_group=template, split=split, target=target,
                supervision="programmatic_exact", provenance=provenance,
            ))
    return output


def _sequence_target(source: dict[str, Any]) -> dict[str, Any]:
    intervals = []
    unit = str(source.get("unit") or "unknown")
    for item in source.get("intervals", []):
        if "top_depth_m" in item:
            top, bottom, thickness, output_unit = item["top_depth_m"], item["bottom_depth_m"], item.get("thickness_m"), "m"
        else:
            top, bottom, thickness, output_unit = item["top_depth_ft"], item["bottom_depth_ft"], item.get("thickness_ft"), "ft"
        intervals.append({
            "top": float(top), "bottom": float(bottom),
            "thickness": float(thickness) if thickness is not None else None,
            "unit": output_unit,
            "lithology": item.get("lithology_raw") or item.get("lithology_normalized"),
            "description": item.get("description_raw") or item.get("comments") or "",
        })
    return {"task": "interval_sequence", "borehole_id": source.get("borehole_id"), "source_unit": unit, "intervals": intervals}


def _stack_images(paths: list[Path], output: Path, *, maximum_width: int = 1600, gap: int = 16) -> tuple[list[dict[str, Any]], int, int]:
    from PIL import Image, ImageOps

    opened = []
    for path in paths:
        image = Image.open(path).convert("RGB")
        if image.width > maximum_width:
            ratio = maximum_width / image.width
            image = image.resize((maximum_width, max(1, round(image.height * ratio))))
        opened.append((path, image))
    width = max(image.width for _, image in opened)
    height = sum(image.height for _, image in opened) + gap * (len(opened) - 1)
    canvas = Image.new("RGB", (width, height), "white")
    segments = []
    y = 0
    for path, image in opened:
        x = (width - image.width) // 2
        canvas.paste(image, (x, y))
        segments.append({"source": str(path), "bbox": _norm_bbox([x, y, x + image.width, y + image.height], width, height)})
        y += image.height + gap
        image.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="JPEG", quality=90, optimize=True)
    return segments, width, height


def build_bgs_samples(manifest_path: Path, analysis_path: Path, output_root: Path) -> tuple[list[NativeMMSample], dict[str, Any]]:
    sources = {row["record_id"]: row for row in load_jsonl(manifest_path)}
    validate_training_source(analysis_path)
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    source_run = Path(analysis["source_run"])
    predictions = {row["record_id"]: row for row in analysis["predictions"]}
    output: list[NativeMMSample] = []
    matched_reference_count = 0
    reference_count = 0
    for record_id, source in sources.items():
        source_group = str(source.get("source_title") or record_id)
        split = "development" if stable_fold(source_group) == 0 else "train"
        page_paths = [source_run / f"{record_id}_page-{page}.png" for page in source["evaluation_pages"]]
        page_paths = [path for path in page_paths if path.exists()]
        if not page_paths:
            continue
        strip_path = output_root / "images" / "bgs" / f"{record_id}.jpg"
        segments, _, _ = _stack_images(page_paths, strip_path)
        output.append(_make_sample(
            sample_id=f"{record_id}::interval_sequence", image=strip_path, task_family="interval_sequence",
            source_tier="GOLD", source_dataset="bgs_offshore_gold_v001", source_group=source_group,
            split=split, target=_sequence_target(source), supervision="official_interval_sequence",
            provenance={"source_hash": source["pdf_sha256"], "pages": source["evaluation_pages"], "page_segments": segments},
        ))

        references = sorted({float(item["top_depth_m"]) for item in source["intervals"]} | {float(item["bottom_depth_m"]) for item in source["intervals"]})
        reference_count += len(references)
        candidates = predictions[record_id]["ranked_candidates"]
        selected = []
        used = set()
        for reference in references:
            options = [
                candidate for candidate in candidates
                if candidate["page"] in source["evaluation_pages"]
                and abs(float(candidate["value_m"]) - reference) <= 0.05
                and (candidate["page"], tuple(candidate["bbox"])) not in used
            ]
            if not options:
                continue
            best = max(options, key=lambda candidate: (float(candidate.get("probability") or 0.0), candidate["candidate_source"] == "printed_depth"))
            used.add((best["page"], tuple(best["bbox"])))
            selected.append((reference, best))
        matched_reference_count += len(selected)
        for page_path in page_paths:
            page = int(page_path.stem.rsplit("-", 1)[-1])
            from PIL import Image
            with Image.open(page_path) as opened:
                width, height = opened.size
            boundaries = [
                {
                    "y": round(((candidate["bbox"][1] + candidate["bbox"][3]) / 2) / height, 6),
                    "bbox": _norm_bbox(candidate["bbox"], width, height),
                    "depth": reference,
                    "unit": "m",
                    "evidence_type": candidate["candidate_source"],
                }
                for reference, candidate in selected if int(candidate["page"]) == page
            ]
            if len(boundaries) < 2:
                continue
            provenance = {
                "source_hash": source["pdf_sha256"], "source_page": page,
                "alignment": "official_depth_to_reference_blind_visual_candidate_at_0.05m",
            }
            output.append(_make_sample(
                sample_id=f"{record_id}::page-{page}::boundary_grounding", image=page_path,
                task_family="boundary_grounding", source_tier="GOLD_DERIVED_SPATIAL",
                source_dataset="bgs_offshore_gold_v001", source_group=source_group, split=split,
                target={"task": "boundary_grounding", "boundaries": boundaries},
                supervision="official_depth_machine_aligned_bbox", provenance=provenance,
            ))
            output.append(_make_sample(
                sample_id=f"{record_id}::page-{page}::depth_scale", image=page_path,
                task_family="depth_scale", source_tier="GOLD_DERIVED_SPATIAL",
                source_dataset="bgs_offshore_gold_v001", source_group=source_group, split=split,
                target={"task": "depth_scale", "scale_points": [{"y": row["y"], "depth": row["depth"], "unit": "m"} for row in boundaries]},
                supervision="official_depth_machine_aligned_bbox", provenance=provenance,
            ))
    return output, {
        "reference_boundary_count": reference_count,
        "spatially_aligned_reference_count": matched_reference_count,
        "structural_evidence_coverage": matched_reference_count / reference_count if reference_count else 0.0,
    }


def build_california_samples(manifest_paths: list[Path], output_root: Path, maximum_documents: int | None = None) -> list[NativeMMSample]:
    import pymupdf
    from PIL import Image

    sources: list[dict[str, Any]] = []
    for path in manifest_paths:
        sources.extend(load_jsonl(path))
    sources.sort(key=lambda row: row["record_id"])
    if maximum_documents is not None:
        sources = sources[:maximum_documents]
    output: list[NativeMMSample] = []
    render_root = output_root / "rendered" / "california"
    for source in sources:
        source_group = str(source.get("county") or "UNKNOWN_COUNTY")
        split = "development" if stable_fold(source_group) == 0 else "train"
        pdf_path = Path(source["pdf_path"])
        validate_training_source(pdf_path)
        page_paths = []
        document = pymupdf.open(pdf_path)
        for page_index, page in enumerate(document):
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(1.6, 1.6), alpha=False)
            page_path = render_root / source["record_id"] / f"page-{page_index + 1}.jpg"
            page_path.parent.mkdir(parents=True, exist_ok=True)
            Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples).save(page_path, quality=88)
            page_paths.append(page_path)
        document.close()
        strip_path = output_root / "images" / "california" / f"{source['record_id']}.jpg"
        segments, _, _ = _stack_images(page_paths, strip_path)
        output.append(_make_sample(
            sample_id=f"{source['record_id']}::interval_sequence", image=strip_path,
            task_family="interval_sequence", source_tier="GOLD",
            source_dataset="california_wcr_gold_development_v001_v003", source_group=source_group,
            split=split, target=_sequence_target(source), supervision="published_manual_interval_sequence",
            provenance={"source_hash": source["pdf_sha256"], "pages": list(range(1, len(page_paths) + 1)), "page_segments": segments},
        ))
    return output


def build_nativemm_corpus(
    output_root: Path,
    *,
    synthetic_manifest: Path,
    bgs_manifest: Path,
    bgs_analysis: Path,
    california_manifests: list[Path],
    maximum_california_documents: int | None = None,
) -> dict[str, Any]:
    output_root = output_root.resolve()
    if output_root.exists():
        raise FileExistsError(f"NativeMM corpus already exists: {output_root}")
    output_root.mkdir(parents=True)
    samples = build_synthetic_samples(synthetic_manifest)
    bgs_samples, bgs_stats = build_bgs_samples(bgs_manifest, bgs_analysis, output_root)
    samples.extend(bgs_samples)
    samples.extend(build_california_samples(california_manifests, output_root, maximum_california_documents))
    samples.sort(key=lambda row: row.sample_id)
    for split in ("train", "development"):
        path = output_root / f"{split}.jsonl"
        rows = [sample.to_swift() for sample in samples if sample.split == split]
        path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    task_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    split_counts: dict[str, int] = {}
    for sample in samples:
        task_counts[sample.task_family] = task_counts.get(sample.task_family, 0) + 1
        source_counts[sample.source_dataset] = source_counts.get(sample.source_dataset, 0) + 1
        split_counts[sample.split] = split_counts.get(sample.split, 0) + 1
    summary = {
        "dataset_version": output_root.name,
        "sample_count": len(samples),
        "task_counts": task_counts,
        "source_counts": source_counts,
        "split_counts": split_counts,
        "bgs_spatial_alignment": bgs_stats,
        "frozen_patterns": list(DEFAULT_FROZEN_PATTERNS),
        "california_development_manifests": [str(path) for path in california_manifests],
        "bgs_development_manifest": str(bgs_manifest),
        "synthetic_manifest": str(synthetic_manifest),
    }
    for split in ("train", "development"):
        path = output_root / f"{split}.jsonl"
        summary[f"{split}_sha256"] = sha256_file(path)
    (output_root / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary

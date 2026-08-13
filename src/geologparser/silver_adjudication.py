"""Field-level adjudication for heterogeneous extraction channels.

This module creates a machine-adjudicated Silver reference from two frozen
prediction channels and optional layout corroboration.  It deliberately keeps
unresolved values null and records all candidates rather than applying an
implicit correction.  The resulting labels are never human/expert labels.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import os
import shutil
import tempfile
from typing import Any, Iterable, Mapping, Sequence

from geologparser.constraints import default_engine
from geologparser.schema import validate_record


BOREHOLE_FIELDS = (
    "borehole_id", "project_name", "page_id", "x_coordinate", "y_coordinate",
    "coordinate_system", "collar_elevation_m", "final_depth_m",
    "groundwater_depth_m", "groundwater_elevation_m", "drilling_date",
)
INTERVAL_FIELDS = (
    "top_depth_m", "bottom_depth_m", "thickness_m", "stratum_code_raw",
    "stratum_code_normalized", "lithology_raw", "lithology_normalized",
    "description_raw", "description_normalized", "weathering", "color",
    "consistency_or_density", "moisture", "structure", "inclusions",
)
CRITICAL_FIELDS = {
    "borehole.borehole_id", "borehole.x_coordinate", "borehole.y_coordinate",
    "borehole.collar_elevation_m", "borehole.final_depth_m",
    "borehole.groundwater_depth_m", "borehole.groundwater_elevation_m",
    "interval.top_depth_m", "interval.bottom_depth_m", "interval.thickness_m",
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _unwrap(value: Any) -> Any:
    return value.get("value") if isinstance(value, Mapping) and "value" in value else value


def _number(value: Any) -> Decimal | None:
    value = _unwrap(value)
    if value is None or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _norm(value: Any, tolerance: Decimal = Decimal("0.01")) -> tuple[str, Any]:
    """Return a comparison key while preserving the original typed value."""
    value = _unwrap(value)
    if value is None:
        return ("missing", None)
    number = _number(value)
    if number is not None:
        # Decimal quantization gives stable comparisons across 15.0/15.00.
        quantum = tolerance if tolerance > 0 else Decimal("0.000001")
        return ("number", number.quantize(quantum))
    return ("text", " ".join(str(value).replace("–", "-").split()).casefold())


def _same(a: Any, b: Any) -> bool:
    ka, va = _norm(a)
    kb, vb = _norm(b)
    if ka == "missing" or kb == "missing":
        return ka == kb
    return ka == kb and va == vb


def _candidate(field: Mapping[str, Any] | None, source: str) -> dict[str, Any]:
    if not isinstance(field, Mapping):
        return {"source": source, "value": None, "source_text": None, "confidence": None}
    return {
        "source": source,
        "value": field.get("value"),
        "source_text": field.get("source_text"),
        "source_bbox": field.get("source_bbox"),
        "confidence": field.get("confidence"),
        "extraction_method": field.get("extraction_method"),
    }


def _select_field(
    a: Mapping[str, Any] | None,
    b: Mapping[str, Any] | None,
    c: Mapping[str, Any] | None,
    path: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Select conservatively and return an evidence-rich field envelope."""
    candidates = [_candidate(a, "extractor_a"), _candidate(b, "extractor_b"), _candidate(c, "layout_corroboration")]
    present = [item for item in candidates if item["value"] is not None]
    values = {source: item["value"] for source, item in ((x["source"], x) for x in present)}
    a_value, b_value = candidates[0]["value"], candidates[1]["value"]
    c_value = candidates[2]["value"]
    if not present:
        status, selected, confidence = "MISSING", None, None
    elif a_value is not None and b_value is not None and _same(a_value, b_value):
        status, selected, confidence = "AGREEMENT", a, 0.98
    elif c_value is not None and a_value is not None and _same(a_value, c_value):
        status, selected, confidence = "CORROBORATED_A", a, 0.90
    elif c_value is not None and b_value is not None and _same(b_value, c_value):
        status, selected, confidence = "CORROBORATED_B", b, 0.90
    elif a_value is None and b_value is not None:
        status, selected, confidence = "SINGLE_SOURCE_B", b, 0.65
    elif b_value is None and a_value is not None:
        status, selected, confidence = "SINGLE_SOURCE_A", a, 0.65
    elif c_value is not None:
        # C is a corroborator, not an independent answer when A/B conflict.
        status, selected, confidence = "DISAGREEMENT_UNRESOLVED", None, 0.20
    else:
        status, selected, confidence = "DISAGREEMENT_UNRESOLVED", None, 0.20

    base = deepcopy(dict(selected)) if isinstance(selected, Mapping) else {
        "value": None, "source_page": None, "source_bbox": None, "display_bbox": None,
        "source_text": None, "extraction_method": "derived", "confidence": None,
        "validation_status": "needs_review", "warning_codes": [],
    }
    base["value"] = _unwrap(selected) if selected is not None and not isinstance(selected, Mapping) else (selected.get("value") if isinstance(selected, Mapping) else None)
    # Selected records use a derived envelope while retaining source evidence.
    if isinstance(selected, Mapping):
        base = deepcopy(dict(selected))
    base.setdefault("source_page", None)
    base.setdefault("source_bbox", None)
    base.setdefault("display_bbox", None)
    base.setdefault("source_text", None)
    base.setdefault("extraction_method", "derived")
    base.setdefault("confidence", None)
    base.setdefault("validation_status", "needs_review")
    base.setdefault("warning_codes", [])
    base["extraction_method"] = "derived"
    base["confidence"] = confidence
    warnings = list(dict.fromkeys([*base.get("warning_codes", []), f"SILVER_{status}"]))
    base["warning_codes"] = warnings
    base["validation_status"] = "passed" if status in {"AGREEMENT", "CORROBORATED_A", "CORROBORATED_B"} else "needs_review"
    decision = {
        "path": path,
        "status": status,
        "confidence": confidence,
        "selected_source": ("extractor_a" if selected is a else "extractor_b" if selected is b else None),
        "candidates": candidates,
        "critical": path in CRITICAL_FIELDS or path.endswith((".top_depth_m", ".bottom_depth_m", ".thickness_m")),
    }
    if status == "DISAGREEMENT_UNRESOLVED":
        decision["reason"] = "A/B values differ and no corroborating layout value resolves the conflict; value withheld"
    elif status == "MISSING":
        decision["reason"] = "all channels missing"
    else:
        decision["reason"] = "selected from agreement, corroboration, or single available channel"
    return base, decision


def _interval_map(record: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for index, item in enumerate(record.get("intervals", []) if isinstance(record, Mapping) else []):
        if not isinstance(item, Mapping):
            continue
        key = str(item.get("interval_id") or f"index_{index:04d}")
        result[key] = item
    return result


def adjudicate_records(
    item_id: str,
    record_a: Mapping[str, Any],
    record_b: Mapping[str, Any],
    record_c: Mapping[str, Any] | None,
    *, source_metadata: Mapping[str, Any], run_metadata: Mapping[str, Any],
) -> dict[str, Any]:
    """Adjudicate one aligned page and return a Silver row."""
    validate_record(record_a)
    validate_record(record_b)
    if record_c is not None:
        validate_record(record_c)
    output = deepcopy(record_b)
    decisions: list[dict[str, Any]] = []
    for field in BOREHOLE_FIELDS:
        selected, decision = _select_field(record_a.get("borehole", {}).get(field), record_b.get("borehole", {}).get(field), (record_c or {}).get("borehole", {}).get(field), f"borehole.{field}")
        output["borehole"][field] = selected
        decisions.append(decision)

    maps = [_interval_map(record) for record in (record_a, record_b, record_c or {})]
    keys = list(dict.fromkeys([*maps[0].keys(), *maps[1].keys(), *maps[2].keys()]))
    intervals_out = []
    for key in keys:
        source_items = [m.get(key, {}) for m in maps]
        interval = deepcopy(source_items[1] if source_items[1] else source_items[0] if source_items[0] else source_items[2])
        interval["interval_id"] = str(interval.get("interval_id") or key)
        for field in INTERVAL_FIELDS:
            selected, decision = _select_field(source_items[0].get(field), source_items[1].get(field), source_items[2].get(field), f"intervals[{interval['interval_id']}].{field}")
            interval[field] = selected
            decisions.append(decision)
        intervals_out.append(interval)
    output["intervals"] = intervals_out
    validate_record(output)
    constraints_before = {
        "A": [asdict(value) for value in default_engine().evaluate(record_a)],
        "B": [asdict(value) for value in default_engine().evaluate(record_b)],
        "C": [asdict(value) for value in default_engine().evaluate(record_c)] if record_c is not None else None,
    }
    constraints_after = [asdict(value) for value in default_engine().evaluate(output)]
    unresolved = [d for d in decisions if d["status"] == "DISAGREEMENT_UNRESOLVED"]
    critical_unresolved = [d for d in unresolved if d["critical"]]
    values = [d for d in decisions if d["status"] != "MISSING"]
    agreement_rate = sum(d["status"] in {"AGREEMENT", "CORROBORATED_A", "CORROBORATED_B"} for d in values) / len(values) if values else 0.0
    tier = "SILVER_HIGH_CONFIDENCE" if not critical_unresolved and not unresolved and values and all(r["passed"] for r in constraints_after if r["status"] != "not_evaluated") else "SILVER_UNCERTAIN"
    return {
        "item_id": item_id,
        "ground_truth_tier": tier,
        "silver_label": output,
        "agreement_rate": agreement_rate,
        "agreement_status": "AGREEMENT" if not unresolved else "FIELD_DISAGREEMENT",
        "confidence": min((d["confidence"] for d in values if d["confidence"] is not None), default=0.0),
        "field_decisions": decisions,
        "constraints_before": constraints_before,
        "constraints_after": constraints_after,
        "hard_case": bool(unresolved or any(not r["passed"] for r in constraints_after if r["status"] != "not_evaluated")),
        "human_ground_truth": False,
        "reference_type": "machine_adjudicated_silver_reference",
        "source_metadata": dict(source_metadata),
        "run_metadata": dict(run_metadata),
        "accuracy_metrics": None,
    }


def load_prediction_rows(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        item_id = str(row.get("item_id") or "")
        if not item_id or item_id in rows:
            raise ValueError(f"invalid or duplicate item_id in {path}: {item_id!r}")
        rows[item_id] = row
    return rows


def build_padova_silver(
    output_root: Path, *, source_manifest: Path, panel_manifest: Path,
    extractor_a_path: Path, extractor_b_path: Path, layout_path: Path | None,
) -> dict[str, Any]:
    output_root = Path(output_root).resolve()
    if output_root.exists():
        raise FileExistsError(f"Silver output already exists: {output_root}")
    a_rows = load_prediction_rows(extractor_a_path)
    b_rows = load_prediction_rows(extractor_b_path)
    c_rows = load_prediction_rows(layout_path) if layout_path is not None else {}
    panel_rows = {str(json.loads(line)["panel_id"]): json.loads(line) for line in panel_manifest.read_text(encoding="utf-8").splitlines() if line.strip()}
    common = sorted(set(a_rows) & set(b_rows))
    if not common:
        raise ValueError("no aligned prediction rows")
    run_metadata = {
        "extractor_a": {"path": str(extractor_a_path), "sha256": file_sha256(extractor_a_path)},
        "extractor_b": {"path": str(extractor_b_path), "sha256": file_sha256(extractor_b_path)},
        "layout_corroboration": (
            {"path": str(layout_path), "sha256": file_sha256(layout_path)}
            if layout_path is not None else None
        ),
        "protocol": "padova_field_adjudication_v001",
    }
    source_hash = file_sha256(source_manifest)
    panel_hash = file_sha256(panel_manifest)
    rows = []
    excluded_items = []
    for item_id in common:
        if not isinstance(a_rows[item_id].get("record"), Mapping) or not isinstance(b_rows[item_id].get("record"), Mapping):
            excluded_items.append({
                "item_id": item_id,
                "reason": "one or more extractor channels did not produce a schema-valid record",
                "extractor_a_record_present": isinstance(a_rows[item_id].get("record"), Mapping),
                "extractor_b_record_present": isinstance(b_rows[item_id].get("record"), Mapping),
            })
            continue
        panel = panel_rows.get(item_id, {})
        source_meta = {
            "item_id": item_id, "source_path": panel.get("source_path"), "source_sha256": panel.get("source_sha256"),
            "image_path": panel.get("rendered_path"), "image_sha256": panel.get("rendered_sha256"),
            "source_manifest": str(source_manifest), "source_manifest_sha256": source_hash,
            "panel_manifest": str(panel_manifest), "panel_manifest_sha256": panel_hash,
            "license_claim": "CC-BY-4.0", "license_verification_status": "recorded_for_pre_submission_human_check",
        }
        rows.append(adjudicate_records(item_id, a_rows[item_id]["record"], b_rows[item_id]["record"], c_rows.get(item_id, {}).get("record"), source_metadata=source_meta, run_metadata=run_metadata))
    temporary = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.", dir=output_root.parent))
    try:
        (temporary / "silver_labels.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
        # Evaluation-compatible projection.  The surrounding row retains the
        # full adjudication evidence in silver_labels.jsonl; this projection
        # makes the reference record explicit without changing its tier.
        references = []
        for row in rows:
            references.append({
                "annotation_schema_version": "silver_reference_v001",
                "annotation_id": row["item_id"],
                "annotation_status": "machine_adjudicated",
                "annotator_id": "MACHINE_ADJUDICATOR_C_V001",
                "ground_truth_tier": row["ground_truth_tier"],
                "human_ground_truth": False,
                "record": row["silver_label"],
                "reference_type": row["reference_type"],
                "source_metadata": row["source_metadata"],
                "adjudication_evidence": {
                    "agreement_rate": row["agreement_rate"],
                    "agreement_status": row["agreement_status"],
                    "confidence": row["confidence"],
                    "run_metadata": row["run_metadata"],
                },
            })
        (temporary / "silver_reference.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in references),
            encoding="utf-8",
        )
        (temporary / "hard_cases.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows if row["hard_case"]), encoding="utf-8")
        summary = {
            "dataset_version": "unipd_field_silver_v001", "reference_type": "machine_adjudicated_silver_reference",
            "source_item_count": len(rows), "high_confidence_count": sum(r["ground_truth_tier"] == "SILVER_HIGH_CONFIDENCE" for r in rows),
            "uncertain_count": sum(r["ground_truth_tier"] == "SILVER_UNCERTAIN" for r in rows), "hard_case_count": sum(r["hard_case"] for r in rows),
            "human_ground_truth_count": 0, "accuracy_metrics": None, "source_manifest_sha256": source_hash,
            "panel_manifest_sha256": panel_hash, "run_metadata": run_metadata,
            "aligned_item_count": len(common), "excluded_item_count": len(excluded_items), "excluded_items": excluded_items,
        }
        (temporary / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        artifacts = []
        for path in sorted(temporary.glob("*.json*")):
            artifacts.append({"path": path.name, "size_bytes": path.stat().st_size, "sha256": file_sha256(path)})
        (temporary / "artifact_manifest.json").write_text(json.dumps({
            "schema_version": "silver_artifacts_v001",
            "scope": "immutable field-level machine-adjudicated Silver artifacts",
            "artifacts": artifacts,
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, output_root)
        return summary
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

"""FastAPI backend for local, revisioned annotation review."""

from __future__ import annotations

import json
import csv
import io
from pathlib import Path
import tempfile
from typing import Any

from geologparser.annotation import (
    bind_human_display_bbox, human_empty_interval, revise_annotation, save_annotation,
    matching_attestations, validate_annotation, validate_annotator_id, validate_display_bbox,
    validate_display_bbox_edits,
)
from geologparser.annotation_export import ground_truth_gate
from geologparser.annotation_reread import run_annotation_reread
from geologparser.constraints import default_engine
from geologparser.export.tabular import write_xlsx
from geologparser.schema import validate_record
from geologparser.review import TimingEventStore, build_review_queue, review_items_to_dict
from geologparser.ocr import OCRBackendUnavailable, TesseractOCRAdapter


def create_app(
    annotation_root: Path, static_root: Path, timing_log: Path | None = None,
    reread_root: Path | None = None, reread_adapters=None,
    expert_annotator_ids: set[str] | None = None,
    allowed_annotator_ids: set[str] | None = None,
    fixed_annotator_id: str | None = None,
):
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import FileResponse, HTMLResponse, Response
    except ImportError as exc:
        raise RuntimeError("annotation UI requires geologparser[annotation]") from exc

    annotation_root = Path(annotation_root).resolve()
    static_root = Path(static_root).resolve()
    app = FastAPI(title="GeoLogParser Annotation API", version="v001")
    timing_store = TimingEventStore(timing_log or annotation_root / "events" / "review_timing.jsonl")
    reread_root = Path(reread_root or annotation_root / "rereading_runs").resolve()
    expert_annotator_ids = {
        validate_annotator_id(item) for item in (expert_annotator_ids or set())
    }
    allowed_annotator_ids = (
        {validate_annotator_id(item) for item in allowed_annotator_ids}
        if allowed_annotator_ids is not None else None
    )
    fixed_annotator_id = (
        validate_annotator_id(fixed_annotator_id)
        if fixed_annotator_id is not None else None
    )
    if allowed_annotator_ids is not None and not expert_annotator_ids <= allowed_annotator_ids:
        raise ValueError("expert annotator IDs must be included in the allowed annotator IDs")
    if (
        fixed_annotator_id is not None
        and allowed_annotator_ids is not None
        and fixed_annotator_id not in allowed_annotator_ids
    ):
        raise ValueError("fixed annotator ID must be included in the allowed annotator IDs")
    if reread_adapters is None:
        reread_adapters = [TesseractOCRAdapter(language="chi_sim+eng", psm=7)]

    def annotation_path(annotation_id: str) -> Path:
        safe = Path(annotation_id).name
        if safe != annotation_id:
            raise HTTPException(400, "invalid annotation id")
        path = annotation_root / f"{safe}.json"
        if not path.is_file():
            raise HTTPException(404, "annotation not found")
        return path

    def authorize_annotator(value: Any) -> str:
        if fixed_annotator_id is not None:
            if value is not None and value != fixed_annotator_id:
                raise ValueError("client annotator_id differs from the server-fixed actor")
            return fixed_annotator_id
        annotator_id = validate_annotator_id(value)
        if allowed_annotator_ids is not None and annotator_id not in allowed_annotator_ids:
            raise ValueError("annotator_id is not authorized for this annotation track")
        return annotator_id

    @app.get("/", response_class=HTMLResponse)
    def index():
        return (static_root / "index.html").read_text(encoding="utf-8")

    @app.get("/app.js")
    def javascript():
        return FileResponse(static_root / "app.js", media_type="application/javascript")

    @app.get("/style.css")
    def stylesheet():
        return FileResponse(static_root / "style.css", media_type="text/css")

    @app.get("/api/annotations")
    def list_annotations():
        items = []
        for path in sorted(annotation_root.glob("*.json")):
            annotation = json.loads(path.read_text(encoding="utf-8"))
            validate_annotation(annotation)
            gate_failures = ground_truth_gate(annotation)
            attestations = matching_attestations(annotation)
            items.append({
                "annotation_id": annotation["annotation_id"],
                "revision": annotation["revision"],
                "annotation_status": annotation["annotation_status"],
                "borehole_id": annotation["record"]["borehole"]["borehole_id"]["value"],
                "ground_truth_exportable": not gate_failures,
                "ground_truth_gate_failures": gate_failures,
                "valid_attestation_count": len(attestations),
                "valid_attestor_ids": sorted({item["annotator_id"] for item in attestations}),
                "has_valid_expert_attestation": any(
                    item["role"] == "expert" for item in attestations
                ),
            })
        return items

    @app.get("/api/status")
    def status():
        statuses: dict[str, int] = {}
        failure_counts: dict[str, int] = {}
        exportable = 0
        total = 0
        for path in sorted(annotation_root.glob("*.json")):
            annotation = json.loads(path.read_text(encoding="utf-8"))
            total += 1
            annotation_status = str(annotation["annotation_status"])
            statuses[annotation_status] = statuses.get(annotation_status, 0) + 1
            failures = ground_truth_gate(annotation)
            if not failures:
                exportable += 1
            for failure in failures:
                category = failure.split(":", 1)[0]
                failure_counts[category] = failure_counts.get(category, 0) + 1
        return {
            "annotation_count": total,
            "status_counts": dict(sorted(statuses.items())),
            "ground_truth_exportable_count": exportable,
            "ground_truth_complete": total > 0 and exportable == total,
            "ground_truth_gate_failure_counts": dict(sorted(failure_counts.items())),
            "fixed_annotator_id": fixed_annotator_id,
            "client_annotator_editable": fixed_annotator_id is None,
        }

    @app.get("/api/annotations/{annotation_id}")
    def get_annotation(annotation_id: str):
        return json.loads(annotation_path(annotation_id).read_text(encoding="utf-8"))

    @app.get("/api/annotations/{annotation_id}/image")
    def get_image(annotation_id: str):
        annotation = json.loads(annotation_path(annotation_id).read_text(encoding="utf-8"))
        image_path = Path(annotation["panel"]["rendered_path"]).resolve()
        if not image_path.is_file():
            raise HTTPException(404, "panel image not found")
        return FileResponse(image_path, media_type="image/png")

    @app.get("/api/exports/{annotation_id}")
    def export_annotation(annotation_id: str, format: str = "json"):
        annotation = json.loads(annotation_path(annotation_id).read_text(encoding="utf-8"))
        record = annotation["record"]
        gate_failures = ground_truth_gate(annotation)
        label = "GT" if not gate_failures else "DRAFT_NOT_GT"
        headers = {
            "Content-Disposition": f'attachment; filename="{annotation_id}_{label}.{format}"',
            "X-GeoLogParser-Ground-Truth": str(not gate_failures).lower(),
            "X-GeoLogParser-Annotation-Status": str(annotation["annotation_status"]),
        }
        if format == "json":
            return Response(
                json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                media_type="application/json", headers=headers,
            )
        if format == "csv":
            output = io.StringIO(newline="")
            fields = (
                "interval_id", "top_depth_m", "bottom_depth_m", "thickness_m",
                "stratum_code_raw", "stratum_code_normalized", "lithology_raw",
                "lithology_normalized", "description_raw", "description_normalized",
            )
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            for interval in record.get("intervals", []):
                writer.writerow({
                    name: (
                        interval.get(name, {}).get("value")
                        if isinstance(interval.get(name), dict) else interval.get(name)
                    )
                    for name in fields
                })
            # UTF-8 BOM keeps Chinese text readable in spreadsheet programs.
            return Response(
                "\ufeff" + output.getvalue(), media_type="text/csv; charset=utf-8", headers=headers,
            )
        if format == "xlsx":
            with tempfile.TemporaryDirectory(prefix="geologparser_export_") as directory:
                path = Path(directory) / "record.xlsx"
                write_xlsx([record], path)
                content = path.read_bytes()
            return Response(
                content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers=headers,
            )
        raise HTTPException(422, "format must be json, csv, or xlsx")

    @app.get("/api/exports/verified/all.jsonl")
    def export_verified_collection():
        annotations = []
        failures = {}
        for path in sorted(annotation_root.glob("*.json")):
            annotation = json.loads(path.read_text(encoding="utf-8"))
            item_failures = ground_truth_gate(annotation)
            if item_failures:
                failures[annotation["annotation_id"]] = item_failures
            annotations.append(annotation)
        if not annotations:
            raise HTTPException(409, "annotation collection is empty")
        if failures:
            raise HTTPException(409, {"message": "Ground Truth gate failed", "failures": failures})
        payload = "".join(
            json.dumps(annotation, ensure_ascii=False, sort_keys=True) + "\n"
            for annotation in annotations
        )
        return Response(
            payload, media_type="application/x-ndjson",
            headers={
                "Content-Disposition": 'attachment; filename="verified_ground_truth.jsonl"',
                "X-GeoLogParser-Ground-Truth": "true",
            },
        )

    @app.get("/api/review-queue")
    def review_queue():
        queue = []
        for path in sorted(annotation_root.glob("*.json")):
            annotation = json.loads(path.read_text(encoding="utf-8"))
            queue.extend(build_review_queue(annotation["annotation_id"], annotation["record"]))
        return review_items_to_dict(queue)

    @app.post("/api/review-sessions/start")
    def start_review(payload: dict[str, Any]):
        try:
            annotation_id = str(payload["annotation_id"])
            annotation_path(annotation_id)
            annotator_id = authorize_annotator(payload.get("annotator_id"))
            return timing_store.start(annotation_id, annotator_id)
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.post("/api/review-sessions/{session_id}/complete")
    def complete_review(session_id: str, payload: dict[str, Any]):
        try:
            return timing_store.complete(session_id, int(payload.get("corrected_fields", 0)))
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.post("/api/validate")
    def validate(payload: dict[str, Any]):
        record = payload.get("record", payload)
        try:
            validate_record(record)
        except Exception as exc:
            return {"schema_valid": False, "schema_error": str(exc), "constraints": []}
        results = default_engine().evaluate(record)
        return {
            "schema_valid": True,
            "schema_error": None,
            "constraints": [
                result.__dict__ | {"violations": [violation.__dict__ for violation in result.violations]}
                for result in results
            ],
        }

    @app.post("/api/interval-template")
    def interval_template(payload: dict[str, Any]):
        try:
            return human_empty_interval(
                str(payload["interval_id"]), int(payload["source_page"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.post("/api/annotations/{annotation_id}/reread")
    def reread_field(annotation_id: str, payload: dict[str, Any]):
        annotation = json.loads(annotation_path(annotation_id).read_text(encoding="utf-8"))
        if payload.get("base_revision") != annotation["revision"]:
            raise HTTPException(409, "revision conflict; reload before re-reading")
        try:
            if "record" in payload:
                validate_record(payload["record"])
                annotation = dict(annotation)
                annotation["record"] = payload["record"]
            bbox_pixels = payload.get("bbox_pixels")
            if bbox_pixels is not None:
                bbox_pixels = validate_display_bbox(bbox_pixels, annotation["panel"])
            return run_annotation_reread(
                annotation, str(payload["field_path"]), reread_adapters, reread_root,
                bbox_pixels=bbox_pixels,
                padding_pixels=int(payload.get("padding_pixels", 12)),
                scale=float(payload.get("scale", 3.0)),
            )
        except (KeyError, TypeError, ValueError, FileNotFoundError, OCRBackendUnavailable) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.post("/api/annotations/{annotation_id}/display-bbox")
    def bind_display_bbox(annotation_id: str, payload: dict[str, Any]):
        annotation = json.loads(annotation_path(annotation_id).read_text(encoding="utf-8"))
        if payload.get("base_revision") != annotation["revision"]:
            raise HTTPException(409, "revision conflict; reload before binding evidence")
        try:
            record = payload.get("record", annotation["record"])
            validate_record(record)
            annotator_id = authorize_annotator(payload.get("annotator_id"))
            return {
                "record": bind_human_display_bbox(
                    record, str(payload["field_path"]), payload["bbox_pixels"],
                    annotation["panel"], annotator_id,
                ),
                "persisted": False,
                "validation_status_changed": False,
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.get("/api/rereading/{annotation_id}/{run_id}/roi")
    def reread_roi(annotation_id: str, run_id: str):
        # Require a live annotation and simple path components before resolving
        # an immutable run artifact.
        annotation_path(annotation_id)
        if Path(run_id).name != run_id:
            raise HTTPException(400, "invalid re-read run id")
        result_path = (reread_root / annotation_id / run_id / "result.json").resolve()
        if reread_root not in result_path.parents or not result_path.is_file():
            raise HTTPException(404, "re-read result not found")
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if result.get("annotation_id") != annotation_id or result.get("run_id") != run_id:
            raise HTTPException(409, "re-read result identity mismatch")
        image_path = (result_path.parent / "roi.png").resolve()
        if not image_path.is_file() or result.get("crop_sha256") != __import__("hashlib").sha256(
            image_path.read_bytes()
        ).hexdigest():
            raise HTTPException(409, "re-read ROI hash mismatch")
        return FileResponse(image_path, media_type="image/png")

    @app.put("/api/annotations/{annotation_id}")
    def update_annotation(annotation_id: str, payload: dict[str, Any]):
        path = annotation_path(annotation_id)
        current = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("base_revision") != current["revision"]:
            raise HTTPException(409, "revision conflict; reload before saving")
        status = payload.get("annotation_status", "single_verified")
        try:
            annotator_id = authorize_annotator(payload.get("annotator_id"))
            validate_display_bbox_edits(
                current["record"], payload["record"], current["panel"],
                annotator_id,
            )
            revised = revise_annotation(
                current, payload["record"], annotator_id, str(status),
                actor_role="expert" if annotator_id in expert_annotator_ids else "reviewer",
            )
            save_annotation(revised, path)
        except Exception as exc:
            raise HTTPException(422, str(exc)) from exc
        return revised

    return app

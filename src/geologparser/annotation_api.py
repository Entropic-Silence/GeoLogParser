"""FastAPI backend for local, revisioned annotation review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from geologparser.annotation import revise_annotation, save_annotation, validate_annotation
from geologparser.constraints import default_engine
from geologparser.schema import validate_record


def create_app(annotation_root: Path, static_root: Path):
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import FileResponse, HTMLResponse
    except ImportError as exc:
        raise RuntimeError("annotation UI requires geologparser[annotation]") from exc

    annotation_root = Path(annotation_root).resolve()
    static_root = Path(static_root).resolve()
    app = FastAPI(title="GeoLogParser Annotation API", version="v001")

    def annotation_path(annotation_id: str) -> Path:
        safe = Path(annotation_id).name
        if safe != annotation_id:
            raise HTTPException(400, "invalid annotation id")
        path = annotation_root / f"{safe}.json"
        if not path.is_file():
            raise HTTPException(404, "annotation not found")
        return path

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
            items.append({
                "annotation_id": annotation["annotation_id"],
                "revision": annotation["revision"],
                "annotation_status": annotation["annotation_status"],
                "borehole_id": annotation["record"]["borehole"]["borehole_id"]["value"],
            })
        return items

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

    @app.put("/api/annotations/{annotation_id}")
    def update_annotation(annotation_id: str, payload: dict[str, Any]):
        path = annotation_path(annotation_id)
        current = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("base_revision") != current["revision"]:
            raise HTTPException(409, "revision conflict; reload before saving")
        status = payload.get("annotation_status", "single_verified")
        try:
            revised = revise_annotation(
                current, payload["record"], str(payload["annotator_id"]), str(status),
            )
            save_annotation(revised, path)
        except Exception as exc:
            raise HTTPException(422, str(exc)) from exc
        return revised

    return app

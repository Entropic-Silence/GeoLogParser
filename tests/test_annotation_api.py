import json
from pathlib import Path

import pytest

from geologparser.annotation import create_annotation, save_annotation


ROOT = Path(__file__).resolve().parents[1]


def build_client(tmp_path: Path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from geologparser.annotation_api import create_app
    annotation_root = tmp_path / "annotations"
    annotation_root.mkdir()
    image = tmp_path / "panel.png"
    image.write_bytes(b"png fixture")
    record = json.loads((ROOT / "examples/boreholes/synthetic_valid.json").read_text(encoding="utf-8"))
    annotation = create_annotation(
        "test-panel", {"panel_id": "test-panel", "rendered_path": str(image)},
        record, "AUTO", "auto",
    )
    save_annotation(annotation, annotation_root / "test-panel.json")
    return TestClient(create_app(annotation_root, ROOT / "app/static")), annotation_root


def test_annotation_api_lists_loads_and_validates(tmp_path: Path):
    client, _ = build_client(tmp_path)
    items = client.get("/api/annotations").json()
    assert items[0]["annotation_id"] == "test-panel"
    assert items[0]["ground_truth_exportable"] is False
    assert "ANNOTATION_NOT_HUMAN_VERIFIED" in items[0]["ground_truth_gate_failures"]
    status = client.get("/api/status").json()
    assert status["annotation_count"] == 1
    assert status["ground_truth_exportable_count"] == 0
    annotation = client.get("/api/annotations/test-panel").json()
    validated = client.post("/api/validate", json={"record": annotation["record"]}).json()
    assert validated["schema_valid"] is True
    assert len(validated["constraints"]) == 10

    template = client.post("/api/interval-template", json={
        "interval_id": "I003", "source_page": 2,
    })
    assert template.status_code == 200
    assert template.json()["top_depth_m"]["source_page"] == 2
    assert template.json()["lithology_raw"]["value"] is None


def test_annotation_api_saves_revision_and_rejects_stale_update(tmp_path: Path):
    client, annotation_root = build_client(tmp_path)
    annotation = client.get("/api/annotations/test-panel").json()
    payload = {
        "base_revision": 1, "record": annotation["record"],
        "annotator_id": "reviewer-1", "annotation_status": "single_verified",
    }
    response = client.put("/api/annotations/test-panel", json=payload)
    assert response.status_code == 200
    assert response.json()["revision"] == 2
    assert (annotation_root / "history/test-panel/revision_0001.json").is_file()
    assert client.put("/api/annotations/test-panel", json=payload).status_code == 409


def test_annotation_api_rejects_path_traversal(tmp_path: Path):
    client, _ = build_client(tmp_path)
    assert client.get("/api/annotations/%2E%2E%2Fsecret").status_code in {400, 404}


def test_annotation_api_review_queue_and_timing(tmp_path: Path):
    client, annotation_root = build_client(tmp_path)
    queue = client.get("/api/review-queue").json()
    assert isinstance(queue, list)
    started = client.post("/api/review-sessions/start", json={
        "annotation_id": "test-panel", "annotator_id": "reviewer-1",
    }).json()
    completed = client.post(
        f"/api/review-sessions/{started['session_id']}/complete",
        json={"corrected_fields": 2},
    )
    assert completed.status_code == 200
    assert completed.json()["corrected_fields"] == 2
    events = (annotation_root / "events/review_timing.jsonl").read_text().splitlines()
    assert [json.loads(line)["event"] for line in events] == ["review_started", "review_completed"]


@pytest.mark.parametrize("format,content_type", [
    ("json", "application/json"), ("csv", "text/csv"),
    ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
])
def test_annotation_api_draft_exports_are_explicitly_not_gt(tmp_path: Path, format: str, content_type: str):
    client, _ = build_client(tmp_path)
    response = client.get(f"/api/exports/test-panel?format={format}")
    assert response.status_code == 200
    assert content_type in response.headers["content-type"]
    assert response.headers["x-geologparser-ground-truth"] == "false"
    assert "DRAFT_NOT_GT" in response.headers["content-disposition"]
    assert response.content


def test_verified_collection_export_fails_with_traceable_reasons(tmp_path: Path):
    client, _ = build_client(tmp_path)
    response = client.get("/api/exports/verified/all.jsonl")
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["message"] == "Ground Truth gate failed"
    assert "test-panel" in detail["failures"]

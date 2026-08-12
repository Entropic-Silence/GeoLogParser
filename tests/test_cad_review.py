import json
from pathlib import Path

import pytest

from geologparser.cad_review import build_review, create_cad_review_app, save_review


ROOT = Path(__file__).resolve().parents[1]


def derivative(incomplete=True):
    return {"source_record_id":"D001","source_sha256":"a"*64,"png_sha256":"b"*64,"conversion_may_be_incomplete":incomplete,"pixel_dimensions":[100,200]}


def payload(decision="internal_only"):
    return {"reviewer_id":"reviewer-1","decision":decision,"single_borehole_log":True,"conversion_complete":False,"redactions_required":False,"notes":None,"checks":{name:{"status":"absent","notes":None} for name in ("organization_or_project","person_or_signature","contact_or_address","coordinates_or_sensitive_location","stamp_or_watermark","third_party_content")}}


def test_incomplete_derivative_cannot_be_eligible():
    value=payload("eligible_for_annotation")
    with pytest.raises(ValueError,match="complete conversion"):
        build_review(value,derivative(),1)


def test_revisioned_review_save_archives_prior_version(tmp_path):
    first=build_review(payload(),derivative(),1);save_review(first,tmp_path)
    second=build_review(payload("exclude"),derivative(),2);save_review(second,tmp_path)
    assert json.loads((tmp_path/"D001.json").read_text())["revision"]==2
    assert json.loads((tmp_path/"history/D001/revision_0001.json").read_text())["revision"]==1


def test_cad_review_api_rejects_eligibility_with_conversion_warning(tmp_path):
    derivative_root=tmp_path/"derivatives";item=derivative_root/"D001";item.mkdir(parents=True)
    image=item/"model.png";image.write_bytes(b"fixture")
    import hashlib
    row=derivative();row["png_sha256"]=hashlib.sha256(b"fixture").hexdigest()
    (derivative_root/"manifest.jsonl").write_text(json.dumps(row)+"\n")
    static=tmp_path/"static";static.mkdir();(static/"index.html").write_text("ok");(static/"app.js").write_text("");(static/"style.css").write_text("")
    app=create_cad_review_app(derivative_root/"manifest.jsonl",derivative_root,tmp_path/"reviews",static,ROOT/"schemas/cad_content_review_v001.schema.json")
    from fastapi.testclient import TestClient
    value=payload("eligible_for_annotation");value["base_revision"]=0
    response=TestClient(app).put("/api/items/D001/review",json=value)
    assert response.status_code==422
    assert not (tmp_path/"reviews/D001.json").exists()

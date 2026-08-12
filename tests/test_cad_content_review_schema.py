import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


def valid_review():
    checks = {
        key: {"status": "absent", "notes": None}
        for key in (
            "organization_or_project", "person_or_signature", "contact_or_address",
            "coordinates_or_sensitive_location", "stamp_or_watermark", "third_party_content",
        )
    }
    return {
        "review_schema_version": "cad_content_review_v001",
        "source_record_id": "MENDELEY_DWG_009",
        "source_sha256": "a" * 64,
        "derivative_sha256": "b" * 64,
        "reviewer_id": "reviewer-001",
        "reviewed_at": "2026-08-12T21:00:00Z",
        "decision": "internal_only",
        "single_borehole_log": True,
        "conversion_complete": False,
        "checks": checks,
        "redactions_required": False,
        "notes": "fixture",
        "benchmark_eligible": False,
    }


def test_cad_content_review_schema_accepts_quarantined_review():
    schema = json.loads((ROOT / "schemas/cad_content_review_v001.schema.json").read_text())
    Draft202012Validator(schema).validate(valid_review())


def test_cad_content_review_schema_forbids_self_declared_eligibility():
    schema = json.loads((ROOT / "schemas/cad_content_review_v001.schema.json").read_text())
    review = valid_review()
    review["benchmark_eligible"] = True
    errors = list(Draft202012Validator(schema).iter_errors(review))
    assert errors

import json
from pathlib import Path

from geologparser.manuscript_metrics import audit


def test_manuscript_metric_bindings_pass_against_publication_evidence():
    root = Path(__file__).resolve().parents[1]
    report = audit(root / "papers/manuscript_metric_bindings.json", root)
    assert report["passed"], report["errors"]
    assert report["observation_count"] >= 20


def test_metric_audit_detects_drift(tmp_path):
    root = tmp_path
    (root / "papers").mkdir()
    (root / "evidence").mkdir()
    (root / "papers/manuscript.md").write_text("matched 9", encoding="utf-8")
    (root / "evidence/metrics.json").write_text(json.dumps({"matched": 8}), encoding="utf-8")
    config = {
        "audit_version": "test",
        "checks": [{
            "id": "drift",
            "manuscript": "papers/manuscript.md",
            "source": "evidence/metrics.json",
            "pattern": r"matched (?P<matched>\d+)",
            "bindings": [{"group": "matched", "pointer": "/matched"}],
        }],
    }
    path = root / "bindings.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    report = audit(path, root)
    assert not report["passed"]
    assert "prose=9" in report["errors"][0]

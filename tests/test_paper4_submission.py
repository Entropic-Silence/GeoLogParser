import json
from pathlib import Path


def test_paper4_cg_package_is_evidence_gated_and_complete():
    root = Path(__file__).resolve().parents[1]
    paper = root / "papers/paper4"
    gate = json.loads((paper / "submission_gate.json").read_text(encoding="utf-8"))
    claims = json.loads((paper / "claim_evidence_audit.json").read_text(encoding="utf-8"))
    assert gate["package_label"] == "DOI_FINAL_RELEASE_CANDIDATE"
    assert gate["submission_ready"] is True
    assert gate["author_metadata_complete"] is True
    assert gate["rights_linkage_signoff_complete"] is True
    assert claims["passed"] is True
    assert claims["claim_count"] == 15
    manuscript = (paper / "manuscript.md").read_text(encoding="utf-8")
    assert "## 7. Discussion" in manuscript
    assert "4/100 (4%)" in manuscript
    assert "reference-relative volume discrepancy" in manuscript
    assert "endpoint-field** quantity" in manuscript
    figure_manifest = json.loads((paper / "figure_manifest.json").read_text(encoding="utf-8"))
    assert all(not path.startswith("results/") for path in figure_manifest["source_manifests"])
    for name in (
        "F1_trustworthy_framework.png",
        "F2_vlm_source_shift.png",
        "F3_assurance_frontier.png",
        "F4_spatial_support_consequence.png",
    ):
        assert (paper / "figures" / name).is_file()

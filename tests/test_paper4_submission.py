import json
import re
from pathlib import Path

import pymupdf


def test_paper4_cg_package_is_evidence_gated_and_complete():
    root = Path(__file__).resolve().parents[1]
    paper = root / "papers/paper4"
    gate = json.loads((paper / "submission_gate.json").read_text(encoding="utf-8"))
    claims = json.loads((paper / "claim_evidence_audit.json").read_text(encoding="utf-8"))
    assert gate["package_label"] == "SUBMISSION_READY_CANDIDATE"
    assert gate["scientific_content_ready"] is True
    assert gate["release_artifacts_ready"] is True
    assert gate["submission_ready"] is False
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
    assert gate["manuscript_wc_word_count"] <= gate["manuscript_wc_limit"] <= 6050
    assert "Supplement S10" not in manuscript
    assert "Supplement S11" not in manuscript
    assert "Supplement S12" not in manuscript
    for name in (
        "F1_trustworthy_framework.png",
        "F2_vlm_source_shift.png",
        "F3_assurance_frontier.png",
        "F4_spatial_support_consequence.png",
    ):
        assert (paper / "figures" / name).is_file()


def test_paper4_final_pdf_preserves_prompt_sha256() -> None:
    root = Path(__file__).resolve().parents[1]
    cageo = root / "papers/paper4/submission/cageo"
    expected = "891bc6beb7ff9cf35c55389191a208c9b09e9e2dc76909f716603f413745104a"

    tex = (cageo / "manuscript.tex").read_text(encoding="utf-8")
    assert "\\usepackage{lineno}" in tex
    assert "\\linenumbers" in tex
    assert r"\newcommand{\hash}[1]{\mbox{\texttt{#1}}}" in tex

    with pymupdf.open(cageo / "manuscript_final.pdf") as document:
        text = "\n".join(page.get_text("text") for page in document)
    match = re.search(r"SHA-256\s+([0-9a-f]{64})", text)
    assert match is not None
    printed_digest = match.group(1)
    assert re.fullmatch(r"[0-9a-f]{64}", printed_digest)
    assert printed_digest == expected

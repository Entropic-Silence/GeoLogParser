import hashlib
import json
import re
import zipfile
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
    font_sources = figure_manifest["canonical_artwork"]["embedded_font_sources"]
    assert font_sources == {
        "papers/paper4/fonts/DejaVuSans-Bold.ttf": (
            "e6476c1b80502924294eed40894c5b18e06c181444ca953e5334262df9c27724"
        ),
        "papers/paper4/fonts/DejaVuSans.ttf": (
            "7da195a74c55bef988d0d48f9508bd5d849425c1770dba5d7bfc6ce9ed848954"
        ),
    }
    for relative_path, expected_sha256 in font_sources.items():
        assert hashlib.sha256((root / relative_path).read_bytes()).hexdigest() == expected_sha256
    assert (paper / "fonts/LICENSE_DEJAVU.txt").is_file()
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

    latex_archive = paper / "submission_bundle/Paper4_CAGEO_LaTeX_Source_v1.0.8.zip"
    with zipfile.ZipFile(latex_archive) as archive:
        source_manifest = json.loads(archive.read("SOURCE_MANIFEST.json"))
        assert source_manifest["entrypoint"] == "manuscript.tex"
        assert source_manifest["tested_engine"] == "Tectonic 0.17.0"
        assert source_manifest["build_command"] == (
            "tectonic manuscript.tex --keep-logs --reruns 2"
        )
        assert source_manifest["build_environment"] == {
            "SOURCE_DATE_EPOCH": str(source_manifest["source_date_epoch"])
        }
        assert source_manifest["expected_pdf_sha256"] == hashlib.sha256(
            (paper / "submission/cageo/manuscript_final.pdf").read_bytes()
        ).hexdigest()
        members = {item["archive_path"]: item for item in source_manifest["files"]}
        assert set(members) == {
            "manuscript.tex",
            "references_cageo.bib",
            "cas-sc.cls",
            "cas-common.sty",
            "cas-model2-names.bst",
            "figures/Figure_1.pdf",
            "figures/Figure_2.pdf",
            "figures/Figure_3.pdf",
            "figures/Figure_4.pdf",
        }
        for archive_path, item in members.items():
            data = archive.read(archive_path)
            assert len(data) == item["bytes"]
            assert hashlib.sha256(data).hexdigest() == item["sha256"]


def test_paper4_final_pdf_preserves_prompt_sha256() -> None:
    root = Path(__file__).resolve().parents[1]
    paper = root / "papers/paper4"
    cageo = root / "papers/paper4/submission/cageo"
    prompt = root / "prompts/vlm_interval_source_units_v002.md"
    expected = hashlib.sha256(prompt.read_bytes()).hexdigest()
    assert expected == "891bc6beb7ff9cf35c55389191a208c9b09e9e2dc76909f716603f413745104a"

    tex = (cageo / "manuscript.tex").read_text(encoding="utf-8")
    manuscript_sha256 = hashlib.sha256((paper / "manuscript.md").read_bytes()).hexdigest()
    assert f"Canonical Markdown SHA-256: {manuscript_sha256}" in tex
    assert "\\usepackage{lineno}" in tex
    assert "\\linenumbers" in tex
    assert r"\newcommand{\hash}[1]{\mbox{\texttt{#1}}}" in tex

    with pymupdf.open(cageo / "manuscript_final.pdf") as document:
        text = "\n".join(page.get_text("text") for page in document)
        info_type, info_reference = document.xref_get_key(-1, "Info")
        assert info_type == "xref"
        info_xref = int(info_reference.split()[0])
        assert document.xref_get_key(info_xref, "Paper4SourceSHA256") == (
            "string",
            manuscript_sha256,
        )
    for content in (
        (paper / "manuscript.md").read_text(encoding="utf-8"),
        (cageo / "manuscript_final.md").read_text(encoding="utf-8"),
        tex,
        text,
    ):
        match = re.search(
            r"SHA-256\s+(?:`|\\hash\{)?([0-9a-f]{64})(?![0-9a-f])",
            content,
        )
        assert match is not None
        assert match.group(1) == expected
        assert re.search(
            r"SHA-256\s+(?:`|\\hash\{)?[0-9a-f]{65,}", content
        ) is None


def _font_program_hashes(document: pymupdf.Document, page_number: int) -> set[str]:
    hashes: set[str] = set()
    for font in document.get_page_fonts(page_number, full=True):
        program = document.extract_font(font[0])[3]
        if program:
            hashes.add(hashlib.sha256(program).hexdigest())
    return hashes


def test_paper4_final_pdf_embeds_exact_canonical_figure_forms() -> None:
    root = Path(__file__).resolve().parents[1]
    paper = root / "papers/paper4"
    tex = (paper / "submission/cageo/manuscript.tex").read_text(encoding="utf-8")

    with pymupdf.open(paper / "submission/cageo/manuscript_final.pdf") as final_pdf:
        for number in range(1, 5):
            canonical_path = paper / f"figures/Figure_{number}.pdf"
            assert f"{{figures/Figure_{number}.pdf}}" in tex
            with pymupdf.open(canonical_path) as canonical_pdf:
                content_xrefs = canonical_pdf[0].get_contents()
                assert len(content_xrefs) == 1
                canonical_stream = canonical_pdf.xref_stream(content_xrefs[0])
                canonical_fonts = _font_program_hashes(canonical_pdf, 0)

            matches = [
                page_number
                for page_number in range(len(final_pdf))
                for xobject in final_pdf.get_page_xobjects(page_number)
                if final_pdf.xref_stream(xobject[0]) == canonical_stream
            ]
            assert len(matches) == 1
            assert canonical_fonts
            assert canonical_fonts <= _font_program_hashes(final_pdf, matches[0])


def test_paper4_generated_manuscript_tracks_canonical_text() -> None:
    root = Path(__file__).resolve().parents[1]
    paper = root / "papers/paper4"
    source = (paper / "manuscript.md").read_text(encoding="utf-8")
    final_markdown = (paper / "submission/cageo/manuscript_final.md").read_text(
        encoding="utf-8"
    )
    tex = (paper / "submission/cageo/manuscript.tex").read_text(encoding="utf-8")
    abstract = source.split("## Abstract", 1)[1].split("**Keywords:**", 1)[0].strip()
    assert abstract in final_markdown

    for label in ("Funding", "Competing interests", "Rights and linkage sign-off"):
        canonical_line = next(
            line for line in source.splitlines() if line.startswith(f"**{label}:**")
        )
        assert canonical_line in final_markdown
    assert "This research did not receive any specific grant" in tex
    assert "exact named-release files" in tex

    labels = {
        1: "fig:framework",
        2: "fig:capability",
        3: "fig:assurance",
        4: "fig:spatial",
    }
    for number, label in labels.items():
        match = re.search(
            rf"^!\[Figure {number}\. ([^\n]+)\]\(figures/[^)]+\)$",
            source,
            flags=re.M,
        )
        assert match is not None
        assert match.group(0) in final_markdown
        assert rf"\caption{{{match.group(1)}}}\label{{{label}}}" in tex

    assert "Garzón, Sebastián" in final_markdown
    with pymupdf.open(paper / "submission/cageo/manuscript_final.pdf") as document:
        pdf_text = "\n".join(page.get_text("text") for page in document)
    assert "Garzón, S." in pdf_text
    assert r"Garz\'on" not in pdf_text
    for term in ("ChatGPT", "OpenAI", "generative AI", "AI-assisted technologies"):
        assert term.casefold() not in source.casefold()
        assert term.casefold() not in final_markdown.casefold()
        assert term.casefold() not in tex.casefold()
        assert term.casefold() not in pdf_text.casefold()

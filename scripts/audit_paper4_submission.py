#!/usr/bin/env python3
"""Run the C&G-facing structural submission gate for Paper 4.

The gate verifies scientific content, author metadata, declarations, and the
author-provided rights/linkage sign-off. DOI registration and portal-side
validation remain external actions.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pymupdf
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "papers/paper4"
CAGEO = PAPER / "submission/cageo"
BUNDLE = PAPER / "submission_bundle"
OUT = PAPER / "submission_gate.json"
RELEASE_METADATA = json.loads(
    (PAPER / "release_metadata.json").read_text(encoding="utf-8")
)
RELEASE_TAG = RELEASE_METADATA["release_tag"]
SOFTWARE_ARCHIVE = RELEASE_METADATA["software_archive"]
SOFTWARE_DOI = SOFTWARE_ARCHIVE["doi"]
DATA_DOI = RELEASE_METADATA["data_archive"]["doi"]
MAX_CAGEO_WORDS = 6050
ARTWORK_RENDER_DPI = 300
SUPPLEMENT_ARTWORK_RENDER_DPI = 600
CANONICAL_FONT_SHA256 = {
    "DejaVuSans.ttf": "7da195a74c55bef988d0d48f9508bd5d849425c1770dba5d7bfc6ce9ed848954",
    "DejaVuSans-Bold.ttf": "e6476c1b80502924294eed40894c5b18e06c181444ca953e5334262df9c27724",
}
ARTWORK_PAIRS = {
    "F1_trustworthy_framework.png": ("Figure_1.pdf", ARTWORK_RENDER_DPI),
    "F2_vlm_source_shift.png": ("Figure_2.pdf", ARTWORK_RENDER_DPI),
    "F3_assurance_frontier.png": ("Figure_3.pdf", ARTWORK_RENDER_DPI),
    "F4_spatial_support_consequence.png": ("Figure_4.pdf", ARTWORK_RENDER_DPI),
    "graphical_abstract.png": ("graphical_abstract.pdf", ARTWORK_RENDER_DPI),
    "F4_risk_coverage_frontier.png": (
        "Supplementary_Figure_S1.pdf",
        SUPPLEMENT_ARTWORK_RENDER_DPI,
    ),
    "F5_threshold_development_curve.png": (
        "Supplementary_Figure_S2.pdf",
        SUPPLEMENT_ARTWORK_RENDER_DPI,
    ),
    "F7_controlled_error_mechanisms.png": (
        "Supplementary_Figure_S3.pdf",
        SUPPLEMENT_ARTWORK_RENDER_DPI,
    ),
}
SUPPLEMENT_REFERENCE_EXPECTATIONS = {
    "controlled support-preservation protocol": "S7",
    "full candidate representation, dynamic-programming objective": "S6",
    "controlled perturbation mechanism study": "S7",
}
ARCHIVE_CITATION_KEYS = {
    "du2026paper4software": (
        "Trustworthy Borehole Database Ingestion from VLM Proposals: "
        "Provenance and Spatial Support"
    ),
    "du2026datav002": "GeoLogParser Public Data Companion v002",
}
BUNDLE_FIGURE_LINKS = {
    f"figures/F{number}_{suffix}.png": f"Paper4_Figure_{number}.png"
    for number, suffix in {
        1: "trustworthy_framework",
        2: "vlm_source_shift",
        3: "assurance_frontier",
        4: "spatial_support_consequence",
    }.items()
}
BUNDLE_MANUSCRIPT_TRANSFORMATION = {
    "type": "markdown_figure_link_rewrite",
    "replacements": BUNDLE_FIGURE_LINKS,
}


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", text))


def cageo_word_counts(source: str) -> tuple[int, int]:
    """Count article text after applying the journal's stated exclusions."""

    body = source.split(
        "## 1. Problem, hypothesis, and research questions", 1
    )[1].split("## References", 1)[0]
    without_captions = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", body)
    without_captions = re.sub(
        r"(?m)^(?:\*\*Table \d+\.\*\*|Table:).*$",
        "",
        without_captions,
    )
    including_tables = count_words(without_captions)
    without_tables = "\n".join(
        line for line in without_captions.splitlines()
        if not line.lstrip().startswith("|")
    )
    return count_words(without_tables), including_tables


def run_gate(command: list[str]) -> str | None:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        return f"{' '.join(command)} failed: {result.stdout}{result.stderr}"
    return None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized_text_bytes(path: Path) -> bytes:
    text = path.read_text(encoding="utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def expected_upload_bytes(
    source: Path, destination: Path, entry: dict[str, object], errors: list[str]
) -> bytes:
    if destination.suffix.lower() not in {".md", ".txt", ".json"}:
        if entry.get("transformation") is not None:
            errors.append(f"binary upload artifact declares a transformation: {entry['file']}")
        return source.read_bytes()
    data = normalized_text_bytes(source)
    transformation = entry.get("transformation")
    if transformation is None:
        return data
    if transformation != BUNDLE_MANUSCRIPT_TRANSFORMATION:
        errors.append(f"upload artifact declares an unknown transformation: {entry['file']}")
        return data
    text = data.decode("utf-8")
    for source_path, bundle_path in BUNDLE_FIGURE_LINKS.items():
        text = text.replace(f"]({source_path})", f"]({bundle_path})")
    return text.encode("utf-8")


def audit_canonical_font_sources(errors: list[str]) -> None:
    """Bind vector artwork to the redistributed DejaVu 2.37 font files."""

    manifest_path = PAPER / "figure_manifest.json"
    if not manifest_path.is_file():
        errors.append("missing figure manifest")
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    recorded = manifest.get("canonical_artwork", {}).get(
        "embedded_font_sources", {}
    )
    for name, expected_sha256 in CANONICAL_FONT_SHA256.items():
        path = PAPER / "fonts" / name
        relative = path.relative_to(ROOT).as_posix()
        if not path.is_file():
            errors.append(f"missing canonical artwork font: {relative}")
            continue
        if sha256(path) != expected_sha256:
            errors.append(f"canonical artwork font hash mismatch: {relative}")
        if recorded.get(relative) != expected_sha256:
            errors.append(f"figure manifest font binding is stale: {relative}")
    if not (PAPER / "fonts" / "LICENSE_DEJAVU.txt").is_file():
        errors.append("missing DejaVu font licence")


def audit_upload_bundle(errors: list[str]) -> None:
    """Verify that every upload artifact matches its declared current source."""

    manifest_path = BUNDLE / "Paper4_Upload_Manifest.json"
    if not manifest_path.is_file():
        errors.append("missing Paper4 upload manifest")
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest.get("files", []):
        destination = BUNDLE / str(entry["file"])
        if not destination.is_file():
            errors.append(f"upload bundle destination missing: {entry['file']}")
            continue
        if destination.stat().st_size != entry.get("bytes") or sha256(destination) != entry.get("sha256"):
            errors.append(f"upload manifest hash is stale: {entry['file']}")
        if "source" in entry:
            source = ROOT / str(entry["source"])
            if not source.is_file():
                errors.append(f"upload bundle source missing: {entry['source']}")
                continue
            expected = expected_upload_bytes(source, destination, entry, errors)
            if destination.read_bytes() != expected:
                errors.append(f"upload artifact differs from canonical source: {entry['file']}")
        elif entry.get("file") == "Paper4_CAGEO_LaTeX_Source_v1.0.9.zip":
            audit_latex_source_archive(errors, destination, entry)
        else:
            errors.append(f"upload manifest entry has no canonical source: {entry['file']}")


def audit_latex_source_archive(
    errors: list[str], archive_path: Path, upload_entry: dict[str, object]
) -> None:
    """Verify every editable-source archive member against its repository source."""

    try:
        with zipfile.ZipFile(archive_path) as archive:
            names = set(archive.namelist())
            if "SOURCE_MANIFEST.json" not in names:
                errors.append("LaTeX source archive has no SOURCE_MANIFEST.json")
                return
            source_manifest = json.loads(archive.read("SOURCE_MANIFEST.json"))
            if source_manifest.get("entrypoint") != "manuscript.tex":
                errors.append("LaTeX source archive entrypoint is incorrect")
            if source_manifest.get("tested_engine") != "Tectonic 0.17.0":
                errors.append("LaTeX source archive engine version is incorrect")
            if source_manifest.get("expected_pdf_sha256") != sha256(
                CAGEO / "manuscript_final.pdf"
            ):
                errors.append("LaTeX source archive expected PDF hash is stale")
            expected_names = {
                str(item["archive_path"])
                for item in source_manifest.get("files", [])
            } | {"SOURCE_MANIFEST.json"}
            if names != expected_names:
                errors.append("LaTeX source archive member list is stale")
            recorded_sources: list[str] = []
            for item in source_manifest.get("files", []):
                source_name = str(item["source"])
                recorded_sources.append(source_name)
                source = ROOT / source_name
                member_name = str(item["archive_path"])
                if not source.is_file() or member_name not in names:
                    errors.append(f"LaTeX source archive member missing: {member_name}")
                    continue
                expected = (
                    source.read_bytes()
                    if source.suffix.lower() == ".pdf"
                    else normalized_text_bytes(source)
                )
                observed = archive.read(member_name)
                if observed != expected:
                    errors.append(f"LaTeX source member differs from canonical source: {member_name}")
                if len(observed) != item.get("bytes") or hashlib.sha256(observed).hexdigest() != item.get("sha256"):
                    errors.append(f"LaTeX source member hash is stale: {member_name}")
            if sorted(recorded_sources) != sorted(
                str(source) for source in upload_entry.get("sources", [])
            ):
                errors.append("LaTeX source archive source list is stale")
    except (OSError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        errors.append(f"could not audit LaTeX source archive: {exc}")


def audit_artwork_pairs(errors: list[str]) -> None:
    """Ensure every submitted PNG is a pixel-identical raster of its PDF."""

    for png_name, (pdf_name, render_dpi) in ARTWORK_PAIRS.items():
        png_path = PAPER / "figures" / png_name
        pdf_path = PAPER / "figures" / pdf_name
        if not png_path.is_file():
            errors.append(f"missing PNG artwork: {png_name}")
        if not pdf_path.is_file():
            errors.append(f"missing PDF artwork: {pdf_name}")
        if not png_path.is_file() or not pdf_path.is_file():
            continue
        try:
            with pymupdf.open(pdf_path) as document:
                if len(document) != 1:
                    errors.append(f"artwork PDF is not single-page: {pdf_name}")
                    continue
                pixmap = document[0].get_pixmap(
                    dpi=render_dpi,
                    colorspace=pymupdf.csRGB,
                    alpha=False,
                )
            rendered = Image.frombytes(
                "RGB", (pixmap.width, pixmap.height), pixmap.samples
            )
            with Image.open(png_path) as supplied:
                if supplied.mode != "RGB":
                    errors.append(f"PNG artwork is not RGB: {png_name}")
                supplied_rgb = supplied.convert("RGB")
                if supplied_rgb.size != rendered.size:
                    errors.append(
                        f"PNG/PDF artwork dimensions differ: {png_name} vs {pdf_name} "
                        f"({supplied_rgb.size} != {rendered.size})"
                    )
                elif supplied_rgb.tobytes() != rendered.tobytes():
                    errors.append(
                        f"PNG/PDF artwork pixels differ: {png_name} is not a "
                        f"{render_dpi}-DPI raster of {pdf_name}"
                    )
                dpi = supplied.info.get("dpi")
                if not dpi or min(dpi) < render_dpi - 1:
                    errors.append(
                        f"PNG artwork does not advertise {render_dpi} DPI: {png_name}"
                    )
        except Exception as exc:  # pragma: no cover - diagnostic path
            errors.append(f"could not audit artwork pair {png_name}/{pdf_name}: {exc}")


def font_program_hashes(document: pymupdf.Document, page_number: int) -> set[str]:
    """Return embedded font-program hashes visible from one PDF page."""

    hashes: set[str] = set()
    for font in document.get_page_fonts(page_number, full=True):
        _, _, _, program = document.extract_font(font[0])
        if program:
            hashes.add(hashlib.sha256(program).hexdigest())
    return hashes


def pdf_info_value(document: pymupdf.Document, key: str) -> str | None:
    info_type, info_reference = document.xref_get_key(-1, "Info")
    if info_type != "xref":
        return None
    info_xref = int(info_reference.split()[0])
    value_type, value = document.xref_get_key(info_xref, key)
    return value if value_type == "string" else None


def audit_final_pdf_artwork_bindings(errors: list[str]) -> None:
    """Bind each final-PDF figure Form and font program to its canonical PDF."""

    final_path = CAGEO / "manuscript_final.pdf"
    if not final_path.is_file():
        errors.append("missing final manuscript PDF")
        return
    with pymupdf.open(final_path) as final_document:
        for number in range(1, 5):
            canonical_path = PAPER / "figures" / f"Figure_{number}.pdf"
            if not canonical_path.is_file():
                continue
            with pymupdf.open(canonical_path) as canonical_document:
                contents = canonical_document[0].get_contents()
                if len(contents) != 1:
                    errors.append(
                        f"canonical Figure_{number}.pdf must have one content stream"
                    )
                    continue
                canonical_stream = canonical_document.xref_stream(contents[0])
                canonical_fonts = font_program_hashes(canonical_document, 0)

            matches = [
                page_number
                for page_number in range(len(final_document))
                for xobject in final_document.get_page_xobjects(page_number)
                if final_document.xref_stream(xobject[0]) == canonical_stream
            ]
            if len(matches) != 1:
                errors.append(
                    f"final PDF contains {len(matches)} exact Form bindings for "
                    f"Figure_{number}.pdf; expected one"
                )
                continue
            final_fonts = font_program_hashes(final_document, matches[0])
            if not canonical_fonts or not canonical_fonts.issubset(final_fonts):
                errors.append(
                    f"final PDF does not preserve Figure_{number}.pdf font programs"
                )


def audit_prompt_digest(
    errors: list[str], manuscript: str, final_markdown: str, cageo_tex: str, pdf_text: str
) -> None:
    """Verify the prompt digest from source bytes through every printed form."""

    prompt_path = ROOT / "prompts" / "vlm_interval_source_units_v002.md"
    expected = sha256(prompt_path)
    strict_pattern = re.compile(
        r"SHA-256\s+(?:`|\\hash\{)?([0-9a-f]{64})(?![0-9a-f])"
    )
    overlong_pattern = re.compile(
        r"SHA-256\s+(?:`|\\hash\{)?[0-9a-f]{65,}"
    )
    for label, content in (
        ("canonical Markdown", manuscript),
        ("final Markdown", final_markdown),
        ("final TeX", cageo_tex),
        ("final PDF", pdf_text),
    ):
        if overlong_pattern.search(content):
            errors.append(f"{label} contains an overlong SHA-256 digest")
            continue
        match = strict_pattern.search(content)
        if match is None:
            errors.append(f"{label} does not contain one strict 64-digit prompt digest")
        elif match.group(1) != expected:
            errors.append(f"{label} prompt digest differs from the prompt source bytes")


def main() -> None:
    manuscript_path = PAPER / "manuscript.md"
    text = manuscript_path.read_text(encoding="utf-8")
    errors: list[str] = []
    manuscript_main_text_word_count, manuscript_word_count = cageo_word_counts(text)
    manuscript_source_whitespace_word_count = len(text.split())
    if manuscript_word_count > MAX_CAGEO_WORDS:
        errors.append(
            f"manuscript article-body word count exceeds C&G working limit "
            f"{MAX_CAGEO_WORDS}: {manuscript_word_count}"
        )
    required_headings = [
        "## Abstract", "## Highlights", "## 1. Problem, hypothesis, and research questions",
        "## 2. Related work and positioning", "## 3. Evidence, data, and task definition",
        "## 4. Methods: provenance-grounded selective assurance", "## 5. Experimental protocol and reproducibility",
        "## 6. Results", "## 7. Discussion", "## 8. Limitations and threats to validity",
        "## 9. Conclusions", "## Computer Code Availability", "## Data Availability", "## Declarations", "## References",
    ]
    for heading in required_headings:
        if heading not in text:
            errors.append(f"missing heading: {heading}")
    abstract = text.split("## Abstract", 1)[1].split("**Keywords:**", 1)[0]
    if count_words(abstract) > 300:
        errors.append(f"structured abstract exceeds 300 words: {count_words(abstract)}")
    keywords = text.split("**Keywords:**", 1)[1].split("\n", 1)[0]
    if len([item for item in keywords.split(";") if item.strip()]) > 6:
        errors.append("more than six keywords")
    highlights = text.split("## Highlights", 1)[1].split("## 1.", 1)[0]
    highlight_lines = [
        line[2:].strip() for line in highlights.splitlines() if line.startswith("- ")
    ]
    highlight_count = len(highlight_lines)
    if not 3 <= highlight_count <= 5:
        errors.append(f"highlights count is {highlight_count}, expected 3–5")
    for index, highlight in enumerate(highlight_lines, 1):
        if len(highlight) > 85:
            errors.append(f"highlight {index} exceeds 85 characters: {len(highlight)}")
    standalone_highlights = (CAGEO / "highlights.txt").read_text(encoding="utf-8").splitlines()
    if standalone_highlights != highlight_lines:
        errors.append("standalone highlights differ from manuscript highlights")
    forbidden = ["fallback manuscript", "ADR-", "project log", "SUBMISSION_READY.md"]
    for term in forbidden:
        if term.lower() in text.lower():
            errors.append(f"internal project language remains in main text: {term}")
    for term in ("Qwen3.8-direct", "Data and code availability"):
        if term.lower() in text.lower():
            errors.append(f"outdated Paper 4 terminology remains in main text: {term}")
    if "**partially reconstructable**" not in text:
        errors.append("main text does not disclose partially reconstructable Qwen runtime provenance")
    supplement_text = (PAPER / "supplement.md").read_text(encoding="utf-8")
    normalized_supplement_text = re.sub(r"\s+", " ", supplement_text)
    available_sections = set(
        re.findall(r"^#{2,3}\s+(S\d+(?:\.\d+)?)\b", supplement_text, flags=re.M)
    )
    available_tables = set(
        f"S{number}"
        for number in re.findall(r"Supplementary Table S(\d+)\b", supplement_text)
    )
    available_sections.update(available_tables)
    supplement_refs = re.findall(
        r"\bSupplement(?:ary)?(?:\s+Methods?)?\s+(S\d+(?:\.\d+)?)\b",
        text,
        flags=re.I,
    )
    missing_supplement_refs = sorted(
        {reference for reference in supplement_refs if reference not in available_sections}
    )
    if missing_supplement_refs:
        errors.append(
            "manuscript cites missing supplementary section(s): "
            + ", ".join(missing_supplement_refs)
        )
    for phrase, expected_section in SUPPLEMENT_REFERENCE_EXPECTATIONS.items():
        pattern = rf"{re.escape(phrase)}[^.\n]*Supplementary Methods {expected_section}\b"
        if not re.search(pattern, text, flags=re.I):
            errors.append(
                f"supplement cross-reference for '{phrase}' must point to {expected_section}"
            )
    if re.search(r"\bSupplement(?:ary)?(?:\s+Methods?)?\s+S(?:10|11|12)\b", text, flags=re.I):
        errors.append("stale Supplement S10/S11/S12 citation remains in manuscript")
    cited_supplementary_figures: set[str] = set()
    combined_manuscript = text + "\n" + supplement_text
    for match in re.finditer(r"Supplementary Figures?", combined_manuscript):
        cited_supplementary_figures.update(
            re.findall(
                r"\bS[1-3]\b",
                combined_manuscript[match.start():match.start() + 120],
            )
        )
    missing_supplementary_figures = sorted(
        {"S1", "S2", "S3"} - cited_supplementary_figures
    )
    if missing_supplementary_figures:
        errors.append(
            "manuscript and supplement do not cite supplementary figure(s): "
            + ", ".join(missing_supplementary_figures)
        )
    for method_anchor in (
        "c_i=(t_i,b_i,p_i,y_i,x_i^t,x_i^b,e_i,q_i)",
        "F(j)=\\max",
        "2.995, 2.999",
        "same-pool risk frontier",
        "If $R$ is non-monotone, automatic modification is rejected",
    ):
        if method_anchor not in normalized_supplement_text:
            errors.append(f"Supplementary Methods S6 omits method anchor: {method_anchor}")
    required_author_text = [
        "Yifan Du",
        "**Funding:**",
        "**Competing interests:**",
        "**Rights and linkage sign-off:**",
        RELEASE_TAG,
        "data-v002",
        SOFTWARE_DOI,
        "this DOI identifies software",
        "source code is released under the MIT license",
        "remain subject to their applicable terms",
    ]
    for term in required_author_text:
        if term not in text:
            errors.append(f"missing author-confirmed submission text: {term}")
    if "result-reproduction package released under the MIT license" in text:
        errors.append("MIT scope incorrectly covers the complete result-reproduction package")
    normalized_manuscript_text = re.sub(r"\s+", " ", text)
    if "all five visible pages are classified as unsupported" in normalized_manuscript_text:
        errors.append("BGS page-family summary incorrectly labels all five pages unsupported")
    if "four explicit-range pages yield no accepted range" not in normalized_manuscript_text:
        errors.append("BGS external-gate summary does not distinguish page families")
    claim_map_text = (PAPER / "claim_evidence_map.md").read_text(encoding="utf-8")
    bgs_publication_metric = (
        "publication_evidence/result_core/results/2026-08-16/"
        "P2_BGS_V028_ROUTED_EXTERNAL_V003_FINAL/metrics.json"
    )
    if bgs_publication_metric not in claim_map_text:
        errors.append("Paper 4 BGS claim map does not use the external-evaluation metric")
    zenodo_metadata = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    if "license" in zenodo_metadata:
        errors.append("mixed-content Zenodo metadata must not assign a blanket package license")
    if "MIT applies to original source code only" not in zenodo_metadata.get("description", ""):
        errors.append("Zenodo metadata does not state the source-code-only MIT scope")
    citation_text = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    if "MIT applies to source code only" not in citation_text:
        errors.append("CITATION.cff does not state the source-code-only MIT scope")
    main_tables = (PAPER / "main_tables.md").read_text(encoding="utf-8")
    if not all(
        heading in main_tables
        for heading in ("Endpoint-field anchor coverage", "Both-endpoint anchor coverage")
    ):
        errors.append("assurance table does not distinguish endpoint-field and interval-level anchor coverage")
    bibliography = (ROOT / "papers/references.bib").read_text(encoding="utf-8")
    known_keys = set(re.findall(r"@[A-Za-z]+\{([^,]+),", bibliography))
    cited_keys: set[str] = set()
    for group in re.findall(r"\[([^\]]*@[^\]]+)\]", text):
        cited_keys.update(re.findall(r"@([A-Za-z0-9_:-]+)", group))
    missing_citations = sorted(cited_keys - known_keys)
    if missing_citations:
        errors.append(f"unresolved bibliography keys: {', '.join(missing_citations)}")
    final_markdown = (CAGEO / "manuscript_final.md").read_text(encoding="utf-8")
    cageo_tex = (CAGEO / "manuscript.tex").read_text(encoding="utf-8")
    with pymupdf.open(CAGEO / "manuscript_final.pdf") as document:
        pdf_text = "\n".join(page.get_text() for page in document)
        pdf_source_sha256 = pdf_info_value(document, "Paper4SourceSHA256")
    manuscript_representations = {
        "canonical Markdown": text,
        "final Markdown": final_markdown,
        "final TeX": cageo_tex,
        "final PDF": pdf_text,
    }
    for term in ("ChatGPT", "OpenAI", "generative AI", "AI-assisted technologies"):
        for representation, representation_text in manuscript_representations.items():
            if term.casefold() in representation_text.casefold():
                errors.append(
                    f"unrequested AI-use disclosure remains in {representation}: {term}"
                )
    expected_source_sha256 = sha256(PAPER / "manuscript.md")
    if f"Canonical Markdown SHA-256: {expected_source_sha256}" not in cageo_tex:
        errors.append("final TeX is not bound to the canonical Markdown hash")
    if pdf_source_sha256 != expected_source_sha256:
        errors.append("final PDF is not bound to the canonical Markdown hash")
    audit_prompt_digest(errors, text, final_markdown, cageo_tex, pdf_text)
    normalized_pdf_text = re.sub(r"\s+", " ", pdf_text).casefold()
    for key, reference_title in ARCHIVE_CITATION_KEYS.items():
        if f"[@{key}]" not in final_markdown:
            errors.append(f"final Markdown omits archive citation: {key}")
        if f"\\citep{{{key}}}" not in cageo_tex:
            errors.append(f"final TeX omits archive citation: {key}")
        if re.sub(r"\s+", " ", reference_title).casefold() not in normalized_pdf_text:
            errors.append(f"final PDF bibliography omits archive citation: {key}")
    if "[dataset] geologparser public data companion v002" not in normalized_pdf_text:
        errors.append("final PDF data reference omits the required [dataset] prefix")
    for stale_math in (
        "(V=(v_1,ldots,v_n))",
        "(C=(c_1,ldots,c_m))",
        "For boundary (r) in borehole (i)",
        "hull-clipped grid (G)",
    ):
        if stale_math in text or stale_math in final_markdown:
            errors.append(f"malformed Markdown math remains: {stale_math}")
    for figure in (
        "F1_trustworthy_framework.png", "F2_vlm_source_shift.png",
        "F3_assurance_frontier.png", "F4_spatial_support_consequence.png",
    ):
        if not (PAPER / "figures" / figure).is_file():
            errors.append(f"missing main figure: {figure}")
    for vector in ("Figure_1.pdf", "Figure_2.pdf", "Figure_3.pdf", "Figure_4.pdf"):
        if not (PAPER / "figures" / vector).is_file():
            errors.append(f"missing canonical vector figure: {vector}")
    audit_canonical_font_sources(errors)
    audit_artwork_pairs(errors)
    audit_final_pdf_artwork_bindings(errors)
    audit_upload_bundle(errors)

    # Every supplementary table cited by the manuscript must have a standalone
    # caption in the upload-facing caption file, not only inside methods.
    caption_text = (PAPER / "supplementary_captions.md").read_text(encoding="utf-8")
    cited_tables = set(re.findall(r"Supplementary Table (S\d+)\b", supplement_text + "\n" + text))
    caption_tables = set(re.findall(r"^### Supplementary Table (S\d+)\.", caption_text, flags=re.M))
    missing_table_captions = sorted(cited_tables - caption_tables)
    if missing_table_captions:
        errors.append(
            "supplementary caption file omits cited table(s): "
            + ", ".join(missing_table_captions)
        )
    readme_text = (PAPER / "README.md").read_text(encoding="utf-8")
    if "Supplementary Tables S1–S4" not in readme_text:
        errors.append("Paper 4 README must list Supplementary Tables S1–S4")
    for required_file in ("supplement.md", "main_tables.md", "claim_evidence_map.md", "cover_letter_points.md"):
        if not (PAPER / required_file).is_file():
            errors.append(f"missing package file: {required_file}")
    for command in (
        [sys.executable, "papers/paper4/verify_claims.py"],
        [sys.executable, "papers/paper4/audit_claim_evidence.py"],
    ):
        error = run_gate(command)
        if error:
            errors.append(error)
    content_ready = not errors
    gate = {
        "gate_version": "paper4_cg_submission_gate_v001",
        "package_label": "SUBMISSION_READY_CANDIDATE" if content_ready else "DRAFT_NOT_SUBMISSION_READY",
        "scientific_content_ready": content_ready,
        "release_artifacts_ready": content_ready,
        "submission_ready": content_ready and os.environ.get("PAPER4_PORTAL_VERIFIED") == "1",
        "author_metadata_complete": content_ready,
        "rights_linkage_signoff_complete": content_ready,
        "release_tag": RELEASE_TAG,
        "data_release_tag": "data-v002",
        "doi": SOFTWARE_DOI,
        "doi_type": "software",
        "article_doi": None,
        "data_doi": DATA_DOI,
        "doi_status": (
            f"published software archive {SOFTWARE_ARCHIVE['version']}; "
            "not a journal-article DOI"
        ),
        "manuscript_wc_word_count": manuscript_word_count,
        "manuscript_main_text_word_count": manuscript_main_text_word_count,
        "manuscript_source_whitespace_word_count": manuscript_source_whitespace_word_count,
        "manuscript_wc_limit": MAX_CAGEO_WORDS,
        "citation_key_count": len(cited_keys),
        "errors": errors,
        "external_review_required": [
            "final Computers & Geosciences portal upload and artwork preview",
            "obtain and record the publisher-assigned C&G article DOI",
            "complete the author-controlled Zenodo upload and Publish action for v1.0.9",
        ],
    }
    # The gate is committed and rebuilt on Ubuntu and Windows CI runners.
    OUT.write_bytes((json.dumps(gate, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps(gate, indent=2, sort_keys=True))
    if errors:
        raise SystemExit("\n".join(errors))


if __name__ == "__main__":
    main()

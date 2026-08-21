#!/usr/bin/env python3
"""Assemble the Paper 4 manuscript-facing upload files.

The bundle intentionally contains no source PDFs, rendered source pages, raw
OCR, model weights, or credentials. Text files are normalized to UTF-8/LF so
the checksums are stable across Windows and Ubuntu checkouts.
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "papers" / "paper4"
OUT = PAPER / "submission_bundle"
CAGEO = PAPER / "submission" / "cageo"
RELEASE_METADATA = json.loads(
    (PAPER / "release_metadata.json").read_text(encoding="utf-8")
)
RELEASE_TAG = RELEASE_METADATA["release_tag"]
DATA_RELEASE_TAG = "data-v002"
SOFTWARE_ARCHIVE = RELEASE_METADATA["software_archive"]
SOFTWARE_DOI = SOFTWARE_ARCHIVE["doi"]
DATA_DOI = RELEASE_METADATA["data_archive"]["doi"]


TEXT_FILES = {
    "Paper4_Main_Manuscript.md": PAPER / "manuscript.md",
    "Paper4_Supplementary_Methods.md": PAPER / "supplement.md",
    "Paper4_Supplementary_Figure_Captions.md": PAPER / "supplementary_captions.md",
    "Paper4_Main_Tables.md": PAPER / "main_tables.md",
    "Paper4_Data_Code_Availability.md": PAPER / "data_code_availability.md",
    "Paper4_Reproduce.md": PAPER / "REPRODUCE.md",
    "Paper4_Rights_Linkage_Signoff.md": CAGEO / "RIGHTS_LINKAGE_SIGNOFF.md",
    "Paper4_Highlights.txt": CAGEO / "highlights.txt",
}

FIGURE_FILES = {
    "Paper4_Figure_1.png": PAPER / "figures" / "F1_trustworthy_framework.png",
    "Paper4_Figure_1.pdf": PAPER / "figures" / "Figure_1.pdf",
    "Paper4_Figure_2.png": PAPER / "figures" / "F2_vlm_source_shift.png",
    "Paper4_Figure_2.pdf": PAPER / "figures" / "Figure_2.pdf",
    "Paper4_Figure_3.png": PAPER / "figures" / "F3_assurance_frontier.png",
    "Paper4_Figure_3.pdf": PAPER / "figures" / "Figure_3.pdf",
    "Paper4_Figure_4.png": PAPER / "figures" / "F4_spatial_support_consequence.png",
    "Paper4_Figure_4.pdf": PAPER / "figures" / "Figure_4.pdf",
    "Paper4_Graphical_Abstract.png": PAPER / "figures" / "graphical_abstract.png",
    "Paper4_Graphical_Abstract.pdf": PAPER / "figures" / "graphical_abstract.pdf",
    "Paper4_Supplementary_Figure_S1.png": PAPER / "figures" / "F4_risk_coverage_frontier.png",
    "Paper4_Supplementary_Figure_S1.pdf": PAPER / "figures" / "Supplementary_Figure_S1.pdf",
    "Paper4_Supplementary_Figure_S2.png": PAPER / "figures" / "F5_threshold_development_curve.png",
    "Paper4_Supplementary_Figure_S2.pdf": PAPER / "figures" / "Supplementary_Figure_S2.pdf",
    "Paper4_Supplementary_Figure_S3.png": PAPER / "figures" / "F7_controlled_error_mechanisms.png",
    "Paper4_Supplementary_Figure_S3.pdf": PAPER / "figures" / "Supplementary_Figure_S3.pdf",
}

JSON_FILES = {
    "Paper4_Figure_Manifest.json": PAPER / "figure_manifest.json",
}

FINAL_FILES = {
    "Paper4_Final_Manuscript.md": CAGEO / "manuscript_final.md",
    "Paper4_Final_Manuscript.pdf": CAGEO / "manuscript_final.pdf",
}
LATEX_SOURCE_ARCHIVE = "Paper4_CAGEO_LaTeX_Source_v1.0.8.zip"
LATEX_SOURCE_FILES = {
    "manuscript.tex": CAGEO / "manuscript.tex",
    "references_cageo.bib": CAGEO / "references_cageo.bib",
    "cas-sc.cls": CAGEO / "cas-sc.cls",
    "cas-common.sty": CAGEO / "cas-common.sty",
    "cas-model2-names.bst": CAGEO / "cas-model2-names.bst",
    **{
        f"figures/Figure_{number}.pdf": PAPER / "figures" / f"Figure_{number}.pdf"
        for number in range(1, 5)
    },
}
RELEASE_DATE_PARTS = tuple(
    int(part) for part in RELEASE_METADATA["release_date"].split("-")
)
ZIP_DATE_TIME = (*RELEASE_DATE_PARTS, 0, 0, 0)
SOURCE_DATE_EPOCH = int(
    datetime(*RELEASE_DATE_PARTS, tzinfo=timezone.utc).timestamp()
)
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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_text_bytes(path: Path) -> bytes:
    # newline=None normalizes CRLF/CR to logical newlines before emitting LF.
    with path.open("r", encoding="utf-8", newline=None) as handle:
        text = handle.read()
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def copy_text(source: Path, destination: Path) -> bytes:
    data = normalized_text_bytes(source)
    destination.write_bytes(data)
    return data


def copy_bundle_manuscript(source: Path, destination: Path) -> bytes:
    text = normalized_text_bytes(source).decode("utf-8")
    for source_path, bundle_path in BUNDLE_FIGURE_LINKS.items():
        text = text.replace(f"]({source_path})", f"]({bundle_path})")
    data = text.encode("utf-8")
    destination.write_bytes(data)
    return data


def copy_binary(source: Path, destination: Path) -> bytes:
    data = source.read_bytes()
    destination.write_bytes(data)
    return data


def latex_archive_bytes(source: Path) -> bytes:
    return source.read_bytes() if source.suffix.lower() == ".pdf" else normalized_text_bytes(source)


def write_stored_zip_member(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=ZIP_DATE_TIME)
    info.create_system = 3
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)


def build_latex_source_archive(destination: Path) -> tuple[bytes, list[Path]]:
    files: list[dict[str, object]] = []
    members: list[tuple[str, bytes]] = []
    sources: list[Path] = []
    for archive_path, source in sorted(LATEX_SOURCE_FILES.items()):
        data = latex_archive_bytes(source)
        members.append((archive_path, data))
        sources.append(source)
        files.append(
            {
                "archive_path": archive_path,
                "source": source.relative_to(ROOT).as_posix(),
                "bytes": len(data),
                "sha256": sha256_bytes(data),
            }
        )
    source_manifest = {
        "schema": "paper4_cageo_latex_source_v001",
        "release_tag": RELEASE_TAG,
        "purpose": "editable Computers & Geosciences LaTeX submission source",
        "entrypoint": "manuscript.tex",
        "tested_engine": "Tectonic 0.17.0",
        "build_command": "tectonic manuscript.tex --keep-logs --reruns 2",
        "build_environment": {"SOURCE_DATE_EPOCH": str(SOURCE_DATE_EPOCH)},
        "source_date_epoch": SOURCE_DATE_EPOCH,
        "expected_pdf_sha256": sha256_bytes(
            (CAGEO / "manuscript_final.pdf").read_bytes()
        ),
        "files": files,
    }
    manifest_bytes = (
        json.dumps(source_manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in members:
            write_stored_zip_member(archive, name, data)
        write_stored_zip_member(archive, "SOURCE_MANIFEST.json", manifest_bytes)
    data = buffer.getvalue()
    destination.write_bytes(data)
    return data, sources


def entry(name: str, source: Path, data: bytes, role: str) -> dict[str, object]:
    return {
        "file": name,
        "role": role,
        "source": source.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "sha256": sha256_bytes(data),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, object]] = []

    for name, source in TEXT_FILES.items():
        destination = OUT / name
        if name == "Paper4_Main_Manuscript.md":
            data = copy_bundle_manuscript(source, destination)
            role = "main manuscript"
        else:
            data = copy_text(source, destination)
            role = (
                "submission highlights"
                if name == "Paper4_Highlights.txt"
                else "supplementary/reproducibility document"
            )
        upload_entry = entry(name, source, data, role)
        if name == "Paper4_Main_Manuscript.md":
            upload_entry["transformation"] = BUNDLE_MANUSCRIPT_TRANSFORMATION
        entries.append(upload_entry)

    for name, source in FIGURE_FILES.items():
        destination = OUT / name
        data = copy_binary(source, destination)
        if name.startswith("Paper4_Figure_"):
            role = "main figure"
        elif name.startswith("Paper4_Graphical_Abstract"):
            role = "graphical abstract"
        else:
            role = "supplementary figure"
        entries.append(entry(name, source, data, role))

    for name, source in JSON_FILES.items():
        destination = OUT / name
        data = copy_text(source, destination)
        entries.append(entry(name, source, data, "figure manifest"))

    for name, source in FINAL_FILES.items():
        destination = OUT / name
        data = (
            copy_bundle_manuscript(source, destination)
            if source.suffix.lower() == ".md"
            else copy_binary(source, destination)
        )
        upload_entry = entry(name, source, data, "final manuscript")
        if source.suffix.lower() == ".md":
            upload_entry["transformation"] = BUNDLE_MANUSCRIPT_TRANSFORMATION
        entries.append(upload_entry)

    latex_destination = OUT / LATEX_SOURCE_ARCHIVE
    latex_data, latex_sources = build_latex_source_archive(latex_destination)
    entries.append(
        {
            "file": LATEX_SOURCE_ARCHIVE,
            "role": "editable LaTeX manuscript source archive",
            "sources": [path.relative_to(ROOT).as_posix() for path in latex_sources],
            "bytes": len(latex_data),
            "sha256": sha256_bytes(latex_data),
        }
    )

    manifest = {
        "schema": "paper4_cg_upload_bundle_v001",
        "package_label": "SUBMISSION_READY_CANDIDATE",
        "submission_ready": False,
        "upload_ready": True,
        "purpose": "fixed manuscript-facing file assembly for Computers & Geosciences submission",
        "rights_scope": "The sole author reviewed the complete Paper 4 package and exact data-v002 selection for public dissemination; the data review covered source terms, item scope, privacy, sensitive locations, embedded content, attribution, and linkage. The sign-off supersedes earlier provisional ledger statuses for this named release scope; historical experiment-run metadata remains historical. Source-specific obligations remain in the ledger.",
        "rights_linkage_signoff": f"Yifan Du, sole and corresponding author, confirms that {RELEASE_TAG} contains the complete result-reproduction package and {DATA_RELEASE_TAG} is its author-reviewed data companion.",
        "release_tag": RELEASE_TAG,
        "data_release_tag": DATA_RELEASE_TAG,
        "doi": SOFTWARE_DOI,
        "doi_type": "software",
        "article_doi": None,
        "data_doi": DATA_DOI,
        "doi_status": (
            f"published software archive {SOFTWARE_ARCHIVE['version']}; "
            "not a journal-article DOI"
        ),
        "supplementary_caption_file": "Paper4_Supplementary_Figure_Captions.md",
        "artwork_pairing": {
            "policy": "Each PNG is a lossless RGB rasterization of its matching canonical PDF page; main artwork uses 300 DPI and supplementary artwork uses 600 DPI.",
            "renderer": "PyMuPDF",
            "main_dpi": 300,
            "supplementary_dpi": 600,
        },
        "files": sorted(entries, key=lambda row: str(row["file"])),
    }
    manifest_path = OUT / "Paper4_Upload_Manifest.json"
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    manifest_path.write_bytes(manifest_bytes)

    readme = """# Paper 4 manuscript-facing upload bundle

This directory contains the fixed files for individual upload to a
Computers & Geosciences submission portal. Author metadata, declarations, and
rights/linkage sign-off are complete. `Paper4_Supplementary_Figure_Captions.md`
is the standalone caption file for Supplementary Figures S1–S3 and
Supplementary Tables S1–S4; the detailed supplementary methods are in
`Paper4_Supplementary_Methods.md`.

The final manuscript pair is `Paper4_Final_Manuscript.md` and
`Paper4_Final_Manuscript.pdf`; the Markdown and PDF carry the same audited
scientific content, declarations, metrics, limitations, and references. The
two bundled manuscript Markdown files link to the flat `Paper4_Figure_*.png`
assets in this directory, so their figure previews resolve offline. The
editable main-manuscript upload is
`Paper4_CAGEO_LaTeX_Source_v1.0.8.zip`; it contains the final TeX, BibTeX,
C&G class/style files, four canonical vector figures, and an internal source
manifest. The
artwork files are the four main figures, the graphical abstract, and three
supplementary figures in paired PDF/PNG form. Each main PNG is rendered from
the same canonical PDF page used in the final manuscript; each supplementary
PNG is rendered at 600 DPI from its matching vector PDF. The other
Markdown files are repository-native supplementary/reproducibility sources;
`Paper4_Highlights.txt` is the separate editable highlights upload required by
the journal;
convert them to the journal's required manuscript format at submission time
without changing audited text or numbers. `Paper4_Upload_Manifest.json`
records source paths and SHA-256 hashes for every file.

The manuscript-facing bundle does not duplicate the large source/data archive
or include model weights or private credentials. The author-reviewed selected
source files and structured datasets are published separately as `data-v002`.
The complete result-reproduction workflow is documented in
`Paper4_Reproduce.md` and the repository-level `publication_evidence/` bundle.
The corrected Paper 4 release is `paper4-cageo-v1.0.8`. The published
Zenodo software archive is `paper4-cageo-v1.0.6` at
`https://doi.org/10.5281/zenodo.22030229`; that is a software DOI, not a
journal-article DOI. The published `data-v002` companion is at
`https://doi.org/10.5281/zenodo.22031703` and is reused without changing its
contents. A future Zenodo v1.0.8 archive must be created as a new version.
"""
    (OUT / "README.md").write_bytes(readme.replace("\r\n", "\n").encode("utf-8"))
    print(OUT)
    print(manifest_path)


if __name__ == "__main__":
    main()

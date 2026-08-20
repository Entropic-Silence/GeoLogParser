#!/usr/bin/env python3
"""Assemble the Paper 4 manuscript-facing upload files.

The bundle intentionally contains no source PDFs, rendered source pages, raw
OCR, model weights, or credentials. Text files are normalized to UTF-8/LF so
the checksums are stable across Windows and Ubuntu checkouts.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "papers" / "paper4"
OUT = PAPER / "submission_bundle"
CAGEO = PAPER / "submission" / "cageo"


TEXT_FILES = {
    "Paper4_Main_Manuscript.md": PAPER / "manuscript.md",
    "Paper4_Supplementary_Methods.md": PAPER / "supplement.md",
    "Paper4_Supplementary_Figure_Captions.md": PAPER / "supplementary_captions.md",
    "Paper4_Main_Tables.md": PAPER / "main_tables.md",
    "Paper4_Data_Code_Availability.md": PAPER / "data_code_availability.md",
    "Paper4_Reproduce.md": PAPER / "REPRODUCE.md",
    "Paper4_Rights_Linkage_Signoff.md": CAGEO / "RIGHTS_LINKAGE_SIGNOFF.md",
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
    "Paper4_Graphical_Abstract.pdf": PAPER / "figures" / "graphical_abstract.pdf",
    "Paper4_Supplementary_Figure_S1.png": PAPER / "figures" / "F4_risk_coverage_frontier.png",
    "Paper4_Supplementary_Figure_S2.png": PAPER / "figures" / "F5_threshold_development_curve.png",
    "Paper4_Supplementary_Figure_S3.png": PAPER / "figures" / "F7_controlled_error_mechanisms.png",
}

JSON_FILES = {
    "Paper4_Figure_Manifest.json": PAPER / "figure_manifest.json",
}

FINAL_FILES = {
    "Paper4_Final_Manuscript.md": CAGEO / "manuscript_final.md",
    "Paper4_Final_Manuscript.pdf": CAGEO / "manuscript_final.pdf",
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


def copy_binary(source: Path, destination: Path) -> bytes:
    data = source.read_bytes()
    destination.write_bytes(data)
    return data


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
        data = copy_text(source, destination)
        role = "main manuscript" if name == "Paper4_Main_Manuscript.md" else "supplementary/reproducibility document"
        entries.append(entry(name, source, data, role))

    for name, source in FIGURE_FILES.items():
        destination = OUT / name
        data = copy_binary(source, destination)
        role = "main figure" if name.startswith("Paper4_Figure_") else "supplementary figure"
        entries.append(entry(name, source, data, role))

    for name, source in JSON_FILES.items():
        destination = OUT / name
        data = copy_text(source, destination)
        entries.append(entry(name, source, data, "figure manifest"))

    for name, source in FINAL_FILES.items():
        destination = OUT / name
        data = copy_text(source, destination) if source.suffix.lower() == ".md" else copy_binary(source, destination)
        entries.append(entry(name, source, data, "final manuscript"))

    manifest = {
        "schema": "paper4_cg_upload_bundle_v001",
        "package_label": "DOI_PENDING_RELEASE_CANDIDATE",
        "submission_ready": True,
        "purpose": "fixed manuscript-facing file assembly for Computers & Geosciences submission",
        "rights_scope": "The sole author reviewed the complete Paper 4 package and exact data-v002 selection for public dissemination; the data review covered source terms, item scope, privacy, sensitive locations, embedded content, attribution, and linkage. Source-specific obligations remain in the ledger.",
        "rights_linkage_signoff": "Yifan Du, sole and corresponding author, confirms that paper4-cageo-v1.0.1 contains the complete result-reproduction package and data-v002 is its author-reviewed data companion.",
        "release_tag": "paper4-cageo-v1.0.1",
        "data_release_tag": "data-v002",
        "doi_status": "pending author-created archival DOI",
        "supplementary_caption_file": "Paper4_Supplementary_Figure_Captions.md",
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
Supplementary Tables S1–S3; the detailed supplementary methods are in
`Paper4_Supplementary_Methods.md`.

The final manuscript pair is `Paper4_Final_Manuscript.md` and
`Paper4_Final_Manuscript.pdf`; the Markdown and PDF carry the same audited
scientific content, declarations, metrics, limitations, and references. The
PNG files are the four main figures and three supplementary figures. The other
Markdown files are repository-native supplementary/reproducibility sources;
convert them to the journal's required manuscript format at submission time
without changing audited text or numbers. `Paper4_Upload_Manifest.json`
records source paths and SHA-256 hashes for every file.

The manuscript-facing bundle does not duplicate the large source/data archive
or include model weights or private credentials. The author-reviewed selected
source files and structured datasets are published separately as `data-v002`.
The complete result-reproduction workflow is documented in
`Paper4_Reproduce.md` and the repository-level `publication_evidence/` bundle.
The complete Paper 4 release tag is `paper4-cageo-v1.0.1`; archival DOI fields
will be appended after deposit.
"""
    (OUT / "README.md").write_bytes(readme.replace("\r\n", "\n").encode("utf-8"))
    print(OUT)
    print(manifest_path)


if __name__ == "__main__":
    main()

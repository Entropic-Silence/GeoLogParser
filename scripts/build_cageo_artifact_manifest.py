#!/usr/bin/env python3
"""Record final Paper 4 C&G artifact hashes and external-action status."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "papers" / "paper4"
CAGEO = PAPER / "submission" / "cageo"
OUT = CAGEO / "CAGEO_ARTIFACT_MANIFEST.json"


FILES = [
    CAGEO / "manuscript_final.md",
    CAGEO / "manuscript_final.pdf",
    CAGEO / "manuscript.tex",
    CAGEO / "references_cageo.bib",
    CAGEO / "highlights.txt",
    CAGEO / "manuscript_review_v2.pdf",
    CAGEO / "CAGEO_REQUIREMENTS.md",
    CAGEO / "FOCUS_AND_REVIEW_AUDIT.md",
    CAGEO / "REVIEW_VERSION_NOTES.md",
    PAPER / "submission_bundle" / "Paper4_Upload_Manifest.json",
    PAPER / "submission_bundle" / "Paper4_Final_Manuscript.md",
    PAPER / "submission_bundle" / "Paper4_Final_Manuscript.pdf",
    PAPER / "figures" / "Figure_1.pdf",
    PAPER / "figures" / "Figure_2.pdf",
    PAPER / "figures" / "Figure_3.pdf",
    PAPER / "figures" / "Figure_4.pdf",
    PAPER / "figures" / "graphical_abstract.pdf",
]


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in FILES if not path.exists()]
    if missing:
        raise SystemExit(f"Missing artifact(s): {missing}")
    payload = {
        "schema": "paper4_cageo_artifact_manifest_v001",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "branch": subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=ROOT, text=True
        ).strip(),
        "source_git_commit": git_head(),
        "repository": "https://github.com/Entropic-Silence/GeoLogParser",
        "license": "MIT (source code)",
        "author": {
            "name": "Yifan Du",
            "affiliation": "North China University of Water Resources and Electric Power",
            "orcid": "0009-0008-7740-5408",
            "email": "duyifan619916@gmail.com",
            "corresponding_author": True,
        },
        "doi": None,
        "doi_status": "pending author-authorized Zenodo/DataCite archival deposit",
        "rights_status": (
            "Programmatic figures and redistributable structured/reanalysis assets are included; "
            "source PDFs, rendered pages, raw OCR regions, and model weights remain excluded "
            "where third-party terms apply. Final item-level rights sign-off is an author action."
        ),
        "files": [
            {
                "file": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in FILES
        ],
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(OUT)
    print(json.dumps({"source_git_commit": payload["source_git_commit"], "file_count": len(FILES)}))


if __name__ == "__main__":
    main()

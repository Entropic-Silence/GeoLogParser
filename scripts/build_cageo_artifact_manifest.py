#!/usr/bin/env python3
"""Record final Paper 4 C&G artifact hashes and release status."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "papers" / "paper4"
CAGEO = PAPER / "submission" / "cageo"
OUT = CAGEO / "CAGEO_ARTIFACT_MANIFEST.json"
DELIVERY_OUT = PAPER / "submission_bundle" / "Paper4_Final_Delivery_SHA256.json"
RELEASE_TAG = os.environ.get("PAPER4_RELEASE_TAG", "paper4-cageo-v1.0.4")
DATA_RELEASE_TAG = "data-v002"


FILES = [
    CAGEO / "manuscript_final.md",
    CAGEO / "manuscript_final.pdf",
    CAGEO / "manuscript.tex",
    CAGEO / "references_cageo.bib",
    CAGEO / "highlights.txt",
    CAGEO / "CAGEO_REQUIREMENTS.md",
    CAGEO / "FOCUS_AND_REVIEW_AUDIT.md",
    CAGEO / "REVIEW_VERSION_NOTES.md",
    CAGEO / "RIGHTS_LINKAGE_SIGNOFF.md",
    PAPER / "submission_bundle" / "Paper4_Upload_Manifest.json",
    PAPER / "submission_bundle" / "Paper4_Final_Manuscript.md",
    PAPER / "submission_bundle" / "Paper4_Final_Manuscript.pdf",
    PAPER / "submission_bundle" / "Paper4_Supplementary_Methods.md",
    PAPER / "submission_bundle" / "Paper4_Supplementary_Figure_Captions.md",
    PAPER / "submission_bundle" / "Paper4_Main_Tables.md",
    PAPER / "submission_bundle" / "Paper4_Rights_Linkage_Signoff.md",
    PAPER / "submission_bundle" / "Paper4_Highlights.txt",
    PAPER / "submission_bundle" / "Paper4_Figure_Manifest.json",
    PAPER / "submission_bundle" / "Paper4_Figure_1.pdf",
    PAPER / "submission_bundle" / "Paper4_Figure_2.pdf",
    PAPER / "submission_bundle" / "Paper4_Figure_3.pdf",
    PAPER / "submission_bundle" / "Paper4_Figure_4.pdf",
    PAPER / "submission_bundle" / "Paper4_Graphical_Abstract.pdf",
    PAPER / "submission_bundle" / "Paper4_Supplementary_Figure_S1.png",
    PAPER / "submission_bundle" / "Paper4_Supplementary_Figure_S2.png",
    PAPER / "submission_bundle" / "Paper4_Supplementary_Figure_S3.png",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_value(*arguments: str) -> str | None:
    """Return a normalized git value without making generation depend on git."""

    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    value = result.stdout.strip()
    return value or None


def git_status() -> str:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return result.stdout


def manifest_git_metadata() -> dict[str, object]:
    head = os.environ.get("PAPER4_SOURCE_GIT_COMMIT") or git_value("rev-parse", "HEAD")
    branch = os.environ.get("PAPER4_SOURCE_GIT_BRANCH") or git_value(
        "symbolic-ref", "--quiet", "--short", "HEAD"
    )
    tag_commit = git_value("rev-parse", "--verify", f"refs/tags/{RELEASE_TAG}^{{}}")
    status = git_status()
    generated_paths = {
        OUT.relative_to(ROOT).as_posix(),
        DELIVERY_OUT.relative_to(ROOT).as_posix(),
    }
    dirty_entries = [
        line[3:].strip()
        for line in status.splitlines()
        if len(line) >= 4 and line[3:].strip() not in generated_paths
    ]
    return {
        "branch": branch or "detached-or-unavailable",
        "source_git_commit": head or "unavailable",
        "source_git_commit_scope": (
            "commit checked out when this manifest was generated; if the release tag "
            "is created after generation, resolved_release_tag_commit records the tag target"
        ),
        "resolved_release_tag_commit": tag_commit,
        "working_tree_dirty": bool(dirty_entries),
    }


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in FILES if not path.exists()]
    if missing:
        raise SystemExit(f"Missing artifact(s): {missing}")
    git_metadata = manifest_git_metadata()
    payload = {
        "schema": "paper4_cageo_artifact_manifest_v001",
        "generated_on": "2026-08-20",
        **git_metadata,
        "release_tag": RELEASE_TAG,
        "data_release_tag": DATA_RELEASE_TAG,
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
        "doi_status": "pending author-created archival DOI for tagged release",
        "rights_status": (
            "Yifan Du, sole and corresponding author, reviewed and screened the complete "
            "Paper 4 package and exact data-v002 selection for public dissemination. The "
            "data review covered source terms, item scope, privacy, sensitive locations, "
            "embedded content, attribution, and linkage. This sign-off supersedes earlier "
            "provisional ledger statuses for the named release scope; historical run "
            "metadata remains historical. Source-specific obligations remain."
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
    OUT.write_bytes((json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    delivery_files = [
        path for path in FILES
        if path.name.startswith("Paper4_Final_Manuscript")
        or path.name.startswith("Paper4_Figure_")
        or path.name == "Paper4_Graphical_Abstract.pdf"
        or path.name == "Paper4_Highlights.txt"
        or path.name.startswith("Paper4_Supplementary_")
        or path.name == "Paper4_Main_Tables.md"
    ]
    delivery = {
        "manifest_version": "paper4_final_delivery_v002",
        "generated_on": "2026-08-20",
        "scope": "Final manuscript, vector artwork, tables, and supplementary material",
        "repository": "https://github.com/Entropic-Silence/GeoLogParser",
        "release_tag": RELEASE_TAG,
        "data_release_tag": DATA_RELEASE_TAG,
        "source_git_commit": git_metadata["source_git_commit"],
        "resolved_release_tag_commit": git_metadata["resolved_release_tag_commit"],
        "doi": None,
        "doi_status": "pending author-created archival DOI for tagged release",
        "files": [
            {
                "name": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in delivery_files
        ],
    }
    DELIVERY_OUT.write_bytes(
        (json.dumps(delivery, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    # Fail immediately if generation or a later Windows checkout changed any
    # path, byte count, or hash.  The manifest intentionally excludes itself
    # and the delivery checksum file to avoid a self-referential hash cycle.
    generated = json.loads(OUT.read_text(encoding="utf-8"))
    for entry in generated["files"]:
        path = ROOT / entry["file"]
        if not path.is_file():
            raise SystemExit(f"Generated manifest points to missing file: {entry['file']}")
        observed = sha256(path)
        if observed != entry["sha256"] or path.stat().st_size != entry["bytes"]:
            raise SystemExit(f"Generated manifest self-check failed: {entry['file']}")
    generated_delivery = json.loads(DELIVERY_OUT.read_text(encoding="utf-8"))
    for entry in generated_delivery["files"]:
        path = PAPER / "submission_bundle" / entry["name"]
        if not path.is_file():
            raise SystemExit(f"Generated delivery manifest points to missing file: {entry['name']}")
        observed = sha256(path)
        if observed != entry["sha256"] or path.stat().st_size != entry["bytes"]:
            raise SystemExit(f"Generated delivery manifest self-check failed: {entry['name']}")
    print(OUT)
    print(DELIVERY_OUT)
    print(json.dumps({"release_tag": RELEASE_TAG, "file_count": len(FILES)}))


if __name__ == "__main__":
    main()

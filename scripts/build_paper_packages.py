#!/usr/bin/env python3
"""Build traceable Markdown review bundles and evidence audits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.paper_package import audit_manuscript, evidence_markdown, review_bundle, sha256


ROOT = Path(__file__).resolve().parents[1]


def write_text_lf(path: Path, contents: str) -> None:
    path.write_bytes(contents.encode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper-root", type=Path, default=ROOT / "papers")
    arguments = parser.parse_args()
    bibliography = arguments.paper_root / "references.bib"
    claim_registry = arguments.paper_root / "claim_registry.json"
    literature_evidence = ROOT / "docs" / "literature_evidence.yaml"
    package_rows = []
    external_gate = ROOT / "docs" / "submission_blockers.md"
    for paper in ("paper1", "paper2", "paper3"):
        paper_root = arguments.paper_root / paper
        manuscript = paper_root / "manuscript.md"
        supplement = paper_root / "supplement.md"
        generated_results = paper_root / "generated" / "current_results.md"
        major_revision_tables = paper_root / "generated" / "major_revision_tables.md"
        index = ROOT / "experiments" / paper / "result_index.jsonl"
        audit = audit_manuscript(
            paper, manuscript, bibliography, index, ROOT, claim_registry=claim_registry,
            literature_evidence=literature_evidence,
        )
        output_root = paper_root / "generated" / "package"
        output_root.mkdir(parents=True, exist_ok=True)
        audit_path = output_root / "evidence_audit.json"
        audit_md_path = output_root / "evidence_audit.md"
        bundle_path = output_root / f"manuscript_{audit['package_label']}.md"
        # Remove stale bundles from an earlier readiness state so the package
        # directory cannot contain both a draft and a current review bundle.
        for stale_bundle in output_root.glob("manuscript_*.md"):
            if stale_bundle != bundle_path:
                stale_bundle.unlink()
        write_text_lf(audit_path, json.dumps(audit, indent=2, sort_keys=True) + "\n")
        write_text_lf(audit_md_path, evidence_markdown(audit))
        manuscript_text = manuscript.read_text(encoding="utf-8")
        if supplement.is_file():
            manuscript_text += "\n\n# Linked Supplementary Material\n\n" + supplement.read_text(encoding="utf-8")
        generated_text = major_revision_tables.read_text(encoding="utf-8")
        generated_text += "\n\n# Full Indexed Result Catalogue\n\n"
        generated_text += generated_results.read_text(encoding="utf-8")
        write_text_lf(bundle_path, review_bundle(manuscript_text, generated_text, audit))
        package_rows.append({
            "paper": paper, "package_label": audit["package_label"],
            "scientific_content_ready": audit["scientific_content_ready"],
            "submission_ready": False,
            "submission_gate_path": external_gate.relative_to(ROOT).as_posix(),
            "evidence_audit_path": audit_path.relative_to(arguments.paper_root).as_posix(),
            "evidence_audit_sha256": sha256(audit_path),
            "review_bundle_path": bundle_path.relative_to(arguments.paper_root).as_posix(),
            "review_bundle_sha256": sha256(bundle_path),
            "supplement_path": supplement.relative_to(arguments.paper_root).as_posix() if supplement.is_file() else None,
            "supplement_sha256": sha256(supplement) if supplement.is_file() else None,
            "major_revision_tables_path": major_revision_tables.relative_to(arguments.paper_root).as_posix(),
            "major_revision_tables_sha256": sha256(major_revision_tables),
        })
        print(bundle_path)
    # Paper 4 is an independently curated C&G package rather than a generated
    # three-paper review bundle.  Include its evidence and submission gate in
    # the central manifest without forcing it through the legacy result-index
    # schema used by Papers I–III.
    paper4_root = arguments.paper_root / "paper4"
    paper4_gate = paper4_root / "submission_gate.json"
    paper4_audit = paper4_root / "claim_evidence_audit.json"
    if paper4_gate.is_file():
        gate = json.loads(paper4_gate.read_text(encoding="utf-8"))
        package_rows.append({
            "paper": "paper4",
            "package_label": gate["package_label"],
            "scientific_content_ready": gate["scientific_content_ready"],
            "submission_ready": bool(gate.get("submission_ready", False)),
            "submission_gate_path": external_gate.relative_to(ROOT).as_posix(),
            "evidence_audit_path": paper4_audit.relative_to(arguments.paper_root).as_posix(),
            "evidence_audit_sha256": sha256(paper4_audit) if paper4_audit.is_file() else None,
            "review_bundle_path": "paper4/manuscript.md",
            "review_bundle_sha256": sha256(paper4_root / "manuscript.md"),
            "supplement_path": "paper4/supplement.md",
            "supplement_sha256": sha256(paper4_root / "supplement.md"),
            "supplementary_captions_path": "paper4/supplementary_captions.md",
            "supplementary_captions_sha256": sha256(paper4_root / "supplementary_captions.md"),
            "major_revision_tables_path": "paper4/main_tables.md",
            "major_revision_tables_sha256": sha256(paper4_root / "main_tables.md"),
            "upload_bundle_path": "paper4/submission_bundle",
            "upload_manifest_path": "paper4/submission_bundle/Paper4_Upload_Manifest.json",
            "upload_manifest_sha256": sha256(paper4_root / "submission_bundle/Paper4_Upload_Manifest.json"),
        })
        print(paper4_root / "manuscript.md")
    manifest = {
        "package_schema_version": "paper_packages_v001",
        "scope": "traceable review packages; submission readiness is evidence-gated",
        "scientific_content_ready": all(row["scientific_content_ready"] for row in package_rows),
        "submission_gate_path": external_gate.relative_to(ROOT).as_posix(),
        "bibliography_path": bibliography.relative_to(ROOT).as_posix(),
        "bibliography_sha256": sha256(bibliography),
        "claim_registry_path": claim_registry.relative_to(ROOT).as_posix(),
        "claim_registry_sha256": sha256(claim_registry),
        "literature_evidence_path": literature_evidence.relative_to(ROOT).as_posix(),
        "literature_evidence_sha256": sha256(literature_evidence),
        "papers": package_rows,
        "all_submission_ready": all(row["submission_ready"] for row in package_rows),
    }
    destination = arguments.paper_root / "package_manifest.json"
    write_text_lf(destination, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(destination)


if __name__ == "__main__":
    main()

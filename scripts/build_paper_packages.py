#!/usr/bin/env python3
"""Build three traceable Markdown review bundles and evidence audits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.paper_package import audit_manuscript, evidence_markdown, review_bundle, sha256


ROOT = Path(__file__).resolve().parents[1]


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
        audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        audit_md_path.write_text(evidence_markdown(audit), encoding="utf-8")
        manuscript_text = manuscript.read_text(encoding="utf-8")
        if supplement.is_file():
            manuscript_text += "\n\n# Linked Supplementary Material\n\n" + supplement.read_text(encoding="utf-8")
        generated_text = major_revision_tables.read_text(encoding="utf-8")
        generated_text += "\n\n# Full Indexed Result Catalogue\n\n"
        generated_text += generated_results.read_text(encoding="utf-8")
        bundle_path.write_text(review_bundle(manuscript_text, generated_text, audit), encoding="utf-8")
        package_rows.append({
            "paper": paper, "package_label": audit["package_label"],
            "scientific_content_ready": audit["submission_ready"],
            "submission_ready": False,
            "submission_gate_path": str(external_gate.relative_to(ROOT)),
            "evidence_audit_path": str(audit_path.relative_to(arguments.paper_root)),
            "evidence_audit_sha256": sha256(audit_path),
            "review_bundle_path": str(bundle_path.relative_to(arguments.paper_root)),
            "review_bundle_sha256": sha256(bundle_path),
            "supplement_path": str(supplement.relative_to(arguments.paper_root)) if supplement.is_file() else None,
            "supplement_sha256": sha256(supplement) if supplement.is_file() else None,
            "major_revision_tables_path": str(major_revision_tables.relative_to(arguments.paper_root)),
            "major_revision_tables_sha256": sha256(major_revision_tables),
        })
        print(bundle_path)
    manifest = {
        "package_schema_version": "paper_packages_v001",
        "scope": "traceable review packages; submission readiness is evidence-gated",
        "scientific_content_ready": all(row["scientific_content_ready"] for row in package_rows),
        "submission_gate_path": str(external_gate.relative_to(ROOT)),
        "bibliography_path": str(bibliography.relative_to(ROOT)),
        "bibliography_sha256": sha256(bibliography),
        "claim_registry_path": str(claim_registry.relative_to(ROOT)),
        "claim_registry_sha256": sha256(claim_registry),
        "literature_evidence_path": str(literature_evidence.relative_to(ROOT)),
        "literature_evidence_sha256": sha256(literature_evidence),
        "papers": package_rows,
        "all_submission_ready": all(row["submission_ready"] for row in package_rows),
    }
    destination = arguments.paper_root / "package_manifest.json"
    destination.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(destination)


if __name__ == "__main__":
    main()

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
    for paper in ("paper1", "paper2", "paper3"):
        paper_root = arguments.paper_root / paper
        manuscript = paper_root / "manuscript.md"
        generated_results = paper_root / "generated" / "current_results.md"
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
        audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        audit_md_path.write_text(evidence_markdown(audit), encoding="utf-8")
        bundle_path.write_text(review_bundle(
            manuscript.read_text(encoding="utf-8"),
            generated_results.read_text(encoding="utf-8"), audit,
        ), encoding="utf-8")
        package_rows.append({
            "paper": paper, "package_label": audit["package_label"],
            "submission_ready": audit["submission_ready"],
            "evidence_audit_path": str(audit_path.relative_to(arguments.paper_root)),
            "evidence_audit_sha256": sha256(audit_path),
            "review_bundle_path": str(bundle_path.relative_to(arguments.paper_root)),
            "review_bundle_sha256": sha256(bundle_path),
        })
        print(bundle_path)
    manifest = {
        "package_schema_version": "paper_packages_v001",
        "scope": "traceable review packages; submission readiness is evidence-gated",
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

#!/usr/bin/env python3
"""Run the C&G-facing structural submission gate for Paper 4.

The gate verifies scientific content, author metadata, declarations, and the
author-provided rights/linkage sign-off. DOI registration and portal-side
validation remain external actions.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "papers/paper4"
OUT = PAPER / "submission_gate.json"


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", text))


def run_gate(command: list[str]) -> str | None:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        return f"{' '.join(command)} failed: {result.stdout}{result.stderr}"
    return None


def main() -> None:
    manuscript_path = PAPER / "manuscript.md"
    text = manuscript_path.read_text(encoding="utf-8")
    errors: list[str] = []
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
    highlight_count = len([line for line in highlights.splitlines() if line.strip().startswith("-")])
    if not 3 <= highlight_count <= 5:
        errors.append(f"highlights count is {highlight_count}, expected 3–5")
    forbidden = ["fallback manuscript", "ADR-", "project log", "SUBMISSION_READY.md"]
    for term in forbidden:
        if term.lower() in text.lower():
            errors.append(f"internal project language remains in main text: {term}")
    for term in ("Qwen3.8-direct", "Data and code availability"):
        if term.lower() in text.lower():
            errors.append(f"outdated Paper 4 terminology remains in main text: {term}")
    if "**partially reconstructable**" not in text:
        errors.append("main text does not disclose partially reconstructable Qwen runtime provenance")
    required_author_text = [
        "Yifan Du",
        "This research received no specific grant",
        "The author declares no competing interests",
        "Rights and linkage sign-off",
        "paper4-cageo-v1.0.1",
        "data-v002",
    ]
    for term in required_author_text:
        if term not in text:
            errors.append(f"missing author-confirmed submission text: {term}")
    for term in ("ChatGPT", "OpenAI", "generative AI", "AI-assisted technologies"):
        if term.lower() in text.lower():
            errors.append(f"unrequested AI-use disclosure remains in manuscript: {term}")
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
    for figure in (
        "F1_trustworthy_framework.png", "F2_vlm_source_shift.png",
        "F3_assurance_frontier.png", "F4_spatial_support_consequence.png",
    ):
        if not (PAPER / "figures" / figure).is_file():
            errors.append(f"missing main figure: {figure}")
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
    gate = {
        "gate_version": "paper4_cg_submission_gate_v001",
        "package_label": "DOI_PENDING_RELEASE_CANDIDATE" if not errors else "DRAFT_NOT_SUBMISSION_READY",
        "scientific_content_ready": not errors,
        "submission_ready": not errors,
        "author_metadata_complete": not errors,
        "rights_linkage_signoff_complete": not errors,
        "release_tag": "paper4-cageo-v1.0.1",
        "data_release_tag": "data-v002",
        "doi": None,
        "doi_status": "pending author-created archival DOI",
        "manuscript_wc_word_count": len(text.split()),
        "citation_key_count": len(cited_keys),
        "errors": errors,
        "external_review_required": [
            "author-created archival DOI field(s) and corresponding data citation",
            "final Computers & Geosciences portal upload and artwork preview",
        ],
    }
    # The gate is committed and rebuilt on Ubuntu and Windows CI runners.
    OUT.write_bytes((json.dumps(gate, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps(gate, indent=2, sort_keys=True))
    if errors:
        raise SystemExit("\n".join(errors))


if __name__ == "__main__":
    main()

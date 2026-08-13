"""Evidence audits and review bundles for the three manuscripts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Any, Mapping, Sequence

from geologparser.result_index import FORMAL_ELIGIBILITY, verify_index


CITATION_PATTERN = re.compile(r"@([A-Za-z0-9_:-]+)")
BIB_KEY_PATTERN = re.compile(r"^@[^{]+\{([^,]+),", flags=re.MULTILINE)
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^]]*]\(([^)]+)\)")
HEADING_PATTERN = re.compile(r"^##\s+(.+?)\s*$", flags=re.MULTILINE)
TBD_PATTERN = re.compile(r"`TBD`|\[CITATION TO VERIFY]")
EVIDENCE_TAG_PATTERN = re.compile(r"<!--\s*evidence:([A-Za-z0-9_.:-]+)\s*-->")


REQUIRED_SECTION_PREFIXES = {
    "paper1": ("Abstract", "1. Introduction", "2. Related Work", "3. Task Definition",
               "4. Dataset Construction", "5. Baselines", "6. Evaluation", "7. Results",
               "8. Discussion", "9. Reproducibility", "10. Conclusion", "References"),
    "paper2": ("Abstract", "1. Introduction", "2. Related Work", "3. Method",
               "4. Experimental Design", "5. Results", "6. Failure Analysis", "7. Discussion",
               "8. Reproducibility", "9. Conclusion", "References"),
    "paper3": ("Abstract", "1. Introduction", "2. Related Work", "3. Workflow",
               "4. Error-Propagation Method", "5. Database", "6. Results",
               "7. Human-in-the-Loop", "8. Discussion", "9. Reproducibility",
               "10. Conclusion", "References"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _section_present(headings: Sequence[str], prefix: str) -> bool:
    return any(heading == prefix or heading.startswith(prefix) for heading in headings)


def _portable_path(path: Path, repository_root: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(repository_root.resolve()))
    except ValueError:
        return str(resolved)


def _local_links(
    manuscript: Path, text: str, repository_root: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    links = []
    missing = []
    for target in MARKDOWN_LINK_PATTERN.findall(text):
        if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target) or target.startswith("#"):
            continue
        path_text = target.split("#", 1)[0]
        target_path = (manuscript.parent / path_text).resolve()
        exists = target_path.is_file()
        links.append({
            "target": target,
            "resolved_path": _portable_path(target_path, repository_root),
            "exists": exists,
            "sha256": sha256(target_path) if exists else None,
        })
        if not exists:
            missing.append(target)
    return links, missing


def _json_pointer(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise ValueError("JSON pointer must be empty or start with /")
    current = document
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(token)]
        elif isinstance(current, Mapping):
            current = current[token]
        else:
            raise KeyError(token)
    return current


def _claim_assertion_errors(claim_id: str, source_path: Path, claim: Mapping[str, Any]) -> list[str]:
    errors = []
    assertions = claim.get("assertions", [])
    json_document: Any | None = None
    jsonl_documents: list[Any] | None = None
    for assertion in assertions:
        assertion_type = assertion.get("type")
        if assertion_type == "json_pointer_equals":
            try:
                if json_document is None:
                    json_document = json.loads(source_path.read_text(encoding="utf-8"))
                actual = _json_pointer(json_document, assertion["pointer"])
            except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
                errors.append(
                    f"{claim_id}: JSON assertion {assertion.get('pointer')!r} could not be evaluated: {exc}"
                )
            else:
                if actual != assertion.get("expected"):
                    errors.append(
                        f"{claim_id}: JSON assertion {assertion['pointer']!r} expected "
                        f"{assertion.get('expected')!r}, found {actual!r}"
                    )
        elif assertion_type in {
            "jsonl_row_count", "jsonl_pointer_unique_count", "jsonl_pointer_sequence_equals",
        }:
            try:
                if jsonl_documents is None:
                    jsonl_documents = [
                        json.loads(line) for line in source_path.read_text(encoding="utf-8").splitlines()
                        if line.strip()
                    ]
                if assertion_type == "jsonl_row_count":
                    actual = len(jsonl_documents)
                else:
                    values = [_json_pointer(row, assertion["pointer"]) for row in jsonl_documents]
                    if assertion_type == "jsonl_pointer_unique_count":
                        actual = len({json.dumps(value, sort_keys=True) for value in values})
                    else:
                        actual = values
            except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
                errors.append(f"{claim_id}: JSONL assertion could not be evaluated: {exc}")
            else:
                if actual != assertion.get("expected"):
                    errors.append(
                        f"{claim_id}: JSONL assertion {assertion_type!r} expected "
                        f"{assertion.get('expected')!r}, found {actual!r}"
                    )
        elif assertion_type == "sqlite_row_count":
            table = assertion.get("table")
            if not isinstance(table, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table):
                errors.append(f"{claim_id}: invalid SQLite table name {table!r}")
                continue
            try:
                uri = source_path.resolve().as_uri() + "?mode=ro"
                with sqlite3.connect(uri, uri=True) as connection:
                    actual = connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            except sqlite3.Error as exc:
                errors.append(f"{claim_id}: SQLite assertion for {table!r} failed: {exc}")
            else:
                if actual != assertion.get("expected"):
                    errors.append(
                        f"{claim_id}: SQLite row count for {table!r} expected "
                        f"{assertion.get('expected')!r}, found {actual!r}"
                    )
        else:
            errors.append(f"{claim_id}: unsupported claim assertion type {assertion_type!r}")
    return errors


def audit_manuscript(
    paper: str, manuscript: Path, bibliography: Path, result_index: Path,
    repository_root: Path, claim_registry: Path | None = None,
) -> dict[str, Any]:
    text = manuscript.read_text(encoding="utf-8")
    bibliography_text = bibliography.read_text(encoding="utf-8")
    headings = HEADING_PATTERN.findall(text)
    citations = sorted(set(CITATION_PATTERN.findall(text)))
    bibliography_keys = set(BIB_KEY_PATTERN.findall(bibliography_text))
    missing_citations = sorted(set(citations) - bibliography_keys)
    local_links, missing_links = _local_links(manuscript, text, repository_root)
    index_errors = verify_index(result_index, repository_root)
    rows = [
        json.loads(line) for line in result_index.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    formal_count = sum(row.get("paper_eligibility") in FORMAL_ELIGIBILITY for row in rows)
    missing_sections = [
        name for name in REQUIRED_SECTION_PREFIXES[paper]
        if not _section_present(headings, name)
    ]
    markers = TBD_PATTERN.findall(text)
    evidence_tags = sorted(set(EVIDENCE_TAG_PATTERN.findall(text)))
    claims = {}
    if claim_registry is not None and claim_registry.is_file():
        claims = json.loads(claim_registry.read_text(encoding="utf-8")).get("claims", {})
    registered_tags = sorted(
        claim_id for claim_id, claim in claims.items() if claim.get("paper") == paper
    )
    missing_claim_registrations = sorted(set(evidence_tags) - set(registered_tags))
    unused_claim_registrations = sorted(set(registered_tags) - set(evidence_tags))
    claim_errors = []
    for claim_id in sorted(set(evidence_tags) & set(registered_tags)):
        claim = claims[claim_id]
        source_path = Path(claim["source_path"])
        if not source_path.is_absolute():
            source_path = repository_root / source_path
        if not source_path.is_file():
            claim_errors.append(f"{claim_id}: missing source {source_path}")
        else:
            if sha256(source_path) != claim["source_sha256"]:
                claim_errors.append(f"{claim_id}: source hash mismatch")
            claim_errors.extend(_claim_assertion_errors(claim_id, source_path, claim))
        if claim.get("experiment_id"):
            matching = [row for row in rows if row.get("experiment_id") == claim["experiment_id"]]
            if not matching:
                claim_errors.append(f"{claim_id}: experiment is not in {paper} result index")
            elif Path(claim["source_path"]).name == "metrics.json" and (
                matching[0].get("metrics_sha256") != claim["source_sha256"]
            ):
                claim_errors.append(f"{claim_id}: metrics hash differs from result index")
    structural_complete = not (
        missing_sections or missing_citations or missing_links or index_errors
        or missing_claim_registrations or unused_claim_registrations or claim_errors
    )
    blockers = []
    if missing_sections:
        blockers.append("missing required manuscript sections")
    if missing_citations:
        blockers.append("citation keys missing from bibliography")
    if missing_links:
        blockers.append("broken local manuscript links")
    if index_errors:
        blockers.append("result index verification failed")
    if missing_claim_registrations:
        blockers.append("manuscript evidence tags are absent from claim registry")
    if unused_claim_registrations:
        blockers.append("claim registry entries are not cited by manuscript")
    if claim_errors:
        blockers.append("claim source verification failed")
    if markers:
        blockers.append("unresolved TBD/citation markers remain")
    if formal_count == 0:
        blockers.append("no formal experiment is indexed")
    submission_ready = structural_complete and not markers and formal_count > 0
    return {
        "paper": paper,
        "manuscript_path": _portable_path(manuscript, repository_root),
        "manuscript_sha256": sha256(manuscript),
        "word_count": len(re.findall(r"\b[\w'-]+\b", text)),
        "headings": headings,
        "missing_required_sections": missing_sections,
        "citation_keys": citations,
        "missing_bibliography_keys": missing_citations,
        "local_links": local_links,
        "broken_local_links": missing_links,
        "tbd_or_citation_marker_count": len(markers),
        "result_index_path": _portable_path(result_index, repository_root),
        "result_index_sha256": sha256(result_index),
        "indexed_experiment_count": len(rows),
        "formal_experiment_count": formal_count,
        "result_index_errors": index_errors,
        "evidence_tags": evidence_tags,
        "registered_evidence_tags": registered_tags,
        "missing_claim_registrations": missing_claim_registrations,
        "unused_claim_registrations": unused_claim_registrations,
        "claim_source_errors": claim_errors,
        "claim_registry_path": (
            _portable_path(claim_registry, repository_root) if claim_registry else None
        ),
        "claim_registry_sha256": sha256(claim_registry) if claim_registry and claim_registry.is_file() else None,
        "structurally_complete": structural_complete,
        "submission_ready": submission_ready,
        "package_label": "SUBMISSION_READY" if submission_ready else "DRAFT_NOT_SUBMISSION_READY",
        "blockers": blockers,
    }


def review_bundle(manuscript_text: str, generated_results_text: str, audit: Mapping[str, Any]) -> str:
    preamble = [
        "<!-- AUTO-GENERATED REVIEW BUNDLE. DO NOT EDIT. -->",
        f"> Package status: **{audit['package_label']}**",
        "> This bundle combines the versioned manuscript and generated results for review.",
    ]
    if audit["blockers"]:
        preamble.append("> Blockers: " + "; ".join(audit["blockers"]) + ".")
    return "\n".join(preamble) + "\n\n" + manuscript_text.rstrip() + (
        "\n\n# Appendix: Machine-Generated Current Results\n\n" + generated_results_text.rstrip() + "\n"
    )


def evidence_markdown(audit: Mapping[str, Any]) -> str:
    lines = [
        "<!-- AUTO-GENERATED. DO NOT EDIT. -->",
        f"# {audit['paper']} evidence audit",
        "",
        f"Package: **{audit['package_label']}**",
        f"Manuscript words: **{audit['word_count']}**; unresolved markers: **{audit['tbd_or_citation_marker_count']}**.",
        f"Indexed runs: **{audit['indexed_experiment_count']}**; formal runs: **{audit['formal_experiment_count']}**.",
        f"Structural audit: **{'PASSED' if audit['structurally_complete'] else 'FAILED'}**.",
        "", "## Blockers", "",
    ]
    lines.extend(f"- {blocker}" for blocker in audit["blockers"])
    if not audit["blockers"]:
        lines.append("- None")
    lines.extend([
        "", "## Trace", "",
        f"- Manuscript SHA256: `{audit['manuscript_sha256']}`",
        f"- Result-index SHA256: `{audit['result_index_sha256']}`",
        f"- Citation keys: {', '.join(audit['citation_keys']) or 'none'}",
        f"- Broken local links: {', '.join(audit['broken_local_links']) or 'none'}",
        f"- Missing required sections: {', '.join(audit['missing_required_sections']) or 'none'}",
        f"- Evidence tags: {', '.join(audit['evidence_tags']) or 'none'}",
        f"- Claim-source errors: {', '.join(audit['claim_source_errors']) or 'none'}",
        "",
    ])
    return "\n".join(lines)

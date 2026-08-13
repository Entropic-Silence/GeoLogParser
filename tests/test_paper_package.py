import hashlib
import json
from pathlib import Path

from geologparser.paper_package import audit_manuscript, evidence_markdown, review_bundle


def fixture(tmp_path: Path):
    manuscript = tmp_path / "paper1/manuscript.md"
    manuscript.parent.mkdir()
    sections = [
        "Abstract", "1. Introduction", "2. Related Work", "3. Task Definition",
        "4. Dataset Construction", "5. Baselines", "6. Evaluation", "7. Results",
        "8. Discussion", "9. Reproducibility", "10. Conclusion", "References",
    ]
    manuscript.write_text(
        "# Title\n\n" + "\n\n".join(f"## {name}\ntext [@known]" for name in sections)
    )
    bibliography = tmp_path / "references.bib"
    bibliography.write_text("@article{known, title={Known}}\n")
    index = tmp_path / "index.jsonl"
    index.write_text("")
    return manuscript, bibliography, index


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_registry(tmp_path: Path, claims: dict) -> Path:
    registry = tmp_path / "claim_registry.json"
    registry.write_text(json.dumps({"claims": claims}))
    return registry


def add_evidence_tag(manuscript: Path, claim_id: str) -> None:
    manuscript.write_text(manuscript.read_text() + f"\n<!-- evidence:{claim_id} -->\n")


def write_indexed_run(tmp_path: Path, experiment_id: str = "E") -> tuple[Path, Path]:
    result = tmp_path / "result"
    result.mkdir()
    for name in ("run.json", "metrics.json"):
        (result / name).write_text("{}")
    for name in ("predictions.jsonl", "errors.jsonl", "run.log"):
        (result / name).write_text("")
    dataset = tmp_path / "dataset.json"
    dataset.write_text("{}")
    row = {
        "experiment_id": experiment_id,
        "result_path": "result",
        "dataset_manifest_path": "dataset.json",
        "dataset_manifest_sha256": digest(dataset),
        "run_sha256": digest(result / "run.json"),
        "metrics_sha256": digest(result / "metrics.json"),
        "predictions_sha256": digest(result / "predictions.jsonl"),
        "errors_sha256": digest(result / "errors.jsonl"),
        "run_log_sha256": digest(result / "run.log"),
        "paper_eligibility": "audit_only",
    }
    index = tmp_path / "index.jsonl"
    index.write_text(json.dumps(row) + "\n")
    return index, result


def test_paper_audit_distinguishes_structure_from_empirical_completion(tmp_path: Path):
    manuscript, bibliography, index = fixture(tmp_path)
    audit = audit_manuscript("paper1", manuscript, bibliography, index, tmp_path)
    assert audit["structurally_complete"] is True
    assert audit["formal_experiment_count"] == 0
    assert audit["submission_ready"] is False
    assert audit["package_label"] == "DRAFT_NOT_SUBMISSION_READY"
    assert "no formal experiment is indexed" in audit["blockers"]
    assert "Package: **DRAFT_NOT_SUBMISSION_READY**" in evidence_markdown(audit)


def test_paper_audit_reports_missing_citation_link_section_and_tbd(tmp_path: Path):
    manuscript, bibliography, index = fixture(tmp_path)
    text = manuscript.read_text().replace("## 7. Results\ntext [@known]", "")
    manuscript.write_text(text + "\nmissing [@unknown] and [asset](missing.png) `TBD`\n")
    audit = audit_manuscript("paper1", manuscript, bibliography, index, tmp_path)
    assert audit["missing_bibliography_keys"] == ["unknown"]
    assert audit["broken_local_links"] == ["missing.png"]
    assert audit["missing_required_sections"] == ["7. Results"]
    assert audit["tbd_or_citation_marker_count"] == 1


def test_paper_audit_requires_structured_literature_evidence_when_configured(tmp_path: Path):
    manuscript, bibliography, index = fixture(tmp_path)
    evidence = tmp_path / "literature_evidence.yaml"
    evidence.write_text(
        "sources:\n"
        "  - key: other\n"
        "    identifier: doi:other\n"
        "    metadata_verified_via: Crossref\n"
        "    verification_level: metadata_only\n"
        "    claim_scope: existence only\n"
    )
    audit = audit_manuscript(
        "paper1", manuscript, bibliography, index, tmp_path,
        literature_evidence=evidence,
    )
    assert audit["missing_literature_evidence_keys"] == ["known"]
    assert audit["structurally_complete"] is False
    assert "citation keys missing from literature evidence registry" in audit["blockers"]


def test_paper_audit_accepts_complete_literature_evidence(tmp_path: Path):
    manuscript, bibliography, index = fixture(tmp_path)
    evidence = tmp_path / "literature_evidence.yaml"
    evidence.write_text(
        "sources:\n"
        "  - key: known\n"
        "    identifier: doi:known\n"
        "    metadata_verified_via: Crossref\n"
        "    verification_level: metadata_only\n"
        "    claim_scope: existence only\n"
    )
    audit = audit_manuscript(
        "paper1", manuscript, bibliography, index, tmp_path,
        literature_evidence=evidence,
    )
    assert audit["missing_literature_evidence_keys"] == []
    assert audit["literature_evidence_errors"] == []
    assert audit["structurally_complete"] is True


def test_review_bundle_is_explicitly_labelled():
    audit = {"package_label": "DRAFT_NOT_SUBMISSION_READY", "blockers": ["TBD remains"]}
    result = review_bundle("# Manuscript\n", "| result |\n", audit)
    assert result.startswith("<!-- AUTO-GENERATED REVIEW BUNDLE")
    assert "DRAFT_NOT_SUBMISSION_READY" in result
    assert "# Appendix: Machine-Generated Current Results" in result


def test_paper_audit_rejects_changed_claim_source(tmp_path: Path):
    manuscript, bibliography, index = fixture(tmp_path)
    source = tmp_path / "evidence.json"
    source.write_text('{"count": 1}')
    add_evidence_tag(manuscript, "p1.count")
    registry = write_registry(tmp_path, {"p1.count": {
        "paper": "paper1", "source_path": str(source), "source_sha256": digest(source),
    }})
    source.write_text('{"count": 2}')
    audit = audit_manuscript("paper1", manuscript, bibliography, index, tmp_path, registry)
    assert audit["claim_source_errors"] == ["p1.count: source hash mismatch"]
    assert audit["structurally_complete"] is False


def test_paper_audit_rejects_unused_registered_claim(tmp_path: Path):
    manuscript, bibliography, index = fixture(tmp_path)
    source = tmp_path / "evidence.json"
    source.write_text("{}")
    registry = write_registry(tmp_path, {"p1.unused": {
        "paper": "paper1", "source_path": str(source), "source_sha256": digest(source),
    }})
    audit = audit_manuscript("paper1", manuscript, bibliography, index, tmp_path, registry)
    assert audit["unused_claim_registrations"] == ["p1.unused"]
    assert "claim registry entries are not cited by manuscript" in audit["blockers"]


def test_paper_audit_rejects_unregistered_manuscript_tag(tmp_path: Path):
    manuscript, bibliography, index = fixture(tmp_path)
    add_evidence_tag(manuscript, "p1.missing")
    registry = write_registry(tmp_path, {})
    audit = audit_manuscript("paper1", manuscript, bibliography, index, tmp_path, registry)
    assert audit["missing_claim_registrations"] == ["p1.missing"]
    assert "manuscript evidence tags are absent from claim registry" in audit["blockers"]


def test_paper_audit_rejects_claim_metrics_different_from_index(tmp_path: Path):
    manuscript, bibliography, _ = fixture(tmp_path)
    index, _ = write_indexed_run(tmp_path)
    external = tmp_path / "external" / "metrics.json"
    external.parent.mkdir()
    external.write_text('{"different": true}')
    add_evidence_tag(manuscript, "p1.metrics")
    registry = write_registry(tmp_path, {"p1.metrics": {
        "paper": "paper1", "experiment_id": "E", "source_path": str(external),
        "source_sha256": digest(external),
    }})
    audit = audit_manuscript("paper1", manuscript, bibliography, index, tmp_path, registry)
    assert audit["result_index_errors"] == []
    assert audit["claim_source_errors"] == ["p1.metrics: metrics hash differs from result index"]


def test_paper_audit_checks_json_and_sqlite_numeric_assertions(tmp_path: Path):
    import sqlite3

    manuscript, bibliography, index = fixture(tmp_path)
    json_source = tmp_path / "summary.json"
    json_source.write_text('{"counts": {"items": 11}}')
    sqlite_source = tmp_path / "records.sqlite"
    with sqlite3.connect(sqlite_source) as connection:
        connection.execute("CREATE TABLE intervals (id INTEGER)")
        connection.executemany("INSERT INTO intervals VALUES (?)", [(1,), (2,)])
    add_evidence_tag(manuscript, "p1.summary")
    add_evidence_tag(manuscript, "p1.database")
    registry = write_registry(tmp_path, {
        "p1.summary": {
            "paper": "paper1", "source_path": str(json_source),
            "source_sha256": digest(json_source), "assertions": [{
                "type": "json_pointer_equals", "pointer": "/counts/items", "expected": 10,
            }],
        },
        "p1.database": {
            "paper": "paper1", "source_path": str(sqlite_source),
            "source_sha256": digest(sqlite_source), "assertions": [{
                "type": "sqlite_row_count", "table": "intervals", "expected": 3,
            }],
        },
    })
    audit = audit_manuscript("paper1", manuscript, bibliography, index, tmp_path, registry)
    assert "p1.summary: JSON assertion '/counts/items' expected 10, found 11" in audit["claim_source_errors"]
    assert "p1.database: SQLite row count for 'intervals' expected 3, found 2" in audit["claim_source_errors"]


def test_paper_audit_checks_jsonl_counts_unique_values_and_sequence(tmp_path: Path):
    manuscript, bibliography, index = fixture(tmp_path)
    source = tmp_path / "manifest.jsonl"
    source.write_text('{"source": "a", "count": 2}\n{"source": "a", "count": 3}\n')
    add_evidence_tag(manuscript, "p1.manifest")
    registry = write_registry(tmp_path, {"p1.manifest": {
        "paper": "paper1", "source_path": str(source), "source_sha256": digest(source),
        "assertions": [
            {"type": "jsonl_row_count", "expected": 2},
            {"type": "jsonl_pointer_unique_count", "pointer": "/source", "expected": 1},
            {"type": "jsonl_pointer_sequence_equals", "pointer": "/count", "expected": [2, 4]},
        ],
    }})
    audit = audit_manuscript("paper1", manuscript, bibliography, index, tmp_path, registry)
    assert audit["claim_source_errors"] == [
        "p1.manifest: JSONL assertion 'jsonl_pointer_sequence_equals' expected [2, 4], found [2, 3]"
    ]


def test_paper_audit_uses_repository_relative_paths(tmp_path: Path):
    manuscript, bibliography, index = fixture(tmp_path)
    audit = audit_manuscript("paper1", manuscript, bibliography, index, tmp_path)
    assert audit["manuscript_path"] == "paper1/manuscript.md"
    assert audit["result_index_path"] == "index.jsonl"

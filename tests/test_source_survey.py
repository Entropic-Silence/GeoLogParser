import json
from pathlib import Path

import pytest

from geologparser.datasets.source_survey import (
    FetchResult,
    SURVEY_USER_AGENT,
    run_open_metadata_survey,
    verify_open_metadata_survey,
)


def _response(value, status=200, error=None):
    return FetchResult(
        status=status,
        headers={"content-type": "application/json"},
        body=json.dumps(value).encode(),
        error=error,
    )


def test_survey_freezes_metadata_without_promoting_non_image_candidate(tmp_path: Path):
    doi = "10.17632/example.1"
    datacite = {
        "data": [{
            "id": doi,
            "attributes": {
                "doi": doi,
                "titles": [{"title": "Chinese borehole table"}],
                "publisher": "Mendeley Data",
                "publicationYear": 2026,
                "types": {"resourceTypeGeneral": "Dataset"},
                "formats": [],
                "sizes": [],
                "rightsList": [{"rightsIdentifier": "cc-by-4.0"}],
                "descriptions": [{"description": "A structured XLSX table"}],
                "url": "https://example.invalid/dataset",
            },
        }],
        "meta": {"total": 1},
    }
    files = [{
        "filename": "boreholes.xlsx",
        "id": "file-1",
        "status": "COMPLETED",
        "content_details": {
            "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "size": 120,
            "sha256_hash": "a" * 64,
        },
    }]

    observed_user_agents = []

    def fetcher(method, url, headers, body, timeout):
        observed_user_agents.append(headers.get("User-Agent"))
        if "articles/search" in url:
            return _response({"message": "forbidden"}, 403, "HTTP 403: Forbidden")
        if "/files?" in url:
            return _response(files)
        return _response(datacite)

    config = {
        "survey_id": "test_survey_v001",
        "datacite_queries": [{"id": "chinese", "query": "borehole China"}],
        "mendeley_file_probes": [{
            "id": "example",
            "dataset_id": "example",
            "version": 1,
            "doi": doi,
        }],
        "repository_probes": [{
            "id": "figshare",
            "provider": "figshare_search",
            "query": "borehole China",
        }],
        "candidate_reviews": [{
            "doi": doi,
            "disposition": "paper3_structured_candidate",
            "reason": "XLSX is not a phase-1 page image.",
        }],
    }
    destination = tmp_path / "survey"
    summary = run_open_metadata_survey(config, destination, fetcher=fetcher)

    assert summary["unique_datacite_records_returned"] == 1
    assert summary["curated_candidate_count"] == 1
    assert summary["candidate_review_provenance"] == "automated_project_agent_metadata_triage"
    assert summary["phase1_content_review_candidate_count"] == 0
    assert summary["benchmark_eligible_candidate_count"] == 0
    assert summary["failed_request_ids"] == ["repository_figshare"]
    reviewed = json.loads((destination / "reviewed_candidates.jsonl").read_text())
    assert reviewed["metadata_found"] is True
    assert reviewed["phase1_content_review_candidate"] is False
    assert reviewed["benchmark_eligible"] is False
    assert reviewed["file_inventory"]["file_count"] == 1
    request = json.loads((destination / "requests/datacite_query_chinese.json").read_text())
    assert request["request_headers"]["User-Agent"] == SURVEY_USER_AGENT
    assert set(observed_user_agents) == {SURVEY_USER_AGENT}
    manifest = json.loads((destination / "manifest.json").read_text())
    assert any(item["path"] == "raw/datacite_query_chinese.body" for item in manifest["artifacts"])
    assert verify_open_metadata_survey(destination)["verified"] is True


def test_survey_only_marks_open_pdf_inventory_for_content_review(tmp_path: Path):
    doi = "10.17632/pdf.1"

    def fetcher(method, url, headers, body, timeout):
        if "/files?" in url:
            return _response([{
                "filename": "logs.pdf",
                "content_details": {"content_type": "application/pdf", "size": 10},
            }])
        return _response({
            "data": [{"id": doi, "attributes": {"doi": doi, "titles": [{"title": "Logs"}]}}],
            "meta": {"total": 1},
        })

    config = {
        "survey_id": "pdf_survey_v001",
        "datacite_queries": [{"id": "logs", "query": "logs"}],
        "mendeley_file_probes": [{
            "id": "pdf",
            "dataset_id": "pdf",
            "version": 1,
            "doi": doi,
        }],
        "candidate_reviews": [{
            "doi": doi,
            "disposition": "phase1_content_review_candidate",
            "license_status": "verified_open",
        }],
    }
    destination = tmp_path / "survey"
    summary = run_open_metadata_survey(config, destination, fetcher=fetcher)
    assert summary["phase1_content_review_candidate_count"] == 1
    reviewed = json.loads((destination / "reviewed_candidates.jsonl").read_text())
    assert reviewed["phase1_content_review_candidate"] is True
    assert reviewed["benchmark_eligible"] is False


def test_survey_prefers_complete_mendeley_dataset_inventory_over_empty_root(tmp_path: Path):
    doi = "10.17632/nested.1"

    def fetcher(method, url, headers, body, timeout):
        if "/files?" in url:
            return _response([])
        if "/public-api/datasets/nested" in url:
            return _response({
                "id": "nested",
                "version": 1,
                "available": True,
                "data_licence": {"short_name": "CC BY 4.0", "url": "https://license"},
                "files": [{
                    "filename": "nested/logs.pdf",
                    "id": "file-1",
                    "content_details": {
                        "content_type": "application/pdf", "size": 10,
                        "sha256_hash": "a" * 64,
                    },
                    "status": "COMPLETED",
                }],
                "versions": [{"version": 1, "available": True, "publish_date": "2026-01-01"}],
            })
        return _response({
            "data": [{"id": doi, "attributes": {"doi": doi, "titles": [{"title": "Logs"}]}}],
            "meta": {"total": 1},
        })

    config = {
        "survey_id": "nested_survey_v001",
        "datacite_queries": [{"id": "logs", "query": "logs"}],
        "mendeley_file_probes": [{
            "id": "nested_root", "dataset_id": "nested", "version": 1, "doi": doi,
        }],
        "mendeley_dataset_probes": [{
            "id": "nested_complete", "dataset_id": "nested", "doi": doi,
        }],
        "candidate_reviews": [{
            "doi": doi,
            "disposition": "phase1_content_review_candidate",
            "license_status": "verified_open",
        }],
    }
    destination = tmp_path / "survey"
    summary = run_open_metadata_survey(config, destination, fetcher=fetcher)
    reviewed = json.loads((destination / "reviewed_candidates.jsonl").read_text())
    assert summary["mendeley_file_inventory_count"] == 2
    assert reviewed["file_inventory_count"] == 2
    assert reviewed["file_inventory"]["inventory_source"] == "mendeley_public_dataset_api"
    assert reviewed["file_inventory"]["file_count"] == 1
    assert reviewed["phase1_content_review_candidate"] is True


def test_survey_verifier_rejects_tampered_response(tmp_path: Path):
    def fetcher(method, url, headers, body, timeout):
        return _response({"data": [], "meta": {"total": 0}})

    destination = tmp_path / "survey"
    run_open_metadata_survey(
        {"survey_id": "tamper_v001", "datacite_queries": [{"id": "empty", "query": "none"}]},
        destination,
        fetcher=fetcher,
    )
    (destination / "raw/datacite_query_empty.body").write_text("tampered")
    with pytest.raises(ValueError, match="size mismatch|SHA256 mismatch"):
        verify_open_metadata_survey(destination)


def test_survey_uses_explicit_user_agent(monkeypatch):
    captured = {}

    class Response:
        status = 200
        headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return b"{}"

    def fake_urlopen(request, timeout):
        captured["user_agent"] = request.get_header("User-agent")
        return Response()

    monkeypatch.setattr("geologparser.datasets.source_survey.urlopen", fake_urlopen)
    from geologparser.datasets.source_survey import _default_fetcher

    result = _default_fetcher("GET", "https://example.invalid", {}, None, 1)
    assert result.status == 200
    assert captured["user_agent"] == SURVEY_USER_AGENT


def test_survey_refuses_to_overwrite_existing_output(tmp_path: Path):
    destination = tmp_path / "existing"
    destination.mkdir()
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        run_open_metadata_survey({"survey_id": "survey_v001"}, destination)


def test_survey_rejects_duplicate_request_ids(tmp_path: Path):
    config = {
        "survey_id": "survey_v001",
        "repository_probes": [
            {"id": "same", "provider": "url_status", "url": "https://example.invalid/a"},
            {"id": "same", "provider": "url_status", "url": "https://example.invalid/b"},
        ],
    }
    with pytest.raises(ValueError, match="request ids must be unique"):
        run_open_metadata_survey(config, tmp_path / "output")

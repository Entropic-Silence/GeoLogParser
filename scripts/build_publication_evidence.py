#!/usr/bin/env python3
"""Build the minimal redistributable evidence bundle for manuscript audit.

The bundle contains exact run metadata and aggregate metrics for every indexed
experiment plus a selected, pseudonymized document-level prediction/error core.
It deliberately excludes page images, OCR text rows, raw identifiers, logs,
model weights, complete source databases, and sensitive source-inventory details.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3


ROOT = Path(__file__).resolve().parents[1]
PAPERS = ("paper1", "paper2", "paper3")
BUNDLE_DATE = "2026-08-17"
DOCUMENT_OUTPUT_RUNS = (
    "results/2026-08-14/P1_CALIFORNIA_WCR_RAPIDOCR_TEST_FORMAL_001",
    "results/2026-08-14/P1_CALIFORNIA_WCR_V002_RAPIDOCR_EXTERNAL_FORMAL_002",
    "results/2026-08-14/P1_CALIFORNIA_WCR_V003_RAPIDOCR_PROSPECTIVE_FORMAL_001",
    "results/2026-08-15/P1_CALIFORNIA_WCR_V004_RAPIDOCR_PROSPECTIVE_FORMAL_001",
    "results/2026-08-15/P1_CALIFORNIA_WCR_V005_RAPIDOCR_EXTERNAL_FORMAL_001",
    "results/2026-08-15/P2_CALIFORNIA_WCR_V004_CONSTRAINT_PROSPECTIVE_FORMAL_001",
    "results/2026-08-15/P2_CALIFORNIA_WCR_V004_CANDIDATE_RISK_PROSPECTIVE_FORMAL_001",
    "results/2026-08-15/P2_CALIFORNIA_WCR_V005_CONSTRAINT_EXTERNAL_FORMAL_001",
    "results/2026-08-15/P2_CALIFORNIA_WCR_V005_CANDIDATE_RISK_EXTERNAL_FORMAL_001",
    "results/2026-08-16/P3_SWISSGEOL_RISK_AWARE_DOWNSTREAM_INPUT_001",
)
ANALYSIS_INPUT_FILES = (
    (
        "experiments/paper2/public/candidate_pool_v001.jsonl",
        "paper2/candidate_pool_v001.jsonl",
        "pseudonymized positioned-candidate pool for same-pool ablation; exact depth sequences remain linkable",
    ),
    (
        "experiments/paper2/public/candidate_pool_v001.metadata.json",
        "paper2/candidate_pool_v001.metadata.json",
        "candidate-pool schema and release limitations",
    ),
    (
        "experiments/paper2/public/candidate_pool_recomputed_v001.jsonl",
        "paper2/candidate_pool_recomputed_v001.jsonl",
        "deterministically recomputed ablation sequences",
    ),
    (
        "experiments/paper3/public/spatial_input_v001.jsonl",
        "paper3/spatial_input_v001.jsonl",
        "rigidly transformed spatial diagnostic input",
    ),
    (
        "experiments/paper3/public/spatial_input_v001.metadata.json",
        "paper3/spatial_input_v001.metadata.json",
        "spatial transform and release limitations",
    ),
    (
        "experiments/paper3/public/spatial_recomputed_v001.json",
        "paper3/spatial_recomputed_v001.json",
        "diagnostics recomputed from transformed public input",
    ),
    (
        "docs/generated/publication_linkage_risk.json",
        "linkage/publication_linkage_risk.json",
        "aggregate exact-sequence and distance-fingerprint linkage diagnostics; no record mapping",
    ),
    (
        "docs/publication_linkage_risk.md",
        "linkage/publication_linkage_risk.md",
        "release-risk interpretation for pseudonymized and transformed inputs",
    ),
)
SENSITIVE_KEYS = {
    "borehole_id", "project_name", "county", "filename", "source_file",
    "document_path", "pdf_path", "pdf_sha256", "reference_path", "source_text",
    "source_bbox", "display_bbox", "bbox", "regions", "ocr_regions_path",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_exact(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def replace_tree(staging: Path, destination: Path) -> None:
    if destination.is_dir():
        shutil.rmtree(destination)
    staging.rename(destination)


def public_record_key(record_id: str) -> str:
    return hashlib.sha256(
        f"geologparser-publication-v001:{record_id}".encode()
    ).hexdigest()[:20]


def sanitize(value: object, key: str | None = None) -> object:
    if key in SENSITIVE_KEYS:
        return None
    if isinstance(value, dict):
        output = {}
        for child_key, child_value in value.items():
            if child_key in SENSITIVE_KEYS:
                continue
            if child_key == "record_id":
                output["record_key"] = public_record_key(str(child_value))
            else:
                output[child_key] = sanitize(child_value, child_key)
        return output
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    return value


def sanitize_jsonl(source: Path, destination: Path) -> int:
    rows = [
        sanitize(json.loads(line))
        for line in source.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )
    return len(rows)


def json_pointer(document: object, pointer: str) -> object:
    current = document
    for raw_token in pointer.removeprefix("/").split("/") if pointer else []:
        token = raw_token.replace("~1", "/").replace("~0", "~")
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current


def assertion_observation(source: Path, assertion: dict[str, object]) -> object:
    assertion_type = assertion["type"]
    if assertion_type == "json_pointer_equals":
        return json_pointer(
            json.loads(source.read_text(encoding="utf-8")), str(assertion["pointer"])
        )
    if str(assertion_type).startswith("jsonl_"):
        rows = [
            json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if assertion_type == "jsonl_row_count":
            return len(rows)
        values = [json_pointer(row, str(assertion["pointer"])) for row in rows]
        if assertion_type == "jsonl_pointer_unique_count":
            return len({json.dumps(value, sort_keys=True) for value in values})
        if assertion_type == "jsonl_pointer_sequence_equals":
            return values
    if assertion_type == "sqlite_row_count":
        table = str(assertion["table"])
        with sqlite3.connect(f"{source.resolve().as_uri()}?mode=ro", uri=True) as connection:
            return connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
    raise ValueError(f"unsupported publication assertion: {assertion_type}")


def build_assertion_snapshot(
    claim_id: str,
    claim: dict[str, object],
    source: Path,
    destination: Path,
) -> None:
    origin_assertions = claim.get("origin_assertions", claim.get("assertions", []))
    if claim_id == "p3.sanming_database_connectivity" and not claim.get("origin_assertions"):
        origin_assertions = [
            {"type": "sqlite_row_count", "table": table, "expected": expected}
            for table, expected in (
                ("boreholes", 4), ("intervals", 12), ("field_provenance", 224)
            )
        ]
    observations = []
    for assertion in origin_assertions:
        observed = assertion_observation(source, assertion)
        if observed != assertion.get("expected"):
            raise ValueError(
                f"claim assertion failed before projection: {claim_id}: "
                f"expected {assertion.get('expected')!r}, found {observed!r}"
            )
        observations.append({"assertion": assertion, "observed": observed})
    document = {
        "publication_evidence_schema_version": "claim_assertion_projection_v001",
        "claim_id": claim_id,
        "scope": claim["scope"],
        "origin_source_sha256": sha256(source),
        "observations": observations,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    claim["origin_assertions"] = origin_assertions
    claim["assertions"] = [
        {
            "type": "json_pointer_equals",
            "pointer": f"/observations/{index}/observed",
            "expected": observation["observed"],
        }
        for index, observation in enumerate(observations)
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    arguments = parser.parse_args()
    root = arguments.repository_root.resolve()
    bundle = root / "publication_evidence"
    core_root = bundle / "result_core"
    external_root = bundle / "external"
    core_staging = bundle / ".result_core.staging"
    external_staging = bundle / ".external.staging"
    for generated_root in (core_staging, external_staging):
        if generated_root.is_dir():
            shutil.rmtree(generated_root)
    registry_path = root / "papers" / "claim_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))

    copied_core: dict[str, dict[str, str]] = {}
    for paper in PAPERS:
        index_path = root / "experiments" / paper / "result_index.jsonl"
        for line in index_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            result_path = Path(entry["result_path"])
            source_root = root / result_path
            target_root = core_staging / result_path
            for filename, hash_key in (("run.json", "run_sha256"), ("metrics.json", "metrics_sha256")):
                source = source_root / filename
                if not source.is_file():
                    source = core_root / result_path / filename
                if not source.is_file():
                    raise FileNotFoundError(source)
                if sha256(source) != entry[hash_key]:
                    raise ValueError(f"index hash mismatch before publication copy: {source}")
                destination = target_root / filename
                copy_exact(source, destination)
                final_destination = core_root / result_path / filename
                copied_core[final_destination.relative_to(root).as_posix()] = {
                    "sha256": sha256(destination),
                    "experiment_id": entry["experiment_id"],
                    "paper": paper,
                }

    copied_external: dict[str, dict[str, str]] = {}
    for claim_id, claim in registry["claims"].items():
        origin_text = claim.get("origin_source_path", claim["source_path"])
        origin = Path(origin_text)
        if not origin.is_absolute() or not str(origin).startswith("/data/GeoLogParser/"):
            continue
        claim.setdefault("origin_source_path", str(origin))
        relative = Path("publication_evidence/external") / claim_id / "claim_snapshot.json"
        destination = external_staging / claim_id / "claim_snapshot.json"
        if origin.is_file():
            claim.setdefault("origin_source_sha256", sha256(origin))
            build_assertion_snapshot(claim_id, claim, origin, destination)
        else:
            committed = root / claim["source_path"]
            if not committed.is_file():
                raise FileNotFoundError(origin)
            if sha256(committed) != claim["source_sha256"]:
                raise ValueError(f"committed external projection hash mismatch: {claim_id}")
            copy_exact(committed, destination)
        claim["source_path"] = relative.as_posix()
        claim["source_sha256"] = sha256(destination)
        claim["publication_evidence_mode"] = "assertion_projection"
        copied_external[relative.as_posix()] = {
            "sha256": sha256(destination),
            "claim_id": claim_id,
            "origin_source_sha256": claim["origin_source_sha256"],
        }

    for claim_id, claim in registry["claims"].items():
        origin_text = claim.get("origin_source_path", claim["source_path"])
        if not origin_text.startswith("results/"):
            continue
        claim.setdefault("origin_source_path", origin_text)
        claim.setdefault("origin_source_sha256", claim["source_sha256"])
        relative = Path("publication_evidence/result_core") / origin_text
        destination = core_staging / origin_text
        if not destination.is_file():
            source = root / origin_text
            if not source.is_file():
                source = core_root / origin_text
            if not source.is_file():
                raise FileNotFoundError(source)
            copy_exact(source, destination)
            copied_core[relative.as_posix()] = {
                "sha256": sha256(destination),
                "experiment_id": claim.get("experiment_id", "claim-only"),
                "paper": claim["paper"],
            }
        if not destination.is_file():
            raise FileNotFoundError(destination)
        if sha256(destination) != claim["origin_source_sha256"]:
            raise ValueError(f"claim/core hash mismatch: {claim_id}")
        claim["source_path"] = relative.as_posix()
        claim["source_sha256"] = sha256(destination)
        claim["publication_evidence_mode"] = "exact_metrics_copy"

    document_root = bundle / "document_outputs"
    document_staging = bundle / ".document_outputs.staging"
    if document_staging.is_dir():
        shutil.rmtree(document_staging)
    document_outputs: dict[str, dict[str, object]] = {}
    for result_path_text in DOCUMENT_OUTPUT_RUNS:
        result_path = Path(result_path_text)
        source_root = root / result_path
        for filename in ("predictions.jsonl", "errors.jsonl"):
            source = source_root / filename
            destination = document_staging / result_path / filename
            if source.is_file():
                row_count = sanitize_jsonl(source, destination)
            else:
                committed = document_root / result_path / filename
                if not committed.is_file():
                    continue
                copy_exact(committed, destination)
                row_count = sum(1 for line in destination.read_text(encoding="utf-8").splitlines() if line.strip())
            relative_path = Path("publication_evidence/document_outputs") / result_path / filename
            relative = relative_path.as_posix()
            document_outputs[relative] = {
                "sha256": sha256(destination),
                "row_count": row_count,
                "sanitization": "stable hashed record key; borehole/project identifiers, source paths, county, page text, and bboxes removed",
            }

    replace_tree(core_staging, core_root)
    replace_tree(external_staging, external_root)
    replace_tree(document_staging, document_root)

    analysis_root = bundle / "analysis_inputs"
    analysis_staging = bundle / ".analysis_inputs.staging"
    if analysis_staging.is_dir():
        shutil.rmtree(analysis_staging)
    analysis_inputs: dict[str, dict[str, str]] = {}
    for source_text, destination_text, scope in ANALYSIS_INPUT_FILES:
        source = root / source_text
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = analysis_staging / destination_text
        copy_exact(source, destination)
        relative = (Path("publication_evidence/analysis_inputs") / destination_text).as_posix()
        analysis_inputs[relative] = {
            "sha256": sha256(destination),
            "origin": Path(source_text).as_posix(),
            "scope": scope,
        }
    replace_tree(analysis_staging, analysis_root)

    registry_path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "publication_evidence_schema_version": "publication_evidence_v003",
        "frozen_date": BUNDLE_DATE,
        "scope": "exact aggregate run/metrics evidence, selected pseudonymized document outputs, public reanalysis inputs, linkage-risk diagnostics, and privacy-minimized claim projections",
        "privacy_classification": "direct identifiers removed; released projections are pseudonymized or transformed and may remain linkable; anonymity is not claimed",
        "excluded": [
            "source page images and PDFs",
            "model weights and caches",
            "unselected development and audit prediction rows",
            "source text and bounding boxes from released prediction rows",
            "run.log and recursive ROI artifacts",
            "complete source databases",
        ],
        "result_core_file_count": len(copied_core),
        "external_summary_file_count": len(copied_external),
        "result_core": dict(sorted(copied_core.items())),
        "external_summaries": dict(sorted(copied_external.items())),
        "document_outputs": dict(sorted(document_outputs.items())),
        "analysis_input_file_count": len(analysis_inputs),
        "analysis_inputs": dict(sorted(analysis_inputs.items())),
    }
    manifest_path = bundle / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(manifest_path)
    print(f"result core files: {len(copied_core)}")
    print(f"external summaries: {len(copied_external)}")
    print(f"pseudonymized document outputs: {len(document_outputs)}")
    print(f"public reanalysis input files: {len(analysis_inputs)}")


if __name__ == "__main__":
    main()

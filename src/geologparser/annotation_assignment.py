"""Immutable, blinded duplicate-annotation task packs and comparison."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Mapping

from geologparser.annotation import (
    matching_attestations, record_sha256, validate_annotation, validate_annotator_id,
)
from geologparser.annotation_export import annotation_agreement, ground_truth_gate
from geologparser.datasets.manifest import sha256_file


def _annotation_paths(root: Path) -> list[Path]:
    paths = sorted(Path(root).glob("*.json"))
    if not paths:
        raise ValueError("annotation root contains no annotations")
    return paths


def build_blinded_annotation_pack(
    source_root: Path,
    output_root: Path,
    track_annotators: Mapping[str, str],
) -> dict[str, Any]:
    """Copy one frozen auto seed into isolated full-overlap reviewer tracks."""
    source_root = Path(source_root).resolve()
    output_root = Path(output_root).resolve()
    if output_root.exists():
        raise FileExistsError(f"blinded annotation output already exists: {output_root}")
    if len(track_annotators) < 2:
        raise ValueError("at least two blinded annotation tracks are required")
    normalized_tracks: dict[str, str] = {}
    for track_id, annotator_id in track_annotators.items():
        if not isinstance(track_id, str) or not track_id.strip() or Path(track_id).name != track_id:
            raise ValueError("track IDs must be non-empty path-safe names")
        normalized_tracks[track_id] = validate_annotator_id(annotator_id)
    if len(set(normalized_tracks.values())) != len(normalized_tracks):
        raise ValueError("each blinded track requires a distinct annotator ID")

    sources = []
    annotation_ids: set[str] = set()
    annotations: list[tuple[Path, dict[str, Any]]] = []
    for path in _annotation_paths(source_root):
        annotation = json.loads(path.read_text(encoding="utf-8"))
        validate_annotation(annotation)
        if annotation["annotation_status"] != "auto":
            raise ValueError(f"source annotation is not an auto seed: {path.name}")
        if annotation.get("verification_attestations"):
            raise ValueError(f"source auto seed already contains verification attestations: {path.name}")
        annotation_id = str(annotation["annotation_id"])
        if annotation_id in annotation_ids:
            raise ValueError(f"duplicate source annotation ID: {annotation_id}")
        annotation_ids.add(annotation_id)
        annotations.append((path, annotation))
        rendered_path = Path(annotation["panel"]["rendered_path"]).resolve()
        if not rendered_path.is_file():
            raise FileNotFoundError(f"rendered panel is missing: {rendered_path}")
        expected_image_hash = annotation["panel"].get("rendered_sha256")
        actual_image_hash = sha256_file(rendered_path)
        if expected_image_hash is not None and expected_image_hash != actual_image_hash:
            raise ValueError(f"rendered panel hash mismatch: {annotation['annotation_id']}")
        sources.append({
            "annotation_id": annotation["annotation_id"],
            "source_annotation_sha256": sha256_file(path),
            "seed_record_sha256": record_sha256(annotation["record"]),
            "rendered_panel_sha256": actual_image_hash,
        })

    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging_root = Path(tempfile.mkdtemp(
        prefix=f".{output_root.name}.building-", dir=output_root.parent,
    ))
    try:
        for track_id in sorted(normalized_tracks):
            annotations_root = staging_root / "tracks" / track_id / "annotations"
            annotations_root.mkdir(parents=True, exist_ok=False)
            for source_path, _ in annotations:
                shutil.copy2(source_path, annotations_root / source_path.name)
        created_at = datetime.now(timezone.utc).isoformat()
        manifest = {
            "assignment_schema_version": "blinded_duplicate_annotation_v001",
            "created_at": created_at,
            "source_annotation_root": str(source_root),
            "source_annotation_count": len(annotations),
            "full_overlap": True,
            "source_items": sources,
            "tracks": [
                {
                    "track_id": track_id,
                    "assigned_annotator_id": normalized_tracks[track_id],
                    "annotation_root": str(output_root / "tracks" / track_id / "annotations"),
                    "peer_results_exposed_by_track_service": False,
                }
                for track_id in sorted(normalized_tracks)
            ],
            "policy": {
                "seed_status": "auto",
                "track_annotation_directories_are_separate": True,
                "shared_host_filesystem_is_not_an_access_control_boundary": True,
                "cross_track_result_access_prohibited_until_freeze": True,
                "agreement_before_adjudication": True,
                "automatic_gt_promotion": False,
            },
        }
        staging_manifest_path = staging_root / "assignment_manifest.json"
        staging_manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(staging_root, output_root)
        manifest_path = output_root / "assignment_manifest.json"
        manifest["assignment_manifest_path"] = str(manifest_path)
        manifest["assignment_manifest_sha256"] = sha256_file(manifest_path)
        return manifest
    except Exception:
        if staging_root.exists():
            shutil.rmtree(staging_root)
        raise


def compare_blinded_annotation_tracks(
    first_root: Path,
    second_root: Path,
    destination: Path,
) -> dict[str, Any]:
    """Freeze pre-adjudication agreement only after both tracks pass GT gates."""
    destination = Path(destination).resolve()
    if destination.exists():
        raise FileExistsError(f"agreement output already exists: {destination}")

    collections: list[list[dict[str, Any]]] = []
    source_hashes: list[dict[str, str]] = []
    for root in (Path(first_root).resolve(), Path(second_root).resolve()):
        annotations = []
        hashes: dict[str, str] = {}
        for path in _annotation_paths(root):
            annotation = json.loads(path.read_text(encoding="utf-8"))
            validate_annotation(annotation)
            failures = ground_truth_gate(annotation)
            if failures:
                raise ValueError(
                    f"annotation {annotation['annotation_id']} failed Ground Truth gate: "
                    + ", ".join(failures)
                )
            annotations.append(annotation)
            hashes[annotation["annotation_id"]] = sha256_file(path)
        collections.append(annotations)
        source_hashes.append(hashes)

    agreement = annotation_agreement(collections[0], collections[1])
    payload = {
        "agreement_schema_version": "blinded_pre_adjudication_agreement_v001",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "first_annotation_root": str(Path(first_root).resolve()),
        "second_annotation_root": str(Path(second_root).resolve()),
        "annotation_file_sha256": {
            "first": source_hashes[0], "second": source_hashes[1],
        },
        "agreement": agreement,
        "interpretation": (
            "pre-adjudication duplicate-annotation agreement; not final Ground Truth"
        ),
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload | {"output_path": str(destination), "sha256": sha256_file(destination)}


def build_adjudication_pack(
    agreement_path: Path,
    first_root: Path,
    second_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    """Freeze both reviewer records for adjudication without creating final GT."""
    agreement_path = Path(agreement_path).resolve()
    first_root, second_root = Path(first_root).resolve(), Path(second_root).resolve()
    output_root = Path(output_root).resolve()
    if output_root.exists():
        raise FileExistsError(f"adjudication output already exists: {output_root}")
    if not agreement_path.is_file():
        raise FileNotFoundError(agreement_path)
    agreement_payload = json.loads(agreement_path.read_text(encoding="utf-8"))
    if agreement_payload.get("agreement_schema_version") != "blinded_pre_adjudication_agreement_v001":
        raise ValueError("unsupported or missing pre-adjudication agreement schema")
    if Path(agreement_payload["first_annotation_root"]).resolve() != first_root:
        raise ValueError("first annotation root differs from frozen agreement")
    if Path(agreement_payload["second_annotation_root"]).resolve() != second_root:
        raise ValueError("second annotation root differs from frozen agreement")

    expected = agreement_payload["annotation_file_sha256"]
    collections: list[dict[str, tuple[Path, dict[str, Any]]]] = []
    for label, root in (("first", first_root), ("second", second_root)):
        items: dict[str, tuple[Path, dict[str, Any]]] = {}
        for path in _annotation_paths(root):
            annotation = json.loads(path.read_text(encoding="utf-8"))
            validate_annotation(annotation)
            annotation_id = str(annotation["annotation_id"])
            if annotation_id in items:
                raise ValueError(f"duplicate annotation ID in {label} track: {annotation_id}")
            items[annotation_id] = (path, annotation)
        if set(items) != set(expected[label]):
            raise ValueError(f"{label} annotation IDs differ from frozen agreement")
        for annotation_id, (path, _) in items.items():
            if sha256_file(path) != expected[label][annotation_id]:
                raise ValueError(
                    f"{label} annotation changed after agreement: {annotation_id}"
                )
        collections.append(items)

    disagreements_by_id: dict[str, list[dict[str, Any]]] = {}
    for disagreement in agreement_payload["agreement"].get("disagreements", []):
        disagreements_by_id.setdefault(disagreement["annotation_id"], []).append(disagreement)

    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging_root = Path(tempfile.mkdtemp(
        prefix=f".{output_root.name}.building-", dir=output_root.parent,
    ))
    try:
        case_rows = []
        for annotation_id in sorted(collections[0]):
            case_root = staging_root / "cases" / annotation_id
            case_root.mkdir(parents=True, exist_ok=False)
            first_path, first_annotation = collections[0][annotation_id]
            second_path, second_annotation = collections[1][annotation_id]
            shutil.copy2(first_path, case_root / "first.json")
            shutil.copy2(second_path, case_root / "second.json")
            disagreements = disagreements_by_id.get(annotation_id, [])
            hashes = agreement_payload["agreement"]["document_record_hashes"][annotation_id]
            case = {
                "adjudication_case_schema_version": "adjudication_case_v001",
                "annotation_id": annotation_id,
                "status": "adjudication_pending" if disagreements else "confirmation_pending",
                "disagreement_count": len(disagreements),
                "disagreements": disagreements,
                "records_equal": hashes["equal"],
                "record_sha256": hashes,
                "first_annotator_id": first_annotation["annotator_id"],
                "second_annotator_id": second_annotation["annotator_id"],
                "automatic_final_record_created": False,
            }
            case_path = case_root / "case.json"
            case_path.write_text(
                json.dumps(case, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            case_rows.append({
                "annotation_id": annotation_id,
                "status": case["status"],
                "disagreement_count": len(disagreements),
                "case_sha256": sha256_file(case_path),
                "first_annotation_sha256": sha256_file(case_root / "first.json"),
                "second_annotation_sha256": sha256_file(case_root / "second.json"),
            })
        manifest = {
            "adjudication_manifest_schema_version": "adjudication_pack_v001",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "agreement_path": str(agreement_path),
            "agreement_sha256": sha256_file(agreement_path),
            "case_count": len(case_rows),
            "pending_adjudication_count": sum(
                item["status"] == "adjudication_pending" for item in case_rows
            ),
            "pending_confirmation_count": sum(
                item["status"] == "confirmation_pending" for item in case_rows
            ),
            "automatic_final_records_created": 0,
            "cases": case_rows,
            "interpretation": (
                "frozen reviewer evidence for human adjudication; not final Ground Truth"
            ),
        }
        staging_manifest = staging_root / "adjudication_manifest.json"
        staging_manifest.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(staging_root, output_root)
        manifest_path = output_root / "adjudication_manifest.json"
        return manifest | {
            "output_path": str(output_root),
            "manifest_sha256": sha256_file(manifest_path),
        }
    except Exception:
        if staging_root.exists():
            shutil.rmtree(staging_root)
        raise


def audit_annotation_assignment(
    assignment_root: Path,
    destination: Path,
) -> dict[str, Any]:
    """Derive current duplicate-review progress without promoting any record."""
    assignment_root, destination = Path(assignment_root).resolve(), Path(destination).resolve()
    manifest_path = assignment_root / "assignment_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("assignment_schema_version") != "blinded_duplicate_annotation_v001":
        raise ValueError("unsupported annotation assignment schema")
    expected_ids = {str(item["annotation_id"]) for item in manifest["source_items"]}
    if len(expected_ids) != len(manifest["source_items"]):
        raise ValueError("assignment manifest contains duplicate annotation IDs")
    tracks = []
    for track in manifest["tracks"]:
        root = Path(track["annotation_root"]).resolve()
        annotations = []
        statuses: dict[str, int] = {}
        effective_attestations = 0
        exportable = 0
        identifiers: set[str] = set()
        for path in _annotation_paths(root):
            annotation = json.loads(path.read_text(encoding="utf-8"))
            validate_annotation(annotation)
            annotation_id = str(annotation["annotation_id"])
            if annotation_id in identifiers:
                raise ValueError(
                    f"track {track['track_id']} contains duplicate annotation ID: {annotation_id}"
                )
            identifiers.add(annotation_id)
            status = str(annotation["annotation_status"])
            statuses[status] = statuses.get(status, 0) + 1
            effective_attestations += len(matching_attestations(annotation))
            exportable += not ground_truth_gate(annotation)
            annotations.append({
                "annotation_id": annotation_id,
                "annotation_sha256": sha256_file(path),
                "record_sha256": record_sha256(annotation["record"]),
                "revision": annotation["revision"],
                "annotation_status": status,
                "effective_attestation_count": len(matching_attestations(annotation)),
                "ground_truth_exportable": not ground_truth_gate(annotation),
            })
        if identifiers != expected_ids:
            raise ValueError(
                f"track {track['track_id']} annotation IDs differ from assignment manifest"
            )
        tracks.append({
            "track_id": track["track_id"],
            "assigned_annotator_id": track["assigned_annotator_id"],
            "annotation_root": str(root),
            "annotation_count": len(annotations),
            "status_counts": dict(sorted(statuses.items())),
            "effective_attestation_count": effective_attestations,
            "ground_truth_exportable_count": exportable,
            "annotations": annotations,
        })
    agreement_files = sorted((assignment_root / "agreement").glob("*.json"))
    adjudication_files = sorted(assignment_root.glob("adjudication/**/adjudication_manifest.json"))
    report = {
        "assignment_audit_schema_version": "annotation_assignment_status_v001",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "assignment_root": str(assignment_root),
        "assignment_manifest_path": str(manifest_path),
        "assignment_manifest_sha256": sha256_file(manifest_path),
        "source_annotation_count": len(expected_ids),
        "track_count": len(tracks),
        "tracks": tracks,
        "total_track_annotations": sum(item["annotation_count"] for item in tracks),
        "total_effective_attestations": sum(
            item["effective_attestation_count"] for item in tracks
        ),
        "total_ground_truth_exportable_annotations": sum(
            item["ground_truth_exportable_count"] for item in tracks
        ),
        "agreement_artifact_count": len(agreement_files),
        "adjudication_manifest_count": len(adjudication_files),
        "human_review_complete": all(
            item["ground_truth_exportable_count"] == item["annotation_count"] for item in tracks
        ),
        "interpretation": (
            "live assignment progress audit; task generation is not human annotation"
        ),
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report | {"output_path": str(destination), "sha256": sha256_file(destination)}

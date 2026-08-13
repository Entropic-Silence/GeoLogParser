"""Immutable, blinded duplicate-annotation task packs and comparison."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Mapping

from geologparser.annotation import record_sha256, validate_annotation, validate_annotator_id
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

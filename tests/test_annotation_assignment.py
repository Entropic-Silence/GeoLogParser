import copy
import json
from pathlib import Path

import pytest
from PIL import Image

from geologparser.annotation import create_annotation, revise_annotation, save_annotation
from geologparser.annotation_assignment import (
    audit_annotation_assignment, build_adjudication_pack, build_blinded_annotation_pack,
    compare_blinded_annotation_tracks,
)
from geologparser.datasets.manifest import sha256_file


ROOT = Path(__file__).resolve().parents[1]


def sample_record():
    return json.loads(
        (ROOT / "examples/boreholes/synthetic_valid.json").read_text(encoding="utf-8")
    )


def source_pack(tmp_path: Path, *, count: int = 2) -> Path:
    source = tmp_path / "source"
    source.mkdir(parents=True)
    for index in range(count):
        image = tmp_path / f"panel-{index}.png"
        Image.new("RGB", (80, 40), "white").save(image)
        record = sample_record()
        record["document"]["document_id"] = f"P{index}"
        annotation = create_annotation(
            f"P{index}", {
                "panel_id": f"P{index}", "rendered_path": str(image),
                "rendered_sha256": sha256_file(image),
                "rendered_width_px": 80, "rendered_height_px": 40,
            }, record, "AUTO_SEED", "auto",
        )
        save_annotation(annotation, source / f"P{index}.json")
    return source


def verify_track(track_root: Path, annotator_id: str, *, change: bool = False) -> None:
    for path in sorted(track_root.glob("*.json")):
        annotation = json.loads(path.read_text(encoding="utf-8"))
        record = copy.deepcopy(annotation["record"])
        if change:
            record["intervals"][0]["bottom_depth_m"]["value"] += 0.1
        revised = revise_annotation(
            annotation, record, annotator_id, "single_verified",
        )
        save_annotation(revised, path)


def test_blinded_pack_copies_identical_auto_seed_into_separate_tracks(tmp_path: Path):
    source = source_pack(tmp_path)
    output = tmp_path / "pack"
    result = build_blinded_annotation_pack(
        source, output, {"track_a": "reviewer-A", "track_b": "reviewer-B"},
    )
    assert result["source_annotation_count"] == 2
    assert len(result["source_items"]) == 2
    assert result["policy"]["automatic_gt_promotion"] is False
    assert result["policy"]["shared_host_filesystem_is_not_an_access_control_boundary"] is True
    for name in ("track_a", "track_b"):
        paths = sorted((output / "tracks" / name / "annotations").glob("*.json"))
        assert len(paths) == 2
        assert all(json.loads(path.read_text())["annotation_status"] == "auto" for path in paths)
    manifest = output / "assignment_manifest.json"
    assert result["assignment_manifest_sha256"] == sha256_file(manifest)
    with pytest.raises(FileExistsError):
        build_blinded_annotation_pack(
            source, output, {"track_a": "reviewer-A", "track_b": "reviewer-B"},
        )


def test_blinded_pack_rejects_duplicate_people_and_non_auto_or_changed_image(tmp_path: Path):
    source = source_pack(tmp_path)
    with pytest.raises(ValueError, match="distinct annotator"):
        build_blinded_annotation_pack(
            source, tmp_path / "duplicate", {"a": "same", "b": "same"},
        )
    assert not (tmp_path / "duplicate").exists()

    first_path = source / "P0.json"
    annotation = json.loads(first_path.read_text())
    human = revise_annotation(annotation, annotation["record"], "reviewer", "single_verified")
    save_annotation(human, first_path)
    with pytest.raises(ValueError, match="not an auto seed"):
        build_blinded_annotation_pack(
            source, tmp_path / "human", {"a": "A", "b": "B"},
        )
    assert not (tmp_path / "human").exists()

    fresh = source_pack(tmp_path / "fresh")
    panel = Path(json.loads((fresh / "P0.json").read_text())["panel"]["rendered_path"])
    panel.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="hash mismatch"):
        build_blinded_annotation_pack(
            fresh, tmp_path / "tampered", {"a": "A", "b": "B"},
        )
    assert not (tmp_path / "tampered").exists()


def test_compare_tracks_requires_completed_independent_gt_and_is_immutable(tmp_path: Path):
    source = source_pack(tmp_path)
    output = tmp_path / "pack"
    build_blinded_annotation_pack(
        source, output, {"track_a": "reviewer-A", "track_b": "reviewer-B"},
    )
    track_a = output / "tracks/track_a/annotations"
    track_b = output / "tracks/track_b/annotations"
    destination = output / "agreement/pre_adjudication.json"
    with pytest.raises(ValueError, match="Ground Truth gate"):
        compare_blinded_annotation_tracks(track_a, track_b, destination)
    verify_track(track_a, "reviewer-A")
    verify_track(track_b, "reviewer-B", change=True)
    result = compare_blinded_annotation_tracks(track_a, track_b, destination)
    assert result["agreement"]["document_count"] == 2
    assert result["agreement"]["independent_annotator_ids"] == {
        "first": ["reviewer-A"], "second": ["reviewer-B"], "disjoint": True,
    }
    assert result["agreement"]["boundary"]["boundary_agreement_mae_m"]["value"] > 0
    assert result["sha256"] == sha256_file(destination)
    with pytest.raises(FileExistsError):
        compare_blinded_annotation_tracks(track_a, track_b, destination)


def test_compare_tracks_rejects_same_annotator_identity(tmp_path: Path):
    source = source_pack(tmp_path)
    output = tmp_path / "pack"
    build_blinded_annotation_pack(
        source, output, {"track_a": "reviewer-A", "track_b": "reviewer-B"},
    )
    track_a = output / "tracks/track_a/annotations"
    track_b = output / "tracks/track_b/annotations"
    verify_track(track_a, "same")
    verify_track(track_b, "same")
    with pytest.raises(ValueError, match="disjoint annotator IDs"):
        compare_blinded_annotation_tracks(
            track_a, track_b, output / "agreement.json",
        )


def test_adjudication_pack_freezes_disagreements_without_creating_gt(tmp_path: Path):
    source = source_pack(tmp_path)
    output = tmp_path / "pack"
    build_blinded_annotation_pack(
        source, output, {"track_a": "reviewer-A", "track_b": "reviewer-B"},
    )
    track_a = output / "tracks/track_a/annotations"
    track_b = output / "tracks/track_b/annotations"
    verify_track(track_a, "reviewer-A")
    verify_track(track_b, "reviewer-B", change=True)
    agreement = output / "agreement/pre_adjudication.json"
    compare_blinded_annotation_tracks(track_a, track_b, agreement)
    adjudication = output / "adjudication/v001"
    result = build_adjudication_pack(agreement, track_a, track_b, adjudication)
    assert result["case_count"] == 2
    assert result["pending_adjudication_count"] == 2
    assert result["pending_confirmation_count"] == 0
    assert result["automatic_final_records_created"] == 0
    assert result["manifest_sha256"] == sha256_file(
        adjudication / "adjudication_manifest.json"
    )
    case = json.loads((adjudication / "cases/P0/case.json").read_text())
    assert case["status"] == "adjudication_pending"
    assert case["automatic_final_record_created"] is False
    assert case["disagreements"][0]["field_path"] == "intervals[0].bottom_depth_m"
    assert not (adjudication / "cases/P0/final.json").exists()
    with pytest.raises(FileExistsError):
        build_adjudication_pack(agreement, track_a, track_b, adjudication)


def test_adjudication_pack_requires_confirmation_even_for_equal_records(tmp_path: Path):
    source = source_pack(tmp_path)
    output = tmp_path / "pack"
    build_blinded_annotation_pack(
        source, output, {"track_a": "reviewer-A", "track_b": "reviewer-B"},
    )
    track_a = output / "tracks/track_a/annotations"
    track_b = output / "tracks/track_b/annotations"
    verify_track(track_a, "reviewer-A")
    verify_track(track_b, "reviewer-B")
    agreement = output / "agreement.json"
    compare_blinded_annotation_tracks(track_a, track_b, agreement)
    adjudication = output / "adjudication"
    result = build_adjudication_pack(agreement, track_a, track_b, adjudication)
    assert result["pending_adjudication_count"] == 0
    assert result["pending_confirmation_count"] == 2
    assert all(item["status"] == "confirmation_pending" for item in result["cases"])


def test_adjudication_pack_rejects_track_mutation_after_agreement(tmp_path: Path):
    source = source_pack(tmp_path)
    output = tmp_path / "pack"
    build_blinded_annotation_pack(
        source, output, {"track_a": "reviewer-A", "track_b": "reviewer-B"},
    )
    track_a = output / "tracks/track_a/annotations"
    track_b = output / "tracks/track_b/annotations"
    verify_track(track_a, "reviewer-A")
    verify_track(track_b, "reviewer-B")
    agreement = output / "agreement.json"
    compare_blinded_annotation_tracks(track_a, track_b, agreement)
    path = track_b / "P0.json"
    path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError, match="changed after agreement"):
        build_adjudication_pack(
            agreement, track_a, track_b, output / "adjudication",
        )
    assert not (output / "adjudication").exists()


def test_assignment_status_audit_reports_real_review_progress(tmp_path: Path):
    source = source_pack(tmp_path)
    output = tmp_path / "pack"
    build_blinded_annotation_pack(
        source, output, {"track_a": "reviewer-A", "track_b": "reviewer-B"},
    )
    destination = output / "status/current.json"
    initial = audit_annotation_assignment(output, destination)
    assert initial["source_annotation_count"] == 2
    assert initial["track_count"] == 2
    assert initial["total_track_annotations"] == 4
    assert initial["total_effective_attestations"] == 0
    assert initial["total_ground_truth_exportable_annotations"] == 0
    assert initial["agreement_artifact_count"] == 0
    assert initial["adjudication_manifest_count"] == 0
    assert initial["human_review_complete"] is False
    assert all(item["status_counts"] == {"auto": 2} for item in initial["tracks"])
    assert initial["sha256"] == sha256_file(destination)

    verify_track(output / "tracks/track_a/annotations", "reviewer-A")
    partial = audit_annotation_assignment(output, destination)
    assert partial["total_effective_attestations"] == 2
    assert partial["total_ground_truth_exportable_annotations"] == 2
    assert partial["human_review_complete"] is False

    verify_track(output / "tracks/track_b/annotations", "reviewer-B")
    complete = audit_annotation_assignment(output, destination)
    assert complete["total_effective_attestations"] == 4
    assert complete["total_ground_truth_exportable_annotations"] == 4
    assert complete["human_review_complete"] is True


def test_assignment_status_audit_rejects_track_id_drift(tmp_path: Path):
    source = source_pack(tmp_path)
    output = tmp_path / "pack"
    build_blinded_annotation_pack(
        source, output, {"track_a": "reviewer-A", "track_b": "reviewer-B"},
    )
    (output / "tracks/track_b/annotations/P1.json").unlink()
    with pytest.raises(ValueError, match="IDs differ"):
        audit_annotation_assignment(output, output / "status.json")

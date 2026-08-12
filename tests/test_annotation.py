import json
from pathlib import Path

import pytest

from geologparser.annotation import (
    PanelSpec, create_annotation, revise_annotation, save_annotation,
)


ROOT = Path(__file__).resolve().parents[1]


def sample_record():
    return json.loads((ROOT / "examples/boreholes/synthetic_valid.json").read_text(encoding="utf-8"))


def test_panel_spec_rejects_invalid_bounds():
    with pytest.raises(ValueError):
        PanelSpec("x", "/tmp/x.pdf", 1, (0.5, 0, 0.4, 1)).validate()


def test_revisioned_annotation_preserves_history(tmp_path: Path):
    panel = {"panel_id": "p1", "source_sha256": "a" * 64}
    first = create_annotation("a1", panel, sample_record(), "annotator-A", "single_verified")
    destination = tmp_path / "a1.json"
    save_annotation(first, destination)
    record = sample_record()
    record["borehole"]["borehole_id"]["value"] = "CORRECTED"
    second = revise_annotation(first, record, "annotator-A", "single_verified")
    save_annotation(second, destination)
    assert json.loads(destination.read_text())["revision"] == 2
    history = tmp_path / "history/a1/revision_0001.json"
    assert json.loads(history.read_text())["revision"] == 1


def test_revision_conflict_is_rejected(tmp_path: Path):
    first = create_annotation("a1", {"panel_id": "p1"}, sample_record(), "A")
    destination = tmp_path / "a1.json"
    save_annotation(first, destination)
    with pytest.raises(ValueError, match="revision conflict"):
        save_annotation(first, destination)

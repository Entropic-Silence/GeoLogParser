import pytest

from geologparser.datasets import assert_group_disjoint, assign_split, split_manifest


def records():
    return [
        {"record_id": f"r{i}", "project_id": f"p{i // 2}", "template_id": f"t{i // 3}"}
        for i in range(12)
    ]


def test_project_split_is_deterministic_and_disjoint():
    first = assign_split(records(), "project_id", seed=7)
    second = assign_split(records(), "project_id", seed=7)
    assert first == second
    assert_group_disjoint(first, "project_id")


def test_random_page_split_treats_each_page_as_group():
    splits = assign_split(records(), None, seed=7)
    assert sum(map(len, splits.values())) == 12


def test_missing_group_and_explicit_leakage_are_rejected():
    with pytest.raises(ValueError, match="missing"):
        assign_split([{"record_id": "r"}], "project_id")
    with pytest.raises(ValueError, match="leakage"):
        assert_group_disjoint({"train": [{"project_id": "p"}], "test": [{"project_id": "p"}]}, "project_id")


def test_split_manifest_records_hash_counts_and_assignments():
    manifest = split_manifest(records(), "project_disjoint_v001", "project_id", {"train": .5, "validation": .25, "test": .25}, 42)
    assert len(manifest["source_manifest_sha256"]) == 64
    assert sum(manifest["counts"].values()) == 12
    assert len(manifest["assignments"]) == 12

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "acquire_swissgeol_thurgau_pilot.py"
SPEC = spec_from_file_location("acquire_swissgeol_thurgau_pilot", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def detail():
    return {
        "id": 12,
        "name": "BH-12",
        "projectName": "Example",
        "locationX": 2700000,
        "locationY": 1250000,
        "elevationZ": 430.0,
        "totalDepth": 3.0,
        "canton": "Thurgau",
        "municipality": "Example",
        "workflow": {
            "status": "Published",
            "publishedTabs": {"profiles": True, "lithology": True},
        },
        "profiles": [
            {"id": 7, "boreholeId": 12, "name": "BH-12.pdf", "public": True, "type": "application/pdf"}
        ],
        "stratigraphies": [
            {
                "id": 8,
                "boreholeId": 12,
                "name": "Primary",
                "isPrimary": True,
                "lithologies": [
                    {"id": 81, "fromDepth": 0, "toDepth": 1.25, "isUnconsolidated": True},
                    {"id": 82, "fromDepth": 1.25, "toDepth": 3, "isUnconsolidated": False},
                ],
            }
        ],
    }


def test_selects_only_public_published_pair():
    item = detail()
    assert MODULE.public_pdf_profile(item)["id"] == 7
    assert MODULE.primary_published_stratigraphy(item)["id"] == 8
    item["workflow"]["publishedTabs"]["lithology"] = False
    assert MODULE.primary_published_stratigraphy(item) is None


def test_depth_reference_keeps_database_scope_narrow():
    item = detail()
    reference = MODULE.depth_reference(item, item["stratigraphies"][0])
    assert reference["reference_type"] == "official_database_derived_ground_truth"
    assert reference["stratigraphy"]["intervals"][0]["thickness_m"] == 1.25
    assert "material_description" in reference["excluded_reference_scope"]


def test_canonical_hash_is_order_stable():
    assert MODULE.canonical_sha256({"b": 2, "a": 1}) == MODULE.canonical_sha256({"a": 1, "b": 2})


def test_completed_dataset_is_immutable(tmp_path):
    root = tmp_path / "frozen"
    root.mkdir()
    (root / "dataset.json").write_text("{}", encoding="utf-8")
    try:
        MODULE.acquire(root, limit=1, maximum_pages=1, client=None, resume=True)
    except FileExistsError as exc:
        assert "already frozen" in str(exc)
    else:
        raise AssertionError("completed dataset must not be overwritten")


def test_dataset_version_can_be_frozen_for_a_successor_acquisition(tmp_path):
    root = tmp_path / "successor"
    class EmptyClient:
        def json(self, path, *, method="GET", body=None):
            return {"totalCount": 0, "totalPages": 0, "boreholes": []}

    summary = MODULE.acquire(
        root, limit=1, maximum_pages=1, client=EmptyClient(),
        dataset_version="swissgeol_thurgau_paired_v002",
    )
    assert summary["dataset_version"] == "swissgeol_thurgau_paired_v002"

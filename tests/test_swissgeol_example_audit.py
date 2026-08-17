import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_swissgeol_audit_rejects_mismatched_layer_fixture(tmp_path: Path, monkeypatch):
    path = ROOT / "scripts/audit_swissgeol_example_groundtruth.py"
    spec = importlib.util.spec_from_file_location("swissgeol_audit", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    source = tmp_path / "swissgeol-boreholes-dataextraction"
    example = source / "example"
    example.mkdir(parents=True)
    (example / "example_borehole_profile.pdf").write_bytes(b"minimal audit fixture")
    (example / "example_groundtruth.json").write_text(
        json.dumps({
            "example_borehole_profile.pdf": [{
                "metadata": {
                    "coordinates": {"E": 615790, "N": 157500},
                    "drilling_date": "1995-09-03",
                    "reference_elevation": 788.6,
                }
            }]
        }),
        encoding="utf-8",
    )
    (example / "example_layers_groundtruth.json").write_text(
        json.dumps({
            "example_borehole_profile.pdf": [{
                "borehole_index": 0,
                "layers": [{"material_description": "Kies und Sand"}],
            }]
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        module,
        "pdf_text",
        lambda _: "SST KB 5  615 790 / 157 500  2.-3. 9. 1995  788,6 Sandstein",
    )
    result = module.audit(source)
    assert result["metadata_groundtruth_matches_pdf"] is True
    assert result["layers_groundtruth_matches_pdf"] is False
    assert result["layer_fixture_decision"] == "EXCLUDE_MISMATCHED_FROM_GOLD"

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_swissgeol_v2_secondary_ablation.py"
SPEC = spec_from_file_location("run_swissgeol_v2_secondary_ablation", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_legacy_parser_preserves_pre_v2_ocr_failures():
    text = "Tiefe Beschreibung Bohrgut\nbis m Art\n6 Kies\n_10___|Mergel\n_200__|Sandstein\n"
    assert MODULE.legacy_choose(text) == ((0.0, 6.0),)
    text = "Tiefe Beschreibung Bohrgut\nvon / bis Art\nOm-20m Kies\n20m-160m Mergel\n"
    assert MODULE.legacy_choose(text) == ((20.0, 160.0),)


def test_v1_acceptance_requires_extension_and_unique_support():
    first = ((0.0, 12.0),)
    support = [{
        "intervals": [
            {"top_depth_m": 0.0, "bottom_depth_m": 12.0},
            {"top_depth_m": 12.0, "bottom_depth_m": 170.0},
        ],
        "support": 3,
    }]
    assert MODULE.v1_acceptance(first, ["reader_disagreement"], support) == (
        (0.0, 12.0), (12.0, 170.0),
    )
    assert MODULE.v1_acceptance(first, ["incomplete_top_boundary"], support) == first

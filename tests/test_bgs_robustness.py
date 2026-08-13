import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_bgs_robustness_profiles_are_narrow_and_include_clean():
    module = load_script("build_bgs_metadata_degradation_set.py")
    assert list(module.PROFILES) == [
        "clean", "resolution_050", "blur_20", "noise_16", "skew_30",
        "jpeg_30", "contrast_040",
    ]


def test_bgs_robustness_summary_counts_errors_and_omissions():
    module = load_script("run_bgs_robustness_benchmark.py")
    rows = [
        {
            "reference": {"borehole_id": "A", "x_coordinate": 10.0, "y_coordinate": 20.0},
            "prediction": {"borehole_id": "A", "x_coordinate": 10.0, "y_coordinate": None},
            "latency_seconds": 1.0,
        },
        {
            "reference": {"borehole_id": "B", "x_coordinate": 11.0, "y_coordinate": 21.0},
            "prediction": {"borehole_id": "X", "x_coordinate": 12.0, "y_coordinate": 21.0},
            "latency_seconds": 3.0,
        },
    ]
    metrics = module.summarize_profile(rows)
    assert metrics["borehole_id_exact_match"]["numerator"] == 1
    assert metrics["x_coordinate"]["x_coordinate_mae"]["value"] == 0.5
    assert metrics["complete_three_field_exact"]["numerator"] == 0
    assert metrics["wrong_nonmissing_numeric_predictions"] == 1
    assert metrics["field_omissions"] == 1
    assert metrics["latency_mean_seconds_per_image"] == 2.0

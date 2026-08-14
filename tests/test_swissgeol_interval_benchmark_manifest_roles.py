from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_swissgeol_interval_gold_benchmark.py"
SPEC = spec_from_file_location("run_swissgeol_interval_gold_benchmark", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_manifest_roles_select_matching_frozen_summary_counts():
    assert MODULE.manifest_count_keys("gold_interval_manifest_heldout_v003.jsonl") == (
        "heldout_documents", "heldout_intervals", "content_group_heldout",
    )
    assert MODULE.manifest_count_keys("gold_interval_manifest_development_v003.jsonl") == (
        "development_documents", "development_intervals", "content_group_development",
    )
    assert MODULE.manifest_count_keys("gold_interval_manifest_incremental_v002.jsonl") == (
        "incremental_gold_documents", "incremental_gold_intervals", "incremental_heldout",
    )

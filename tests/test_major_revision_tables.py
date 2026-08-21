import json
from pathlib import Path

from geologparser.major_revision_tables import (
    paper1_major_revision_table,
    paper2_major_revision_tables,
    paper3_major_revision_tables,
)


ROOT = Path(__file__).resolve().parents[1]


def test_paper1_table_binds_v005_counts_and_document_unit():
    rendered = paper1_major_revision_table(
        ROOT / "experiments/paper1/analysis/california_replication_statistics_v001.json"
    )
    assert "California v005 | 100 | 2069 | 741 | 546" in rendered
    assert "statistical unit for confidence intervals is the document" in rendered


def test_paper2_tables_expose_same_pool_and_document_risk():
    rendered = paper2_major_revision_tables(
        ROOT / "experiments/paper2/analysis/california_candidate_pool_ablation_v001.json",
        ROOT / "experiments/paper2/analysis/california_document_risk_v001.json",
    )
    assert "identical documents" in rendered
    assert "Complete archived score" in rendered
    assert "82 actions in 19 documents" in rendered
    assert "0.1459 per accepted document" in rendered
    assert "Net additional matches / 100 documents" in rendered
    assert "Net change in incorrect predictions" in rendered
    assert "Worsened documents (document F1)" in rendered


def test_paper3_tables_keep_full_and_matched_estimands_separate():
    path = ROOT / "experiments/paper3/analysis/swissgeol_spatial_sensitivity_v001.json"
    rendered = paper3_major_revision_tables(path)
    source = json.loads(path.read_text(encoding="utf-8"))
    assert "Full support | risk | 35" in rendered
    assert "Matched accepted subset | raw | 15" in rendered
    assert f"{source['matched_subset_comparison']['raw']['aggregate']['relative_absolute_volume_error']:.4f}" in rendered
    assert "selection/support effect" in rendered
    assert "Full reference | risk" in rendered and "79 |" in rendered
    assert "| Matched accepted | reference | 15 /" in rendered
    assert "15 /" in rendered and "4 /" in rendered and "0 / --" in rendered

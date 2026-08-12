import json

from geologparser.readiness import project_readiness, readiness_markdown


def write_index(path, eligibility):
    path.write_text("".join(
        json.dumps({"experiment_id": f"E{i}", "paper_eligibility": value}) + "\n"
        for i, value in enumerate(eligibility)
    ))


def test_audit_only_runs_cannot_satisfy_formal_readiness(tmp_path):
    annotations = tmp_path / "annotations"
    annotations.mkdir()
    indexes = {}
    for paper in ("paper1", "paper2", "paper3"):
        path = tmp_path / f"{paper}.jsonl"
        write_index(path, ["audit_only", "protocol_only"])
        indexes[paper] = path
    report = project_readiness([annotations], indexes)
    assert report["ground_truth_exportable_count"] == 0
    assert report["all_three_papers_empirically_complete"] is False
    assert all(not value for value in report["gates"].values())
    assert "NOT COMPLETED" in readiness_markdown(report)


def test_only_explicit_formal_eligibility_is_counted(tmp_path):
    annotations = tmp_path / "annotations"
    annotations.mkdir()
    indexes = {}
    for paper, formal in (
        ("paper1", "formal_benchmark"), ("paper2", "formal_method"), ("paper3", "formal_downstream"),
    ):
        path = tmp_path / f"{paper}.jsonl"
        write_index(path, [formal])
        indexes[paper] = path
    report = project_readiness([annotations], indexes)
    assert all(value["formal_experiment_count"] == 1 for value in report["paper_indexes"].values())
    assert report["gates"]["human_ground_truth_exists"] is False
    assert report["all_three_papers_empirically_complete"] is False

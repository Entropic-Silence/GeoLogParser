from geologparser.vlm.assurance import (
    agreeing_interval_pairs,
    monotonic_nonoverlapping_indices,
    numeric_region_evidence,
)


def interval(top: float, bottom: float) -> dict[str, float]:
    return {"top_depth_m": top, "bottom_depth_m": bottom}


def test_complete_interval_agreement_and_numeric_bbox_evidence() -> None:
    proposals = [interval(0.0, 1.0), interval(1.0, 3.0)]
    candidates = [interval(0.0, 1.0), interval(1.0, 2.0)]
    assert agreeing_interval_pairs(proposals, candidates) == [(0, 0)]
    regions = [{"text": "0-1 Sand", "bbox": [1, 2, 3, 4], "confidence": 0.98, "page_index": 1, "regions_path": "p1.jsonl"}]
    assert numeric_region_evidence(regions, 1.0)[0]["bbox"] == [1, 2, 3, 4]


def test_nonoverlap_rejects_conflicting_agreement() -> None:
    intervals = [interval(0.0, 2.0), interval(1.0, 3.0), interval(3.0, 4.0)]
    assert monotonic_nonoverlapping_indices(intervals, [0, 1, 2]) == ([0, 2], [1])

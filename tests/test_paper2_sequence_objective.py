"""Regression tests tying the Paper II objective to the frozen decoder."""
from __future__ import annotations

from itertools import combinations

from geologparser.paper2_sequence import path_score, select_sequence, start_path_score


def _candidate(name: str, top: float, bottom: float, score: float) -> dict:
    return {"name": name, "page": 1, "y": top / 100, "top": top, "bottom": bottom, "node_score": score}


def _edge(left: dict, right: dict) -> float | None:
    if right["top"] < left["bottom"] or right["y"] <= left["y"]:
        return None
    return 0.25 if right["top"] == left["bottom"] else -0.5


def test_frozen_decoder_matches_exhaustive_path_objective() -> None:
    candidates = [
        _candidate("shallow", 0.0, 10.0, 2.0),
        _candidate("middle", 10.0, 20.0, 2.2),
        _candidate("deep", 20.0, 30.0, 2.1),
        _candidate("distractor", 12.0, 18.0, 2.95),
    ]
    admissible = []
    for length in range(1, len(candidates) + 1):
        for subset in combinations(candidates, length):
            if all(_edge(left, right) is not None for left, right in zip(subset, subset[1:])):
                admissible.append(subset)
    expected = max(admissible, key=lambda path: (path_score(list(path), _edge), len(path)))
    selected = select_sequence(candidates, _edge)
    assert [item["name"] for item in selected] == [item["name"] for item in expected]
    assert start_path_score(candidates[2]) == 2.1 - 0.0005 * 20.0
    assert path_score(selected, _edge) == path_score(list(expected), _edge)

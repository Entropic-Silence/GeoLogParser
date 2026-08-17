"""Deterministic scoring primitives for the Paper II California sequence study.

The implementation is deliberately small and data-agnostic so the manuscript
objective, experiment runner, ablation analysis, and regression tests all use
one definition.  The depth term is a path-start prior, not a per-node penalty.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any


Candidate = dict[str, Any]
Transition = Callable[[Candidate, Candidate], float | None]

DEPTH_START_PENALTY_PER_FOOT = 0.0005


def raw_node_score(candidate: Candidate) -> float:
    """Return the frozen evidence score before any path-start prior."""
    return float(candidate["node_score"])


def start_path_score(
    candidate: Candidate,
    *,
    depth_penalty_per_foot: float = DEPTH_START_PENALTY_PER_FOOT,
) -> float:
    """Score a singleton path starting at ``candidate``.

    This is intentionally the *only* location at which the shallow-start
    preference enters the frozen California decoder.
    """
    return raw_node_score(candidate) - depth_penalty_per_foot * float(candidate["top"])


def path_score(path: list[Candidate], transition_score: Transition) -> float:
    """Evaluate one admissible candidate path under the published objective."""
    if not path:
        raise ValueError("a sequence path must contain at least one candidate")
    total = start_path_score(path[0])
    for left, right in zip(path, path[1:]):
        transition = transition_score(left, right)
        if transition is None:
            raise ValueError("path contains an inadmissible transition")
        total += raw_node_score(right) + transition
    return total


def select_sequence(
    candidates: list[Candidate],
    transition_score: Transition,
    *,
    maximum_predecessors: int | None = None,
    depth_penalty_per_foot: float = DEPTH_START_PENALTY_PER_FOOT,
) -> list[Candidate]:
    """Return the dynamic-programming path with length tie-breaking.

    The published objective considers every earlier candidate.  An explicit
    ``maximum_predecessors`` may be supplied for engineering profiling, but no
    truncation is applied by default.
    """
    ordered = sorted(candidates, key=lambda item: (item["page"], item["y"], item["top"], item["bottom"]))
    if not ordered:
        return []
    scores = [
        start_path_score(item, depth_penalty_per_foot=depth_penalty_per_foot)
        for item in ordered
    ]
    parents: list[int | None] = [None] * len(ordered)
    lengths = [1] * len(ordered)
    for right_index, right in enumerate(ordered):
        first_predecessor = (
            0 if maximum_predecessors is None
            else max(0, right_index - maximum_predecessors)
        )
        for left_index in range(first_predecessor, right_index):
            edge = transition_score(ordered[left_index], right)
            if edge is None:
                continue
            candidate_score = scores[left_index] + raw_node_score(right) + edge
            candidate_length = lengths[left_index] + 1
            if candidate_score > scores[right_index] or (
                abs(candidate_score - scores[right_index]) < 1e-9
                and candidate_length > lengths[right_index]
            ):
                scores[right_index] = candidate_score
                parents[right_index] = left_index
                lengths[right_index] = candidate_length
    end = max(range(len(ordered)), key=lambda index: (scores[index], lengths[index]))
    selected: list[Candidate] = []
    while end is not None:
        selected.append(ordered[end])
        end = parents[end]
    return list(reversed(selected))

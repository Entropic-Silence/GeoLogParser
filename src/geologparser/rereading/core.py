"""Constraint-guided candidate ranking with audited, non-mutating acceptance."""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any, Mapping, Sequence

from geologparser.constraints import default_engine


@dataclass(frozen=True)
class Candidate:
    value: Any
    source: str
    source_text: str | None = None
    model_confidence: float | None = None
    pixel_evidence: float | None = None
    layout_confidence: float | None = None


@dataclass(frozen=True)
class CandidateScore:
    candidate: Candidate
    evidence_score: float
    cross_model_agreement: float
    constraint_score: float
    total_score: float
    violations_before: int
    violations_after: int


@dataclass(frozen=True)
class RereadDecision:
    status: str
    field_path: str
    original_value: Any
    accepted_value: Any | None
    reason: str
    scores: tuple[CandidateScore, ...]
    proposed_record: Mapping[str, Any] | None = None


def _field_parts(path: str) -> tuple[int | None, str]:
    if path.startswith("borehole."):
        return None, path.split(".", 1)[1]
    import re
    match = re.fullmatch(r"intervals\[(\d+)]\.([A-Za-z0-9_]+)", path)
    if not match:
        raise ValueError(f"unsupported field path: {path}")
    return int(match.group(1)), match.group(2)


def get_field(record: Mapping[str, Any], path: str) -> Mapping[str, Any]:
    index, name = _field_parts(path)
    container = record["borehole"] if index is None else record["intervals"][index]
    envelope = container[name]
    if not isinstance(envelope, Mapping) or "value" not in envelope:
        raise ValueError(f"field is not a provenance envelope: {path}")
    return envelope


def record_with_candidate(record: Mapping[str, Any], path: str, candidate: Candidate) -> dict[str, Any]:
    revised = copy.deepcopy(record)
    index, name = _field_parts(path)
    container = revised["borehole"] if index is None else revised["intervals"][index]
    envelope = container[name]
    envelope["value"] = candidate.value
    envelope["source_text"] = candidate.source_text
    envelope["extraction_method"] = "fusion"
    envelope["confidence"] = candidate.model_confidence
    envelope["validation_status"] = "needs_review"
    codes = list(envelope.get("warning_codes", []))
    if "CONSTRAINT_GUIDED_REREAD_PROPOSAL" not in codes:
        codes.append("CONSTRAINT_GUIDED_REREAD_PROPOSAL")
    envelope["warning_codes"] = codes
    return revised


def _violations_for_path(record: Mapping[str, Any], path: str) -> tuple[int, int]:
    results = default_engine().evaluate(record)
    affected = 0
    evaluated = 0
    for result in results:
        evaluated += int(result.evaluated_count > 0)
        affected += sum(
            path in violation.affected_fields or any(
                field.startswith(path.rsplit(".", 1)[0]) for field in violation.affected_fields
            )
            for violation in result.violations
        )
    return affected, evaluated


def rank_candidates(
    record: Mapping[str, Any],
    field_path: str,
    candidates: Sequence[Candidate],
    weights: Mapping[str, float] | None = None,
) -> list[CandidateScore]:
    if not candidates:
        return []
    weights = weights or {"evidence": 0.45, "agreement": 0.20, "constraint": 0.35}
    if abs(sum(weights.values()) - 1.0) > 1e-9:
        raise ValueError("candidate ranking weights must sum to 1")
    before, _ = _violations_for_path(record, field_path)
    agreement_counts: dict[str, set[str]] = {}
    for candidate in candidates:
        agreement_counts.setdefault(str(candidate.value), set()).add(candidate.source)
    source_count = len({candidate.source for candidate in candidates})
    scores: list[CandidateScore] = []
    for candidate in candidates:
        components = [
            value for value in (
                candidate.model_confidence, candidate.pixel_evidence, candidate.layout_confidence,
            ) if value is not None
        ]
        if any(value < 0 or value > 1 for value in components):
            raise ValueError("candidate evidence scores must be within [0, 1]")
        evidence = sum(components) / len(components) if components else 0.0
        agreement = len(agreement_counts[str(candidate.value)]) / source_count if source_count else 0.0
        proposed = record_with_candidate(record, field_path, candidate)
        after, _ = _violations_for_path(proposed, field_path)
        constraint = 1.0 if before > after else (0.5 if before == after else 0.0)
        total = (
            weights["evidence"] * evidence + weights["agreement"] * agreement
            + weights["constraint"] * constraint
        )
        scores.append(CandidateScore(candidate, evidence, agreement, constraint, total, before, after))
    return sorted(scores, key=lambda score: score.total_score, reverse=True)


def decide_reread(
    record: Mapping[str, Any],
    field_path: str,
    candidates: Sequence[Candidate],
    minimum_score: float = 0.75,
    minimum_margin: float = 0.10,
) -> RereadDecision:
    original = get_field(record, field_path).get("value")
    scores = rank_candidates(record, field_path, candidates)
    if not scores:
        return RereadDecision("NEEDS_REVIEW", field_path, original, None, "no_candidates", ())
    best = scores[0]
    competing = next(
        (score for score in scores[1:] if str(score.candidate.value) != str(best.candidate.value)),
        None,
    )
    margin = best.total_score - competing.total_score if competing is not None else 1.0
    if best.violations_after >= best.violations_before:
        return RereadDecision(
            "NEEDS_REVIEW", field_path, original, None,
            "best_candidate_does_not_reduce_target_constraint_violations", tuple(scores),
        )
    if best.total_score < minimum_score:
        return RereadDecision("NEEDS_REVIEW", field_path, original, None, "score_below_threshold", tuple(scores))
    if margin < minimum_margin:
        return RereadDecision("NEEDS_REVIEW", field_path, original, None, "top_candidates_ambiguous", tuple(scores))
    proposed = record_with_candidate(record, field_path, best.candidate)
    return RereadDecision(
        "ACCEPT_PROPOSAL", field_path, original, best.candidate.value,
        "constraint_reduced_with_sufficient_score_and_margin", tuple(scores), proposed,
    )


def decision_to_dict(decision: RereadDecision) -> dict[str, Any]:
    result = asdict(decision)
    # Decimal candidate values remain serialized as source strings if needed.
    for score in result["scores"]:
        if isinstance(score["candidate"]["value"], Decimal):
            score["candidate"]["value"] = str(score["candidate"]["value"])
    return result

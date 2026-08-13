"""Composable constraint engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .base import ConstraintResult, GeologicalConstraint
from .depth import (
    ContinuityConstraint,
    DepthValidityConstraint,
    FinalDepthConsistencyConstraint,
    MonotonicityConstraint,
    ThicknessConsistencyConstraint,
)
from .semantic import (
    CoordinateFormatConstraint,
    FieldTypeConsistencyConstraint,
    GroundwaterReasonablenessConstraint,
    PercentageRangeConstraint,
    StratumCodeSequenceConstraint,
)


class ConstraintEngine:
    def __init__(self, constraints: Iterable[GeologicalConstraint]) -> None:
        self.constraints = tuple(constraints)

    def evaluate(self, record: Mapping[str, Any]) -> tuple[ConstraintResult, ...]:
        return tuple(constraint.evaluate(record) for constraint in self.constraints)


def default_engine(tolerance_m: str = "0.05") -> ConstraintEngine:
    return ConstraintEngine((
        DepthValidityConstraint(),
        ThicknessConsistencyConstraint(tolerance_m),
        ContinuityConstraint(tolerance_m),
        MonotonicityConstraint(),
        FinalDepthConsistencyConstraint(tolerance_m),
        GroundwaterReasonablenessConstraint(),
        PercentageRangeConstraint(),
        CoordinateFormatConstraint(),
        StratumCodeSequenceConstraint(),
        FieldTypeConsistencyConstraint(),
    ))


CONFIG_VERSION = "v001"
CONFIG_SECTIONS = (
    "depth_validity",
    "thickness_consistency",
    "continuity",
    "monotonicity",
    "final_depth_consistency",
    "groundwater_reasonableness",
    "percentage_range",
    "coordinate_format",
    "stratum_code_sequence",
    "field_type_consistency",
)
COMMON_KEYS = {"enabled", "severity"}
SECTION_KEYS = {
    "depth_validity": COMMON_KEYS,
    "thickness_consistency": COMMON_KEYS | {"tolerance_m"},
    "continuity": COMMON_KEYS | {"tolerance_m"},
    "monotonicity": COMMON_KEYS | {"tolerance_m"},
    "final_depth_consistency": COMMON_KEYS | {"tolerance_m"},
    "groundwater_reasonableness": COMMON_KEYS,
    "percentage_range": COMMON_KEYS | {"fields", "minimum", "maximum"},
    "coordinate_format": COMMON_KEYS | {"minimum_digits", "maximum_digits", "confusables"},
    "stratum_code_sequence": COMMON_KEYS,
    "field_type_consistency": COMMON_KEYS,
}


def _section(config: Mapping[str, Any], name: str) -> dict[str, Any]:
    value = config.get(name)
    if not isinstance(value, Mapping):
        raise ValueError(f"constraint config section {name!r} must be a mapping")
    unknown = sorted(set(value) - SECTION_KEYS[name])
    if unknown:
        raise ValueError(f"constraint config section {name!r} has unknown keys: {unknown}")
    if not isinstance(value.get("enabled"), bool):
        raise ValueError(f"constraint config section {name!r} requires boolean enabled")
    severity = value.get("severity")
    if not isinstance(severity, str) or not severity.strip():
        raise ValueError(f"constraint config section {name!r} requires non-empty severity")
    return dict(value)


def engine_from_config(config: Mapping[str, Any]) -> ConstraintEngine:
    """Build C1-C10 from a strict, complete, versioned configuration mapping."""

    if config.get("version") != CONFIG_VERSION:
        raise ValueError(f"constraint config version must be {CONFIG_VERSION!r}")
    unknown_sections = sorted(set(config) - ({"version"} | set(CONFIG_SECTIONS)))
    missing_sections = sorted(set(CONFIG_SECTIONS) - set(config))
    if unknown_sections:
        raise ValueError(f"constraint config has unknown sections: {unknown_sections}")
    if missing_sections:
        raise ValueError(f"constraint config lacks sections: {missing_sections}")

    sections = {name: _section(config, name) for name in CONFIG_SECTIONS}
    factories: dict[str, Callable[[], GeologicalConstraint]] = {
        "depth_validity": lambda: DepthValidityConstraint(
            severity=sections["depth_validity"]["severity"],
        ),
        "thickness_consistency": lambda: ThicknessConsistencyConstraint(
            tolerance_m=sections["thickness_consistency"].get("tolerance_m", "0.05"),
            severity=sections["thickness_consistency"]["severity"],
        ),
        "continuity": lambda: ContinuityConstraint(
            tolerance_m=sections["continuity"].get("tolerance_m", "0.05"),
            severity=sections["continuity"]["severity"],
        ),
        "monotonicity": lambda: MonotonicityConstraint(
            tolerance_m=sections["monotonicity"].get("tolerance_m", "0.00"),
            severity=sections["monotonicity"]["severity"],
        ),
        "final_depth_consistency": lambda: FinalDepthConsistencyConstraint(
            tolerance_m=sections["final_depth_consistency"].get("tolerance_m", "0.05"),
            severity=sections["final_depth_consistency"]["severity"],
        ),
        "groundwater_reasonableness": lambda: GroundwaterReasonablenessConstraint(
            severity=sections["groundwater_reasonableness"]["severity"],
        ),
        "percentage_range": lambda: PercentageRangeConstraint(
            field_names=sections["percentage_range"].get("fields", ("rqd_percent", "core_recovery_percent")),
            minimum=sections["percentage_range"].get("minimum", "0"),
            maximum=sections["percentage_range"].get("maximum", "100"),
            severity=sections["percentage_range"]["severity"],
        ),
        "coordinate_format": lambda: CoordinateFormatConstraint(
            minimum_digits=int(sections["coordinate_format"].get("minimum_digits", 4)),
            maximum_digits=int(sections["coordinate_format"].get("maximum_digits", 12)),
            confusables=tuple(sections["coordinate_format"].get("confusables", ("O/0", "I/1", "l/1"))),
            severity=sections["coordinate_format"]["severity"],
        ),
        "stratum_code_sequence": lambda: StratumCodeSequenceConstraint(
            severity=sections["stratum_code_sequence"]["severity"],
        ),
        "field_type_consistency": lambda: FieldTypeConsistencyConstraint(
            severity=sections["field_type_consistency"]["severity"],
        ),
    }
    constraints = [factories[name]() for name in CONFIG_SECTIONS if sections[name]["enabled"]]
    names = [constraint.name for constraint in constraints]
    if len(names) != len(set(names)):
        raise ValueError("constraint config produced duplicate constraint names")
    return ConstraintEngine(constraints)


def load_engine_config(path: Path) -> ConstraintEngine:
    """Load a strict YAML constraint configuration from disk."""

    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - environment-dependent guard
        raise RuntimeError("YAML constraint configuration requires PyYAML") from exc
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("constraint config root must be a mapping")
    return engine_from_config(payload)

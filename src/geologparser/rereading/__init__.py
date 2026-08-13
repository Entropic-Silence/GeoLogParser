"""Constraint-guided, evidence-preserving re-reading primitives."""
from .core import (
    Candidate, CandidateScore, RereadDecision, decide_reread, decision_to_dict,
    get_field, rank_candidates, record_with_candidate,
)
from .roi import (
    AuditedROIReader, ROICrop, ROIReaderOutput, crop_roi,
    numeric_candidates_from_regions, reread_numeric_roi, reread_numeric_roi_audited,
)
from .vlm_roi import VLMNumericROIAdapter

__all__ = [
    "Candidate", "CandidateScore", "RereadDecision", "decide_reread",
    "decision_to_dict", "get_field", "rank_candidates", "record_with_candidate",
    "AuditedROIReader", "ROICrop", "ROIReaderOutput", "VLMNumericROIAdapter",
    "crop_roi", "numeric_candidates_from_regions", "reread_numeric_roi",
    "reread_numeric_roi_audited",
]

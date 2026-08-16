"""Native multimodal structural reasoning for borehole logs.

The package deliberately separates visual structural evidence from the
deterministic geometry decoder.  Generative model outputs are hypotheses; they
are never treated as final critical depths without geometric reconstruction
and constraint validation.
"""

from .data import (
    DEFAULT_FROZEN_PATTERNS,
    LeakageError,
    NativeMMSample,
    build_nativemm_corpus,
    validate_training_source,
)
from .geometry import GeometryDecodeResult, decode_depth_geometry
from .structural_graph import StructuralGraphDecode, decode_structural_graph
from .dense_data import build_dense_boundary_corpus
from .dense_boundary import DenseBoundaryHead, SpatialBoundaryHead, extract_peaks

__all__ = [
    "DEFAULT_FROZEN_PATTERNS",
    "GeometryDecodeResult",
    "LeakageError",
    "NativeMMSample",
    "build_nativemm_corpus",
    "build_dense_boundary_corpus",
    "DenseBoundaryHead",
    "SpatialBoundaryHead",
    "extract_peaks",
    "decode_depth_geometry",
    "StructuralGraphDecode",
    "decode_structural_graph",
    "validate_training_source",
]

"""Dataset acquisition and manifest utilities."""
from .splits import assert_group_disjoint, assign_split, split_manifest, stable_manifest_hash

__all__ = ["assert_group_disjoint", "assign_split", "split_manifest", "stable_manifest_hash"]

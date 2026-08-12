"""Stable interfaces for vision-language model inference.

Heavy runtimes are imported only by concrete adapters so that the core package
and its unit tests remain usable on CPU-only machines.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class VLMGeneration:
    """One traceable VLM response before schema normalization."""

    text: str
    latency_seconds: float
    input_image_count: int
    prompt_version: str
    model_id: str
    model_revision: str
    peak_gpu_memory_bytes: int | None = None
    output_tokens: int | None = None
    hit_max_new_tokens: bool | None = None
    generation_config: Mapping[str, Any] = field(default_factory=dict)


class VLMAdapter(ABC):
    """Backend-neutral adapter used by B4/B5 and fusion experiments."""

    @abstractmethod
    def generate(
        self,
        images: Sequence[Path],
        prompt: str,
        *,
        prompt_version: str,
    ) -> VLMGeneration:
        raise NotImplementedError

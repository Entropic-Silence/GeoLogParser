"""Backend-neutral text-only LLM generation contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class LLMGeneration:
    text: str
    latency_seconds: float
    prompt_version: str
    model_id: str
    model_revision: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    peak_gpu_memory_bytes: int | None = None
    hit_max_new_tokens: bool | None = None
    generation_config: Mapping[str, Any] = field(default_factory=dict)


class LLMAdapter(ABC):
    @abstractmethod
    def generate(self, text: str, prompt: str, *, prompt_version: str) -> LLMGeneration:
        raise NotImplementedError

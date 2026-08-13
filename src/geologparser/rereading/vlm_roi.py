"""Strict numeric ROI transcription through a backend-neutral VLM adapter."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import re

from geologparser.ocr import TextRegion
from geologparser.vlm import VLMAdapter, parse_json_object

from .roi import ROIReaderOutput


NUMERIC_TOKEN = re.compile(r"[-+]?(?:\d+(?:[.,]\d+)?|[.,]\d+)")


class VLMNumericROIAdapter:
    """Transcribe visible numeric tokens without assigning uncalibrated confidence."""

    def __init__(
        self, adapter: VLMAdapter, prompt: str, *, prompt_version: str,
        name: str = "vlm_numeric_roi",
    ) -> None:
        if not prompt.strip():
            raise ValueError("numeric ROI prompt must not be empty")
        if not prompt_version.strip():
            raise ValueError("numeric ROI prompt version must not be empty")
        self.adapter = adapter
        self.prompt = prompt
        self.prompt_version = prompt_version
        self.name = name

    def read(self, path: Path) -> ROIReaderOutput:
        generation = self.adapter.generate(
            [path], self.prompt, prompt_version=self.prompt_version,
        )
        audit = asdict(generation)
        audit.update({
            "adapter_type": "vlm",
            "parse_status": "failed",
            "numeric_tokens": [],
            "confidence_policy": "none_uncalibrated",
            "grounding_policy": "whole_roi_no_token_bbox",
        })
        try:
            payload = parse_json_object(generation.text)
            if set(payload) != {"numeric_tokens", "uncertain"}:
                raise ValueError("response must contain only numeric_tokens and uncertain")
            tokens = payload["numeric_tokens"]
            if not isinstance(tokens, list) or any(not isinstance(token, str) for token in tokens):
                raise ValueError("numeric_tokens must be an array of strings")
            if not isinstance(payload["uncertain"], bool):
                raise ValueError("uncertain must be boolean")
            invalid = [token for token in tokens if NUMERIC_TOKEN.fullmatch(token.strip()) is None]
            if invalid:
                raise ValueError(f"non-numeric token(s): {invalid}")
            cleaned = [token.strip() for token in tokens]
        except (KeyError, TypeError, ValueError) as exc:
            audit["parse_error"] = f"{type(exc).__name__}: {exc}"
            return ROIReaderOutput((), audit)
        audit.update({
            "parse_status": "valid",
            "numeric_tokens": cleaned,
            "uncertain": payload["uncertain"],
        })
        if payload["uncertain"]:
            audit["candidate_policy"] = "withheld_uncertain"
            return ROIReaderOutput((), audit)
        audit["candidate_policy"] = "eligible_uncalibrated"
        regions = tuple(
            TextRegion(page=1, bbox=None, text=token, confidence=None, method="vlm")
            for token in cleaned
        )
        return ROIReaderOutput(regions, audit)

"""Dense multimodal boundary detector with deterministic depth reconstruction."""

from __future__ import annotations

import math

import torch
from torch import nn
from torch.nn import functional as F


class ResidualBlock(nn.Module):
    def __init__(self, channels: int, dilation: int) -> None:
        super().__init__()
        self.norm = nn.GroupNorm(8, channels)
        self.conv1 = nn.Conv1d(channels, channels, 5, padding=2 * dilation, dilation=dilation)
        self.conv2 = nn.Conv1d(channels, channels, 3, padding=dilation, dilation=dilation)
        self.dropout = nn.Dropout(0.10)

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        hidden = F.gelu(self.conv1(self.norm(value)))
        hidden = self.dropout(self.conv2(hidden))
        return value + hidden


class DenseBoundaryHead(nn.Module):
    """Fuse document-VLM row embeddings with native-resolution pixel evidence."""

    def __init__(self, visual_dim: int, pixel_dim: int, hidden_dim: int = 128) -> None:
        super().__init__()
        self.visual_dim = visual_dim
        self.pixel_dim = pixel_dim
        self.input_projection = nn.Conv1d(visual_dim + pixel_dim, hidden_dim, 1)
        self.blocks = nn.Sequential(
            ResidualBlock(hidden_dim, 1),
            ResidualBlock(hidden_dim, 2),
            ResidualBlock(hidden_dim, 4),
            ResidualBlock(hidden_dim, 8),
        )
        self.logit_head = nn.Conv1d(hidden_dim, 1, 1)

    def forward(self, visual: torch.Tensor, pixels: torch.Tensor) -> torch.Tensor:
        value = torch.cat([visual, pixels], dim=1)
        hidden = F.gelu(self.input_projection(value))
        return self.logit_head(self.blocks(hidden)).squeeze(1)


class SpatialBoundaryHead(nn.Module):
    """Preserve column semantics while fusing VLM and native pixel evidence.

    Four learned column-role attention heads allow different evidence routes
    (lithology, recovery, description/contact and depth scale) without assuming
    a fixed template-specific x coordinate.
    """

    def __init__(
        self,
        visual_dim: int = 1024,
        hidden_dim: int = 64,
        role_heads: int = 4,
        mode: str = "fused",
    ) -> None:
        super().__init__()
        if mode not in {"fused", "pixel_only", "visual_only"}:
            raise ValueError(f"unknown evidence mode: {mode}")
        self.mode = mode
        self.role_heads = role_heads
        if mode != "pixel_only":
            self.visual_projection = nn.Conv2d(visual_dim, hidden_dim // 2, 1)
        if mode != "visual_only":
            self.pixel_encoder = nn.Sequential(
                nn.Conv2d(1, hidden_dim // 4, (7, 5), padding=(3, 2)),
                nn.GELU(),
                nn.Conv2d(hidden_dim // 4, hidden_dim // 2, (5, 5), stride=(1, 2), padding=2),
                nn.GELU(),
                nn.Conv2d(hidden_dim // 2, hidden_dim // 2, (5, 5), stride=(1, 2), padding=2),
                nn.GELU(),
            )
        input_dim = hidden_dim if mode == "fused" else hidden_dim // 2
        self.fusion = nn.Sequential(
            nn.Conv2d(input_dim, hidden_dim, 1),
            nn.GELU(),
            nn.Conv2d(hidden_dim, hidden_dim, (7, 3), padding=(3, 1)),
            nn.GELU(),
            nn.Conv2d(hidden_dim, hidden_dim, (7, 3), padding=(6, 1), dilation=(2, 1)),
            nn.GELU(),
            nn.Conv2d(hidden_dim, hidden_dim, (7, 3), padding=(12, 1), dilation=(4, 1)),
            nn.GELU(),
        )
        self.role_head = nn.Conv1d(hidden_dim, role_heads, 1)
        self.evidence_head = nn.Conv2d(hidden_dim, role_heads, 1)

    def forward(self, visual_grid: torch.Tensor, pixels: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        routes = []
        target_size = (pixels.shape[-2], pixels.shape[-1] // 4)
        if self.mode != "pixel_only":
            visual = self.visual_projection(visual_grid)
            routes.append(F.interpolate(visual, size=target_size, mode="bilinear", align_corners=False))
        if self.mode != "visual_only":
            routes.append(self.pixel_encoder(pixels))
        else:
            # Visual-only still uses the declared output grid for a fair y/x
            # resolution and never consumes pixel values as evidence.
            routes[0] = F.interpolate(routes[0], size=target_size, mode="bilinear", align_corners=False)
        hidden = self.fusion(torch.cat(routes, dim=1) if len(routes) > 1 else routes[0])
        role_logits = self.role_head(hidden.mean(dim=2))
        role_weights = torch.softmax(role_logits, dim=-1)
        evidence = self.evidence_head(hidden)
        per_role = (evidence * role_weights.unsqueeze(2)).sum(dim=-1)
        logits = torch.logsumexp(per_role, dim=1) - math.log(self.role_heads)
        return logits, role_weights


def gaussian_targets(boundaries_y: list[float], bins: int, sigma_bins: float = 1.35) -> torch.Tensor:
    positions = torch.arange(bins, dtype=torch.float32)
    target = torch.zeros(bins, dtype=torch.float32)
    for value in boundaries_y:
        center = max(0.0, min(float(bins - 1), float(value) * (bins - 1)))
        target = torch.maximum(target, torch.exp(-0.5 * ((positions - center) / sigma_bins) ** 2))
    return target


def boundary_loss(logits: torch.Tensor, targets: torch.Tensor, positive_weight: float = 12.0) -> torch.Tensor:
    weights = 1.0 + targets * (positive_weight - 1.0)
    bce = F.binary_cross_entropy_with_logits(logits, targets, weight=weights)
    probability = torch.sigmoid(logits)
    intersection = (probability * targets).sum(dim=-1)
    dice = 1.0 - (2.0 * intersection + 1.0) / (probability.sum(dim=-1) + targets.sum(dim=-1) + 1.0)
    return bce + dice.mean()


def extract_peaks(
    probabilities: torch.Tensor,
    *,
    threshold: float,
    minimum_separation_bins: int = 3,
) -> list[tuple[float, float]]:
    """Return sub-bin normalized y and confidence after one-dimensional NMS."""
    values = probabilities.detach().float().cpu()
    candidates = []
    for index in range(len(values)):
        left = values[index - 1] if index else -math.inf
        right = values[index + 1] if index + 1 < len(values) else -math.inf
        if values[index] >= threshold and values[index] >= left and values[index] >= right:
            candidates.append(index)
    selected: list[int] = []
    for index in sorted(candidates, key=lambda item: float(values[item]), reverse=True):
        if all(abs(index - existing) >= minimum_separation_bins for existing in selected):
            selected.append(index)
    output = []
    for index in sorted(selected):
        lo, hi = max(0, index - 1), min(len(values), index + 2)
        local = values[lo:hi].clamp_min(1e-6)
        coordinate = (local * torch.arange(lo, hi, dtype=torch.float32)).sum() / local.sum()
        output.append((float(coordinate / (len(values) - 1)), float(values[index])))
    return output

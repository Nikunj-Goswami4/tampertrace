"""
Pydantic response models for the document analysis API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SignalResult(BaseModel):
    """Result from a single forensic signal."""

    name: str = Field(
        ...,
        description="Signal identifier (e.g. 'trufor', 'ela', 'copy_move', 'exif', 'ocr').",
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Signal-specific score normalised to [0, 1].",
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Signal-specific detail payload (diff maps, regions, tags, …).",
    )


class PageAnalysis(BaseModel):
    """Analysis results for a single page / image."""

    page_number: int = Field(
        ...,
        ge=1,
        description="1-indexed page number.",
    )
    verdict: str = Field(
        ...,
        description="Overall verdict: 'Authentic', 'Uncertain', or 'Likely Tampered'.",
    )
    confidence_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Confidence in the verdict (0–100 %).",
    )
    fused_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weighted ensemble score.",
    )
    original_image_b64: Optional[str] = Field(
        None,
        description="Base64-encoded JPEG of the original page image.",
    )
    heatmap_base64: Optional[str] = Field(
        None,
        description="Base64-encoded PNG anomaly heatmap (from TruFor or ELA).",
    )
    signals: List[SignalResult] = Field(
        default_factory=list,
        description="Per-signal breakdown.",
    )


class AnalysisResponse(BaseModel):
    """Top-level response returned by ``POST /api/analyze``."""

    filename: str = Field(..., description="Original uploaded filename.")
    total_pages: int = Field(..., ge=1, description="Number of pages analysed.")
    pages: List[PageAnalysis] = Field(
        default_factory=list,
        description="Per-page analysis results.",
    )


class HealthResponse(BaseModel):
    """Response for the ``GET /healthz`` endpoint."""

    status: str = Field("ok", description="Service health status.")
    version: str = Field(..., description="Application version string.")

"""
POST /api/analyze — document tampering analysis endpoint.

Accepts a multipart file upload (JPEG, PNG, or PDF), runs all forensic
signals on each page, fuses the results, and returns a structured
:class:`AnalysisResponse`.
"""

from __future__ import annotations

import logging
from typing import List

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile, File

from app.forensics.ela import run_ela
from app.forensics.copy_move import detect_copy_move
from app.forensics.exif_check import check_exif
from app.forensics.trufor_wrapper import run_trufor
from app.forensics.ocr_consistency import check_ocr_consistency
from app.forensics.fusion import fuse_signals
from app.services.pdf_converter import pdf_to_images
from app.schemas.analysis import (
    AnalysisResponse,
    PageAnalysis,
    SignalResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])

_ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/jpg",
    "application/pdf",
}


def _decode_image(raw: bytes) -> np.ndarray:
    """Decode raw image bytes to a BGR ``np.ndarray``."""
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image bytes.")
    return img


def _analyse_page(
    image: np.ndarray,
    raw_bytes: bytes,
    page_num: int,
) -> PageAnalysis:
    """Run all forensic signals on a single page image and fuse."""

    # ── individual signals ────────────────────────────────────────────
    ela_result = run_ela(image)
    cm_result = detect_copy_move(image)
    exif_result = check_exif(raw_bytes)
    ocr_result = check_ocr_consistency(image)

    # TruFor — may return an error dict if weights are missing
    trufor_result = run_trufor(image)

    # ── extract scores (default to 0 on error) ────────────────────────
    trufor_score = trufor_result.get("integrity_score", 0.0) if "error" not in trufor_result else 0.0
    ela_score = ela_result.get("ela_score", 0.0) if "error" not in ela_result else 0.0
    cm_score = cm_result.get("copy_move_score", 0.0)

    # OCR/EXIF combined: take the max signal
    ocr_score = ocr_result.get("ocr_anomaly_score", 0.0) if "error" not in ocr_result else 0.0
    exif_editor = 1.0 if exif_result.get("software_is_editor") else 0.0
    exif_ts = 1.0 if exif_result.get("timestamp_discrepancy") else 0.0
    ocr_exif_score = max(ocr_score, exif_editor, exif_ts)

    # ── fuse ──────────────────────────────────────────────────────────
    fusion = fuse_signals(
        trufor_score=trufor_score,
        ela_score=ela_score,
        copy_move_score=cm_score,
        ocr_exif_score=ocr_exif_score,
    )

    # ── pick best available heatmap ───────────────────────────────────
    heatmap = trufor_result.get("anomaly_heatmap_b64") or ela_result.get("diff_map_b64")

    # ── build signal breakdown ────────────────────────────────────────
    signals: List[SignalResult] = [
        SignalResult(
            name="trufor",
            score=trufor_score,
            details={k: v for k, v in trufor_result.items() if k != "integrity_score"},
        ),
        SignalResult(
            name="ela",
            score=ela_score,
            details={k: v for k, v in ela_result.items() if k != "ela_score"},
        ),
        SignalResult(
            name="copy_move",
            score=cm_score,
            details={k: v for k, v in cm_result.items() if k != "copy_move_score"},
        ),
        SignalResult(
            name="exif",
            score=max(exif_editor, exif_ts),
            details=exif_result,
        ),
        SignalResult(
            name="ocr",
            score=ocr_score,
            details={k: v for k, v in ocr_result.items() if k != "ocr_anomaly_score"},
        ),
    ]

    import base64
    success, buffer = cv2.imencode(".jpg", image)
    original_b64 = base64.b64encode(buffer).decode("utf-8") if success else None

    return PageAnalysis(
        page_number=page_num,
        verdict=fusion["verdict"],
        confidence_pct=fusion["confidence_pct"],
        fused_score=fusion["fused_score"],
        original_image_b64=original_b64,
        heatmap_base64=heatmap,
        signals=signals,
    )


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Analyse a document for tampering",
)
async def analyze_document(
    file: UploadFile = File(..., description="JPEG, PNG, or PDF document to analyse."),
) -> AnalysisResponse:
    """Accept a multipart file upload and return per-page forensic analysis."""

    # ── validate content type ─────────────────────────────────────────
    content_type = (file.content_type or "").lower()
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported media type '{content_type}'. "
                f"Accepted: {', '.join(sorted(_ALLOWED_CONTENT_TYPES))}."
            ),
        )

    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    filename = file.filename or "unknown"

    # ── convert to page images ────────────────────────────────────────
    page_images: List[np.ndarray]

    if content_type == "application/pdf":
        try:
            page_images = pdf_to_images(raw_bytes)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        if not page_images:
            raise HTTPException(status_code=400, detail="PDF contains no pages.")
    else:
        try:
            page_images = [_decode_image(raw_bytes)]
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    # ── analyse each page sequentially ────────────────────────────────
    pages: List[PageAnalysis] = []
    for idx, img in enumerate(page_images, start=1):
        logger.info("Analysing page %d / %d of '%s'", idx, len(page_images), filename)
        page_result = _analyse_page(img, raw_bytes, page_num=idx)
        pages.append(page_result)

    return AnalysisResponse(
        filename=filename,
        total_pages=len(pages),
        pages=pages,
    )

"""
Error Level Analysis (ELA).

Re-compresses an image at a given JPEG quality and measures the pixel-wise
difference from the original.  Tampered regions that were saved at a
different quality level will show larger residuals.

Pure function: np.ndarray in → structured dict out.
"""

from __future__ import annotations

import base64
from typing import Dict, Any

import cv2
import numpy as np


def run_ela(
    image: np.ndarray,
    quality: int = 90,
    scale: int = 15,
) -> Dict[str, Any]:
    """Run Error Level Analysis on *image*.

    Parameters
    ----------
    image : np.ndarray
        BGR image (OpenCV convention).
    quality : int
        JPEG re-compression quality (1-100).  Lower values amplify
        differences but also raise the noise floor.
    scale : int
        Multiplier applied to the absolute difference so that subtle
        artefacts become visible.

    Returns
    -------
    dict
        ``ela_score``  – float in [0, 1]; 0 = pristine, 1 = heavily tampered.
        ``diff_map_b64`` – base64-encoded PNG of the amplified diff image.
        ``quality_used`` – the JPEG quality that was applied.
    """
    # ── guard: validate input ───────────────────────────────────────────
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        return {"error": "Invalid or empty image array."}

    if image.ndim < 2:
        return {"error": "Image must be at least 2-dimensional."}

    # ── JPEG re-compression in memory ──────────────────────────────────
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    success, jpeg_buf = cv2.imencode(".jpg", image, encode_params)
    if not success:
        return {"error": "JPEG encoding failed – image may be corrupt."}

    recompressed = cv2.imdecode(
        np.frombuffer(jpeg_buf, dtype=np.uint8), cv2.IMREAD_COLOR
    )

    # ── pixel-wise difference ──────────────────────────────────────────
    diff = cv2.absdiff(image, recompressed).astype(np.float32)
    scaled_diff = np.clip(diff * scale, 0, 255).astype(np.uint8)

    # ── tamper score (mean intensity normalised to 0-1) ────────────────
    ela_score = float(np.mean(scaled_diff) / 255.0)

    # ── encode diff map as base64 PNG ──────────────────────────────────
    _, png_buf = cv2.imencode(".png", scaled_diff)
    diff_map_b64 = base64.b64encode(png_buf).decode("ascii")

    return {
        "ela_score": ela_score,
        "diff_map_b64": diff_map_b64,
        "quality_used": quality,
    }

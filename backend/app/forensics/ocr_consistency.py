"""
OCR consistency analysis.

Runs RapidOCR to extract text bounding boxes, then performs statistical
outlier detection (IQR method) on character spacing and baseline heights
to flag regions with anomalous typographic properties.

Pure function: np.ndarray in → structured dict out.
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

try:
    from rapidocr_onnxruntime import RapidOCR
except ImportError:  # pragma: no cover
    RapidOCR = None  # type: ignore[assignment,misc]

# ----------------
# Initialize ONNX engine globally so it stays in RAM
_OCR_ENGINE = RapidOCR()
# ----------------

def _iqr_bounds(values: np.ndarray) -> tuple:
    """Return (Q1, Q3, lower_fence, upper_fence) using the 1.5×IQR rule."""
    q1 = float(np.percentile(values, 25))
    q3 = float(np.percentile(values, 75))
    iqr = q3 - q1
    return q1, q3, q1 - 1.5 * iqr, q3 + 1.5 * iqr


def _bbox_centre_y(bbox: list) -> float:
    """Compute the vertical centre of a quadrilateral bounding box.

    RapidOCR returns each bbox as ``[[x0,y0],[x1,y1],[x2,y2],[x3,y3]]``.
    """
    ys = [pt[1] for pt in bbox]
    return float(np.mean(ys))


def _bbox_width(bbox: list) -> float:
    """Compute the horizontal span of a quadrilateral bounding box."""
    xs = [pt[0] for pt in bbox]
    return float(max(xs) - min(xs))


def check_ocr_consistency(
    image: np.ndarray,
    lang: str = "en",
) -> Dict[str, Any]:
    """Detect typographic inconsistencies in text regions of *image*.

    Parameters
    ----------
    image : np.ndarray
        BGR image (OpenCV convention).
    lang : str
        Language code (not actively passed to RapidOCR which supports multi-lang automatically, but kept for signature compatibility).

    Returns
    -------
    dict
        ``ocr_anomaly_score`` – float in [0, 1]; ratio of outlier boxes.
        ``total_boxes``       – total detected text boxes.
        ``outlier_boxes``     – count of flagged outliers.
        ``outliers``          – detailed list of flagged boxes.
        ``spacing_stats``     – descriptive statistics for char spacing.
        ``baseline_stats``    – descriptive statistics for baseline height.
    """

    
    # ---------------------------------------------------------
    # Use the global engine instead of recreating it
    result, _ = _OCR_ENGINE(image)
    # ---------------------------------------------------------


    # ── guard ──────────────────────────────────────────────────────────
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        return {
            "ocr_anomaly_score": 0.0,
            "total_boxes": 0,
            "outlier_boxes": 0,
            "outliers": [],
            "spacing_stats": {},
            "baseline_stats": {},
        }

    # ── RapidOCR availability guard ─────────────────────────────────────
    if RapidOCR is None:
        return {"error": "rapidocr_onnxruntime is not installed."}

    engine = RapidOCR()
    result, _ = engine(image)

    # RapidOCR returns a list of [bbox, text, conf] or None.
    if not result:
        return {
            "ocr_anomaly_score": 0.0,
            "total_boxes": 0,
            "outlier_boxes": 0,
            "outliers": [],
            "spacing_stats": {},
            "baseline_stats": {},
        }

    detections = result  # list of [bbox, text, conf]

    # ── collect metrics ────────────────────────────────────────────────
    records: List[Dict[str, Any]] = []
    for det in detections:
        bbox, text, _conf = det
        char_count = len(text.strip())
        width = _bbox_width(bbox)
        baseline = _bbox_centre_y(bbox)
        spacing = width / max(char_count, 1)
        records.append(
            {
                "text": text,
                "bbox": bbox,
                "char_spacing": spacing,
                "baseline_height": baseline,
                "flags": [],
            }
        )

    total_boxes = len(records)
    if total_boxes < 3:
        # Not enough data for meaningful outlier detection.
        return {
            "ocr_anomaly_score": 0.0,
            "total_boxes": total_boxes,
            "outlier_boxes": 0,
            "outliers": [],
            "spacing_stats": {},
            "baseline_stats": {},
        }

    spacings = np.array([r["char_spacing"] for r in records])
    baselines = np.array([r["baseline_height"] for r in records])

    sp_q1, sp_q3, sp_lo, sp_hi = _iqr_bounds(spacings)
    bl_q1, bl_q3, bl_lo, bl_hi = _iqr_bounds(baselines)

    # ── flag outliers ──────────────────────────────────────────────────
    outliers: List[Dict[str, Any]] = []
    for rec in records:
        if rec["char_spacing"] < sp_lo or rec["char_spacing"] > sp_hi:
            rec["flags"].append("spacing_outlier")
        if rec["baseline_height"] < bl_lo or rec["baseline_height"] > bl_hi:
            rec["flags"].append("baseline_outlier")
        if rec["flags"]:
            outliers.append(rec)

    outlier_count = len(outliers)
    score = min(1.0, outlier_count / total_boxes) if total_boxes else 0.0

    return {
        "ocr_anomaly_score": float(score),
        "total_boxes": total_boxes,
        "outlier_boxes": outlier_count,
        "outliers": outliers,
        "spacing_stats": {
            "mean": float(np.mean(spacings)),
            "std": float(np.std(spacings)),
            "q1": sp_q1,
            "q3": sp_q3,
        },
        "baseline_stats": {
            "mean": float(np.mean(baselines)),
            "std": float(np.std(baselines)),
            "q1": bl_q1,
            "q3": bl_q3,
        },
    }

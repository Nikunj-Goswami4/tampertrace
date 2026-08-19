"""
Fusion scoring engine.

Loads calibrated weights from ``config/calibrated_config.json`` (via
:pydata:`Settings.calibrated_config`) and computes a weighted ensemble
score from the individual forensic signals, mapping the result to a
three-way verdict.

Pure function: individual scores in → structured dict out.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── hardcoded defaults (used if calibrated_config.json is absent) ──────
_DEFAULT_WEIGHTS: Dict[str, float] = {
    "trufor": 0.50,
    "ela": 0.25,
    "copy_move": 0.15,
    "ocr_exif": 0.10,
}
_DEFAULT_THRESH_AUTHENTIC = 0.30
_DEFAULT_THRESH_TAMPERED = 0.65


def _load_weights() -> Dict[str, float]:
    """Return the weight vector from calibrated config, falling back to
    defaults."""
    cfg = settings.calibrated_config
    return cfg.get("weights", _DEFAULT_WEIGHTS)


def _load_thresholds() -> tuple[float, float]:
    """Return ``(authentic_below, tampered_above)``."""
    cfg = settings.calibrated_config
    thresholds = cfg.get("thresholds", {})
    return (
        thresholds.get("authentic_below", _DEFAULT_THRESH_AUTHENTIC),
        thresholds.get("tampered_above", _DEFAULT_THRESH_TAMPERED),
    )


def _verdict_confidence(score: float, lo: float, hi: float) -> tuple[str, float]:
    """Map *score* to a verdict string and a confidence percentage.

    Confidence reflects how far the score sits from the nearest decision
    boundary:
    - score ≤ lo  → 'Authentic',   confidence = 100 × (1 - score / lo)
    - score ≥ hi  → 'Likely Tampered', confidence = 100 × ((score - hi) / (1 - hi))
    - otherwise   → 'Uncertain',   confidence scales from 0 at boundaries
                     to a maximum at the midpoint between lo and hi.
    """
    if score <= lo:
        # Confidence: 100 % at score=0, 0 % at score=lo
        conf = 100.0 * (1.0 - score / lo) if lo > 0 else 100.0
        return "Authentic", round(min(max(conf, 0.0), 100.0), 1)

    if score >= hi:
        # Confidence: 0 % at score=hi, 100 % at score=1
        denom = 1.0 - hi
        conf = 100.0 * ((score - hi) / denom) if denom > 0 else 100.0
        return "Likely Tampered", round(min(max(conf, 0.0), 100.0), 1)

    # Uncertain zone — confidence is low; peaks at the midpoint.
    mid = (lo + hi) / 2.0
    half_span = (hi - lo) / 2.0
    distance_from_mid = abs(score - mid)
    conf = 100.0 * (1.0 - distance_from_mid / half_span) if half_span > 0 else 0.0
    # Cap at 50 % for uncertain verdicts to signal low trust.
    conf = min(conf, 50.0)
    return "Uncertain", round(min(max(conf, 0.0), 100.0), 1)


def fuse_signals(
    trufor_score: float = 0.0,
    ela_score: float = 0.0,
    copy_move_score: float = 0.0,
    ocr_exif_score: float = 0.0,
) -> Dict[str, Any]:
    """Compute a weighted ensemble of forensic signal scores.

    Parameters
    ----------
    trufor_score, ela_score, copy_move_score, ocr_exif_score : float
        Individual signal scores, each in [0, 1].

    Returns
    -------
    dict
        ``fused_score``    – float in [0, 1].
        ``verdict``        – ``'Authentic'``, ``'Uncertain'``, or
                             ``'Likely Tampered'``.
        ``confidence_pct`` – 0-100 indicating decision confidence.
        ``weights_used``   – the weight vector that was applied.
    """
    weights = _load_weights()

    fused = (
        weights.get("trufor", 0.50) * trufor_score
        + weights.get("ela", 0.25) * ela_score
        + weights.get("copy_move", 0.15) * copy_move_score
        + weights.get("ocr_exif", 0.10) * ocr_exif_score
    )
    fused = max(0.0, min(1.0, fused))

    lo, hi = _load_thresholds()
    verdict, confidence = _verdict_confidence(fused, lo, hi)

    return {
        "fused_score": round(fused, 4),
        "verdict": verdict,
        "confidence_pct": confidence,
        "weights_used": weights,
    }

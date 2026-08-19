"""
EXIF metadata inspection.

Extracts EXIF tags from raw image bytes, checks for editing-software
signatures and timestamp discrepancies.

Pure function: bytes in → structured dict out.
"""

from __future__ import annotations

import re
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image
from PIL.ExifTags import TAGS

# Known image-editing applications (case-insensitive substring match).
_EDITOR_PATTERNS: List[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"photoshop",
        r"gimp",
        r"affinity",
        r"paint\.net",
        r"snapseed",
        r"lightroom",
        r"pixlr",
        r"capture\s*one",
        r"darktable",
        r"luminar",
        r"adobe",
    )
]

# EXIF tag IDs for the three standard date/time fields.
_TAG_DATETIME = 0x0132          # DateTime (modified)
_TAG_DATETIME_ORIGINAL = 0x9003  # DateTimeOriginal
_TAG_DATETIME_DIGITIZED = 0x9004  # DateTimeDigitized
_TAG_SOFTWARE = 0x0131           # Software

_EXIF_DT_FMT = "%Y:%m:%d %H:%M:%S"


def _parse_exif_dt(value: Optional[str]) -> Optional[datetime]:
    """Try to parse an EXIF date/time string; return *None* on failure."""
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), _EXIF_DT_FMT)
    except (ValueError, TypeError):
        return None


def _timestamps_diverge(
    ts: Dict[str, Optional[str]], max_delta_seconds: float = 1.0
) -> bool:
    """Return *True* if any pair of non-null timestamps differs by more than
    *max_delta_seconds*."""
    parsed: List[Tuple[str, datetime]] = []
    for label, raw in ts.items():
        dt = _parse_exif_dt(raw)
        if dt is not None:
            parsed.append((label, dt))

    for i in range(len(parsed)):
        for j in range(i + 1, len(parsed)):
            if abs((parsed[i][1] - parsed[j][1]).total_seconds()) > max_delta_seconds:
                return True
    return False


def check_exif(image_bytes: bytes) -> Dict[str, Any]:
    """Inspect EXIF metadata for editing-software signatures and timestamp
    discrepancies.

    Parameters
    ----------
    image_bytes : bytes
        Raw file bytes (JPEG, PNG, TIFF, …).  Passing raw bytes rather
        than a decoded array preserves the EXIF data.

    Returns
    -------
    dict
        ``has_exif``             – bool
        ``software``             – str | None
        ``software_is_editor``   – bool
        ``timestamps``           – dict with keys original / digitized / modified
        ``timestamp_discrepancy``– bool
        ``all_tags``             – dict of human-readable tag name → value
    """
    try:
        img = Image.open(BytesIO(image_bytes))
    except Exception:
        return {
            "has_exif": False,
            "software": None,
            "software_is_editor": False,
            "timestamps": {"original": None, "digitized": None, "modified": None},
            "timestamp_discrepancy": False,
            "all_tags": {},
        }

    raw_exif: Dict[int, Any] = {}
    try:
        raw_exif = img._getexif() or {}  # type: ignore[union-attr]
    except (AttributeError, Exception):
        pass

    has_exif = bool(raw_exif)

    # ── human-readable tag dump ────────────────────────────────────────
    all_tags: Dict[str, Any] = {}
    for tag_id, value in raw_exif.items():
        tag_name = TAGS.get(tag_id, f"0x{tag_id:04X}")
        # Some tags contain bytes that are not JSON-serialisable.
        try:
            if isinstance(value, bytes):
                value = value.hex()
            all_tags[tag_name] = value
        except Exception:
            all_tags[tag_name] = str(value)

    # ── software check ─────────────────────────────────────────────────
    software: Optional[str] = raw_exif.get(_TAG_SOFTWARE)
    if isinstance(software, bytes):
        software = software.decode("utf-8", errors="replace")
    software_is_editor = False
    if software:
        software_is_editor = any(pat.search(software) for pat in _EDITOR_PATTERNS)

    # ── timestamps ─────────────────────────────────────────────────────
    def _get_str(tag_id: int) -> Optional[str]:
        val = raw_exif.get(tag_id)
        if isinstance(val, bytes):
            return val.decode("utf-8", errors="replace")
        return val if isinstance(val, str) else None

    timestamps = {
        "original": _get_str(_TAG_DATETIME_ORIGINAL),
        "digitized": _get_str(_TAG_DATETIME_DIGITIZED),
        "modified": _get_str(_TAG_DATETIME),
    }
    timestamp_discrepancy = _timestamps_diverge(timestamps)

    return {
        "has_exif": has_exif,
        "software": software,
        "software_is_editor": software_is_editor,
        "timestamps": timestamps,
        "timestamp_discrepancy": timestamp_discrepancy,
        "all_tags": all_tags,
    }

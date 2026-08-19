"""
Forensic signal analysis modules.

Each function is a pure function: image array (or bytes) in, structured dict out.
No side effects.
"""

from .ela import run_ela
from .copy_move import detect_copy_move
from .exif_check import check_exif
from .trufor_wrapper import run_trufor
from .ocr_consistency import check_ocr_consistency

__all__ = [
    "run_ela",
    "detect_copy_move",
    "check_exif",
    "run_trufor",
    "check_ocr_consistency",
]

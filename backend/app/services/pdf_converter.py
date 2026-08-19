"""
PDF-to-image conversion service.

Uses PyMuPDF (``fitz``) to render each page of a PDF document into a
BGR ``np.ndarray`` suitable for the forensic analysis pipeline.

Pure function: bytes in → list of np.ndarray out.
"""

from __future__ import annotations

from typing import List

import fitz  # PyMuPDF
import numpy as np


def pdf_to_images(
    pdf_bytes: bytes,
    dpi: int = 200,
) -> List[np.ndarray]:
    """Convert a multi-page PDF to a list of BGR images.

    Parameters
    ----------
    pdf_bytes : bytes
        Raw PDF file content.
    dpi : int
        Resolution for rasterisation.  200 dpi strikes a balance between
        detail and memory usage.

    Returns
    -------
    list[np.ndarray]
        One BGR image (OpenCV convention) per page.

    Raises
    ------
    ValueError
        If *pdf_bytes* cannot be opened as a PDF.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError(f"Could not open PDF: {exc}") from exc

    images: List[np.ndarray] = []
    zoom = dpi / 72.0  # fitz default is 72 dpi
    matrix = fitz.Matrix(zoom, zoom)

    for page in doc:
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        # pix.samples is RGB, shape (h, w, 3)
        img_rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, 3
        )
        # Convert RGB → BGR for OpenCV / forensic modules
        img_bgr = img_rgb[:, :, ::-1].copy()
        images.append(img_bgr)

    doc.close()
    return images

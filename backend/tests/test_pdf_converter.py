"""Tests for backend.app.services.pdf_converter – PDF-to-image conversion."""

import numpy as np
import pytest

from app.services.pdf_converter import pdf_to_images


def _make_minimal_pdf() -> bytes:
    """Create a tiny 1-page PDF in memory using PyMuPDF."""
    import fitz

    doc = fitz.open()
    page = doc.new_page(width=100, height=100)
    # Draw something so the raster isn't blank
    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(10, 10, 90, 90))
    shape.finish(color=(1, 0, 0), fill=(0, 0, 1))
    shape.commit()

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def _make_multipage_pdf(n: int = 3) -> bytes:
    """Create an *n*-page PDF."""
    import fitz

    doc = fitz.open()
    for _ in range(n):
        doc.new_page(width=100, height=100)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


class TestPdfToImages:
    """Unit tests for ``pdf_to_images``."""

    def test_single_page(self) -> None:
        images = pdf_to_images(_make_minimal_pdf())
        assert len(images) == 1
        assert isinstance(images[0], np.ndarray)
        assert images[0].ndim == 3
        assert images[0].shape[2] == 3  # BGR

    def test_multipage(self) -> None:
        images = pdf_to_images(_make_multipage_pdf(3))
        assert len(images) == 3

    def test_dpi_affects_size(self) -> None:
        lo = pdf_to_images(_make_minimal_pdf(), dpi=72)
        hi = pdf_to_images(_make_minimal_pdf(), dpi=200)
        # Higher DPI → larger pixel dimensions
        assert hi[0].shape[0] > lo[0].shape[0]
        assert hi[0].shape[1] > lo[0].shape[1]

    def test_invalid_bytes_raises(self) -> None:
        with pytest.raises(ValueError, match="Could not open PDF"):
            pdf_to_images(b"not a pdf")

    def test_empty_bytes_raises(self) -> None:
        with pytest.raises(ValueError):
            pdf_to_images(b"")

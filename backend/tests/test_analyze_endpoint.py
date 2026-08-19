"""Tests for backend.app.api.analyze – POST /api/analyze endpoint."""

from io import BytesIO
from unittest.mock import patch, MagicMock

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── helpers ────────────────────────────────────────────────────────────

def _make_jpeg_bytes() -> bytes:
    img = np.full((100, 100, 3), 128, dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    return bytes(buf)


def _make_png_bytes() -> bytes:
    img = np.full((100, 100, 3), 128, dtype=np.uint8)
    _, buf = cv2.imencode(".png", img)
    return bytes(buf)


def _make_pdf_bytes() -> bytes:
    import fitz
    doc = fitz.open()
    doc.new_page(width=100, height=100)
    data = doc.tobytes()
    doc.close()
    return data


# ── mock helpers ───────────────────────────────────────────────────────

def _patch_heavy_signals():
    """Return a context manager that mocks TruFor and OCR to avoid loading
    heavy models during endpoint tests."""
    trufor_mock = patch(
        "app.api.analyze.run_trufor",
        return_value={
            "integrity_score": 0.1,
            "anomaly_heatmap_b64": "fakeb64==",
            "reliability_map_b64": "fakeb64==",
        },
    )
    ocr_mock = patch(
        "app.api.analyze.check_ocr_consistency",
        return_value={
            "ocr_anomaly_score": 0.0,
            "total_boxes": 0,
            "outlier_boxes": 0,
            "outliers": [],
            "spacing_stats": {},
            "baseline_stats": {},
        },
    )

    class _Combined:
        def __enter__(self):
            self._t = trufor_mock.__enter__()
            self._o = ocr_mock.__enter__()
            return self

        def __exit__(self, *args):
            self._o.__exit__(*args)
            self._t.__exit__(*args)

    return _Combined()


# ── tests ──────────────────────────────────────────────────────────────

class TestHealthz:
    def test_healthz(self) -> None:
        resp = client.get("/healthz")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert "version" in body


class TestAnalyzeEndpoint:
    def test_jpeg_upload(self) -> None:
        with _patch_heavy_signals():
            resp = client.post(
                "/api/analyze",
                files={"file": ("test.jpg", _make_jpeg_bytes(), "image/jpeg")},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["filename"] == "test.jpg"
        assert body["total_pages"] == 1
        assert len(body["pages"]) == 1

        page = body["pages"][0]
        assert page["page_number"] == 1
        assert page["verdict"] in ("Authentic", "Uncertain", "Likely Tampered")
        assert 0.0 <= page["fused_score"] <= 1.0
        assert 0.0 <= page["confidence_pct"] <= 100.0
        assert len(page["signals"]) == 5

    def test_png_upload(self) -> None:
        with _patch_heavy_signals():
            resp = client.post(
                "/api/analyze",
                files={"file": ("test.png", _make_png_bytes(), "image/png")},
            )
        assert resp.status_code == 200
        assert resp.json()["total_pages"] == 1

    def test_pdf_upload(self) -> None:
        with _patch_heavy_signals():
            resp = client.post(
                "/api/analyze",
                files={"file": ("doc.pdf", _make_pdf_bytes(), "application/pdf")},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_pages"] >= 1

    def test_unsupported_type_rejected(self) -> None:
        resp = client.post(
            "/api/analyze",
            files={"file": ("test.txt", b"hello", "text/plain")},
        )
        assert resp.status_code == 415

    def test_empty_file_rejected(self) -> None:
        resp = client.post(
            "/api/analyze",
            files={"file": ("empty.jpg", b"", "image/jpeg")},
        )
        assert resp.status_code == 400

    def test_corrupt_image_rejected(self) -> None:
        resp = client.post(
            "/api/analyze",
            files={"file": ("bad.jpg", b"not-an-image", "image/jpeg")},
        )
        assert resp.status_code == 400

    def test_signal_breakdown_structure(self) -> None:
        with _patch_heavy_signals():
            resp = client.post(
                "/api/analyze",
                files={"file": ("test.jpg", _make_jpeg_bytes(), "image/jpeg")},
            )
        signals = resp.json()["pages"][0]["signals"]
        names = {s["name"] for s in signals}
        assert names == {"trufor", "ela", "copy_move", "exif", "ocr"}
        for s in signals:
            assert 0.0 <= s["score"] <= 1.0
            assert isinstance(s["details"], dict)

"""Tests for backend.app.forensics.ocr_consistency – OCR consistency."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.forensics.ocr_consistency import check_ocr_consistency


class TestCheckOcrConsistency:
    """Unit tests for the ``check_ocr_consistency`` pure function."""

    def test_return_keys_blank_image(self) -> None:
        """A blank white image should produce zero boxes (PaddleOCR finds
        nothing).  We mock PaddleOCR to avoid the heavyweight import."""
        mock_ocr_instance = MagicMock()
        mock_ocr_instance.ocr.return_value = [None]

        with patch(
            "app.forensics.ocr_consistency.PaddleOCR",
            return_value=mock_ocr_instance,
        ):
            result = check_ocr_consistency(
                np.full((200, 200, 3), 255, dtype=np.uint8)
            )

        assert result["total_boxes"] == 0
        assert result["ocr_anomaly_score"] == 0.0

    def test_uniform_text_low_anomaly(self) -> None:
        """Consistent bounding boxes should NOT be flagged as outliers."""
        # Simulate 5 uniform text boxes — all similar spacing & baseline.
        detections = []
        for i in range(5):
            y = 50 + i * 30
            bbox = [[10, y], [200, y], [200, y + 20], [10, y + 20]]
            text = "Hello World"
            detections.append((bbox, (text, 0.95)))

        mock_ocr = MagicMock()
        mock_ocr.ocr.return_value = [detections]

        with patch(
            "app.forensics.ocr_consistency.PaddleOCR",
            return_value=mock_ocr,
        ):
            result = check_ocr_consistency(
                np.full((300, 300, 3), 255, dtype=np.uint8)
            )

        assert result["total_boxes"] == 5
        assert result["ocr_anomaly_score"] == 0.0
        assert result["outlier_boxes"] == 0

    def test_one_outlier_flagged(self) -> None:
        """Inject one box with wildly different spacing → should be flagged."""
        detections = []
        # 4 normal boxes
        for i in range(4):
            y = 50 + i * 30
            bbox = [[10, y], [200, y], [200, y + 20], [10, y + 20]]
            detections.append((bbox, ("Normal text here", 0.90)))

        # 1 anomalous box — very narrow with long text → tiny spacing
        bbox_outlier = [[10, 300], [30, 300], [30, 320], [10, 320]]
        detections.append((bbox_outlier, ("This is way too much text", 0.80)))

        mock_ocr = MagicMock()
        mock_ocr.ocr.return_value = [detections]

        with patch(
            "app.forensics.ocr_consistency.PaddleOCR",
            return_value=mock_ocr,
        ):
            result = check_ocr_consistency(
                np.full((400, 400, 3), 255, dtype=np.uint8)
            )

        assert result["total_boxes"] == 5
        assert result["outlier_boxes"] >= 1
        assert result["ocr_anomaly_score"] > 0.0

        # Verify the outlier record has the expected structure.
        for outlier in result["outliers"]:
            assert "text" in outlier
            assert "flags" in outlier
            assert len(outlier["flags"]) > 0

    def test_none_image(self) -> None:
        result = check_ocr_consistency(None)  # type: ignore[arg-type]
        assert result["ocr_anomaly_score"] == 0.0
        assert result["total_boxes"] == 0

    def test_empty_image(self) -> None:
        result = check_ocr_consistency(np.array([]))
        assert result["ocr_anomaly_score"] == 0.0

    def test_stats_populated(self) -> None:
        """When enough boxes exist, spacing/baseline stats should be populated."""
        detections = []
        for i in range(5):
            y = 50 + i * 30
            bbox = [[10, y], [200, y], [200, y + 20], [10, y + 20]]
            detections.append((bbox, ("sample text", 0.90)))

        mock_ocr = MagicMock()
        mock_ocr.ocr.return_value = [detections]

        with patch(
            "app.forensics.ocr_consistency.PaddleOCR",
            return_value=mock_ocr,
        ):
            result = check_ocr_consistency(
                np.full((300, 300, 3), 255, dtype=np.uint8)
            )

        for stat_key in ("spacing_stats", "baseline_stats"):
            stats = result[stat_key]
            assert "mean" in stats
            assert "std" in stats
            assert "q1" in stats
            assert "q3" in stats

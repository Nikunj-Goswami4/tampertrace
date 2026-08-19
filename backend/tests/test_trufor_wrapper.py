"""Tests for backend.app.forensics.trufor_wrapper – TruFor model wrapper."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import torch

from app.forensics.trufor_wrapper import run_trufor, _WEIGHTS_PATH

_WEIGHTS_EXIST = _WEIGHTS_PATH.is_file()


class TestRunTruforMocked:
    """Tests that mock the model to avoid needing the 280 MB weight file."""

    def _make_mock_output(self, h: int = 200, w: int = 200):
        """Return (pred, conf, det, npp) tensors matching TruFor's output
        shapes."""
        pred = torch.randn(1, 2, h, w)
        conf = torch.randn(1, 1, h, w)
        det = torch.tensor([[0.8]])
        npp = torch.randn(1, 1, h, w)
        return pred, conf, det, npp

    @patch("app.forensics.trufor_wrapper._load_model")
    def test_return_keys(self, mock_load: MagicMock) -> None:
        mock_model = MagicMock()
        mock_model.return_value = self._make_mock_output()
        mock_load.return_value = mock_model

        img = np.full((200, 200, 3), 128, dtype=np.uint8)
        # Temporarily pretend weights exist
        with patch("app.forensics.trufor_wrapper._WEIGHTS_PATH") as mock_path:
            mock_path.is_file.return_value = True
            result = run_trufor(img)

        assert "integrity_score" in result
        assert "anomaly_heatmap_b64" in result
        assert "reliability_map_b64" in result

    @patch("app.forensics.trufor_wrapper._load_model")
    def test_integrity_score_range(self, mock_load: MagicMock) -> None:
        mock_model = MagicMock()
        mock_model.return_value = self._make_mock_output()
        mock_load.return_value = mock_model

        img = np.full((200, 200, 3), 128, dtype=np.uint8)
        with patch("app.forensics.trufor_wrapper._WEIGHTS_PATH") as mock_path:
            mock_path.is_file.return_value = True
            result = run_trufor(img)

        assert 0.0 <= result["integrity_score"] <= 1.0

    def test_missing_weights_returns_error(self) -> None:
        with patch("app.forensics.trufor_wrapper._WEIGHTS_PATH") as mock_path:
            mock_path.is_file.return_value = False
            result = run_trufor(np.full((100, 100, 3), 128, dtype=np.uint8))
        assert "error" in result

    def test_none_image_returns_error(self) -> None:
        result = run_trufor(None)  # type: ignore[arg-type]
        assert "error" in result

    def test_empty_image_returns_error(self) -> None:
        result = run_trufor(np.array([]))
        assert "error" in result


_HAS_TIMM = True
try:
    import timm  # noqa: F401
except ImportError:
    _HAS_TIMM = False


@pytest.mark.skipif(
    not _WEIGHTS_EXIST or not _HAS_TIMM,
    reason="TruFor weights not found or timm not installed",
)
class TestRunTruforIntegration:
    """Integration tests that load the real model.  Skipped in CI when
    weights are absent."""

    def test_real_inference(self) -> None:
        img = np.full((256, 256, 3), 128, dtype=np.uint8)
        result = run_trufor(img, device="cpu")
        assert "integrity_score" in result
        assert 0.0 <= result["integrity_score"] <= 1.0
        assert result["anomaly_heatmap_b64"]  # non-empty string
        assert result["reliability_map_b64"]

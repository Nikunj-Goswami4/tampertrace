"""Tests for backend.app.forensics.fusion – weighted ensemble scoring."""

from unittest.mock import patch, PropertyMock

import pytest

from app.forensics.fusion import fuse_signals, _verdict_confidence


class TestFuseSignals:
    """Unit tests for the ``fuse_signals`` pure function."""

    def test_return_keys(self) -> None:
        result = fuse_signals()
        for key in ("fused_score", "verdict", "confidence_pct", "weights_used"):
            assert key in result

    def test_all_zero_is_authentic(self) -> None:
        result = fuse_signals(0.0, 0.0, 0.0, 0.0)
        assert result["fused_score"] == 0.0
        assert result["verdict"] == "Authentic"

    def test_all_one_is_tampered(self) -> None:
        result = fuse_signals(1.0, 1.0, 1.0, 1.0)
        assert result["fused_score"] == 1.0
        assert result["verdict"] == "Likely Tampered"

    def test_mid_range_is_uncertain(self) -> None:
        # 0.5 * 0.5 + 0.25 * 0.5 + 0.15 * 0.5 + 0.10 * 0.5 = 0.5
        result = fuse_signals(0.5, 0.5, 0.5, 0.5)
        assert result["verdict"] == "Uncertain"

    def test_score_clamped_to_unit(self) -> None:
        result = fuse_signals(2.0, 2.0, 2.0, 2.0)
        assert result["fused_score"] <= 1.0

    def test_weights_used_returned(self) -> None:
        result = fuse_signals()
        w = result["weights_used"]
        assert "trufor" in w
        assert "ela" in w
        assert abs(sum(w.values()) - 1.0) < 1e-9

    def test_custom_config_weights(self) -> None:
        """Verify that custom weights from calibrated_config are respected."""
        custom_cfg = {
            "weights": {"trufor": 0.0, "ela": 1.0, "copy_move": 0.0, "ocr_exif": 0.0},
            "thresholds": {"authentic_below": 0.3, "tampered_above": 0.65},
        }
        with patch(
            "app.forensics.fusion.settings"
        ) as mock_settings:
            type(mock_settings).calibrated_config = PropertyMock(return_value=custom_cfg)
            result = fuse_signals(trufor_score=1.0, ela_score=0.0)
        # Only ELA weight = 1.0 and ela_score = 0.0 → fused = 0.0
        assert result["fused_score"] == 0.0

    def test_confidence_range(self) -> None:
        for scores in [(0.0,) * 4, (1.0,) * 4, (0.5,) * 4]:
            result = fuse_signals(*scores)
            assert 0.0 <= result["confidence_pct"] <= 100.0


class TestVerdictConfidence:
    """Unit tests for the internal ``_verdict_confidence`` helper."""

    def test_zero_score(self) -> None:
        verdict, conf = _verdict_confidence(0.0, 0.3, 0.65)
        assert verdict == "Authentic"
        assert conf == 100.0

    def test_one_score(self) -> None:
        verdict, conf = _verdict_confidence(1.0, 0.3, 0.65)
        assert verdict == "Likely Tampered"
        assert conf == 100.0

    def test_boundary_low(self) -> None:
        verdict, _ = _verdict_confidence(0.3, 0.3, 0.65)
        assert verdict == "Authentic"

    def test_boundary_high(self) -> None:
        verdict, _ = _verdict_confidence(0.65, 0.3, 0.65)
        assert verdict == "Likely Tampered"

    def test_uncertain_midpoint(self) -> None:
        verdict, conf = _verdict_confidence(0.475, 0.3, 0.65)
        assert verdict == "Uncertain"
        assert conf <= 50.0  # capped

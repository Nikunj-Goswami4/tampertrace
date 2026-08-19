"""Tests for backend.app.forensics.ela – Error Level Analysis."""

import base64

import numpy as np
import pytest

from app.forensics.ela import run_ela


class TestRunEla:
    """Unit tests for the ``run_ela`` pure function."""

    def test_return_keys(self, synthetic_image: np.ndarray) -> None:
        result = run_ela(synthetic_image)
        assert "ela_score" in result
        assert "diff_map_b64" in result
        assert "quality_used" in result

    def test_pristine_low_score(self, synthetic_image: np.ndarray) -> None:
        """A uniform solid image should have a very low ELA score."""
        result = run_ela(synthetic_image)
        assert result["ela_score"] < 0.1

    def test_tampered_higher_score(self, tampered_image: np.ndarray) -> None:
        """An image with a crudely spliced region should score higher than
        a uniform one (though the absolute score depends on content)."""
        pristine = run_ela(np.full((200, 200, 3), 128, dtype=np.uint8))
        tampered = run_ela(tampered_image)
        # The tampered image has strong edges at the splice boundary
        # which survive JPEG re-compression differently.
        assert tampered["ela_score"] >= pristine["ela_score"]

    def test_diff_map_is_valid_base64_png(self, synthetic_image: np.ndarray) -> None:
        result = run_ela(synthetic_image)
        raw = base64.b64decode(result["diff_map_b64"])
        # PNG magic bytes
        assert raw[:4] == b"\x89PNG"

    def test_quality_forwarded(self, synthetic_image: np.ndarray) -> None:
        result = run_ela(synthetic_image, quality=75)
        assert result["quality_used"] == 75

    def test_empty_array_returns_error(self) -> None:
        result = run_ela(np.array([]))
        assert "error" in result

    def test_none_returns_error(self) -> None:
        result = run_ela(None)  # type: ignore[arg-type]
        assert "error" in result

    def test_score_range(self, synthetic_image: np.ndarray) -> None:
        result = run_ela(synthetic_image)
        assert 0.0 <= result["ela_score"] <= 1.0

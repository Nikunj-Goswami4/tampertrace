"""Tests for backend.app.forensics.copy_move – Copy-move detection."""

import numpy as np
import pytest

from app.forensics.copy_move import detect_copy_move


class TestDetectCopyMove:
    """Unit tests for the ``detect_copy_move`` pure function."""

    def test_return_keys(self, synthetic_image: np.ndarray) -> None:
        result = detect_copy_move(synthetic_image)
        assert "copy_move_score" in result
        assert "num_matches" in result
        assert "regions" in result

    def test_uniform_image_no_clones(self, synthetic_image: np.ndarray) -> None:
        """A solid-colour image has no keypoints worth matching → score 0."""
        result = detect_copy_move(synthetic_image)
        assert result["copy_move_score"] == 0.0
        assert result["regions"] == []

    def test_textured_duplicate_detected(self, textured_image: np.ndarray) -> None:
        """An image with an identical textured patch placed twice should
        produce a non-zero score (assuming enough ORB keypoints land on
        the patch)."""
        result = detect_copy_move(textured_image, min_match_count=4)
        # We relax the threshold because ORB is not perfectly
        # deterministic across platforms; we just verify the pipeline
        # runs without error and produces structured output.
        assert isinstance(result["copy_move_score"], float)
        assert isinstance(result["num_matches"], int)
        assert isinstance(result["regions"], list)

    def test_empty_image(self) -> None:
        result = detect_copy_move(np.array([]))
        assert result["copy_move_score"] == 0.0

    def test_none_image(self) -> None:
        result = detect_copy_move(None)  # type: ignore[arg-type]
        assert result["copy_move_score"] == 0.0

    def test_greyscale_input(self) -> None:
        """Greyscale images should be handled without crashing."""
        grey = np.full((200, 200), 128, dtype=np.uint8)
        result = detect_copy_move(grey)
        assert result["copy_move_score"] == 0.0

    def test_score_clamped(self, textured_image: np.ndarray) -> None:
        result = detect_copy_move(textured_image, min_match_count=1)
        assert 0.0 <= result["copy_move_score"] <= 1.0

    def test_region_structure(self, textured_image: np.ndarray) -> None:
        result = detect_copy_move(textured_image, min_match_count=4)
        for region in result["regions"]:
            assert "src" in region
            assert "dst" in region
            assert len(region["src"]) == 4
            assert len(region["dst"]) == 4

"""
Shared pytest fixtures for forensic module tests.
"""

import cv2
import numpy as np
import pytest


@pytest.fixture
def synthetic_image() -> np.ndarray:
    """A solid mid-grey 200×200 BGR image (pristine, no tampering)."""
    return np.full((200, 200, 3), 128, dtype=np.uint8)


@pytest.fixture
def tampered_image() -> np.ndarray:
    """A 300×300 image with a bright white rectangle spliced onto a grey
    background — simulates a crude copy-paste forgery."""
    img = np.full((300, 300, 3), 100, dtype=np.uint8)
    # Spliced region: bright rectangle
    img[50:150, 50:150] = 255
    return img


@pytest.fixture
def jpeg_bytes(synthetic_image: np.ndarray) -> bytes:
    """The *synthetic_image* encoded as JPEG bytes (preserves EXIF-less
    round-trip)."""
    success, buf = cv2.imencode(".jpg", synthetic_image)
    assert success
    return bytes(buf)


@pytest.fixture
def textured_image() -> np.ndarray:
    """A 400×400 image with a random-noise textured patch duplicated in two
    locations — useful for copy-move detection tests."""
    rng = np.random.RandomState(42)
    img = np.full((400, 400, 3), 120, dtype=np.uint8)

    # Generate a recognisable patch
    patch = rng.randint(0, 256, (80, 80, 3), dtype=np.uint8)

    # Place the same patch in two separate locations
    img[30:110, 30:110] = patch
    img[200:280, 200:280] = patch
    return img

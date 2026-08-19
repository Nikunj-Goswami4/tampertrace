"""Tests for backend.app.forensics.exif_check – EXIF metadata inspection."""

from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from app.forensics.exif_check import check_exif


def _make_jpeg_bytes_no_exif() -> bytes:
    """Create a minimal JPEG with no EXIF metadata."""
    img = Image.new("RGB", (10, 10), color="red")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_jpeg_with_exif(software: str = "", exif_dict: dict | None = None) -> bytes:
    """Create a JPEG with controlled EXIF tags via *piexif*.

    Falls back to a bare JPEG if piexif is not installed.
    """
    try:
        import piexif
    except ImportError:
        pytest.skip("piexif not installed – skipping EXIF-injection test")

    exif_ifd = {}
    zeroth_ifd = {}

    if software:
        zeroth_ifd[piexif.ImageIFD.Software] = software.encode()

    if exif_dict:
        for key, val in exif_dict.items():
            exif_ifd[key] = val.encode() if isinstance(val, str) else val

    exif_bytes = piexif.dump({"0th": zeroth_ifd, "Exif": exif_ifd})

    img = Image.new("RGB", (10, 10), color="blue")
    buf = BytesIO()
    img.save(buf, format="JPEG", exif=exif_bytes)
    return buf.getvalue()


class TestCheckExif:
    """Unit tests for the ``check_exif`` pure function."""

    def test_return_keys_no_exif(self) -> None:
        result = check_exif(_make_jpeg_bytes_no_exif())
        for key in (
            "has_exif",
            "software",
            "software_is_editor",
            "timestamps",
            "timestamp_discrepancy",
            "all_tags",
        ):
            assert key in result

    def test_no_exif_flags(self) -> None:
        result = check_exif(_make_jpeg_bytes_no_exif())
        assert result["has_exif"] is False
        assert result["software"] is None
        assert result["software_is_editor"] is False

    def test_photoshop_detected(self) -> None:
        data = _make_jpeg_with_exif(software="Adobe Photoshop CC 2023")
        result = check_exif(data)
        assert result["software_is_editor"] is True
        assert "Photoshop" in (result["software"] or "")

    def test_gimp_detected(self) -> None:
        data = _make_jpeg_with_exif(software="GIMP 2.10")
        result = check_exif(data)
        assert result["software_is_editor"] is True

    def test_camera_firmware_not_flagged(self) -> None:
        data = _make_jpeg_with_exif(software="NIKON D850 Ver.1.10")
        result = check_exif(data)
        assert result["software_is_editor"] is False

    def test_timestamp_discrepancy(self) -> None:
        try:
            import piexif
        except ImportError:
            pytest.skip("piexif not installed")

        data = _make_jpeg_with_exif(
            exif_dict={
                piexif.ExifIFD.DateTimeOriginal: "2024:01:15 10:30:00",
                piexif.ExifIFD.DateTimeDigitized: "2025:06:01 08:00:00",
            }
        )
        result = check_exif(data)
        assert result["timestamp_discrepancy"] is True

    def test_matching_timestamps_no_discrepancy(self) -> None:
        try:
            import piexif
        except ImportError:
            pytest.skip("piexif not installed")

        data = _make_jpeg_with_exif(
            exif_dict={
                piexif.ExifIFD.DateTimeOriginal: "2024:01:15 10:30:00",
                piexif.ExifIFD.DateTimeDigitized: "2024:01:15 10:30:00",
            }
        )
        result = check_exif(data)
        assert result["timestamp_discrepancy"] is False

    def test_corrupt_bytes(self) -> None:
        result = check_exif(b"not-an-image")
        assert result["has_exif"] is False
        assert result["all_tags"] == {}

    def test_png_bytes_handled(self) -> None:
        """PNG files don't carry EXIF in the same way — should not crash."""
        img = Image.new("RGB", (10, 10))
        buf = BytesIO()
        img.save(buf, format="PNG")
        result = check_exif(buf.getvalue())
        assert isinstance(result["has_exif"], bool)

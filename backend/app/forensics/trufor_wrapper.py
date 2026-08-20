"""
TruFor model wrapper.

Wraps the pretrained TruFor model (GRIP-UNINA) to produce a pixel-level
anomaly heatmap, an integrity score, and a reliability (confidence) map.

The model is lazily loaded on first call and cached at module level to
avoid repeated 280 MB checkpoint loads.

Pure function interface: np.ndarray in → structured dict out.
"""

from __future__ import annotations

import base64
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import cv2
import numpy as np
import torch
import torchvision
from torch.nn import functional as F

import spaces

logger = logging.getLogger(__name__)

# ── paths ──────────────────────────────────────────────────────────────
_THIS_DIR = Path(__file__).resolve().parent              # forensics/
_APP_DIR = _THIS_DIR.parent                              # app/
_TRUFOR_LIB = _APP_DIR / "trufor_lib"                    # app/trufor_lib/
_PROJECT_ROOT = _APP_DIR.parent.parent                   # tampertrace/
_WEIGHTS_PATH = _PROJECT_ROOT / "models" / "trufor" / "weights" / "trufor.pth.tar"
_YAML_PATH = _TRUFOR_LIB / "trufor.yaml"

# ── module-level model cache ──────────────────────────────────────────
_model_cache: Optional[torch.nn.Module] = None
_model_device: Optional[str] = None


def _load_model(device: str) -> torch.nn.Module:
    """Load and cache the TruFor model."""
    global _model_cache, _model_device

    if _model_cache is not None and _model_device == device:
        return _model_cache

    # The vendored trufor_lib uses bare imports (``from config import …``,
    # ``from models.DnCNN import …``).  We temporarily prepend its
    # directory to sys.path so those imports resolve without modifying
    # the upstream code.
    trufor_str = str(_TRUFOR_LIB)
    path_added = False
    if trufor_str not in sys.path:
        sys.path.insert(0, trufor_str)
        path_added = True

    try:
        from config import _C as cfg  # type: ignore[import-untyped]

        cfg.defrost()
        cfg.merge_from_file(str(_YAML_PATH))
        # Override weights path to an absolute location
        cfg.TEST.MODEL_FILE = str(_WEIGHTS_PATH)
        cfg.freeze()

        from models.cmx.builder_np_conf import myEncoderDecoder as ConfCMX  # type: ignore[import-untyped]

        model = ConfCMX(cfg=cfg)

        checkpoint = torch.load(str(_WEIGHTS_PATH), map_location=torch.device(device), weights_only=False)
        model.load_state_dict(checkpoint["state_dict"])
        model = model.to(device)
        model.eval()

        _model_cache = model
        _model_device = device
        logger.info("TruFor model loaded on %s", device)
        return model
    finally:
        if path_added:
            sys.path.remove(trufor_str)


def _ndarray_to_b64_png(arr: np.ndarray) -> str:
    """Encode a single-channel float map [0, 1] to a base64 PNG string."""
    vis = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
    # Apply a colour-map so the heatmap is easy to interpret visually
    coloured = cv2.applyColorMap(vis, cv2.COLORMAP_JET)
    _, buf = cv2.imencode(".png", coloured)
    return base64.b64encode(buf).decode("ascii")


@spaces.GPU
def run_trufor(
    image: np.ndarray,
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
    # device: str = "cpu",
) -> Dict[str, Any]:
    """Run TruFor inference on *image*.

    Parameters
    ----------
    image : np.ndarray
        BGR image (OpenCV convention).
    device : str
        ``"cpu"`` or ``"cuda:N"``.

    Returns
    -------
    dict
        ``integrity_score``      – float in [0, 1]; 1 = likely tampered.
        ``anomaly_heatmap_b64``  – base64 PNG of the pixel anomaly map.
        ``reliability_map_b64`` – base64 PNG of the confidence map.
    """
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        return {"error": "Invalid or empty image array."}

    if not _WEIGHTS_PATH.is_file():
        return {"error": f"TruFor weights not found at {_WEIGHTS_PATH}"}

    # ── prepare tensor (same as data_core.myDataset) ───────────────────
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Scale down if too large to avoid OOM on GPUs with limited memory
    orig_h, orig_w = rgb.shape[:2]
    max_size = 768
    if max(orig_h, orig_w) > max_size:
        scale = max_size / max(orig_h, orig_w)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        # Ensure dimensions are multiples of 32
        new_w = max(32, (new_w // 32) * 32)
        new_h = max(32, (new_h // 32) * 32)
        rgb = cv2.resize(rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)

    tensor = (
        torch.tensor(rgb.transpose(2, 0, 1), dtype=torch.float32)
        .unsqueeze(0)
        / 256.0
    )
    tensor = tensor.to(device)

    # ── inference ──────────────────────────────────────────────────────
    model = _load_model(device)
    with torch.no_grad():
        pred, conf, det, _npp = model(tensor)

    # ── post-process: anomaly heatmap ──────────────────────────────────
    pred = torch.squeeze(pred, 0)
    heatmap = F.softmax(pred, dim=0)[1].cpu().numpy()
    if heatmap.shape != (orig_h, orig_w):
        heatmap = cv2.resize(heatmap, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)

    # ── post-process: reliability map ──────────────────────────────────
    reliability: Optional[np.ndarray] = None
    if conf is not None:
        conf = torch.squeeze(conf, 0)
        reliability = torch.sigmoid(conf)[0].cpu().numpy()
        if reliability.shape != (orig_h, orig_w):
            reliability = cv2.resize(reliability, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)

    # ── post-process: integrity score ──────────────────────────────────
    integrity_score = 0.0
    if det is not None:
        integrity_score = float(torch.sigmoid(det).item())

    # ── encode visual outputs ──────────────────────────────────────────
    heatmap_b64 = _ndarray_to_b64_png(heatmap)
    reliability_b64 = (
        _ndarray_to_b64_png(reliability) if reliability is not None else ""
    )

    return {
        "integrity_score": integrity_score,
        "anomaly_heatmap_b64": heatmap_b64,
        "reliability_map_b64": reliability_b64,
    }

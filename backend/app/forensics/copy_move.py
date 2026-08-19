"""
Copy-move (clone) forgery detection.

Uses ORB keypoint extraction + BFMatcher + RANSAC spatial verification to
locate duplicated regions within a single image.

Pure function: np.ndarray in → structured dict out.
"""

from __future__ import annotations

from typing import Dict, Any, List

import cv2
import numpy as np


def _bounding_rect(pts: np.ndarray) -> List[int]:
    """Return ``[x, y, w, h]`` for a set of 2-D points."""
    x, y, w, h = cv2.boundingRect(pts.reshape(-1, 1, 2).astype(np.float32))
    return [int(x), int(y), int(w), int(h)]


def detect_copy_move(
    image: np.ndarray,
    min_match_count: int = 10,
    ransac_thresh: float = 5.0,
    max_keypoints: int = 5000,
    ratio_thresh: float = 0.75,
    identity_dist: float = 10.0,
) -> Dict[str, Any]:
    """Detect copy-move forgery via ORB self-matching.

    Parameters
    ----------
    image : np.ndarray
        BGR image (OpenCV convention).
    min_match_count : int
        Minimum RANSAC inliers to consider the match significant.
    ransac_thresh : float
        RANSAC reprojection threshold in pixels.
    max_keypoints : int
        Maximum number of ORB keypoints to extract.
    ratio_thresh : float
        Lowe's ratio test threshold.
    identity_dist : float
        Keypoint pairs closer than this (in pixels) are treated as
        identity matches and discarded.

    Returns
    -------
    dict
        ``copy_move_score`` – float in [0, 1]; 0 = no clones, 1 = strong
        evidence.
        ``num_matches`` – inlier count after RANSAC.
        ``regions`` – list of ``{"src": [x,y,w,h], "dst": [x,y,w,h]}``.
    """
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        return {"copy_move_score": 0.0, "num_matches": 0, "regions": []}

    # ── greyscale ──────────────────────────────────────────────────────
    if image.ndim == 3:
        grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        grey = image

    # ── ORB keypoints ──────────────────────────────────────────────────
    orb = cv2.ORB_create(nfeatures=max_keypoints)
    kps, descs = orb.detectAndCompute(grey, None)

    if descs is None or len(kps) < 2:
        return {"copy_move_score": 0.0, "num_matches": 0, "regions": []}

    # ── self-matching (kNN, k=2) ───────────────────────────────────────
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    raw_matches = bf.knnMatch(descs, descs, k=2)

    # Lowe's ratio test  +  discard identity matches
    good: list = []
    for m, n in raw_matches:
        if m.distance < ratio_thresh * n.distance:
            pt_q = np.array(kps[m.queryIdx].pt)
            pt_t = np.array(kps[m.trainIdx].pt)
            spatial_dist = np.linalg.norm(pt_q - pt_t)
            if spatial_dist > identity_dist:
                good.append(m)

    if len(good) < min_match_count:
        return {
            "copy_move_score": 0.0,
            "num_matches": len(good),
            "regions": [],
        }

    # ── RANSAC spatial verification ────────────────────────────────────
    src_pts = np.float32([kps[m.queryIdx].pt for m in good])
    dst_pts = np.float32([kps[m.trainIdx].pt for m in good])

    _, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, ransac_thresh)

    if mask is None:
        return {
            "copy_move_score": 0.0,
            "num_matches": 0,
            "regions": [],
        }

    inlier_mask = mask.ravel().astype(bool)
    inlier_count = int(inlier_mask.sum())

    # ── bounding regions ───────────────────────────────────────────────
    regions: List[Dict[str, List[int]]] = []
    if inlier_count >= min_match_count:
        src_inliers = src_pts[inlier_mask]
        dst_inliers = dst_pts[inlier_mask]
        regions.append(
            {
                "src": _bounding_rect(src_inliers),
                "dst": _bounding_rect(dst_inliers),
            }
        )

    score = min(1.0, inlier_count / min_match_count)

    return {
        "copy_move_score": float(score),
        "num_matches": inlier_count,
        "regions": regions,
    }

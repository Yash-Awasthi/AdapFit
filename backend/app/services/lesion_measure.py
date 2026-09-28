"""
Measures a skin spot in a photo with classical image processing (OpenCV).

Segments the darker region nearest the centre, then measures asymmetry about
its principal axes, border compactness, colour spread in CIELAB and, when the
photo includes a coin or sticker of known size, the diameter in millimetres.
The photo is not stored.

The 0-1 feature scales put the screening cutoff at 0.5 for asymmetry and border
and 0.4 for colour. Those cutoffs are unvalidated screening choices; what a phone
photo measures reliably is change between photos of the same spot.
"""
from typing import Optional

import cv2
import numpy as np

MAX_SIDE = 900
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
# Width of the spot's edge in pixels at MAX_SIDE; wider means out of focus.
MAX_EDGE_WIDTH_PX = 9.0

# Coins of the 2019 series; older coins differ, so the user confirms which one.
COINS_MM = {"1_rupee": 20.0, "2_rupee": 23.0, "5_rupee": 25.0, "10_rupee": 27.0}


def _decode(data: bytes) -> Optional[np.ndarray]:
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None
    scale = MAX_SIDE / max(img.shape[:2])
    return cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else img


def _find_reference(gray: np.ndarray) -> Optional[tuple[int, int, int]]:
    h, w = gray.shape
    circles = cv2.HoughCircles(cv2.medianBlur(gray, 5), cv2.HOUGH_GRADIENT, dp=1.2, minDist=min(h, w) // 4,
                               param1=100, param2=40, minRadius=min(h, w) // 20, maxRadius=min(h, w) // 3)
    if circles is None:
        return None
    x, y, r = max(np.round(circles[0]).astype(int), key=lambda c: c[2])
    return int(x), int(y), int(r)


def _segment(img: np.ndarray, exclude: Optional[tuple[int, int, int]]) -> Optional[np.ndarray]:
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L = cv2.GaussianBlur(lab[:, :, 0], (7, 7), 0)
    _, mask = cv2.threshold(L, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    if exclude:
        cv2.circle(mask, exclude[:2], int(exclude[2] * 1.15), 0, -1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel), cv2.MORPH_CLOSE, kernel)

    n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
    h, w = mask.shape
    centre = np.array([w / 2, h / 2])
    best, best_d = None, None
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area < 150 or area > 0.6 * h * w:
            continue
        if x == 0 or y == 0 or x + bw >= w or y + bh >= h:
            continue
        d = np.linalg.norm(centroids[i] - centre)
        if best_d is None or d < best_d:
            best, best_d = i, d
    if best is None:
        return None
    region = (labels == best).astype(np.uint8) * 255
    contours, _ = cv2.findContours(region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    filled = np.zeros_like(region)
    cv2.drawContours(filled, contours, -1, 255, -1)
    return filled


def _asymmetry(mask: np.ndarray) -> float:
    """Worse non-overlap of the two principal-axis flips, as a fraction of area; ABCDE asks whether either half differs."""
    m = cv2.moments(mask, binaryImage=True)
    cx, cy = m["m10"] / m["m00"], m["m01"] / m["m00"]
    angle = 0.5 * np.degrees(np.arctan2(2 * m["mu11"], m["mu20"] - m["mu02"]))
    h, w = mask.shape
    side = int(np.hypot(h, w))
    rot = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)
    rot[0, 2] += side / 2 - cx
    rot[1, 2] += side / 2 - cy
    aligned = cv2.warpAffine(mask, rot, (side, side), flags=cv2.INTER_NEAREST) > 0
    area = aligned.sum()
    ratios = [np.logical_xor(aligned, np.flip(aligned, axis)).sum() / 2 / area for axis in (0, 1)]
    return float(max(ratios))


def _edge_width(img: np.ndarray, mask: np.ndarray, contour: np.ndarray) -> float:
    """Contrast across the edge divided by the steepest gradient on it: a step blurred over n pixels gives n."""
    L = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    ring = cv2.dilate(mask, kernel) - mask
    core = cv2.erode(mask, kernel)
    if not core.any() or not ring.any():
        return float("inf")
    contrast = abs(float(np.median(L[ring > 0])) - float(np.median(L[core > 0])))
    gy, gx = np.gradient(cv2.GaussianBlur(L, (3, 3), 0))
    grad = cv2.dilate(np.hypot(gx, gy), np.ones((5, 5), np.uint8))
    pts = contour[:, 0, :]
    peak = float(np.median(grad[pts[:, 1], pts[:, 0]]))
    return contrast / peak if peak > 0 else float("inf")


def measure(data: bytes, reference_mm: Optional[float] = None) -> dict:
    if len(data) > MAX_UPLOAD_BYTES:
        return {"status": "retake", "message": "That image is too large. Send a normal phone photo."}
    img = _decode(data)
    if img is None:
        return {"status": "retake", "message": "The image could not be read."}
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    ref = _find_reference(gray) if reference_mm else None
    if reference_mm and ref is None:
        return {"status": "retake", "message": "The coin was not found. Place it flat beside the spot, fully in the photo."}
    mask = _segment(img, ref)
    if mask is None:
        return {"status": "retake",
                "message": "No spot found. Centre it in the photo with clear skin all around and no shadow."}

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contour = max(contours, key=cv2.contourArea)
    edge_width = _edge_width(img, mask, contour)
    if edge_width > MAX_EDGE_WIDTH_PX:
        return {"status": "retake", "message": "The photo is blurry. Hold the phone steady about 10 cm away, in daylight."}
    area_px = float(cv2.contourArea(contour))
    perimeter = float(cv2.arcLength(contour, True))
    compactness = perimeter ** 2 / (4 * np.pi * area_px)
    asym = _asymmetry(mask)

    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
    inside = lab[mask > 0]
    colour_spread = float(np.sqrt(inside.var(axis=0).sum()))

    (_, _), (w_px, h_px), _ = cv2.minAreaRect(contour)
    diameter_mm = None
    if ref:
        mm_per_px = reference_mm / (2 * ref[2])
        diameter_mm = round(max(w_px, h_px) * mm_per_px, 1)

    return {
        "status": "measured",
        "raw": {"asymmetry_index": round(asym, 3), "compactness": round(compactness, 2),
                "colour_spread_lab": round(colour_spread, 1), "area_px": int(area_px), "edge_width_px": round(edge_width, 1)},
        "features": {
            "asymmetry_score": round(min(1.0, asym / 0.2), 2),
            "border_irregularity": round(min(1.0, max(0.0, compactness - 1) / 0.6), 2),
            "color_variation": round(min(1.0, colour_spread / 40), 2),
            "diameter_mm": diameter_mm,
        },
        "scale": "coin" if ref else "none",
        "note": ("Diameter needs a coin in the photo." if not ref else
                 "Measured from the coin. Keep the phone parallel to the skin for an accurate size."),
    }

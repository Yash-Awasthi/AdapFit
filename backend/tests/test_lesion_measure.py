"""The photo measurement separates a round even spot from an irregular one, and sizes it from a coin."""
import cv2
import numpy as np

from app.services.lesion_measure import measure

SKIN = (150, 180, 220)


def _photo(draw, coin=False, seed=0):
    rng = np.random.default_rng(seed)
    img = np.full((600, 600, 3), SKIN, np.uint8)
    img = np.clip(img.astype(int) + rng.integers(-12, 12, img.shape), 0, 255).astype(np.uint8)
    draw(img)
    if coin:
        cv2.circle(img, (470, 470), 80, (190, 190, 190), -1)
        cv2.circle(img, (470, 470), 80, (120, 120, 120), 3)
    return cv2.imencode(".png", cv2.GaussianBlur(img, (3, 3), 0))[1].tobytes()


def _round(img):
    cv2.circle(img, (300, 300), 60, (40, 60, 90), -1)


def _irregular(img):
    pts = []
    for k in range(24):
        a = 2 * np.pi * k / 24
        r = 60 + (25 if k % 2 else -5) + (70 if 2 < k < 8 else 0)
        pts.append((300 + r * np.cos(a), 300 + r * np.sin(a)))
    cv2.fillPoly(img, [np.array(pts, np.int32)], (40, 60, 90))
    cv2.circle(img, (340, 340), 40, (20, 20, 160), -1)


def test_round_even_spot_scores_low():
    f = measure(_photo(_round))["features"]
    assert f["asymmetry_score"] < 0.5 and f["border_irregularity"] < 0.5 and f["color_variation"] < 0.4
    assert f["diameter_mm"] is None


def test_irregular_spot_scores_high():
    f = measure(_photo(_irregular))["features"]
    assert f["asymmetry_score"] >= 0.5 and f["border_irregularity"] >= 0.5 and f["color_variation"] >= 0.4


def test_coin_gives_diameter():
    out = measure(_photo(_round, coin=True), reference_mm=20.0)
    # 120 px spot beside a 160 px coin of 20 mm is 15 mm.
    assert abs(out["features"]["diameter_mm"] - 15.0) < 1.5


def test_blank_and_blurry_photos_ask_for_retake():
    assert measure(_photo(lambda img: None))["status"] == "retake"
    blurry = cv2.imencode(".png", cv2.GaussianBlur(cv2.imdecode(np.frombuffer(_photo(_round), np.uint8), 1), (41, 41), 0))[1].tobytes()
    assert measure(blurry)["status"] == "retake"
    assert measure(b"not an image")["status"] == "retake"

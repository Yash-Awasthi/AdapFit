"""NEWS2 home check: bands, the single-parameter red score, and plain next steps."""
from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)
NORMAL = {"respiratory_rate": 16, "oxygen_saturation": 98, "systolic_bp": 120, "pulse_rate": 70, "temperature": 36.8}


def test_normal_readings():
    r = c.post("/api/v1/vitals/check", json=NORMAL).json()
    assert r["score"] == 0 and r["band"] == "none"


def test_one_red_parameter_is_urgent_on_its_own():
    r = c.post("/api/v1/vitals/check", json={**NORMAL, "oxygen_saturation": 90}).json()
    assert r["score"] == 3 and r["band"] == "medium" and "doctor now" in r["next_step"]


def test_new_confusion_scores():
    r = c.post("/api/v1/vitals/check", json={**NORMAL, "new_confusion": True}).json()
    assert r["parameter_scores"]["consciousness"] == 3


def test_high_band_says_call_112():
    r = c.post("/api/v1/vitals/check", json={"respiratory_rate": 26, "oxygen_saturation": 90, "systolic_bp": 95,
                                                  "pulse_rate": 125, "temperature": 39.5}).json()
    assert r["band"] == "high" and "112" in r["next_step"]

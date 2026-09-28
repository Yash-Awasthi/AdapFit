"""One HRV API: trend from check-ins, analysis of a cleaned RR recording, biofeedback."""
import math

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _rr(n=300, base=900.0):
    # Respiratory sinus arrhythmia at 0.25 Hz gives a real HF component.
    rr, t = [], 0.0
    for _ in range(n):
        value = base + 40 * math.sin(2 * math.pi * 0.25 * t)
        rr.append(value)
        t += value / 1000
    return rr


def test_analysis_reports_all_domains():
    r = client.post("/api/v1/hrv/analyze", json={"rr_intervals_ms": _rr()})
    assert r.status_code == 200
    body = r.json()
    assert body["time_domain"]["rmssd"] > 0
    assert body["frequency_domain"] is not None
    assert body["artifacts"]["found"] == 0


def test_an_ectopic_beat_is_corrected_not_counted():
    rr = _rr()
    rr[150] = 450.0
    rr[151] = 1350.0
    body = client.post("/api/v1/hrv/analyze", json={"rr_intervals_ms": rr}).json()
    assert body["artifacts"]["found"] >= 1


def test_impossible_intervals_are_rejected():
    assert client.post("/api/v1/hrv/analyze", json={"rr_intervals_ms": [100.0] * 40}).status_code == 422


def test_four_seven_eight_is_four_seven_eight():
    p = client.get("/api/v1/hrv/breathing-pattern?goal=sleep").json()
    assert (p["inhale_seconds"], p["hold_in_seconds"], p["exhale_seconds"]) == (4.0, 7.0, 8.0)


def test_biofeedback_scores_a_session():
    beats, t = [], 0.0
    for rr in _rr(200):
        t += rr
        beats.append({"timestamp_ms": t, "rr_interval_ms": rr, "heart_rate": 60000 / rr})
    r = client.post("/api/v1/hrv/biofeedback", json={"pattern": "coherence", "beats": beats})
    assert r.status_code == 200 and "coherence_score" in r.json()


def test_trend_without_checkins_is_empty():
    assert client.get("/api/v1/hrv/trend").json()["data_points"] == []

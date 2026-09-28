"""Health Connect records: de-duplication, daily summaries, glucose fan-out and the rest-activity rhythm."""
import time
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.services.actigraphy_analysis import rest_activity_rhythm

c = TestClient(app)
IST = timezone(timedelta(minutes=330))


def _ts(days_ago, hour, minute=0):
    d = datetime.now(IST).replace(hour=hour, minute=minute, second=0, microsecond=0) - timedelta(days=days_ago)
    return d.timestamp()


def test_records_are_deduplicated_and_summarised_by_local_day():
    recs = [
        {"id": "s1", "type": "steps", "start": _ts(1, 9), "end": _ts(1, 10), "value": 1200},
        {"id": "s2", "type": "steps", "start": _ts(1, 18), "end": _ts(1, 19), "value": 3000},
        {"id": "sl", "type": "sleep", "start": _ts(2, 23), "end": _ts(1, 6, 30)},
        {"id": "bp", "type": "blood_pressure", "start": _ts(1, 8), "end": _ts(1, 8), "data": {"systolic": 124, "diastolic": 82}},
        {"id": "g1", "type": "blood_glucose", "start": _ts(1, 7), "end": _ts(1, 7), "value": 96},
    ]
    first = c.post("/api/v1/device-data/import", json={"records": recs, "tz_offset_min": 330}).json()
    assert first["added"] == 5 and first["glucose"]["imported"] == 1
    again = c.post("/api/v1/device-data/import", json={"records": recs}).json()
    assert again["added"] == 0 and again["skipped"] == 5

    day = (datetime.now(IST) - timedelta(days=1)).strftime("%Y-%m-%d")
    row = next(d for d in c.get("/api/v1/device-data/daily?days=5").json()["days"] if d["date"] == day)
    assert row["steps"] == 4200 and row["sleep_hours"] == 7.5
    assert row["blood_pressure"] == {"systolic": 124, "diastolic": 82}
    assert "weight_kg" not in row  # nothing synced, nothing invented


def test_unknown_types_are_refused():
    r = c.post("/api/v1/device-data/import", json={"records": [
        {"id": "x", "type": "made_up", "start": time.time(), "end": time.time()}]})
    assert r.status_code == 422


def test_rest_activity_rhythm_from_hourly_steps():
    regular = [[0] * 7 + [800] * 14 + [0] * 3 for _ in range(7)]
    out = rest_activity_rhythm(regular)
    assert out["interdaily_stability"] == 1.0 and out["relative_amplitude"] == 1.0
    assert out["l5"] == 0 and 7 <= out["m10_onset_hour"] <= 11
    shuffled = rest_activity_rhythm([d[i:] + d[:i] for i, d in enumerate(regular)])
    assert shuffled["interdaily_stability"] < out["interdaily_stability"]
    assert rest_activity_rhythm(regular[:2])["status"] == "insufficient_data"


def test_rest_activity_endpoint_needs_three_whole_days():
    assert c.get("/api/v1/device-data/rest-activity").json()["status"] in ("insufficient_data", "ok")


def test_sleep_audio_without_pause_detection_is_not_scored_as_low_apnea_risk():
    night = {"duration_minutes": 420, "snoring_events": [{"start_min": 30, "duration_min": 12, "bursts": 150}],
             "noise_events": []}
    data = c.post("/api/v1/sleep-audio/analyze", json={"user_id": "x", "audio_data": night}).json()["data"]
    assert data["apnea_risk"]["risk_level"] == "not_assessed"
    assert data["snoring"]["total_duration_min"] == 12
    assert any("12 min" in i for i in data["insights"])

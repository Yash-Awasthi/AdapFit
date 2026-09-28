"""Imports land in the caller's records, once, and the log is private."""
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from tests.conftest import register_user

c = TestClient(app)
GPX = """<?xml version="1.0"?><gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1"><trk><trkseg>
<trkpt lat="12.9716" lon="77.5946"><ele>920</ele><time>2026-08-01T06:00:00Z</time></trkpt>
<trkpt lat="12.9800" lon="77.5946"><ele>925</ele><time>2026-08-01T06:05:00Z</time></trkpt>
<trkpt lat="12.9900" lon="77.5946"><ele>930</ele><time>2026-08-01T06:10:00Z</time></trkpt>
</trkseg></trk></gpx>"""


@pytest.fixture(autouse=True)
def _auth(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_DISABLED", False)


def _h(name):
    return {"Authorization": f"Bearer {register_user(f'{name}@example.com', name)['tokens']['access_token']}"}


def test_gpx_becomes_a_workout_once():
    h = _h("gpx-user")
    r = c.post("/api/v1/wearable/gpx/import", headers=h, json={"gpx": GPX, "activity": "run"}).json()
    assert r["saved"] is True and 1.9 < r["distance_km"] < 2.1 and r["duration_minutes"] == 10.0
    assert c.post("/api/v1/wearable/gpx/import", headers=h, json={"gpx": GPX}).json()["saved"] is False
    assert c.get("/api/v1/export/workouts?format=json", headers=h).json()["data"]["workouts"][0]["source"] == "gpx"


def test_entity_expansion_is_refused():
    bomb = '<?xml version="1.0"?><!DOCTYPE gpx [<!ENTITY a "aaaa">]><gpx>&a;</gpx>'
    assert c.post("/api/v1/wearable/gpx/import", headers=_h("gpx-bomb"), json={"gpx": bomb}).status_code == 422


def test_import_log_is_private():
    a, b = _h("log-a"), _h("log-b")
    c.post("/api/v1/wearable/gpx/import", headers=a, json={"gpx": GPX})
    assert c.get("/api/v1/wearable/status", headers=b).json()["gpx"]["imports"] == 0


def test_a_hill_in_a_gpx_ride_is_found():
    pts = []
    for i in range(40):
        ele = 900 + max(0, min(20, i - 10)) * 8
        pts.append(f'<trkpt lat="{12.97 + i * 0.001:.4f}" lon="77.59"><ele>{ele}</ele>'
                   f'<time>2026-08-02T06:{i:02d}:00Z</time></trkpt>')
    gpx = ('<?xml version="1.0"?><gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1"><trk><trkseg>'
           + "".join(pts) + "</trkseg></trk></gpx>")
    r = c.post("/api/v1/wearable/gpx/import", headers=_h("gpx-hill"), json={"gpx": gpx, "activity": "ride"}).json()
    assert r["climbs"] and r["climbs"][0]["gain_m"] >= 100

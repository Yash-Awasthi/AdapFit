"""Regressions found while wiring the Conditions & Recovery hub."""
from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)


def test_rehab_progress_logs_without_crashing_and_keeps_missing_values_missing():
    pid = c.post("/api/v1/rehab/program/start", json={"injury_type": "lower_back_pain"}).json()["program"]["program_id"]
    assert c.post("/api/v1/rehab/progress", json={"program_id": pid, "pain_level": 4}).status_code == 200
    point = c.get(f"/api/v1/rehab/progress/{pid}").json()["progress"][-1]
    assert point["pain"] == 4 and point["rom"] is None


def test_all_eye_exercises_route_is_reachable():
    assert c.get("/api/v1/vision/exercises/all").status_code == 200


def test_breathless_allergy_log_gets_a_safety_step():
    r = c.post("/api/v1/allergies/symptoms", json={"user_id": "a", "date": "2026-03-01",
                                                   "data": {"severity": 6, "respiratory": {"breathlessness": True}}}).json()
    assert "112" in str(r)

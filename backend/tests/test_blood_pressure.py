"""BP readings get ranges and next steps, never a diagnosis or medication advice."""
from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)


def test_very_high_reading_mentions_112():
    r = c.post("/api/v1/blood-pressure/log?user_id=bp1", json={"systolic": 190, "diastolic": 110}).json()
    assert r["range"] == "very_high" and "112" in r["next_step"]


def test_average_drives_the_summary_and_no_medication_advice():
    for s, d in ((142, 92), (138, 88), (145, 94)):
        c.post("/api/v1/blood-pressure/log?user_id=bp2", json={"systolic": s, "diastolic": d})
    summ = c.get("/api/v1/blood-pressure/log?user_id=bp2").json()["summary"]
    assert summ["average"] == "142/91" and "medication" not in str(summ).lower()
    assert "hypertension" not in str(summ).lower()

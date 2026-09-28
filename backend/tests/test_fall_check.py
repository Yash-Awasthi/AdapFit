from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)


def test_steadi_threshold():
    low = c.post("/api/v1/senior-health/fall-check", json={"worried": True, "sad": True}).json()
    high = c.post("/api/v1/senior-health/fall-check", json={"fallen_past_year": True, "walking_aid": True}).json()
    assert (low["score"], low["at_risk"]) == (2, False)
    assert (high["score"], high["at_risk"]) == (4, True)

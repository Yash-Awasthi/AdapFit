"""IDRS matches the published scoring."""
from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)


def test_published_example_high_risk():
    r = c.post("/api/v1/health-risk/idrs", json={"age": 52, "sex": "male", "waist_cm": 102,
                                                 "activity": "sedentary", "parents_with_diabetes": 1}).json()
    assert r["score"] == 90 and r["band"] == "high" and "HbA1c" in r["next_step"]


def test_young_active_is_low():
    r = c.post("/api/v1/health-risk/idrs", json={"age": 28, "sex": "female", "waist_cm": 74,
                                                 "activity": "vigorous", "parents_with_diabetes": 0}).json()
    assert r["score"] == 0 and r["band"] == "low"


def test_female_waist_cutoffs_are_lower():
    base = {"age": 30, "waist_cm": 85, "activity": "vigorous", "parents_with_diabetes": 0}
    assert c.post("/api/v1/health-risk/idrs", json={**base, "sex": "female"}).json()["parts"]["waist"] == 10
    assert c.post("/api/v1/health-risk/idrs", json={**base, "sex": "male"}).json()["parts"]["waist"] == 0

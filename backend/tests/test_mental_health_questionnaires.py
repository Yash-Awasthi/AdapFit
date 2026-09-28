"""Questionnaires score to published ranges, give safe next steps, never medication."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.mental_health import score

c = TestClient(app)


def test_phq9_ranges_and_crisis_item():
    assert score("phq9", [0] * 9)["range"] == "minimal"
    moderate = score("phq9", [2, 2, 1, 1, 1, 1, 1, 1, 0])
    assert moderate["score"] == 10 and moderate["range"] == "moderate" and "crisis" not in moderate
    assert "crisis" in score("phq9", [0] * 8 + [1])


def test_who5_is_a_percentage():
    assert score("who5", [5] * 5)["score"] == 100
    assert score("who5", [2] * 5)["range"] == "low"


def test_no_result_mentions_medication():
    for key, n, top in (("phq9", 9, 3), ("gad7", 7, 3), ("who5", 5, 5)):
        for v in range(top + 1):
            text = score(key, [v] * n)["next_step"].lower()
            assert "medication" not in text and "medicine" not in text


def test_wrong_answer_count_is_rejected():
    with pytest.raises(ValueError):
        score("gad7", [1] * 6)


def test_results_are_kept_per_user():
    r = c.post("/api/v1/mental-health/questionnaires/gad7", json={"user_id": "mh-q", "answers": [1] * 7})
    assert r.status_code == 201 and r.json()["score"] == 7
    latest = c.get("/api/v1/mental-health/questionnaires?user_id=mh-q").json()["latest"]
    assert latest["gad7"]["range"] == "mild"

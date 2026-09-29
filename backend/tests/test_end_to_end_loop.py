"""
The loop the product is built around, exercised the way the app drives it.

    register -> log in -> morning check-in with wearable data
             -> recovery score against this user's own baseline
             -> today's training decision
             -> the next check-in is judged against a baseline that moved

Runs with the development auth bypass switched off, so it also proves that two
accounts on the same server never see each other's numbers.
"""
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from tests.conftest import register_user

c = TestClient(app)


@pytest.fixture(autouse=True)
def _auth_enforced(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_DISABLED", False)


def _account(email, username):
    result = register_user(email, username)
    assert "error" not in result, result
    return result["user"]["id"], {"Authorization": f"Bearer {result['tokens']['access_token']}"}


def _checkin(headers, day, *, hrv, sleep_hours, soreness, fatigue, rhr=60):
    return c.post(
        "/api/v1/recovery-logs",
        headers=headers,
        json={
            # Deliberately someone else's id: the server binds it to the token.
            "user_id": "not-the-caller",
            "log_date": f"2026-04-{day:02d}",
            "wearable_data": {
                "hrv_rmssd": hrv,
                "sleep_duration_hours": sleep_hours,
                "sleep_efficiency_pct": 90,
                "resting_heart_rate": rhr,
            },
            "subjective_checkin": {"soreness": soreness, "fatigue": fatigue, "stress": 3},
        },
    )


def test_a_new_account_can_complete_the_whole_loop():
    user_id, headers = _account("loop-a@example.com", "loop-a")

    r = _checkin(headers, 1, hrv=55, sleep_hours=7.5, soreness=3, fatigue=3)
    assert r.status_code == 201, r.text
    score = r.json()["recovery_score"]
    assert 0 <= score <= 100

    decision = c.get("/api/v1/decision/today?day=2026-04-01", headers=headers)
    assert decision.status_code == 200, decision.text
    body = decision.json()
    assert body["user_id"] == user_id
    assert body["decision"] in {"TRAIN", "REDUCE", "RECOVER", "REST"}
    assert body["headline"]

    # The next day, that check-in is stale: no decision until a new one.
    stale = c.get("/api/v1/decision/today?day=2026-04-02", headers=headers).json()
    assert stale["decision"] is None and stale["headline"] == "Check in to see today's plan"

    baseline = c.get(f"/api/v1/users/{user_id}/baselines", headers=headers)
    assert baseline.status_code == 200, baseline.text
    assert baseline.json()["hrv_mean_rmssd"] > 0


def test_the_baseline_tracks_the_user_over_repeated_check_ins():
    user_id, headers = _account("loop-b@example.com", "loop-b")

    start = c.get(f"/api/v1/users/{user_id}/baselines", headers=headers)
    for day in range(1, 15):
        assert _checkin(headers, day, hrv=92, sleep_hours=8.2, soreness=2, fatigue=2, rhr=47).status_code == 201

    end = c.get(f"/api/v1/users/{user_id}/baselines", headers=headers).json()
    assert end["hrv_mean_rmssd"] > 80, end
    assert end["rhr_baseline"] < 55, end
    if start.status_code == 200:
        assert end["hrv_mean_rmssd"] > start.json()["hrv_mean_rmssd"]


def test_the_same_reading_scores_differently_for_two_different_people():
    """The hyper-personalization claim, end to end through the API."""
    _, low = _account("loop-low@example.com", "loop-low")
    _, high = _account("loop-high@example.com", "loop-high")

    for day in range(1, 15):
        _checkin(low, day, hrv=38, sleep_hours=6.5, soreness=5, fatigue=5, rhr=70)
        _checkin(high, day, hrv=88, sleep_hours=8.0, soreness=2, fatigue=2, rhr=48)

    # Day 15: both wake up at exactly 60 ms.
    low_score = _checkin(low, 15, hrv=60, sleep_hours=7.5, soreness=3, fatigue=3).json()["recovery_score"]
    high_score = _checkin(high, 15, hrv=60, sleep_hours=7.5, soreness=3, fatigue=3).json()["recovery_score"]

    assert low_score > high_score, (
        f"60ms should read as a good morning for the low-baseline user ({low_score}) "
        f"and a poor one for the high-baseline user ({high_score})"
    )


def test_one_account_never_sees_another_accounts_numbers():
    a_id, a = _account("loop-iso-a@example.com", "loop-iso-a")
    b_id, b = _account("loop-iso-b@example.com", "loop-iso-b")

    for day in range(1, 8):
        _checkin(a, day, hrv=95, sleep_hours=8.5, soreness=1, fatigue=1, rhr=45)

    # B has logged nothing, and asking for A's id changes nothing.
    logs = c.get(f"/api/v1/recovery-logs?user_id={a_id}", headers=b)
    assert logs.status_code == 200, logs.text
    assert logs.json()["user_id"] == b_id
    assert logs.json()["count"] == 0

    baseline = c.get(f"/api/v1/users/{a_id}/baselines", headers=b).json()
    assert baseline.get("hrv_mean_rmssd") != pytest.approx(95, abs=5)


def test_an_unauthenticated_client_gets_nothing():
    r = c.get("/api/v1/decision/today")
    assert r.status_code == 401

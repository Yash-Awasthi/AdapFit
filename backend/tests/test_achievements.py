"""Achievements come only from logged activity; nothing can grant them."""
from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.api.v1.endpoints.achievements import _day_streaks
from app.main import app

client = TestClient(app)


def test_streaks_count_consecutive_days_and_keep_the_best():
    today = date.today()
    days = [today - timedelta(days=n) for n in (0, 1, 2, 10, 11, 12, 13)]
    current, best = _day_streaks([d.isoformat() for d in days])
    assert (current, best) == (3, 4)


def test_a_lapsed_streak_is_not_current():
    old = date.today() - timedelta(days=5)
    assert _day_streaks([old.isoformat()]) == (0, 1)


def test_a_new_user_has_nothing_unlocked():
    badges = client.get("/api/v1/achievements").json()
    assert len(badges) >= 15 and not any(b["unlocked"] for b in badges if b["category"] == "sleep")


def test_logging_sleep_unlocks_the_sleep_badge():
    for day in range(7):
        client.post("/api/v1/sleep/logs", json={
            "bedtime": "23:00", "wake_time": "07:00", "date": f"2026-02-0{day + 1}", "efficiency_pct": 92,
        })
    badges = {b["id"]: b for b in client.get("/api/v1/achievements").json()}
    assert badges["sleep_7"]["unlocked"] and badges["sleep_efficient"]["unlocked"]
    summary = client.get("/api/v1/achievements/summary").json()
    assert summary["points"] >= 60 and summary["earned"] >= 2


def test_there_is_no_way_to_grant_points():
    assert client.post("/api/v1/achievements/grant", json={"achievement_id": "hundred_workouts"}).status_code in (404, 405)
    assert client.post("/api/v1/gamification/xp", json={"amount": 10000}).status_code == 404


def test_leaderboard_hides_other_users():
    board = client.get("/api/v1/achievements/leaderboard").json()
    assert all(e["name"] == "You" or e["name"].startswith("Athlete ") for e in board["leaderboard"])

"""Habit streaks come from completion dates, not a counter."""
from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.services.habit_coach import HabitCoachService

c = TestClient(app)


def test_completing_twice_in_a_day_counts_once():
    uid = "habit-twice"
    hid = c.post("/api/v1/habits/custom", json={"user_id": uid, "name": "Floss"}).json()["habit_id"]
    c.post(f"/api/v1/habits/complete/{hid}?user_id={uid}")
    r = c.post(f"/api/v1/habits/complete/{hid}?user_id={uid}").json()
    assert r["streak"] == 1 and r["total"] == 1


def test_a_missed_day_breaks_the_current_streak():
    today = date.today()
    dates = [(today - timedelta(days=d)).isoformat() for d in (5, 4, 3)]
    assert HabitCoachService._streaks(dates) == (0, 3)
    assert HabitCoachService._streaks(dates + [today.isoformat()]) == (1, 3)


def test_no_invented_statistics_in_nudges():
    uid = "habit-nudge"
    hid = c.post("/api/v1/habits/custom", json={"user_id": uid, "name": "Walk"}).json()["habit_id"]
    for _ in range(20):
        assert "%" not in c.get(f"/api/v1/habits/nudge/{uid}").json()["message"]

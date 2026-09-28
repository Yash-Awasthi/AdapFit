"""Reduced fetal movement goes to the maternity team the same day, judged against the baby's own pattern."""
from app.services.pregnancy_tracker import PregnancyTrackerService


def test_few_kicks_in_two_hours_means_call_today():
    out = PregnancyTrackerService().kick_counter("u", {"kicks": 4, "duration_minutes": 120})
    assert out["status"] == "fewer_than_usual" and "today" in out["next_step"]
    assert "snack" not in str(out)


def test_drop_against_own_pattern_is_flagged():
    svc = PregnancyTrackerService()
    for _ in range(3):
        svc.kick_counter("u", {"kicks": 10, "duration_minutes": 20})
    assert svc.kick_counter("u", {"kicks": 10, "duration_minutes": 60})["status"] == "fewer_than_usual"
    assert svc.kick_counter("u", {"kicks": 10, "duration_minutes": 22})["status"] == "recorded"

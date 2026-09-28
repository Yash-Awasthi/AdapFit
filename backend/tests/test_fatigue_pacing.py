"""Pacing uses a measured resting heart rate or no ceiling at all, and spots boom-bust."""
from app.services.chronic_fatigue import ChronicFatigueService


def test_no_resting_rate_means_no_ceiling():
    svc = ChronicFatigueService()
    assert svc.plan()["heart_rate_ceiling"] is None
    assert svc.log_day("2026-09-01", 5, 30, peak_hr=150)["entry"]["over_ceiling"] is None


def test_ceiling_is_resting_plus_fifteen():
    svc = ChronicFatigueService()
    svc.set_resting_hr(62)
    out = svc.log_day("2026-09-01", 5, 30, peak_hr=90)
    assert svc.ceiling == 77 and out["entry"]["over_ceiling"] and out["advice"]


def test_boom_then_crash_is_flagged():
    svc = ChronicFatigueService()
    svc.log_day("2026-09-01", 5, 30)
    svc.log_day("2026-09-02", 7, 120)
    svc.log_day("2026-09-03", 2, 10)
    svc.log_crash("2026-09-03", "severe")
    s = svc.summary()
    assert s["boom_bust_days"] == ["2026-09-02"] and len(s["crashes"]) == 1

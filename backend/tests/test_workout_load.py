"""Training load: only measured sessions count, and ACWR follows the daily EWMA of Williams et al. 2017."""
from datetime import date, timedelta

from app.core.workout_metrics import acwr, acwr_ratio, session_load

TODAY = date(2026, 9, 29)


def _log(days_ago, load=None, **kw):
    return {"recorded_at": (TODAY - timedelta(days=days_ago)).isoformat(), **({"session_load": load} if load else {}), **kw}


def test_unmeasured_sessions_have_no_load():
    assert session_load({"actual_duration_minutes": 40}) is None  # a Health Connect session, no RPE
    assert session_load({"session_rpe": 6}) is None
    assert session_load({"session_rpe": 6, "actual_duration_minutes": 40}) == 240
    assert session_load({"session_rpe": 6, "target_duration_minutes": 40}) is None  # a plan is not a measurement


def test_no_acwr_before_four_weeks():
    assert acwr([_log(d, 300) for d in range(0, 27)], TODAY) == (None, None)
    assert acwr([_log(3, None, actual_duration_minutes=50)] * 40, TODAY) == (None, None)


def test_steady_training_sits_near_one_and_a_spike_raises_it():
    steady = [_log(d, 300) for d in range(0, 60, 2)]  # every other day for 8 weeks
    assert 0.85 <= acwr_ratio(steady, TODAY) <= 1.15
    spike = steady + [_log(d, 900) for d in range(0, 5)]
    assert acwr_ratio(spike, TODAY) > 1.5


def test_rest_days_count_as_zero():
    trained_then_rested = [_log(d, 400) for d in range(14, 60)]
    acute, chronic = acwr(trained_then_rested, TODAY)
    assert acute < chronic * 0.3  # two weeks off drains the 7-day average far faster than the 28-day one

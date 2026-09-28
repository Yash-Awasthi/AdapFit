"""The alertness curve follows the user's own sleep timing."""
from datetime import datetime, timedelta

from app.services.fatigue_prediction import SleepPeriod, alertness_curve, mid_sleep_hour, summarise


def _nights(bed_hour, days=5):
    base = datetime(2026, 3, 1)
    return [SleepPeriod(base + timedelta(days=d, hours=bed_hour), base + timedelta(days=d, hours=bed_hour + 8))
            for d in range(days)]


def test_mid_sleep_wraps_midnight():
    assert round(mid_sleep_hour(_nights(22))) == 2


def test_a_late_sleeper_peaks_later():
    day = datetime(2026, 3, 5)
    early = summarise(alertness_curve(_nights(22), day))
    late = summarise(alertness_curve(_nights(26), day))
    to_h = lambda w: int(w.split("-")[0].split(":")[0])  # noqa: E731
    assert to_h(late["peak_window"]) > to_h(early["peak_window"])


def test_sleep_hours_have_no_alertness_value():
    day = datetime(2026, 3, 5)
    curve = alertness_curve(_nights(22), day)
    assert all(v is None for t, v in curve if t.hour in (1, 3))

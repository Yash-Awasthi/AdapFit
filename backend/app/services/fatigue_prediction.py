"""
Alertness across the day from the two-process model of sleep regulation
(Borbely 1982; Daan, Beersma & Borbely 1984).

Process S (sleep pressure) rises while awake and falls while asleep with the
published time constants; Process C (the body clock) is a 24-hour sinusoid
whose timing comes from the user's own mid-sleep, so a late sleeper's curve
peaks later. Alertness is C minus S, scaled 0-100 for display.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta

TAU_RISE_H = 18.2
TAU_DECAY_H = 4.2
# Body-clock alertness peaks roughly 14 hours after mid-sleep in entrained adults.
PEAK_AFTER_MIDSLEEP_H = 14.0
C_AMPLITUDE = 0.12
STEP_MIN = 15


@dataclass(frozen=True)
class SleepPeriod:
    start: datetime
    end: datetime


def mid_sleep_hour(periods: list[SleepPeriod]) -> float:
    """Average clock hour of mid-sleep, averaged on the circle so 23:00 and 01:00 give 00:00."""
    angles = []
    for p in periods:
        mid = p.start + (p.end - p.start) / 2
        angles.append(2 * math.pi * (mid.hour + mid.minute / 60) / 24)
    x = sum(math.cos(a) for a in angles) / len(angles)
    y = sum(math.sin(a) for a in angles) / len(angles)
    return (math.atan2(y, x) * 24 / (2 * math.pi)) % 24


def alertness_curve(periods: list[SleepPeriod], day: datetime) -> list[tuple[datetime, float]]:
    """Alertness 0-100 every 15 minutes across `day`, simulated from the first sleep period."""
    periods = sorted(periods, key=lambda p: p.start)
    peak = (mid_sleep_hour(periods) + PEAK_AFTER_MIDSLEEP_H) % 24
    t = periods[0].start
    end = day.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    s = 0.3
    step_h = STEP_MIN / 60
    out = []
    while t < end:
        asleep = any(p.start <= t < p.end for p in periods)
        if asleep:
            s *= math.exp(-step_h / TAU_DECAY_H)
        else:
            s = 1 - (1 - s) * math.exp(-step_h / TAU_RISE_H)
        if t.date() == day.date():
            hour = t.hour + t.minute / 60
            c = C_AMPLITUDE * math.cos(2 * math.pi * (hour - peak) / 24)
            out.append((t, None if asleep else round(max(0.0, min(100.0, (c - s + 0.9) * 100)), 1)))
        t += timedelta(minutes=STEP_MIN)
    return out


def summarise(curve: list[tuple[datetime, float | None]]) -> dict:
    awake = [(t, v) for t, v in curve if v is not None]
    if not awake:
        return {}

    def best_window(points, hours, pick):
        n = int(hours * 60 / STEP_MIN)
        best = None
        for i in range(len(points) - n + 1):
            avg = sum(v for _, v in points[i:i + n]) / n
            if best is None or pick(avg, best[1]):
                best = (points[i][0], avg)
        return best

    peak = best_window(awake, 2, lambda a, b: a > b)
    # The post-lunch dip is searched only in the middle of the waking day.
    third = len(awake) // 3
    dip = best_window(awake[third:2 * third] or awake, 1, lambda a, b: a < b)
    fmt = lambda t: t.strftime("%H:%M")  # noqa: E731
    return {
        "peak_window": f"{fmt(peak[0])}-{fmt(peak[0] + timedelta(hours=2))}",
        "dip_window": f"{fmt(dip[0])}-{fmt(dip[0] + timedelta(hours=1))}",
        "suggestions": [
            f"Hard training or demanding work fits best around {fmt(peak[0])}.",
            f"Expect a dip around {fmt(dip[0])}; a short walk or daylight helps more than caffeine late in the day.",
        ],
    }

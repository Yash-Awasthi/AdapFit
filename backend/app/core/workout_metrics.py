"""
Readers for the numeric fields of a workout log, and the training load built on them.

Duration is stored under `actual_duration_minutes`, and `dict.get(key,
default)` yields None whenever the key is present and null, so neither the
field name nor the default can be assumed. A session without a recorded RPE
or duration (a Health Connect session, a GPS run) has no measured load and is
left out of every load figure rather than given an assumed one.
"""
from datetime import date, datetime, timezone
from typing import Any, Iterable, Mapping, Optional, Tuple

ACUTE_DAYS = 7
CHRONIC_DAYS = 28
# Workload entries to read for a load figure: enough to reach back past the chronic window.
HISTORY_ENTRIES = 400

_DURATION_KEYS = ("actual_duration_minutes", "duration_minutes")


def _first_number(log: Mapping[str, Any], keys: tuple[str, ...]) -> Optional[float]:
    for key in keys:
        value = log.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def session_duration_minutes(log: Mapping[str, Any]) -> Optional[float]:
    """Recorded duration of a session, or None."""
    value = _first_number(log, _DURATION_KEYS)
    return value if value is not None and value > 0 else None


def session_rpe(log: Mapping[str, Any]) -> Optional[float]:
    """Session RPE on the 1-10 scale, clamped so a bad log cannot skew a model; None if not recorded."""
    value = _first_number(log, ("session_rpe", "rpe"))
    return None if value is None else max(1.0, min(10.0, value))


def session_load(log: Mapping[str, Any]) -> Optional[float]:
    """Session RPE x minutes (Foster), preferring the load stored at log time; None when not measured."""
    stored = _first_number(log, ("session_load",))
    if stored is not None and stored > 0:
        return stored
    rpe, minutes = session_rpe(log), session_duration_minutes(log)
    return rpe * minutes if rpe is not None and minutes is not None else None


def _day(log: Mapping[str, Any]) -> Optional[date]:
    raw = log.get("recorded_at") or log.get("completed_at") or log.get("created_at")
    if isinstance(raw, datetime):
        return raw.astimezone(timezone.utc).date() if raw.tzinfo else raw.date()
    try:
        return date.fromisoformat(str(raw)[:10]) if raw else None
    except ValueError:
        return None


def acwr(logs: Iterable[Mapping[str, Any]], today: Optional[date] = None) -> Tuple[Optional[float], Optional[float]]:
    """
    (acute, chronic) daily training load as exponentially weighted averages
    (Williams et al. 2017, Br J Sports Med 51:209): lambda = 2 / (N + 1) with
    N = 7 and 28, rest days count as zero. Both are None until the first
    measured session is 28 days old, since a chronic load needs that history.
    """
    daily: dict[date, float] = {}
    for log in logs:
        load, day = session_load(log), _day(log)
        if load is not None and day is not None:
            daily[day] = daily.get(day, 0.0) + load
    if not daily:
        return None, None
    today = today or datetime.now(timezone.utc).date()
    first = min(daily)
    if (today - first).days + 1 < CHRONIC_DAYS:
        return None, None
    acute = chronic = 0.0
    la, lc = 2 / (ACUTE_DAYS + 1), 2 / (CHRONIC_DAYS + 1)
    for offset in range((today - first).days + 1):
        load = daily.get(date.fromordinal(first.toordinal() + offset), 0.0)
        acute = la * load + (1 - la) * acute
        chronic = lc * load + (1 - lc) * chronic
    return round(acute, 1), round(chronic, 1)


def acwr_ratio(logs: Iterable[Mapping[str, Any]], today: Optional[date] = None) -> Optional[float]:
    acute, chronic = acwr(logs, today)
    return round(acute / chronic, 2) if acute is not None and chronic else None

"""
Readers for the numeric fields of a workout log.

Duration is stored under `actual_duration_minutes`, and `dict.get(key,
default)` yields None whenever the key is present and null, so neither the
field name nor the default can be assumed. A None from either source
propagates silently into training-load and ML features.
"""
from typing import Any, Mapping, Optional

DEFAULT_DURATION_MINUTES = 45.0
DEFAULT_RPE = 5.0

_DURATION_KEYS = ("actual_duration_minutes", "duration_minutes", "target_duration_minutes")


def _first_number(log: Mapping[str, Any], keys: tuple[str, ...]) -> Optional[float]:
    for key in keys:
        value = log.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def session_duration_minutes(log: Mapping[str, Any], default: float = DEFAULT_DURATION_MINUTES) -> float:
    """Duration of a logged session, falling back when it was never recorded."""
    value = _first_number(log, _DURATION_KEYS)
    return value if value is not None and value > 0 else default


def session_rpe(log: Mapping[str, Any], default: float = DEFAULT_RPE) -> float:
    """Session RPE on the 1-10 scale, clamped so a bad log cannot skew a model."""
    value = _first_number(log, ("session_rpe", "rpe"))
    if value is None:
        return default
    return max(1.0, min(10.0, value))


def session_load(log: Mapping[str, Any]) -> float:
    """
    Session training load (TRIMP-style RPE x duration).

    Prefers the load stored at log time so a recalculation cannot disagree
    with the value the recovery engine already used.
    """
    stored = _first_number(log, ("session_load",))
    if stored is not None and stored > 0:
        return stored
    return session_rpe(log) * session_duration_minutes(log)

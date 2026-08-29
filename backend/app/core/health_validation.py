"""
Physiological plausibility ranges and computed confidence for health measurements.

Ranges are wide enough to cover trained-athlete outliers but reject values that
are not survivable or not physically achievable in a day. Sources:

- hrv_rmssd: rMSSD values below ~5ms or above ~200ms are outside published
  population norms (Shaffer & Ginsberg, 2017 Frontiers in Public Health review).
- resting_heart_rate / heart_rate: elite-endurance-athlete lows sit around
  30 bpm; sustained rates above 220 bpm are not physiologically survivable.
- sleep_duration_hours: 0-16h covers polyphasic sleepers and pathological
  hypersomnia without allowing more than a day's worth of sleep.
- sleep_efficiency_pct / spo2: bounded percentages, 0-100.
- spo2: below 60% is incompatible with consciousness; used as a hard floor.
- body_temperature: 30-45 C spans severe hypothermia to lethal hyperthermia.
- steps: 100k/day is an extreme but reachable ultramarathon ceiling.
- active_calories: 8000 kcal/day covers ultra-endurance events.
- weight_kg: 20-300 covers pediatric through bariatric extremes.

A value inside its range is not guaranteed correct (a fat-fingered 88 instead
of 8.8 hours of sleep can still land in range) — confidence below scores that
separately, from source trust and where the value falls in the range.
"""
from typing import Optional

from app.core.health_data import DataConfidence, DataSource

# measurement_type -> (min, max)
PHYSIOLOGICAL_RANGES: dict[str, tuple[float, float]] = {
    "hrv_rmssd": (5, 200),
    "resting_heart_rate": (30, 120),
    "heart_rate": (30, 220),
    "sleep_duration_hours": (0, 16),
    "sleep_efficiency_pct": (0, 100),
    "steps": (0, 100_000),
    "active_calories": (0, 8_000),
    "spo2": (60, 100),
    "body_temperature": (30, 45),
    "weight_kg": (20, 300),
}

# how much a data source is trusted before we look at the value itself
_SOURCE_TRUST: dict[str, float] = {
    DataSource.SENSOR.value: 1.0,
    DataSource.DEVICE.value: 0.9,
    DataSource.CALCULATED.value: 0.7,
    DataSource.IMPORT.value: 0.6,
    DataSource.MANUAL.value: 0.45,
}

# (type_a, type_b) -> function(value_a, value_b) -> True if the pair is
# physiologically plausible together. Checked in both directions.
_CONSISTENCY_CHECKS = {
    ("resting_heart_rate", "hrv_rmssd"): lambda rhr, hrv: not (rhr > 100 and hrv > 120),
    ("sleep_duration_hours", "sleep_efficiency_pct"): lambda hours, eff: not (hours < 0.5 and eff > 50),
}


def validate(measurement_type: str, value: float) -> tuple[bool, Optional[float], str]:
    """Check value against its plausible physiological range.

    Returns (ok, normalized_value, reason). normalized_value is the input
    rounded to 2 decimals when ok, otherwise None.
    """
    if measurement_type not in PHYSIOLOGICAL_RANGES:
        return False, None, f"no plausible range defined for measurement type '{measurement_type}'"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False, None, f"value {value!r} is not numeric"
    lo, hi = PHYSIOLOGICAL_RANGES[measurement_type]
    if numeric < lo or numeric > hi:
        return False, None, f"{measurement_type}={numeric} is outside plausible range [{lo}, {hi}]"
    return True, round(numeric, 2), "within plausible range"


def _range_position_score(measurement_type: str, value: float) -> float:
    """1.0 at the range center, tapering to 0.5 at the edges."""
    lo, hi = PHYSIOLOGICAL_RANGES[measurement_type]
    span = hi - lo
    if span <= 0:
        return 1.0
    center = (lo + hi) / 2
    distance = abs(value - center) / (span / 2)
    return 1.0 - 0.5 * min(distance, 1.0)


def compute_confidence(
    measurement_type: str,
    value: float,
    source: str,
    related_readings: Optional[dict[str, float]] = None,
) -> DataConfidence:
    """Derive confidence from source trust, in-range position, and cross-field
    consistency. Never accepts a caller-supplied confidence — this is the only
    place confidence should be produced.
    """
    ok, normalized, _reason = validate(measurement_type, value)
    if not ok:
        return DataConfidence.LOW

    score = 0.6 * _SOURCE_TRUST.get(source, 0.4) + 0.4 * _range_position_score(measurement_type, normalized)

    for related_type, related_value in (related_readings or {}).items():
        check = _CONSISTENCY_CHECKS.get((measurement_type, related_type)) or _CONSISTENCY_CHECKS.get((related_type, measurement_type))
        if check is None:
            continue
        args = (normalized, related_value) if (measurement_type, related_type) in _CONSISTENCY_CHECKS else (related_value, normalized)
        if not check(*args):
            score -= 0.3

    if score >= 0.85:
        return DataConfidence.HIGH
    if score >= 0.6:
        return DataConfidence.MEDIUM
    if score >= 0.35:
        return DataConfidence.LOW
    return DataConfidence.ESTIMATED

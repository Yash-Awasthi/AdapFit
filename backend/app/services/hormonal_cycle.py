"""
Hormonal cycle tracking — pure functions, no DB dependency.

Uses standard calendar-based methods:
  - Average cycle length calculation
  - Ovulation prediction (Ogino-Knaus / standard days method)
  - Phase detection (menstrual, follicular, ovulation, luteal)
  - Fertility window estimation
  - PMS symptom correlation

All dates as ISO 8601 strings. No external dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Sequence


@dataclass(frozen=True)
class CycleDay:
    """A single day in the cycle."""
    date: str  # ISO date
    cycle_day_number: int  # 1-based from start of menstruation
    phase: str  # "menstrual", "follicular", "ovulation", "luteal"
    is_fertile: bool
    is_peak_fertility: bool
    confidence: str  # "high", "moderate", "low"


@dataclass(frozen=True)
class CyclePrediction:
    """Predicted next cycle dates."""
    predicted_start: str  # ISO date
    predicted_end: str
    predicted_ovulation: str
    fertile_window_start: str
    fertile_window_end: str
    predicted_cycle_length: int
    confidence: str
    based_on_cycles: int


@dataclass(frozen=True)
class PhaseInfo:
    """Current phase details."""
    phase: str
    day_in_phase: int
    days_remaining: int
    phase_description: str
    recommendations: list[str]


@dataclass(frozen=True)
class SymptomEntry:
    """A logged symptom."""
    date: str
    symptom: str  # e.g. "cramps", "bloating", "mood_swings", "headache"
    severity: int  # 1-5


@dataclass(frozen=True)
class SymptomCorrelation:
    """Correlation between symptoms and cycle phase."""
    symptom: str
    most_common_phase: str
    average_severity_by_phase: dict[str, float]
    correlation_strength: str  # "strong", "moderate", "weak"


# ── Constants ────────────────────────────────────────────────────────────────

DEFAULT_CYCLE_LENGTH = 28
MIN_CYCLE_LENGTH = 21
MAX_CYCLE_LENGTH = 40
MENSTRUAL_DURATION = 5
LUTEAL_PHASE_LENGTH = 14  # relatively constant across women
FERTILE_WINDOW_DAYS = 6  # 5 days before ovulation + ovulation day
PEAK_FERTILITY_DAYS = 2  # 2 days before ovulation


# ── Cycle Length Calculation ─────────────────────────────────────────────────


def calculate_cycle_lengths(period_starts: Sequence[str]) -> list[int]:
    """Calculate cycle lengths from a list of period start dates (ISO dates)."""
    if len(period_starts) < 2:
        return []

    dates = sorted(datetime.fromisoformat(d) for d in period_starts)
    lengths = []
    for i in range(1, len(dates)):
        diff = (dates[i] - dates[i - 1]).days
        if MIN_CYCLE_LENGTH <= diff <= MAX_CYCLE_LENGTH:
            lengths.append(diff)
    return lengths


def average_cycle_length(period_starts: Sequence[str]) -> int:
    """Calculate average cycle length. Returns default if insufficient data."""
    lengths = calculate_cycle_lengths(period_starts)
    if not lengths:
        return DEFAULT_CYCLE_LENGTH
    return round(sum(lengths) / len(lengths))


# ── Ovulation Prediction ────────────────────────────────────────────────────


def predict_ovulation(cycle_start: str, cycle_length: int) -> str:
    """
    Predict ovulation date using standard days method.
    Ovulation typically occurs 14 days before next period.
    """
    start = datetime.fromisoformat(cycle_start)
    ovulation_day = cycle_length - LUTEAL_PHASE_LENGTH
    if ovulation_day < 10:
        ovulation_day = 10  # floor
    return (start + timedelta(days=ovulation_day)).date().isoformat()


def calculate_fertile_window(cycle_start: str, cycle_length: int) -> tuple[str, str]:
    """
    Calculate fertile window: 5 days before ovulation through ovulation day.
    Returns (start_date, end_date) as ISO strings.
    """
    ovulation = datetime.fromisoformat(predict_ovulation(cycle_start, cycle_length))
    window_start = ovulation - timedelta(days=FERTILE_WINDOW_DAYS - 1)
    window_end = ovulation
    return window_start.date().isoformat(), window_end.date().isoformat()


# ── Phase Detection ─────────────────────────────────────────────────────────


def detect_phase(cycle_start: str, cycle_length: int, current_date: str) -> str:
    """Detect which phase a given date falls in."""
    start = datetime.fromisoformat(cycle_start)
    current = datetime.fromisoformat(current_date)
    day_num = (current - start).days + 1

    if day_num < 1:
        return "unknown"
    elif day_num <= MENSTRUAL_DURATION:
        return "menstrual"
    elif day_num <= cycle_length - LUTEAL_PHASE_LENGTH - PEAK_FERTILITY_DAYS:
        return "follicular"
    elif day_num <= cycle_length - LUTEAL_PHASE_LENGTH + 1:
        return "ovulation"
    elif day_num <= cycle_length:
        return "luteal"
    else:
        return "unknown"  # past expected cycle end


def get_phase_info(phase: str) -> PhaseInfo:
    """Get detailed information about a cycle phase."""
    info = {
        "menstrual": PhaseInfo(
            phase="menstrual",
            day_in_phase=1,
            days_remaining=MENSTRUAL_DURATION,
            phase_description="Menstruation — uterine lining is being shed",
            recommendations=[
                "Rest and stay hydrated",
                "Iron-rich foods to compensate for blood loss",
                "Gentle exercise like walking or yoga",
                "Heat therapy for cramps",
            ],
        ),
        "follicular": PhaseInfo(
            phase="follicular",
            day_in_phase=1,
            days_remaining=DEFAULT_CYCLE_LENGTH - MENSTRUAL_DURATION - LUTEAL_PHASE_LENGTH,
            phase_description="Follicular phase — estrogen rises, energy typically increases",
            recommendations=[
                "Great time for high-intensity workouts",
                "Estrogen peaks — energy and mood typically improve",
                "Plan important tasks during peak energy days",
                "Strength training is especially effective",
            ],
        ),
        "ovulation": PhaseInfo(
            phase="ovulation",
            day_in_phase=1,
            days_remaining=2,
            phase_description="Ovulation — peak fertility, estrogen and LH surge",
            recommendations=[
                "Peak energy and confidence",
                "Best time for social activities and presentations",
                "Body temperature may rise slightly",
                "Fertility awareness: use protection if not planning pregnancy",
            ],
        ),
        "luteal": PhaseInfo(
            phase="luteal",
            day_in_phase=1,
            days_remaining=LUTEAL_PHASE_LENGTH,
            phase_description="Luteal phase — progesterone rises, PMS symptoms may appear",
            recommendations=[
                "Moderate exercise — avoid overtraining",
                "Complex carbs may help with mood",
                "Track PMS symptoms for pattern recognition",
                "Prioritize sleep — progesterone promotes drowsiness",
            ],
        ),
    }
    return info.get(phase, PhaseInfo(
        phase=phase,
        day_in_phase=0,
        days_remaining=0,
        phase_description="Phase unknown",
        recommendations=[],
    ))


# ── Cycle Prediction ─────────────────────────────────────────────────────────


def predict_next_cycle(
    period_starts: Sequence[str],
    current_date: str | None = None,
) -> CyclePrediction | None:
    """Predict next cycle based on historical period starts."""
    if len(period_starts) < 1:
        return None

    avg_length = average_cycle_length(period_starts)
    last_start = max(datetime.fromisoformat(d) for d in period_starts)
    next_start = last_start + timedelta(days=avg_length)
    next_end = next_start + timedelta(days=MENSTRUAL_DURATION - 1)
    next_ovulation = datetime.fromisoformat(
        predict_ovulation(next_start.isoformat(), avg_length)
    )
    fertile_start, fertile_end = calculate_fertile_window(
        next_start.isoformat(), avg_length
    )

    # Confidence based on cycle regularity
    lengths = calculate_cycle_lengths(period_starts)
    if len(lengths) >= 6:
        std_dev = (sum((x - avg_length) ** 2 for x in lengths) / len(lengths)) ** 0.5
        confidence = "high" if std_dev <= 2 else "moderate" if std_dev <= 4 else "low"
    elif len(lengths) >= 3:
        confidence = "moderate"
    else:
        confidence = "low"

    return CyclePrediction(
        predicted_start=next_start.date().isoformat(),
        predicted_end=next_end.date().isoformat(),
        predicted_ovulation=next_ovulation.date().isoformat(),
        fertile_window_start=fertile_start,
        fertile_window_end=fertile_end,
        predicted_cycle_length=avg_length,
        confidence=confidence,
        based_on_cycles=len(lengths),
    )


# ── Fertility Window ─────────────────────────────────────────────────────────


def is_fertile(cycle_start: str, cycle_length: int, check_date: str) -> bool:
    """Check if a given date falls within the fertile window."""
    start, end = calculate_fertile_window(cycle_start, cycle_length)
    check = datetime.fromisoformat(check_date).date()
    return start <= check.isoformat() <= end


def is_peak_fertility(cycle_start: str, cycle_length: int, check_date: str) -> bool:
    """Check if a given date is peak fertility (2 days before ovulation)."""
    ovulation = datetime.fromisoformat(
        predict_ovulation(cycle_start, cycle_length)
    )
    check = datetime.fromisoformat(check_date).date()
    peak_start = (ovulation - timedelta(days=PEAK_FERTILITY_DAYS)).date()
    peak_end = ovulation.date()
    return peak_start <= check <= peak_end


# ── Symptom Correlation ──────────────────────────────────────────────────────


def correlate_symptoms(
    symptoms: Sequence[SymptomEntry],
    period_starts: Sequence[str],
    cycle_length: int | None = None,
) -> list[SymptomCorrelation]:
    """Analyze symptom patterns across cycle phases."""
    if not symptoms or len(period_starts) < 1:
        return []

    avg_len = cycle_length or average_cycle_length(period_starts)
    starts = sorted(datetime.fromisoformat(d) for d in period_starts)

    # Group symptoms by phase
    symptom_phases: dict[str, dict[str, list[float]]] = {}
    for s in symptoms:
        s_date = datetime.fromisoformat(s.date)
        # Find which cycle this symptom belongs to
        phase = "unknown"
        for i, cycle_start in enumerate(reversed(starts)):
            day_num = (s_date - cycle_start).days + 1
            if 1 <= day_num <= avg_len:
                phase = detect_phase(
                    cycle_start.isoformat(), avg_len, s_date.isoformat()
                )
                break

        if phase == "unknown":
            continue

        if s.symptom not in symptom_phases:
            symptom_phases[s.symptom] = {}
        if phase not in symptom_phases[s.symptom]:
            symptom_phases[s.symptom][phase] = []
        symptom_phases[s.symptom][phase].append(float(s.severity))

    results = []
    for symptom, phases in symptom_phases.items():
        # Find most common phase
        phase_counts = {p: len(vals) for p, vals in phases.items()}
        most_common = max(phase_counts, key=phase_counts.get)  # type: ignore

        # Average severity by phase
        avg_by_phase = {
            p: round(sum(vals) / len(vals), 1)
            for p, vals in phases.items()
        }

        # Correlation strength based on concentration
        total = sum(phase_counts.values())
        max_count = phase_counts[most_common]
        ratio = max_count / total if total > 0 else 0

        if ratio >= 0.7:
            strength = "strong"
        elif ratio >= 0.5:
            strength = "moderate"
        else:
            strength = "weak"

        results.append(SymptomCorrelation(
            symptom=symptom,
            most_common_phase=most_common,
            average_severity_by_phase=avg_by_phase,
            correlation_strength=strength,
        ))

    return results

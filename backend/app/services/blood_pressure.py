"""
Blood pressure analysis — pure functions, no DB dependency.

Classification follows AHA/ACC 2017 guidelines:
  Normal:        systolic < 120 AND diastolic < 80
  Elevated:      systolic 120-129 AND diastolic < 80
  Stage 1 HTN:   systolic 130-139 OR diastolic 80-89
  Stage 2 HTN:   systolic >= 140 OR diastolic >= 90
  Hypertensive Crisis: systolic > 180 OR diastolic > 120
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class BPClassification(str, Enum):
    NORMAL = "normal"
    ELEVATED = "elevated"
    STAGE1 = "stage_1_hypertension"
    STAGE2 = "stage_2_hypertension"
    CRISIS = "hypertensive_crisis"


@dataclass(frozen=True)
class BPReading:
    systolic: float  # mmHg
    diastolic: float  # mmHg
    timestamp: str | None = None  # ISO 8601


@dataclass(frozen=True)
class BPClassificationResult:
    classification: BPClassification
    systolic: float
    diastolic: float
    pulse_pressure: float
    mean_arterial_pressure: float
    description: str


@dataclass(frozen=True)
class BPTrend:
    mean_systolic: float
    mean_diastolic: float
    systolic_trend: str  # "rising", "falling", "stable"
    diastolic_trend: str
    variability_systolic: float  # standard deviation
    variability_diastolic: float
    reading_count: int
    classification_distribution: dict[str, int]


@dataclass(frozen=True)
class BPRiskAssessment:
    overall_risk: str  # "low", "moderate", "high", "very_high"
    risk_score: int  # 0-100
    factors: list[str]
    recommendation: str


# ── Classification ───────────────────────────────────────────────────────────


def classify_reading(reading: BPReading) -> BPClassificationResult:
    """Classify a single BP reading per AHA/ACC 2017 guidelines."""
    s, d = reading.systolic, reading.diastolic

    if s > 180 or d > 120:
        cls = BPClassification.CRISIS
        desc = "Hypertensive crisis — seek immediate medical attention"
    elif s >= 140 or d >= 90:
        cls = BPClassification.STAGE2
        desc = "Stage 2 hypertension — medication typically required"
    elif s >= 130 or d >= 80:
        cls = BPClassification.STAGE1
        desc = "Stage 1 hypertension — lifestyle changes + possible medication"
    elif 120 <= s <= 129 and d < 80:
        cls = BPClassification.ELEVATED
        desc = "Elevated blood pressure — lifestyle modifications recommended"
    else:
        cls = BPClassification.NORMAL
        desc = "Normal blood pressure — maintain healthy habits"

    pp = s - d
    map_ = d + (pp / 3)

    return BPClassificationResult(
        classification=cls,
        systolic=s,
        diastolic=d,
        pulse_pressure=round(pp, 1),
        mean_arterial_pressure=round(map_, 1),
        description=desc,
    )


# ── Pulse Pressure ───────────────────────────────────────────────────────────


def calculate_pulse_pressure(systolic: float, diastolic: float) -> float:
    """Pulse pressure = systolic - diastolic. Normal: 30-40 mmHg."""
    return round(systolic - diastolic, 1)


def interpret_pulse_pressure(pp: float) -> str:
    """Interpret pulse pressure value."""
    if pp < 25:
        return "Low pulse pressure — may indicate reduced cardiac output"
    elif pp <= 40:
        return "Normal pulse pressure"
    elif pp <= 60:
        return "Elevated pulse pressure — associated with arterial stiffness"
    else:
        return "Widened pulse pressure — significant arterial stiffness or aortic regurgitation"


# ── Mean Arterial Pressure ───────────────────────────────────────────────────


def calculate_map(systolic: float, diastolic: float) -> float:
    """MAP = diastolic + (systolic - diastolic) / 3. Normal: 70-100 mmHg."""
    return round(diastolic + (systolic - diastolic) / 3, 1)


def interpret_map(map_value: float) -> str:
    """Interpret MAP value."""
    if map_value < 60:
        return "Low MAP — inadequate organ perfusion"
    elif map_value <= 100:
        return "Normal MAP — adequate organ perfusion"
    else:
        return "Elevated MAP — increased cardiovascular risk"


# ── Trend Analysis ───────────────────────────────────────────────────────────


def analyze_trends(readings: Sequence[BPReading]) -> BPTrend | None:
    """Analyze BP trends across multiple readings."""
    if len(readings) < 3:
        return None

    systolics = [r.systolic for r in readings]
    diastolics = [r.diastolic for r in readings]

    mean_s = sum(systolics) / len(systolics)
    mean_d = sum(diastolics) / len(diastolics)

    # Simple linear trend: compare first half to second half
    mid = len(readings) // 2
    first_s = sum(systolics[:mid]) / mid
    second_s = sum(systolics[mid:]) / (len(systolics) - mid)
    first_d = sum(diastolics[:mid]) / mid
    second_d = sum(diastolics[mid:]) / (len(diastolics) - mid)

    diff_s = second_s - first_s
    diff_d = second_d - first_d

    def trend方向(diff: float) -> str:
        if diff > 3:
            return "rising"
        elif diff < -3:
            return "falling"
        return "stable"

    # Variance
    var_s = sum((x - mean_s) ** 2 for x in systolics) / len(systolics)
    var_d = sum((x - mean_d) ** 2 for x in diastolics) / len(diastolics)

    # Classification distribution
    dist: dict[str, int] = {}
    for r in readings:
        c = classify_reading(r)
        key = c.classification.value
        dist[key] = dist.get(key, 0) + 1

    return BPTrend(
        mean_systolic=round(mean_s, 1),
        mean_diastolic=round(mean_d, 1),
        systolic_trend=trend方向(diff_s),
        diastolic_trend=trend方向(diff_d),
        variability_systolic=round(var_s**0.5, 1),
        variability_diastolic=round(var_d**0.5, 1),
        reading_count=len(readings),
        classification_distribution=dist,
    )


# ── Risk Assessment ──────────────────────────────────────────────────────────


def assess_risk(
    readings: Sequence[BPReading],
    age: int = 40,
    has_diabetes: bool = False,
    has_ckd: bool = False,
    has_cardiovascular_history: bool = False,
) -> BPRiskAssessment:
    """Comprehensive CV risk assessment based on BP + risk factors."""
    if not readings:
        return BPRiskAssessment(
            overall_risk="low",
            risk_score=0,
            factors=["No readings available"],
            recommendation="Begin regular blood pressure monitoring",
        )

    latest = readings[-1]
    result = classify_reading(latest)
    factors: list[str] = []
    score = 0

    # Classification-based risk
    cls_scores = {
        BPClassification.NORMAL: 0,
        BPClassification.ELEVATED: 15,
        BPClassification.STAGE1: 35,
        BPClassification.STAGE2: 55,
        BPClassification.CRISIS: 90,
    }
    score += cls_scores[result.classification]
    if result.classification != BPClassification.NORMAL:
        factors.append(f"BP classification: {result.classification.value}")

    # Age risk
    if age > 65:
        score += 10
        factors.append("Age > 65")
    elif age > 55:
        score += 5

    # Comorbidities
    if has_diabetes:
        score += 10
        factors.append("Diabetes")
    if has_ckd:
        score += 10
        factors.append("Chronic kidney disease")
    if has_cardiovascular_history:
        score += 15
        factors.append("Cardiovascular disease history")

    # Pulse pressure
    pp = result.pulse_pressure
    if pp > 60:
        score += 10
        factors.append(f"Widened pulse pressure ({pp} mmHg)")

    # MAP
    if result.mean_arterial_pressure > 105:
        score += 5
        factors.append(f"Elevated MAP ({result.mean_arterial_pressure} mmHg)")

    # Trend
    trend = analyze_trends(readings)
    if trend and trend.systolic_trend == "rising":
        score += 10
        factors.append("Rising systolic trend")

    score = min(score, 100)

    if score >= 80:
        risk = "very_high"
        rec = "Urgent: consult a physician immediately. Medication adjustment likely needed."
    elif score >= 60:
        risk = "high"
        rec = "Schedule physician visit within 1-2 weeks. Lifestyle changes + medication review."
    elif score >= 30:
        risk = "moderate"
        rec = "Monitor regularly. Focus on lifestyle modifications: diet, exercise, sodium reduction."
    else:
        risk = "low"
        rec = "Continue healthy habits. Annual BP check recommended."

    return BPRiskAssessment(
        overall_risk=risk,
        risk_score=score,
        factors=factors,
        recommendation=rec,
    )

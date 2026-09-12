"""
Cardiovascular Analysis Service — Heart rate analysis, VO2 max estimation, risk assessment
Inspired by openhrv, athlete-injury-risk-detection
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field


class RiskLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class HeartRateZone:
    name: str
    min_bpm: float
    max_bpm: float
    zone_number: int
    description: str


@dataclass
class CardioAnalysis:
    resting_hr: float
    max_hr: float
    hr_reserve: float
    vo2_max_estimate: float
    zones: List[HeartRateZone]
    risk_level: RiskLevel
    fitness_score: float


class CardiovascularAnalyzer:
    """Pure function cardiovascular analysis."""

    @staticmethod
    def estimate_max_hr(age: int) -> float:
        return 220 - age

    @staticmethod
    def calculate_hr_reserve(resting_hr: float, max_hr: float) -> float:
        return max_hr - resting_hr

    @staticmethod
    def calculate_zones(resting_hr: float, max_hr: float) -> List[HeartRateZone]:
        reserve = max_hr - resting_hr
        return [
            HeartRateZone("Recovery", resting_hr + reserve * 0.5, resting_hr + reserve * 0.6, 1, "Light activity"),
            HeartRateZone("Aerobic", resting_hr + reserve * 0.6, resting_hr + reserve * 0.7, 2, "Cardio training"),
            HeartRateZone("Tempo", resting_hr + reserve * 0.7, resting_hr + reserve * 0.8, 3, "Threshold training"),
            HeartRateZone("Threshold", resting_hr + reserve * 0.8, resting_hr + reserve * 0.9, 4, "Hard effort"),
            HeartRateZone("Maximal", resting_hr + reserve * 0.9, max_hr, 5, "Sprint effort"),
        ]

    @staticmethod
    def estimate_vo2_max(resting_hr: float, age: int, sex: str = "male") -> float:
        if resting_hr <= 0:
            return 0.0
        max_hr = CardiovascularAnalyzer.estimate_max_hr(age)
        vo2 = 15.3 * (max_hr / resting_hr)
        if sex == "female":
            vo2 *= 0.87
        age_factor = 1 - (age - 20) * 0.005
        vo2 *= max(0.5, age_factor)
        return round(vo2, 1)

    @staticmethod
    def assess_risk(resting_hr: float, age: int, vo2_max: float,
                    has_conditions: bool = False) -> RiskLevel:
        score = 0
        if resting_hr > 80:
            score += 2
        elif resting_hr > 70:
            score += 1
        if vo2_max < 30:
            score += 3
        elif vo2_max < 40:
            score += 2
        elif vo2_max < 50:
            score += 1
        if age > 60:
            score += 1
        if has_conditions:
            score += 2
        if score >= 5:
            return RiskLevel.VERY_HIGH
        elif score >= 3:
            return RiskLevel.HIGH
        elif score >= 1:
            return RiskLevel.MODERATE
        return RiskLevel.LOW

    @staticmethod
    def calculate_fitness_score(resting_hr: float, vo2_max: float, age: int) -> float:
        hr_score = max(0, min(40, (80 - resting_hr) * 0.8))
        vo2_score = max(0, min(40, (vo2_max - 20) * 0.5))
        age_score = max(0, min(20, (60 - age) * 0.3))
        return round(hr_score + vo2_score + age_score, 1)

    @staticmethod
    def analyze_heart_rate_series(hr_values: List[float]) -> Dict:
        if not hr_values:
            return {"error": "No data"}
        avg = sum(hr_values) / len(hr_values)
        min_hr = min(hr_values)
        max_hr = max(hr_values)
        variance = sum((h - avg) ** 2 for h in hr_values) / len(hr_values)
        std_dev = math.sqrt(variance)
        rmssd_values = [hr_values[i] - hr_values[i-1] for i in range(1, len(hr_values))]
        rmssd = math.sqrt(sum(d ** 2 for d in rmssd_values) / len(rmssd_values)) if rmssd_values else 0
        return {
            "average_hr": round(avg, 1),
            "min_hr": round(min_hr, 1),
            "max_hr": round(max_hr, 1),
            "std_dev": round(std_dev, 2),
            "rmssd": round(rmssd, 2),
            "sample_count": len(hr_values),
        }

    @classmethod
    def full_analysis(cls, resting_hr: float, age: int, sex: str = "male",
                     hr_values: Optional[List[float]] = None) -> CardioAnalysis:
        max_hr = cls.estimate_max_hr(age)
        hr_reserve = cls.calculate_hr_reserve(resting_hr, max_hr)
        vo2_max = cls.estimate_vo2_max(resting_hr, age, sex)
        zones = cls.calculate_zones(resting_hr, max_hr)
        risk = cls.assess_risk(resting_hr, age, vo2_max)
        fitness = cls.calculate_fitness_score(resting_hr, vo2_max, age)
        return CardioAnalysis(
            resting_hr=resting_hr,
            max_hr=max_hr,
            hr_reserve=hr_reserve,
            vo2_max_estimate=vo2_max,
            zones=zones,
            risk_level=risk,
            fitness_score=fitness,
        )


# ── Endpoint-facing API ──────────────────────────────────────────────────────
# The endpoints speak in zone-name-keyed ranges and JSON-ready dicts, while the
# analyser works in HeartRateZone objects. These helpers are that boundary.

class HRVReading(BaseModel):
    """One HRV reading as reported by a wearable."""
    model_config = {"extra": "ignore"}

    timestamp: Optional[str] = None
    hrv_rmssd: float = Field(default=0.0, ge=0, le=300)
    heart_rate: Optional[float] = Field(default=None, ge=20, le=250)


class CVRiskProfile(BaseModel):
    """Cardiovascular risk profile across measured and reported factors."""
    cardiovascular_risk_score: int
    risk_category: str
    vo2_max_estimate: float
    hr_zones: Dict[str, Tuple[float, float]]
    max_heart_rate: float
    heart_rate_reserve: float
    recommendations: List[str]


def max_hr_from_age(age: int) -> float:
    """Age-predicted maximum heart rate."""
    return CardiovascularAnalyzer.estimate_max_hr(age)


def _zones_as_ranges(resting_hr: float, max_hr: float) -> Dict[str, Tuple[float, float]]:
    return {
        zone.name.lower(): (round(zone.min_bpm, 1), round(zone.max_bpm, 1))
        for zone in CardiovascularAnalyzer.calculate_zones(resting_hr, max_hr)
    }


def calculate_hr_zones(resting_hr: float, max_hr: float) -> Dict[str, Tuple[float, float]]:
    """Heart rate training zones, as name-keyed (min, max) bpm ranges."""
    return _zones_as_ranges(resting_hr, max_hr)


def classify_hr_zone(bpm: float, zones: Dict[str, Tuple[float, float]]) -> str:
    """Name of the zone a heart rate falls in; the highest one starts above it."""
    for name, (low, high) in zones.items():
        if low <= bpm <= high:
            return name
    if zones:
        highest = max(zones.items(), key=lambda item: item[1][1])
        if bpm > highest[1][1]:
            return highest[0]
        lowest = min(zones.items(), key=lambda item: item[1][0])
        if bpm < lowest[1][0]:
            return "below_" + lowest[0]
    return "unknown"


def analyze_hrv(readings: List[HRVReading]) -> Dict:
    """Summarise a series of HRV readings into a cardiovascular picture."""
    values = [r.hrv_rmssd for r in readings if r.hrv_rmssd > 0]
    if not values:
        return {
            "reading_count": len(readings),
            "error": "No positive HRV values to analyse",
        }

    mean_rmssd = sum(values) / len(values)
    variance = sum((v - mean_rmssd) ** 2 for v in values) / len(values)
    std_dev = math.sqrt(variance)

    half = max(1, len(values) // 2)
    first_half = sum(values[:half]) / half
    last_half = sum(values[half:]) / (len(values) - half) if len(values) > half else first_half
    change = last_half - first_half
    if change > 2:
        direction = "improving"
    elif change < -2:
        direction = "declining"
    else:
        direction = "stable"

    heart_rates = [r.heart_rate for r in readings if r.heart_rate]
    avg_hr = sum(heart_rates) / len(heart_rates) if heart_rates else None

    if mean_rmssd < 20:
        level, interpretation = "low", (
            "Low HRV — often reflects fatigue, stress or incomplete recovery."
        )
    elif mean_rmssd < 50:
        level, interpretation = "normal", "HRV is within the usual adult range."
    else:
        level, interpretation = "high", "High HRV — generally indicates good recovery capacity."

    return {
        "reading_count": len(values),
        "mean_rmssd": round(mean_rmssd, 1),
        "min_rmssd": round(min(values), 1),
        "max_rmssd": round(max(values), 1),
        "std_dev_rmssd": round(std_dev, 2),
        "avg_heart_rate": round(avg_hr, 1) if avg_hr else None,
        "trend": direction,
        "change_rmssd": round(change, 1),
        "level": level,
        "interpretation": interpretation,
    }


def calculate_cv_risk(
    age: int,
    resting_hr: int,
    avg_hrv: float,
    systolic_bp: Optional[int] = None,
    smoker: bool = False,
    diabetic: bool = False,
    family_history: bool = False,
) -> CVRiskProfile:
    """Cardiovascular risk score from vitals plus reported risk factors."""
    analyzer = CardiovascularAnalyzer
    max_hr = analyzer.estimate_max_hr(age)
    hr_reserve = analyzer.calculate_hr_reserve(resting_hr, max_hr)
    vo2_max = analyzer.estimate_vo2_max(resting_hr, age)
    zones = _zones_as_ranges(resting_hr, max_hr)

    has_conditions = smoker or diabetic or family_history
    base_risk = analyzer.assess_risk(resting_hr, age, vo2_max, has_conditions)

    # The analyser grades the vitals; the reported factors and blood pressure
    # then move the score within that frame.
    category_scores = {"low": 15, "moderate": 40, "high": 65, "very_high": 85}
    score = category_scores[base_risk.value]
    recommendations: List[str] = []

    if resting_hr > 80:
        score += 5
        recommendations.append("Resting heart rate is elevated — build aerobic base with easy sessions.")
    if vo2_max < 35:
        score += 5
        recommendations.append("VO2 max is below average — add two interval sessions a week.")
    if systolic_bp is not None and systolic_bp >= 130:
        score += 10
        recommendations.append("Systolic blood pressure is raised — reduce sodium and monitor weekly.")
    if avg_hrv < 20:
        score += 5
        recommendations.append("HRV is low — prioritise sleep and ease training load until it recovers.")
    if smoker:
        score += 10
        recommendations.append("Smoking is the single largest modifiable cardiovascular risk factor.")
    if diabetic:
        score += 8
        recommendations.append("Diabetes raises cardiovascular risk — keep HbA1c in the target range.")
    if family_history:
        score += 5
        recommendations.append("Family history warrants earlier and more frequent screening.")

    score = max(0, min(100, score))
    if score >= 80:
        category = "very_high"
    elif score >= 60:
        category = "high"
    elif score >= 30:
        category = "moderate"
    else:
        category = "low"
    if not recommendations:
        recommendations.append("All measured factors are in a healthy range — maintain current habits.")

    return CVRiskProfile(
        cardiovascular_risk_score=score,
        risk_category=category,
        vo2_max_estimate=vo2_max,
        hr_zones=zones,
        max_heart_rate=max_hr,
        heart_rate_reserve=hr_reserve,
        recommendations=recommendations,
    )


def ecg_to_hrv(signal: List[float], sampling_rate: int = 250) -> Dict:
    """Detect R-peaks in a raw ECG signal and derive heart rate and HRV."""
    from app.services.biosignal_analysis import detect_r_peaks_simple

    if sampling_rate <= 0:
        return {"error": "Sampling rate must be positive"}
    if len(signal) < 10:
        return {"error": "Signal is too short to detect R-peaks"}

    peaks = detect_r_peaks_simple(signal, float(sampling_rate))
    if len(peaks) < 2:
        return {"error": "Fewer than two R-peaks detected in the signal"}

    rr_intervals_ms = [
        (peaks[i] - peaks[i - 1]) / sampling_rate * 1000.0
        for i in range(1, len(peaks))
    ]
    mean_rr = sum(rr_intervals_ms) / len(rr_intervals_ms)
    heart_rate = 60_000.0 / mean_rr if mean_rr > 0 else 0.0

    successive = [rr_intervals_ms[i] - rr_intervals_ms[i - 1] for i in range(1, len(rr_intervals_ms))]
    rmssd = (
        math.sqrt(sum(d ** 2 for d in successive) / len(successive))
        if successive else 0.0
    )

    return {
        "r_peak_count": len(peaks),
        "r_peak_indices": peaks,
        "rr_intervals_ms": [round(rr, 1) for rr in rr_intervals_ms],
        "heart_rate_bpm": round(heart_rate, 1),
        "mean_rr_ms": round(mean_rr, 1),
        "rmssd_ms": round(rmssd, 1),
        "sdnn_ms": round(
            math.sqrt(
                sum((rr - mean_rr) ** 2 for rr in rr_intervals_ms) / len(rr_intervals_ms)
            ),
            1,
        ),
        "duration_seconds": round(len(signal) / sampling_rate, 2),
    }

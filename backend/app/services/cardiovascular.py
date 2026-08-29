"""
Cardiovascular Analysis Engine

Provides HRV analysis, heart rate zone classification, cardiovascular risk
scoring, and ECG signal processing. Designed for integration with wearable
sensor data (heart rate, HRV, SpO2, blood pressure).
"""
from dataclasses import dataclass, field
from typing import Optional
import math
import statistics


@dataclass
class HRVReading:
    """Single HRV measurement."""
    timestamp: str
    hrv_rmssd: float  # RMSSD in ms
    heart_rate: int   # BPM
    spO2: Optional[float] = None  # Blood oxygen percentage
    stress_index: Optional[float] = None


@dataclass
class CardiovascularProfile:
    """Aggregated cardiovascular profile for a user."""
    avg_hrv: float
    resting_heart_rate: int
    max_heart_rate: int
    heart_rate_reserve: int
    vo2_max_estimate: float
    cardiovascular_risk_score: float  # 0-100 (lower is better)
    risk_category: str  # "low", "moderate", "elevated", "high"
    hr_zones: dict  # zone name -> (min_bpm, max_bpm)
    hrv_trend: str  # "improving", "stable", "declining"
    recommendations: list[str] = field(default_factory=list)


# Heart rate zones (Karvonen method)
def calculate_hr_zones(resting_hr: int, max_hr: int) -> dict:
    """Calculate heart rate training zones using Karvonen formula."""
    hrr = max_hr - resting_hr  # Heart rate reserve
    return {
        "rest":        (resting_hr,                      resting_hr + int(0.50 * hrr)),
        "easy":        (resting_hr + int(0.50 * hrr) + 1, resting_hr + int(0.60 * hrr)),
        "aerobic":     (resting_hr + int(0.60 * hrr) + 1, resting_hr + int(0.70 * hrr)),
        "tempo":       (resting_hr + int(0.70 * hrr) + 1, resting_hr + int(0.80 * hrr)),
        "threshold":   (resting_hr + int(0.80 * hrr) + 1, resting_hr + int(0.90 * hrr)),
        "vo2max":      (resting_hr + int(0.90 * hrr) + 1, max_hr),
    }


def classify_hr_zone(bpm: int, zones: dict) -> str:
    """Classify a heart rate value into a training zone."""
    for zone_name, (lo, hi) in zones.items():
        if lo <= bpm <= hi:
            return zone_name
    return "unknown"


# HRV Analysis
def analyze_hrv(readings: list[HRVReading]) -> dict:
    """Analyze HRV readings for cardiovascular health indicators."""
    if not readings:
        return {"error": "No readings provided"}

    hrv_values = [r.hrv_rmssd for r in readings]
    hr_values = [r.heart_rate for r in readings]

    avg_hrv = statistics.mean(hrv_values)
    std_hrv = statistics.stdev(hrv_values) if len(hrv_values) > 1 else 0
    min_hrv = min(hrv_values)
    max_hrv = max(hrv_values)

    # HRV trend (simple linear regression slope)
    if len(hrv_values) >= 3:
        n = len(hrv_values)
        x_vals = list(range(n))
        x_mean = statistics.mean(x_vals)
        y_mean = statistics.mean(hrv_values)
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, hrv_values))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)
        slope = numerator / denominator if denominator > 0 else 0
        trend = "improving" if slope > 0.5 else "declining" if slope < -0.5 else "stable"
    else:
        slope = 0
        trend = "stable"

    # Stress index (lower HRV = higher stress)
    stress_score = max(0, min(100, 100 - (avg_hrv / 1.5)))

    return {
        "avg_hrv_rmssd": round(avg_hrv, 1),
        "std_hrv_rmssd": round(std_hrv, 1),
        "min_hrv": round(min_hrv, 1),
        "max_hrv": round(max_hrv, 1),
        "avg_heart_rate": round(statistics.mean(hr_values)),
        "resting_heart_rate": round(statistics.percentile(hr_values, 10)),
        "hrv_trend": trend,
        "hrv_slope": round(slope, 3),
        "stress_score": round(stress_score, 1),
        "reading_count": len(readings),
    }


# VO2 Max estimation (Uth formula)
def estimate_vo2_max(resting_hr: int, age: int) -> float:
    """Estimate VO2 max from resting heart rate and age (Uth et al.)."""
    if resting_hr <= 0 or age <= 0:
        return 0.0
    return round(15.3 * (max_hr_from_age(age) / resting_hr), 1)


def max_hr_from_age(age: int) -> int:
    """Predicted max heart rate (Tanaka formula, more accurate than 220-age)."""
    return round(208 - 0.7 * age)


# Cardiovascular risk scoring
def calculate_cv_risk(
    age: int,
    resting_hr: int,
    avg_hrv: float,
    systolic_bp: Optional[int] = None,
    smoker: bool = False,
    diabetic: bool = False,
    family_history: bool = False,
) -> CardiovascularProfile:
    """
    Calculate cardiovascular risk score based on multiple factors.

    Scoring:
    - Age: +1 per year over 40 (max 30)
    - Resting HR: +0.5 per bpm over 70 (max 20)
    - HRV: +0.3 per ms below 50 (max 20)
    - BP: +1 per mmHg over 130 (max 15)
    - Risk factors: +5 each (max 15)
    """
    max_hr = max_hr_from_age(age)
    hrr = max_hr - resting_hr

    score = 0

    # Age factor
    if age > 40:
        score += min(30, (age - 40) * 1)

    # Resting HR factor
    if resting_hr > 70:
        score += min(20, (resting_hr - 70) * 0.5)

    # HRV factor (low HRV = higher risk)
    if avg_hrv < 50:
        score += min(20, (50 - avg_hrv) * 0.3)

    # Blood pressure factor
    if systolic_bp and systolic_bp > 130:
        score += min(15, (systolic_bp - 130) * 1)

    # Risk factors
    risk_factors = sum([smoker, diabetic, family_history])
    score += min(15, risk_factors * 5)

    score = min(100, max(0, score))

    if score < 25:
        category = "low"
    elif score < 50:
        category = "moderate"
    elif score < 75:
        category = "elevated"
    else:
        category = "high"

    zones = calculate_hr_zones(resting_hr, max_hr)
    vo2 = estimate_vo2_max(resting_hr, age)

    recommendations = []
    if resting_hr > 80:
        recommendations.append("Resting heart rate is elevated. Consider aerobic exercise 3-5x/week.")
    if avg_hrv < 30:
        recommendations.append("HRV is low. Focus on sleep quality and stress management.")
    if age > 50:
        recommendations.append("Annual cardiac screening recommended after age 50.")
    if smoker:
        recommendations.append("Smoking significantly increases cardiovascular risk. Cessation is the single biggest modifiable factor.")
    if not recommendations:
        recommendations.append("Cardiovascular health looks good. Maintain current activity level.")

    return CardiovascularProfile(
        avg_hrv=avg_hrv,
        resting_heart_rate=resting_hr,
        max_heart_rate=max_hr,
        heart_rate_reserve=hrr,
        vo2_max_estimate=vo2,
        cardiovascular_risk_score=round(score, 1),
        risk_category=category,
        hr_zones=zones,
        hrv_trend="stable",
        recommendations=recommendations,
    )


# ECG signal processing (simplified R-peak detection)
def detect_r_peaks(signal: list[float], sampling_rate: int = 250) -> list[int]:
    """
    Simple R-peak detection using adaptive thresholding.
    For production use, consider Pan-Tompkins algorithm.
    """
    if not signal or len(signal) < sampling_rate:
        return []

    # Moving average for baseline
    window = sampling_rate // 10  # 100ms window
    baseline = []
    for i in range(len(signal)):
        start = max(0, i - window)
        baseline.append(sum(signal[start:i + 1]) / (i - start + 1))

    # Detrend
    detrended = [s - b for s, b in zip(signal, baseline)]

    # Adaptive threshold
    threshold = statistics.mean([abs(d) for d in detrended[:sampling_rate]]) * 1.5

    # Find peaks
    r_peaks = []
    min_distance = sampling_rate // 3  # Minimum 200ms between beats
    last_peak = -min_distance

    for i in range(1, len(detrended) - 1):
        if (detrended[i] > detrended[i - 1] and
            detrended[i] > detrended[i + 1] and
            detrended[i] > threshold and
            i - last_peak >= min_distance):
            r_peaks.append(i)
            last_peak = i

    return r_peaks


def compute_rr_intervals(r_peaks: list[int], sampling_rate: int) -> list[float]:
    """Compute RR intervals (time between consecutive heartbeats) in milliseconds."""
    if len(r_peaks) < 2:
        return []
    return [(r_peaks[i + 1] - r_peaks[i]) / sampling_rate * 1000 for i in range(len(r_peaks) - 1)]


def ecg_to_hrv(signal: list[float], sampling_rate: int = 250) -> dict:
    """Full ECG → HRV pipeline: detect R-peaks → compute RR intervals → analyze HRV."""
    r_peaks = detect_r_peaks(signal, sampling_rate)
    rr_intervals = compute_rr_intervals(r_peaks, sampling_rate)

    if not rr_intervals:
        return {"error": "No R-peaks detected", "r_peak_count": 0}

    hrv_rmssd = math.sqrt(sum((rr_intervals[i + 1] - rr_intervals[i]) ** 2
                              for i in range(len(rr_intervals) - 1)) / max(1, len(rr_intervals) - 1))

    avg_rr = statistics.mean(rr_intervals)
    heart_rate = round(60000 / avg_rr) if avg_rr > 0 else 0

    return {
        "r_peak_count": len(r_peaks),
        "avg_rr_interval_ms": round(avg_rr, 1),
        "hrv_rmssd_ms": round(hrv_rmssd, 1),
        "estimated_heart_rate": heart_rate,
        "signal_quality": "good" if len(r_peaks) > sampling_rate * 5 else "short_recording",
    }

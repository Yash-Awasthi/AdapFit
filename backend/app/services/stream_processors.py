"""
Stream Processors — Real-time processing for health data streams.

Processors for heart rate, activity, sleep, and stress streams.
Each processor takes raw data points and outputs enriched metrics.
All pure functions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from app.services.realtime_pipeline import DataPoint, StreamType


# ---------------------------------------------------------------------------
# Heart Rate Processor
# ---------------------------------------------------------------------------

class HRZone(str, Enum):
    REST = "rest"          # < 60% max HR
    WARM_UP = "warm_up"    # 60-70%
    FAT_BURN = "fat_burn"  # 70-80%
    CARDIO = "cardio"      # 80-90%
    PEAK = "peak"          # 90-100%


@dataclass
class HRMetrics:
    """Processed heart rate metrics."""
    current_bpm: float
    zone: HRZone
    zone_name: str
    resting_hr: float
    max_hr: float
    hr_reserve: float  # max - resting
    pct_max: float
    hrv_rmssd: float
    arrhythmia_detected: bool
    recovery_status: str  # "recovered", "recovering", "elevated"


def classify_hr_zone(bpm: float, max_hr: float = 190) -> HRZone:
    """Classify heart rate into training zones."""
    pct = bpm / max_hr
    if pct < 0.6:
        return HRZone.REST
    elif pct < 0.7:
        return HRZone.WARM_UP
    elif pct < 0.8:
        return HRZone.FAT_BURN
    elif pct < 0.9:
        return HRZone.CARDIO
    else:
        return HRZone.PEAK


def calculate_hrv_rmssd(rr_intervals_ms: List[float]) -> float:
    """
    Calculate HRV using RMSSD (Root Mean Square of Successive Differences).
    
    RMSSD is the primary time-domain measure of HRV, reflecting
    parasympathetic nervous system activity.
    """
    if len(rr_intervals_ms) < 2:
        return 0.0
    
    successive_diffs = [
        (rr_intervals_ms[i] - rr_intervals_ms[i - 1]) ** 2
        for i in range(1, len(rr_intervals_ms))
    ]
    
    mean_sq_diff = sum(successive_diffs) / len(successive_diffs)
    return round(math.sqrt(mean_sq_diff), 2)


def detect_arrhythmia(
    rr_intervals_ms: List[float],
    threshold_premature: float = 0.8,
    threshold_late: float = 1.2,
) -> bool:
    """
    Simple arrhythmia detection based on RR interval irregularity.
    
    Detects premature beats (significantly shorter RR) and
    late beats (significantly longer RR) compared to local average.
    """
    if len(rr_intervals_ms) < 5:
        return False
    
    for i in range(2, len(rr_intervals_ms) - 2):
        # Local average (excluding current)
        local_avg = sum(rr_intervals_ms[i-2:i] + rr_intervals_ms[i+1:i+3]) / 4
        
        if local_avg > 0:
            ratio = rr_intervals_ms[i] / local_avg
            if ratio < threshold_premature or ratio > threshold_late:
                return True
    
    return False


def process_hr_stream(
    current_bpm: float,
    rr_intervals_ms: Optional[List[float]] = None,
    max_hr: float = 190,
    resting_hr: float = 60,
) -> HRMetrics:
    """Process a heart rate data point into enriched metrics."""
    zone = classify_hr_zone(current_bpm, max_hr)
    pct_max = (current_bpm / max_hr * 100) if max_hr > 0 else 0
    hr_reserve = max_hr - resting_hr
    
    hrv = calculate_hrv_rmssd(rr_intervals_ms or [])
    arrhythmia = detect_arrhythmia(rr_intervals_ms or [])
    
    # Recovery status based on resting HR comparison
    if current_bpm <= resting_hr * 1.1:
        recovery = "recovered"
    elif current_bpm <= resting_hr * 1.3:
        recovery = "recovering"
    else:
        recovery = "elevated"
    
    return HRMetrics(
        current_bpm=round(current_bpm, 1),
        zone=zone,
        zone_name=zone.value,
        resting_hr=resting_hr,
        max_hr=max_hr,
        hr_reserve=hr_reserve,
        pct_max=round(pct_max, 1),
        hrv_rmssd=hrv,
        arrhythmia_detected=arrhythmia,
        recovery_status=recovery,
    )


# ---------------------------------------------------------------------------
# Activity Processor
# ---------------------------------------------------------------------------

@dataclass
class ActivityMetrics:
    """Processed activity metrics."""
    steps: int
    distance_km: float
    calories: float
    active_minutes: int
    intensity: str  # "sedentary", "light", "moderate", "vigorous"
    pace_min_km: float  # minutes per km
    floors_climbed: int


def estimate_distance_km(steps: int, stride_length_m: float = 0.75) -> float:
    """Estimate distance from step count."""
    return round(steps * stride_length_m / 1000, 2)


def estimate_calories(
    steps: int,
    weight_kg: float = 70,
    height_cm: float = 170,
    age: int = 30,
) -> float:
    """Estimate calorie burn from steps using MET-based calculation."""
    # MET for walking ~3.5
    met = 3.5
    hours = steps / 15000  # Rough: 15000 steps/hour brisk walking
    calories = met * weight_kg * hours
    return round(calories, 1)


def classify_intensity(
    steps_per_minute: float,
    heart_rate: Optional[float] = None,
    max_hr: float = 190,
) -> str:
    """Classify activity intensity from step rate and optional HR."""
    if steps_per_minute < 1:
        return "sedentary"
    elif steps_per_minute < 100:
        return "light"
    elif steps_per_minute < 130:
        return "moderate"
    else:
        return "vigorous"


def process_activity_stream(
    steps: int,
    duration_seconds: float,
    weight_kg: float = 70,
    stride_length_m: float = 0.75,
) -> ActivityMetrics:
    """Process activity data into enriched metrics."""
    distance = estimate_distance_km(steps, stride_length_m)
    calories = estimate_calories(steps, weight_kg)
    
    active_minutes = int(duration_seconds / 60) if steps > 0 else 0
    
    steps_per_min = steps / (duration_seconds / 60) if duration_seconds > 0 else 0
    intensity = classify_intensity(steps_per_min)
    
    pace = (duration_seconds / 60 / distance) if distance > 0 else 0
    
    return ActivityMetrics(
        steps=steps,
        distance_km=distance,
        calories=calories,
        active_minutes=active_minutes,
        intensity=intensity,
        pace_min_km=round(pace, 1),
        floors_climbed=0,
    )


# ---------------------------------------------------------------------------
# Sleep Stream Processor
# ---------------------------------------------------------------------------

class SleepStageState(str, Enum):
    AWAKE = "awake"
    LIGHT = "light"
    DEEP = "deep"
    REM = "rem"


@dataclass
class SleepStreamMetrics:
    """Processed sleep stream metrics."""
    current_stage: SleepStageState
    time_in_stage_minutes: float
    movement_count: int
    breathing_rate: float
    sleep_quality_score: float  # 0-100
    estimated_time_to_fall_asleep: float  # minutes


def classify_sleep_stage_from_motion(
    movement_intensity: float,
    heart_rate: float,
    hr_variability: float,
) -> SleepStageState:
    """
    Classify sleep stage from motion and physiological signals.
    
    Simplified rule-based classification:
    - High movement or elevated HR → awake
    - Low movement, low HR, low HRV → deep sleep
    - Low movement, moderate HR, high HRV → REM
    - Low movement, moderate HR → light sleep
    """
    if movement_intensity > 0.5 or heart_rate > 80:
        return SleepStageState.AWAKE
    
    if movement_intensity < 0.1 and heart_rate < 55 and hr_variability > 40:
        return SleepStageState.DEEP
    
    if movement_intensity < 0.15 and hr_variability > 50:
        return SleepStageState.REM
    
    return SleepStageState.LIGHT


def calculate_sleep_quality_score(
    total_sleep_minutes: float,
    deep_pct: float,
    rem_pct: float,
    awakenings: int,
    sleep_latency_minutes: float,
) -> float:
    """
    Calculate sleep quality score (0-100).
    
    Factors: duration, deep sleep %, REM %, awakenings, latency.
    """
    # Duration score (optimal: 420-540 minutes)
    if 420 <= total_sleep_minutes <= 540:
        dur_score = 100
    elif 360 <= total_sleep_minutes < 420:
        dur_score = 75
    elif 540 < total_sleep_minutes <= 600:
        dur_score = 85
    else:
        dur_score = max(0, 50 - abs(total_sleep_minutes - 480) / 10)
    
    # Deep sleep score (optimal: 15-25%)
    deep_score = max(0, 100 - abs(deep_pct - 20) * 5)
    
    # REM score (optimal: 20-30%)
    rem_score = max(0, 100 - abs(rem_pct - 25) * 4)
    
    # Awakening penalty
    awaken_penalty = min(30, awakenings * 5)
    
    # Latency penalty (optimal: < 20 minutes)
    latency_penalty = min(20, max(0, sleep_latency_minutes - 20))
    
    score = dur_score * 0.3 + deep_score * 0.25 + rem_score * 0.25 + \
            (100 - awaken_penalty) * 0.1 + (100 - latency_penalty) * 0.1
    
    return round(min(100, max(0, score)), 1)


def process_sleep_stream(
    movement_intensity: float,
    heart_rate: float,
    hr_variability: float,
    duration_in_stage_minutes: float = 0,
) -> SleepStreamMetrics:
    """Process sleep data point."""
    stage = classify_sleep_stage_from_motion(movement_intensity, heart_rate, hr_variability)
    
    return SleepStreamMetrics(
        current_stage=stage,
        time_in_stage_minutes=duration_in_stage_minutes,
        movement_count=0,
        breathing_rate=round(heart_rate / 10, 1),  # Rough estimate
        sleep_quality_score=0,  # Computed at session end
        estimated_time_to_fall_asleep=0,
    )


# ---------------------------------------------------------------------------
# Stress Stream Processor
# ---------------------------------------------------------------------------

class StressLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class StressMetrics:
    """Processed stress metrics."""
    stress_level: StressLevel
    stress_score: float  # 0-100
    hrv_indicator: float
    is_recovery_detected: bool
    recommended_action: str


def calculate_stress_score(
    hrv_rmssd: float,
    resting_hr: float,
    breathing_rate: float,
    baseline_hrv: float = 40,
    baseline_rhr: float = 65,
) -> float:
    """
    Calculate stress score from physiological signals.
    
    Higher HRV = lower stress. Higher resting HR = higher stress.
    """
    # HRV component (higher is better → lower stress)
    hrv_factor = max(0, 100 - (baseline_hrv - hrv_rmssd) * 2)
    
    # Resting HR component
    rhr_factor = max(0, 100 - (resting_hr - baseline_rhr) * 3)
    
    # Breathing rate component (optimal: 12-20 breaths/min)
    br_factor = max(0, 100 - abs(breathing_rate - 16) * 5)
    
    stress = 100 - (hrv_factor * 0.5 + rhr_factor * 0.3 + br_factor * 0.2)
    return round(min(100, max(0, stress)), 1)


def classify_stress_level(score: float) -> StressLevel:
    """Classify stress level from score."""
    if score < 25:
        return StressLevel.LOW
    elif score < 50:
        return StressLevel.MODERATE
    elif score < 75:
        return StressLevel.HIGH
    else:
        return StressLevel.VERY_HIGH


def detect_recovery(
    hrv_trend: List[float],  # Recent HRV readings
    hr_trend: List[float],   # Recent HR readings
    window: int = 10,
) -> bool:
    """
    Detect if the body is entering recovery state.
    
    Recovery = increasing HRV + decreasing HR over recent window.
    """
    if len(hrv_trend) < window or len(hr_trend) < window:
        return False
    
    recent_hrv = hrv_trend[-window:]
    recent_hr = hr_trend[-window:]
    
    # Simple trend: average of second half vs first half
    mid = window // 2
    hrv_first = sum(recent_hrv[:mid]) / mid
    hrv_second = sum(recent_hrv[mid:]) / (window - mid)
    hr_first = sum(recent_hr[:mid]) / mid
    hr_second = sum(recent_hr[mid:]) / (window - mid)
    
    return hrv_second > hrv_first and hr_second < hr_first


def process_stress_stream(
    hrv_rmssd: float,
    resting_hr: float,
    breathing_rate: float,
    hrv_trend: Optional[List[float]] = None,
    hr_trend: Optional[List[float]] = None,
) -> StressMetrics:
    """Process stress data point."""
    score = calculate_stress_score(hrv_rmssd, resting_hr, breathing_rate)
    level = classify_stress_level(score)
    recovery = detect_recovery(hrv_trend or [], hr_trend or [])
    
    actions = {
        StressLevel.LOW: "Maintain current state. Good time for focused work.",
        StressLevel.MODERATE: "Consider a short break. Deep breathing can help.",
        StressLevel.HIGH: "Take a 10-minute break. Practice mindfulness.",
        StressLevel.VERY_HIGH: "Stop current activity. Rest and hydrate immediately.",
    }
    
    return StressMetrics(
        stress_level=level,
        stress_score=score,
        hrv_indicator=round(hrv_rmssd, 1),
        is_recovery_detected=recovery,
        recommended_action=actions[level],
    )

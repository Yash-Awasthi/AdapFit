"""Garmin Data Analyzer Service.

Extracted from claude-garmin-ai-trainer (inspiration).
Garmin health data analysis: HRV metrics, training load,
body battery, sleep analysis, and readiness assessment.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Any


class ReadinessLevel(Enum):
    OPTIMAL = "optimal"
    GOOD = "good"
    MODERATE = "moderate"
    LOW = "low"
    POOR = "poor"


class TrainingIntensity(Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    REST = "rest"


class WorkoutType(Enum):
    ENDURANCE = "endurance"
    TEMPO = "tempo"
    INTERVAL = "interval"
    RECOVERY = "recovery"
    REST = "rest"
    STRENGTH = "strength"


class HRVStatus(Enum):
    BALANCED = "balanced"
    UNBALANCED = "unbalanced"
    LOW = "low"
    HIGH = "high"
    POOR = "poor"


class SleepQuality(Enum):
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


@dataclass
class DailyMetrics:
    metric_date: date
    steps: int = 0
    distance_meters: float = 0.0
    calories: int = 0
    active_minutes: int = 0
    floors_climbed: int = 0
    resting_heart_rate: int | None = None
    max_heart_rate: int | None = None
    avg_heart_rate: int | None = None
    hrv_sdnn: float | None = None
    hrv_rmssd: float | None = None
    stress_score: int | None = None
    body_battery_charged: int | None = None
    body_battery_drained: int | None = None
    body_battery_max: int | None = None
    body_battery_min: int | None = None
    sleep_score: int | None = None
    total_sleep_minutes: int | None = None
    deep_sleep_minutes: int | None = None
    light_sleep_minutes: int | None = None
    rem_sleep_minutes: int | None = None
    awake_minutes: int | None = None
    vo2_max: float | None = None
    weight_kg: float | None = None
    body_fat_percent: float | None = None


@dataclass
class ReadinessAssessment:
    level: ReadinessLevel
    score: float  # 0-100
    hrv_status: HRVStatus
    sleep_quality: SleepQuality
    training_load_recommendation: TrainingIntensity
    recovery_days_needed: int
    insights: list[str] = field(default_factory=list)
    acwr: float = 1.0
    form_score: float = 0.0  # TSB


@dataclass
class TrainingLoadMetrics:
    acute_load: float  # 7-day average
    chronic_load: float  # 28-day average
    acwr: float  # acute:chronic workload ratio
    trend: str  # "increasing", "stable", "decreasing"
    risk_level: str  # "low", "moderate", "high", "very_high"


def calculate_hrv_status(current_hrv: float, baseline_7d: float, baseline_30d: float) -> HRVStatus:
    """Classify HRV status relative to baselines."""
    if current_hrv is None or baseline_7d is None:
        return HRVStatus.UNBALANCED
    pct_of_7d = current_hrv / baseline_7d if baseline_7d > 0 else 1.0
    if pct_of_7d > 1.2:
        return HRVStatus.HIGH
    elif pct_of_7d > 0.9:
        return HRVStatus.BALANCED
    elif pct_of_7d > 0.7:
        return HRVStatus.UNBALANCED
    else:
        return HRVStatus.LOW


def classify_sleep_quality(sleep_score: int | None, deep_pct: float = 0.0) -> SleepQuality:
    """Classify sleep quality from score and deep sleep percentage."""
    if sleep_score is None:
        return SleepQuality.FAIR
    if sleep_score >= 85 and deep_pct >= 0.15:
        return SleepQuality.EXCELLENT
    elif sleep_score >= 70:
        return SleepQuality.GOOD
    elif sleep_score >= 50:
        return SleepQuality.FAIR
    else:
        return SleepQuality.POOR


def calculate_training_load(metrics_list: list[DailyMetrics]) -> TrainingLoadMetrics:
    """Calculate training load metrics from daily data."""
    if len(metrics_list) < 7:
        return TrainingLoadMetrics(0, 0, 1.0, "stable", "low")
    loads = []
    for m in metrics_list:
        load = 0
        if m.active_minutes:
            load += m.active_minutes * 0.5
        if m.calories:
            load += m.calories * 0.01
        if m.avg_heart_rate and m.resting_heart_rate:
            hr_load = (m.avg_heart_rate - m.resting_heart_rate) * 0.1
            load += max(0, hr_load)
        loads.append(load)
    acute = statistics.mean(loads[-7:]) if len(loads) >= 7 else statistics.mean(loads)
    chronic = statistics.mean(loads[-28:]) if len(loads) >= 28 else statistics.mean(loads)
    acwr = acute / chronic if chronic > 0 else 1.0
    if len(loads) >= 14:
        recent = statistics.mean(loads[-7:])
        previous = statistics.mean(loads[-14:-7])
        if recent > previous * 1.1:
            trend = "increasing"
        elif recent < previous * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "stable"
    if acwr > 1.5:
        risk = "very_high"
    elif acwr > 1.2:
        risk = "high"
    elif acwr > 0.8:
        risk = "moderate"
    else:
        risk = "low"
    return TrainingLoadMetrics(
        acute_load=round(acute, 1), chronic_load=round(chronic, 1),
        acwr=round(acwr, 2), trend=trend, risk_level=risk,
    )


def calculate_body_battery_trend(metrics_list: list[DailyMetrics]) -> dict[str, Any]:
    """Analyze body battery trends."""
    max_values = [m.body_battery_max for m in metrics_list if m.body_battery_max is not None]
    min_values = [m.body_battery_min for m in metrics_list if m.body_battery_min is not None]
    charged = [m.body_battery_charged for m in metrics_list if m.body_battery_charged is not None]
    drained = [m.body_battery_drained for m in metrics_list if m.body_battery_drained is not None]
    return {
        "avg_max": round(statistics.mean(max_values), 1) if max_values else 0,
        "avg_min": round(statistics.mean(min_values), 1) if min_values else 0,
        "avg_charged": round(statistics.mean(charged), 1) if charged else 0,
        "avg_drained": round(statistics.mean(drained), 1) if drained else 0,
        "recovery_efficiency": round(statistics.mean(charged) / statistics.mean(drained), 2)
        if charged and drained and statistics.mean(drained) > 0 else 0,
    }


def calculate_vo2max_trend(metrics_list: list[DailyMetrics]) -> dict[str, Any]:
    """Analyze VO2max trends."""
    vo2_values = [m.vo2_max for m in metrics_list if m.vo2_max is not None]
    if len(vo2_values) < 2:
        return {"current": vo2_values[0] if vo2_values else 0, "trend": "stable", "change": 0}
    current = vo2_values[-1]
    avg = statistics.mean(vo2_values)
    change = current - vo2_values[0]
    if change > 1:
        trend = "improving"
    elif change < -1:
        trend = "declining"
    else:
        trend = "stable"
    return {"current": round(current, 1), "trend": trend, "change": round(change, 1), "average": round(avg, 1)}


def assess_readiness(metrics: DailyMetrics, metrics_list: list[DailyMetrics] | None = None) -> ReadinessAssessment:
    """Assess training readiness from daily metrics."""
    score = 50.0
    insights = []
    hrv_status = HRVStatus.UNBALANCED
    sleep_quality = SleepQuality.FAIR
    if metrics.hrv_sdnn and metrics_list:
        recent_hrv = [m.hrv_sdnn for m in metrics_list[-7:] if m.hrv_sdnn is not None]
        if recent_hrv:
            baseline = statistics.mean(recent_hrv)
            hrv_status = calculate_hrv_status(metrics.hrv_sdnn, baseline, baseline)
            if hrv_status == HRVStatus.BALANCED:
                score += 15
                insights.append("HRV is balanced — recovery looks good")
            elif hrv_status == HRVStatus.LOW:
                score -= 15
                insights.append("HRV is below baseline — consider rest")
    if metrics.sleep_score:
        deep_pct = (metrics.deep_sleep_minutes / metrics.total_sleep_minutes) if metrics.total_sleep_minutes and metrics.deep_sleep_minutes else 0
        sleep_quality = classify_sleep_quality(metrics.sleep_score, deep_pct)
        if sleep_quality == SleepQuality.EXCELLENT:
            score += 15
            insights.append("Excellent sleep — well recovered")
        elif sleep_quality == SleepQuality.GOOD:
            score += 10
        elif sleep_quality == SleepQuality.POOR:
            score -= 10
            insights.append("Poor sleep — may affect performance")
    if metrics.resting_heart_rate and metrics_list:
        recent_rhr = [m.resting_heart_rate for m in metrics_list[-7:] if m.resting_heart_rate is not None]
        if recent_rhr:
            avg_rhr = statistics.mean(recent_rhr)
            if metrics.resting_heart_rate > avg_rhr + 5:
                score -= 10
                insights.append("Resting HR elevated — possible overtraining")
            elif metrics.resting_heart_rate < avg_rhr - 2:
                score += 5
                insights.append("Resting HR low — good recovery")
    if metrics.stress_score:
        if metrics.stress_score < 30:
            score += 5
        elif metrics.stress_score > 70:
            score -= 5
            insights.append("High stress detected — consider recovery activities")
    if metrics.body_battery_max and metrics.body_battery_max < 40:
        score -= 10
        insights.append("Body battery low — prioritize rest")
    score = max(0, min(100, score))
    if score >= 80:
        level = ReadinessLevel.OPTIMAL
        intensity = TrainingIntensity.HIGH
        recovery = 0
    elif score >= 60:
        level = ReadinessLevel.GOOD
        intensity = TrainingIntensity.MODERATE
        recovery = 0
    elif score >= 40:
        level = ReadinessLevel.MODERATE
        intensity = TrainingIntensity.LOW
        recovery = 1
    elif score >= 20:
        level = ReadinessLevel.LOW
        intensity = TrainingIntensity.REST
        recovery = 1
    else:
        level = ReadinessLevel.POOR
        intensity = TrainingIntensity.REST
        recovery = 2
    return ReadinessAssessment(
        level=level, score=round(score, 1), hrv_status=hrv_status,
        sleep_quality=sleep_quality, training_load_recommendation=intensity,
        recovery_days_needed=recovery, insights=insights,
    )


def calculate_fatigue_fitness_form(metrics_list: list[DailyMetrics]) -> tuple[float, float, float]:
    """Calculate CTL (fitness), ATL (fatigue), TSB (form)."""
    if len(metrics_list) < 28:
        return 0, 0, 0
    loads = []
    for m in metrics_list:
        load = 0
        if m.active_minutes:
            load += m.active_minutes * 0.5
        if m.avg_heart_rate and m.resting_heart_rate:
            load += max(0, (m.avg_heart_rate - m.resting_heart_rate) * 0.1)
        loads.append(load)
    ctl = 0
    atl = 0
    for i, load in enumerate(loads):
        ctl = ctl * (42 / 43) + load * (1 / 43)
        atl = atl * (7 / 8) + load * (1 / 8)
    tsb = ctl - atl
    return round(ctl, 1), round(atl, 1), round(tsb, 1)


def generate_daily_summary(metrics_list: list[DailyMetrics]) -> dict[str, Any]:
    """Generate summary from list of daily metrics."""
    if not metrics_list:
        return {"error": "No metrics provided"}
    latest = metrics_list[-1]
    assessment = assess_readiness(latest, metrics_list)
    load = calculate_training_load(metrics_list)
    bb_trend = calculate_body_battery_trend(metrics_list)
    vo2_trend = calculate_vo2max_trend(metrics_list)
    ctl, atl, tsb = calculate_fatigue_fitness_form(metrics_list)
    return {
        "readiness": {
            "level": assessment.level.value,
            "score": assessment.score,
            "hrv_status": assessment.hrv_status.value,
            "sleep_quality": assessment.sleep_quality.value,
            "recommendation": assessment.training_load_recommendation.value,
            "insights": assessment.insights,
        },
        "training_load": {
            "acute": load.acute_load,
            "chronic": load.chronic_load,
            "acwr": load.acwr,
            "risk": load.risk_level,
        },
        "fitness_fatigue": {"ctl": ctl, "atl": atl, "tsb": tsb},
        "body_battery": bb_trend,
        "vo2max": vo2_trend,
    }

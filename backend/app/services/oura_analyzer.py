"""
Oura Ring analysis from oura-ring — sleep and readiness scoring.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class OuraSleepSummary:
    score: int = 0
    total_minutes: int = 0
    deep_minutes: int = 0
    light_minutes: int = 0
    rem_minutes: int = 0
    awake_minutes: int = 0
    efficiency: float = 0.0
    latency: int = 0
    hrv_average: float = 0.0
    resting_heart_rate: float = 0.0
    respiratory_rate: float = 0.0
    temperature_deviation: float = 0.0
    bedtime_start: str = ""
    bedtime_end: str = ""


@dataclass
class OuraReadinessSummary:
    score: int = 0
    resting_heart_rate: float = 0.0
    hrv_balance: float = 0.0
    body_temperature: float = 0.0
    respiratory_rate: float = 0.0
    activity_balance: float = 0.0
    previous_day_activity: float = 0.0
    recovery_index: float = 0.0


@dataclass
class OuraActivitySummary:
    score: int = 0
    active_calories: float = 0.0
    steps: int = 0
    total_calories: float = 0.0
    distance: float = 0.0
    daily_movement: float = 0.0
    low_activity_minutes: int = 0
    medium_activity_minutes: int = 0
    high_activity_minutes: int = 0
    inactivity_minutes: int = 0


@dataclass
class OuraInsight:
    category: str
    title: str
    description: str
    recommendation: str
    severity: str  # info, warning, critical


def analyze_sleep_quality(sleep: OuraSleepSummary) -> List[OuraInsight]:
    insights = []
    if sleep.score < 70:
        insights.append(OuraInsight("sleep", "Poor Sleep Score", f"Score: {sleep.score}/100", "Focus on sleep hygiene — consistent bedtime, cool room", "warning"))
    if sleep.deep_minutes < 30:
        insights.append(OuraInsight("sleep", "Low Deep Sleep", f"{sleep.deep_minutes} min deep sleep", "Avoid alcohol before bed, exercise earlier in the day", "warning"))
    if sleep.rem_minutes < 30:
        insights.append(OuraInsight("sleep", "Low REM Sleep", f"{sleep.rem_minutes} min REM", "Maintain consistent wake time, reduce screen time before bed", "info"))
    if sleep.efficiency < 0.85:
        insights.append(OuraInsight("sleep", "Low Sleep Efficiency", f"{sleep.efficiency:.0%}", "Reduce time in bed when not sleeping", "warning"))
    if sleep.resting_heart_rate > 70:
        insights.append(OuraInsight("sleep", "Elevated Resting HR", f"{sleep.resting_heart_rate:.0f} bpm", "Consider stress management and recovery", "info"))
    return insights


def analyze_readiness(readiness: OuraReadinessSummary) -> List[OuraInsight]:
    insights = []
    if readiness.score < 60:
        insights.append(OuraInsight("readiness", "Low Readiness", f"Score: {readiness.score}/100", "Consider lighter training today", "warning"))
    if readiness.hrv_balance < 30:
        insights.append(OuraInsight("readiness", "Poor HRV Balance", f"Balance: {readiness.hrv_balance:.0f}", "Focus on recovery — breathing exercises, meditation", "warning"))
    if readiness.activity_balance < 20:
        insights.append(OuraInsight("readiness", "Activity Imbalance", f"Balance: {readiness.activity_balance:.0f}", "Gradually increase activity level", "info"))
    return insights


def analyze_activity(activity: OuraActivitySummary) -> List[OuraInsight]:
    insights = []
    if activity.steps < 5000:
        insights.append(OuraInsight("activity", "Low Step Count", f"{activity.steps} steps", "Aim for 8,000-10,000 steps daily", "warning"))
    if activity.inactivity_minutes > 60:
        insights.append(OuraInsight("activity", "Extended Inactivity", f"{activity.inactivity_minutes} min inactive", "Take movement breaks every 30 minutes", "info"))
    return insights


def compute_daily_wellness(sleep: OuraSleepSummary, readiness: OuraReadinessSummary, activity: OuraActivitySummary) -> float:
    sleep_score = sleep.score / 100.0
    readiness_score = readiness.score / 100.0
    activity_score = min(1.0, activity.steps / 10000)
    return (sleep_score * 0.4 + readiness_score * 0.35 + activity_score * 0.25) * 100

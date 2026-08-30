"""
Unified Wellness Score — Combines all ZFIT health services into a single metric.

Provides a composite wellness score (0-100) weighted across sleep, recovery,
activity, nutrition, stress, and cardiovascular health. Includes daily reports,
weekly trends, and personalized recommendations.

All pure functions — no DB, no async, just math.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Enums and data structures
# ---------------------------------------------------------------------------

class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class TrendDirection(str, Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


@dataclass
class ComponentScore:
    """Score for a single wellness component."""
    name: str
    score: float  # 0-100
    weight: float  # 0-1
    details: Dict[str, float] = field(default_factory=dict)
    status: str = "normal"  # normal, elevated, low, critical


@dataclass
class WellnessScore:
    """Unified wellness score."""
    overall: float  # 0-100
    components: List[ComponentScore]
    grade: str  # A+, A, B+, B, C+, C, D, F
    timestamp: str
    confidence: float  # 0-1, based on data availability


@dataclass
class WellnessAlert:
    """Health alert based on wellness score."""
    severity: AlertSeverity
    component: str
    message: str
    score: float
    threshold: float
    recommendation: str


@dataclass
class WellnessRecommendation:
    """Personalized wellness recommendation."""
    category: str
    priority: int  # 1=highest
    title: str
    description: str
    impact: str  # high, medium, low
    action: str


@dataclass
class DailyReport:
    """Comprehensive daily wellness report."""
    date: str
    score: WellnessScore
    alerts: List[WellnessAlert]
    recommendations: List[WellnessRecommendation]
    highlights: List[str]
    compare_to_yesterday: float  # positive = improvement


@dataclass
class WeeklyTrend:
    """Weekly wellness trend analysis."""
    period: str
    scores: List[Dict]  # [{date, score}]
    trend: TrendDirection
    trend_strength: float  # 0-1
    average_score: float
    best_day: Dict
    worst_day: Dict
    insights: List[str]


# ---------------------------------------------------------------------------
# Component scoring
# ---------------------------------------------------------------------------

_WEIGHTS = {
    "sleep": 0.25,
    "recovery": 0.20,
    "activity": 0.20,
    "nutrition": 0.15,
    "stress": 0.10,
    "cardiovascular": 0.10,
}


def score_sleep(
    sleep_hours: float = 0,
    sleep_quality: float = 0,  # 0-100
    deep_sleep_pct: float = 0,
    rem_pct: float = 0,
    sleep_debt_hours: float = 0,
) -> ComponentScore:
    """
    Score sleep component (0-100).
    
    Factors: duration, quality, stage distribution, sleep debt.
    Optimal: 7-9 hours, 20% deep, 25% REM, minimal debt.
    """
    details = {}
    
    # Duration score (optimal: 7-9 hours)
    if 7 <= sleep_hours <= 9:
        duration_score = 100
    elif 6 <= sleep_hours < 7:
        duration_score = 70
    elif 9 < sleep_hours <= 10:
        duration_score = 80
    elif 5 <= sleep_hours < 6:
        duration_score = 50
    else:
        duration_score = max(0, 30 - abs(sleep_hours - 8) * 10)
    details["duration"] = duration_score
    
    # Quality score
    details["quality"] = min(100, max(0, sleep_quality))
    
    # Stage distribution (optimal: 20% deep, 25% REM)
    deep_score = max(0, 100 - abs(deep_sleep_pct - 20) * 5)
    rem_score = max(0, 100 - abs(rem_pct - 25) * 4)
    details["deep_sleep"] = deep_score
    details["rem_sleep"] = rem_score
    
    # Sleep debt penalty
    debt_penalty = min(40, sleep_debt_hours * 5)
    details["debt_penalty"] = -debt_penalty
    
    # Weighted combination
    score = (
        duration_score * 0.3 +
        sleep_quality * 0.25 +
        deep_score * 0.2 +
        rem_score * 0.15 +
        max(0, 100 - debt_penalty) * 0.1
    )
    
    # Status
    if score >= 80:
        status = "optimal"
    elif score >= 60:
        status = "normal"
    elif score >= 40:
        status = "suboptimal"
    else:
        status = "critical"
    
    return ComponentScore(
        name="sleep",
        score=round(min(100, max(0, score)), 1),
        weight=_WEIGHTS["sleep"],
        details=details,
        status=status,
    )


def score_recovery(
    hrv_score: float = 50,  # 0-100
    resting_hr_delta: float = 0,  # deviation from baseline (bpm)
    readiness_score: float = 50,  # 0-100
    muscle_soreness: float = 0,  # 0-10 (10 = very sore)
) -> ComponentScore:
    """
    Score recovery component (0-100).
    
    Factors: HRV, resting HR deviation, readiness, soreness.
    """
    details = {}
    
    # HRV score (higher is better)
    details["hrv"] = min(100, max(0, hrv_score))
    
    # Resting HR deviation (closer to baseline is better)
    hr_penalty = min(50, abs(resting_hr_delta) * 5)
    details["resting_hr"] = max(0, 100 - hr_penalty)
    
    # Readiness score
    details["readiness"] = min(100, max(0, readiness_score))
    
    # Soreness penalty
    soreness_penalty = muscle_soreness * 8
    details["soreness"] = max(0, 100 - soreness_penalty)
    
    score = (
        hrv_score * 0.35 +
        max(0, 100 - hr_penalty) * 0.25 +
        readiness_score * 0.25 +
        max(0, 100 - soreness_penalty) * 0.15
    )
    
    if score >= 80:
        status = "optimal"
    elif score >= 60:
        status = "normal"
    elif score >= 40:
        status = "recovering"
    else:
        status = "depleted"
    
    return ComponentScore(
        name="recovery",
        score=round(min(100, max(0, score)), 1),
        weight=_WEIGHTS["recovery"],
        details=details,
        status=status,
    )


def score_activity(
    steps: int = 0,
    active_minutes: int = 0,
    calories_burned: int = 0,
    target_steps: int = 10000,
    target_active_minutes: int = 30,
    target_calories: int = 2500,
) -> ComponentScore:
    """
    Score activity component (0-100).
    
    Factors: steps, active minutes, calorie expenditure vs targets.
    """
    details = {}
    
    # Steps score
    step_pct = min(100, (steps / target_steps) * 100)
    details["steps"] = step_pct
    
    # Active minutes score
    active_pct = min(100, (active_minutes / target_active_minutes) * 100)
    details["active_minutes"] = active_pct
    
    # Calorie expenditure
    cal_pct = min(100, (calories_burned / target_calories) * 100)
    details["calories"] = cal_pct
    
    score = step_pct * 0.4 + active_pct * 0.35 + cal_pct * 0.25
    
    if score >= 90:
        status = "excellent"
    elif score >= 70:
        status = "good"
    elif score >= 50:
        status = "moderate"
    else:
        status = "low"
    
    return ComponentScore(
        name="activity",
        score=round(min(100, max(0, score)), 1),
        weight=_WEIGHTS["activity"],
        details=details,
        status=status,
    )


def score_nutrition(
    calorie_intake: int = 0,
    protein_g: float = 0,
    water_ml: int = 0,
    target_calories: int = 2000,
    target_protein_g: float = 50,
    target_water_ml: int = 2500,
) -> ComponentScore:
    """
    Score nutrition component (0-100).
    
    Factors: calorie balance, protein intake, hydration.
    """
    details = {}
    
    # Calorie balance (closer to target is better)
    cal_deviation = abs(calorie_intake - target_calories) / target_calories
    cal_score = max(0, 100 - cal_deviation * 100)
    details["calorie_balance"] = cal_score
    
    # Protein intake
    protein_pct = min(100, (protein_g / target_protein_g) * 100)
    details["protein"] = protein_pct
    
    # Hydration
    water_pct = min(100, (water_ml / target_water_ml) * 100)
    details["hydration"] = water_pct
    
    score = cal_score * 0.4 + protein_pct * 0.3 + water_pct * 0.3
    
    if score >= 80:
        status = "optimal"
    elif score >= 60:
        status = "adequate"
    elif score >= 40:
        status = "suboptimal"
    else:
        status = "poor"
    
    return ComponentScore(
        name="nutrition",
        score=round(min(100, max(0, score)), 1),
        weight=_WEIGHTS["nutrition"],
        details=details,
        status=status,
    )


def score_stress(
    hrv_rmssd: float = 0,
    resting_hr: float = 60,
    sleep_quality: float = 50,
    activity_level: float = 50,
) -> ComponentScore:
    """
    Score stress component (0-100, higher = less stressed).
    
    Factors: HRV (higher = less stress), resting HR, sleep quality, activity.
    """
    details = {}
    
    # HRV-based stress (higher HRV = lower stress)
    hrv_score = min(100, max(0, (hrv_rmssd / 50) * 100))
    details["hrv_indicator"] = hrv_score
    
    # Resting HR (lower is generally better for stress)
    hr_score = max(0, 100 - max(0, resting_hr - 60) * 3)
    details["resting_hr"] = hr_score
    
    # Sleep quality contribution
    details["sleep_factor"] = min(100, sleep_quality)
    
    # Activity as stress reliever
    details["activity_factor"] = min(100, activity_level)
    
    score = hrv_score * 0.35 + hr_score * 0.25 + sleep_quality * 0.2 + activity_level * 0.2
    
    if score >= 75:
        status = "calm"
    elif score >= 50:
        status = "moderate"
    elif score >= 25:
        status = "elevated"
    else:
        status = "high"
    
    return ComponentScore(
        name="stress",
        score=round(min(100, max(0, score)), 1),
        weight=_WEIGHTS["stress"],
        details=details,
        status=status,
    )


def score_cardiovascular(
    resting_hr: float = 60,
    max_hr: float = 180,
    hr_recovery_1min: int = 15,
    blood_pressure_systolic: int = 120,
    blood_pressure_diastolic: int = 80,
) -> ComponentScore:
    """
    Score cardiovascular component (0-100).
    
    Factors: resting HR, HR recovery, blood pressure.
    """
    details = {}
    
    # Resting HR (60-70 is optimal for most adults)
    if 55 <= resting_hr <= 70:
        hr_score = 100
    elif 70 < resting_hr <= 80:
        hr_score = 80
    elif 50 <= resting_hr < 55:
        hr_score = 85
    elif 80 < resting_hr <= 90:
        hr_score = 60
    else:
        hr_score = max(0, 50 - abs(resting_hr - 65) * 2)
    details["resting_hr"] = hr_score
    
    # HR recovery (higher is better, 15+ is good)
    recovery_score = min(100, (hr_recovery_1min / 20) * 100)
    details["hr_recovery"] = recovery_score
    
    # Blood pressure (120/80 is optimal)
    sys_dev = max(0, blood_pressure_systolic - 120) * 2
    dia_dev = max(0, blood_pressure_diastolic - 80) * 3
    bp_score = max(0, 100 - sys_dev - dia_dev)
    details["blood_pressure"] = bp_score
    
    score = hr_score * 0.35 + recovery_score * 0.3 + bp_score * 0.35
    
    if score >= 80:
        status = "excellent"
    elif score >= 60:
        status = "good"
    elif score >= 40:
        status = "fair"
    else:
        status = "needs_attention"
    
    return ComponentScore(
        name="cardiovascular",
        score=round(min(100, max(0, score)), 1),
        weight=_WEIGHTS["cardiovascular"],
        details=details,
        status=status,
    )


# ---------------------------------------------------------------------------
# Unified scoring
# ---------------------------------------------------------------------------

def calculate_wellness_score(
    components: List[ComponentScore],
    timestamp: str = "",
) -> WellnessScore:
    """
    Calculate unified wellness score from component scores.
    
    Weighted average with data availability confidence.
    """
    if not components:
        return WellnessScore(
            overall=0, components=[], grade="F",
            timestamp=timestamp, confidence=0,
        )
    
    # Calculate weighted score
    total_weight = sum(c.weight for c in components)
    if total_weight == 0:
        overall = 0
    else:
        overall = sum(c.score * c.weight for c in components) / total_weight
    
    # Confidence based on how many components have data
    available = sum(1 for c in components if c.score > 0)
    confidence = available / len(_WEIGHTS)
    
    # Grade mapping
    if overall >= 95:
        grade = "A+"
    elif overall >= 90:
        grade = "A"
    elif overall >= 85:
        grade = "B+"
    elif overall >= 80:
        grade = "B"
    elif overall >= 75:
        grade = "C+"
    elif overall >= 70:
        grade = "C"
    elif overall >= 60:
        grade = "D"
    else:
        grade = "F"
    
    return WellnessScore(
        overall=round(overall, 1),
        components=components,
        grade=grade,
        timestamp=timestamp,
        confidence=round(confidence, 2),
    )


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

_ALERT_THRESHOLDS = {
    "sleep": {"warning": 50, "critical": 30},
    "recovery": {"warning": 40, "critical": 25},
    "activity": {"warning": 30, "critical": 15},
    "nutrition": {"warning": 40, "critical": 20},
    "stress": {"warning": 30, "critical": 15},
    "cardiovascular": {"warning": 50, "critical": 30},
}


def generate_alerts(
    components: List[ComponentScore],
    overall_score: float,
) -> List[WellnessAlert]:
    """Generate health alerts based on component and overall scores."""
    alerts = []
    
    for comp in components:
        thresholds = _ALERT_THRESHOLDS.get(comp.name, {})
        critical = thresholds.get("critical", 20)
        warning = thresholds.get("warning", 40)
        
        if comp.score <= critical:
            alerts.append(WellnessAlert(
                severity=AlertSeverity.CRITICAL,
                component=comp.name,
                message=f"{comp.name.title()} score critically low: {comp.score}/100",
                score=comp.score,
                threshold=critical,
                recommendation=_get_recommendation(comp.name, "critical"),
            ))
        elif comp.score <= warning:
            alerts.append(WellnessAlert(
                severity=AlertSeverity.WARNING,
                component=comp.name,
                message=f"{comp.name.title()} score below optimal: {comp.score}/100",
                score=comp.score,
                threshold=warning,
                recommendation=_get_recommendation(comp.name, "warning"),
            ))
    
    # Overall score alert
    if overall_score < 40:
        alerts.append(WellnessAlert(
            severity=AlertSeverity.CRITICAL,
            component="overall",
            message=f"Overall wellness critically low: {overall_score}/100",
            score=overall_score,
            threshold=40,
            recommendation="Focus on sleep and recovery today. Consider taking it easy.",
        ))
    
    return alerts


def _get_recommendation(component: str, level: str) -> str:
    """Get recommendation for a component at a given alert level."""
    recommendations = {
        "sleep": {
            "critical": "Prioritize 8+ hours of sleep tonight. Avoid screens before bed.",
            "warning": "Aim for 7-9 hours of sleep. Maintain consistent sleep schedule.",
        },
        "recovery": {
            "critical": "Take a complete rest day. Focus on gentle stretching and hydration.",
            "warning": "Consider light activity today. Prioritize recovery-focused tasks.",
        },
        "activity": {
            "critical": "Get moving! Even a 15-minute walk can help.",
            "warning": "Aim for 30 minutes of moderate activity today.",
        },
        "nutrition": {
            "critical": "Eat a balanced meal with protein and vegetables. Hydrate well.",
            "warning": "Track your intake and ensure adequate protein and water.",
        },
        "stress": {
            "critical": "Practice deep breathing or meditation for 10 minutes.",
            "warning": "Take breaks throughout the day. Consider mindfulness practice.",
        },
        "cardiovascular": {
            "critical": "Rest and monitor your heart rate. Consult a doctor if persistent.",
            "warning": "Light cardio activity can help improve cardiovascular health.",
        },
    }
    return recommendations.get(component, {}).get(level, "Monitor this metric closely.")


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

def generate_recommendations(
    components: List[ComponentScore],
) -> List[WellnessRecommendation]:
    """Generate personalized recommendations based on component scores."""
    recommendations = []
    priority = 1
    
    # Sort by score (lowest first = highest priority)
    sorted_comps = sorted(components, key=lambda c: c.score)
    
    for comp in sorted_comps:
        if comp.score < 60:
            rec = _generate_component_recommendation(comp, priority)
            if rec:
                recommendations.append(rec)
                priority += 1
    
    # Add positive reinforcement for high scores
    for comp in sorted_comps:
        if comp.score >= 85 and priority <= 5:
            recommendations.append(WellnessRecommendation(
                category=comp.name,
                priority=priority,
                title=f"Great {comp.name.title()}!",
                description=f"Your {comp.name} score of {comp.score} is excellent. Keep it up!",
                impact="positive",
                action="Maintain current habits",
            ))
            priority += 1
    
    return recommendations[:8]  # Max 8 recommendations


def _generate_component_recommendation(
    comp: ComponentScore,
    priority: int,
) -> Optional[WellnessRecommendation]:
    """Generate a specific recommendation for a component."""
    recs = {
        "sleep": {
            "title": "Improve Sleep Quality",
            "description": "Your sleep score needs attention. Focus on consistent bedtime, cool room, and no screens 1hr before bed.",
            "action": "Set a bedtime alarm for 30 min before target sleep time",
        },
        "recovery": {
            "title": "Boost Recovery",
            "description": "Your body needs recovery time. Consider a rest day or light yoga.",
            "action": "Schedule 10 minutes of guided stretching or foam rolling",
        },
        "activity": {
            "title": "Increase Activity",
            "description": "You're below your activity targets. Even short walks help.",
            "action": "Take a 15-minute walk after your next meal",
        },
        "nutrition": {
            "title": "Optimize Nutrition",
            "description": "Your nutrition score suggests room for improvement in hydration or protein intake.",
            "action": "Drink a glass of water and add protein to your next meal",
        },
        "stress": {
            "title": "Reduce Stress",
            "description": "Elevated stress detected. Mindfulness can help reset your nervous system.",
            "action": "Try 5 minutes of box breathing (4-4-4-4 pattern)",
        },
        "cardiovascular": {
            "title": "Heart Health Check",
            "description": "Your cardiovascular metrics suggest monitoring. Light cardio can help.",
            "action": "Do 20 minutes of moderate-intensity cardio today",
        },
    }
    
    info = recs.get(comp.name, {})
    if not info:
        return None
    
    return WellnessRecommendation(
        category=comp.name,
        priority=priority,
        title=info["title"],
        description=f"{info['description']} (Current score: {comp.score}/100)",
        impact="high" if comp.score < 40 else "medium",
        action=info["action"],
    )


# ---------------------------------------------------------------------------
# Trend analysis
# ---------------------------------------------------------------------------

def analyze_weekly_trend(
    daily_scores: List[Dict],  # [{date: str, score: float, components: dict}]
) -> WeeklyTrend:
    """
    Analyze weekly wellness trend.
    
    Computes trend direction, best/worst days, and generates insights.
    """
    if not daily_scores:
        return WeeklyTrend(
            period="7d", scores=[], trend=TrendDirection.STABLE,
            trend_strength=0, average_score=0,
            best_day={}, worst_day={}, insights=[],
        )
    
    scores = [d["score"] for d in daily_scores]
    n = len(scores)
    
    # Average
    avg = sum(scores) / n
    
    # Trend via linear regression
    x_mean = (n - 1) / 2
    y_mean = avg
    num = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
    den = sum((i - x_mean) ** 2 for i in range(n))
    slope = num / den if den != 0 else 0
    
    trend_strength = min(1.0, abs(slope) * 5)
    
    if slope > 1:
        trend = TrendDirection.IMPROVING
    elif slope < -1:
        trend = TrendDirection.DECLINING
    else:
        trend = TrendDirection.STABLE
    
    # Best and worst days
    best_idx = scores.index(max(scores))
    worst_idx = scores.index(min(scores))
    
    # Insights
    insights = []
    if trend == TrendDirection.IMPROVING:
        insights.append("Your wellness is trending upward. Keep up the great habits!")
    elif trend == TrendDirection.DECLINING:
        insights.append("Your wellness has been declining. Focus on recovery and sleep.")
    
    if max(scores) - min(scores) > 20:
        insights.append("High day-to-day variability detected. Consistency could help.")
    
    if avg >= 80:
        insights.append("Excellent average wellness this week!")
    elif avg < 60:
        insights.append("Average wellness is below target. Consider adjusting your routine.")
    
    return WeeklyTrend(
        period=f"{n}d",
        scores=daily_scores,
        trend=trend,
        trend_strength=round(trend_strength, 3),
        average_score=round(avg, 1),
        best_day=daily_scores[best_idx],
        worst_day=daily_scores[worst_idx],
        insights=insights,
    )


# ---------------------------------------------------------------------------
# Daily report
# ---------------------------------------------------------------------------

def generate_daily_report(
    date: str,
    sleep_hours: float = 7.5,
    sleep_quality: float = 70,
    deep_sleep_pct: float = 18,
    rem_pct: float = 22,
    sleep_debt_hours: float = 0,
    hrv_score: float = 60,
    resting_hr_delta: float = 0,
    readiness_score: float = 65,
    muscle_soreness: float = 3,
    steps: int = 8000,
    active_minutes: int = 25,
    calories_burned: int = 2200,
    calorie_intake: int = 2000,
    protein_g: float = 45,
    water_ml: int = 2000,
    hrv_rmssd: float = 35,
    resting_hr: float = 62,
    blood_pressure_systolic: int = 118,
    blood_pressure_diastolic: int = 76,
    prev_score: float = 0,
) -> DailyReport:
    """
    Generate a comprehensive daily wellness report.
    
    Combines all component scores into a unified report with
    alerts, recommendations, and highlights.
    """
    # Calculate all component scores
    components = [
        score_sleep(sleep_hours, sleep_quality, deep_sleep_pct, rem_pct, sleep_debt_hours),
        score_recovery(hrv_score, resting_hr_delta, readiness_score, muscle_soreness),
        score_activity(steps, active_minutes, calories_burned),
        score_nutrition(calorie_intake, protein_g, water_ml),
        score_stress(hrv_rmssd, resting_hr, sleep_quality, min(100, active_minutes * 3)),
        score_cardiovascular(resting_hr, 180, 15, blood_pressure_systolic, blood_pressure_diastolic),
    ]
    
    # Unified score
    wellness = calculate_wellness_score(components, date)
    
    # Alerts
    alerts = generate_alerts(components, wellness.overall)
    
    # Recommendations
    recommendations = generate_recommendations(components)
    
    # Highlights
    highlights = []
    best = max(components, key=lambda c: c.score)
    worst = min(components, key=lambda c: c.score)
    highlights.append(f"Strongest area: {best.name.title()} ({best.score}/100)")
    highlights.append(f"Area to improve: {worst.name.title()} ({worst.score}/100)")
    
    if prev_score > 0:
        change = wellness.overall - prev_score
        if change > 0:
            highlights.append(f"Up {change:.1f} points from yesterday")
        elif change < 0:
            highlights.append(f"Down {abs(change):.1f} points from yesterday")
    
    return DailyReport(
        date=date,
        score=wellness,
        alerts=alerts,
        recommendations=recommendations,
        highlights=highlights,
        compare_to_yesterday=round(wellness.overall - prev_score, 1) if prev_score > 0 else 0,
    )

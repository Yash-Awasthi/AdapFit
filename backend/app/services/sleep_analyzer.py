"""
Sleep Quality Analyzer — analyzes sleep patterns, calculates sleep scores,
and provides personalized recommendations for improving sleep quality.
"""

from datetime import datetime, timedelta
from typing import Optional
import math

from pydantic import BaseModel, Field


class SleepStage:
    AWAKE = "awake"
    LIGHT = "light"
    DEEP = "deep"
    REM = "rem"


class SleepAnalyzer:
    """Analyze sleep patterns and generate quality scores."""

    # Weight constants for sleep score calculation
    WEIGHTS = {
        "duration": 0.25,
        "efficiency": 0.20,
        "deep_sleep": 0.20,
        "rem_sleep": 0.15,
        "consistency": 0.10,
        "interruptions": 0.10,
    }

    def calculate_sleep_score(
        self,
        duration_hours: float,
        deep_minutes: float,
        rem_minutes: float,
        awake_minutes: float,
        interruptions: int,
        bedtime_consistency_std: float,
    ) -> dict:
        """Calculate comprehensive sleep score (0-100)."""
        # Duration score: optimal is 7-9 hours
        if 7 <= duration_hours <= 9:
            duration_score = 100
        elif 6 <= duration_hours < 7:
            duration_score = 70 + (duration_hours - 6) * 30
        elif 9 < duration_hours <= 10:
            duration_score = 100 - (duration_hours - 9) * 30
        elif duration_hours < 6:
            duration_score = max(0, duration_hours * 11.67)
        else:
            duration_score = max(0, 100 - (duration_hours - 10) * 40)

        # Efficiency: percentage of time asleep
        total_minutes = duration_hours * 60
        time_asleep = total_minutes - awake_minutes
        efficiency = (time_asleep / max(total_minutes, 1)) * 100

        # Deep sleep: should be 13-23% of total
        deep_pct = (deep_minutes / max(total_minutes, 1)) * 100
        if 13 <= deep_pct <= 23:
            deep_score = 100
        elif deep_pct < 13:
            deep_score = max(0, deep_pct * (100 / 13))
        else:
            deep_score = max(0, 100 - (deep_pct - 23) * 10)

        # REM sleep: should be 20-25% of total
        rem_pct = (rem_minutes / max(total_minutes, 1)) * 100
        if 20 <= rem_pct <= 25:
            rem_score = 100
        elif rem_pct < 20:
            rem_score = max(0, rem_pct * (100 / 20))
        else:
            rem_score = max(0, 100 - (rem_pct - 25) * 10)

        # Consistency: lower std = better (ideal < 30 min)
        consistency_score = max(0, 100 - bedtime_consistency_std * 2)

        # Interruptions: 0-1 ideal, 2-3 okay, >5 bad
        if interruptions <= 1:
            interruption_score = 100
        elif interruptions <= 3:
            interruption_score = 70 - (interruptions - 1) * 10
        else:
            interruption_score = max(0, 50 - (interruptions - 3) * 15)

        # Weighted composite
        total_score = (
            self.WEIGHTS["duration"] * duration_score
            + self.WEIGHTS["efficiency"] * efficiency
            + self.WEIGHTS["deep_sleep"] * deep_score
            + self.WEIGHTS["rem_sleep"] * rem_score
            + self.WEIGHTS["consistency"] * consistency_score
            + self.WEIGHTS["interruptions"] * interruption_score
        )

        total_score = round(min(100, max(0, total_score)), 1)

        # Determine quality label
        if total_score >= 90:
            label = "excellent"
        elif total_score >= 80:
            label = "good"
        elif total_score >= 70:
            label = "fair"
        elif total_score >= 50:
            label = "poor"
        else:
            label = "very_poor"

        return {
            "sleep_score": total_score,
            "quality_label": label,
            "breakdown": {
                "duration": {"score": round(duration_score, 1), "weight": self.WEIGHTS["duration"]},
                "efficiency": {"score": round(efficiency, 1), "weight": self.WEIGHTS["efficiency"]},
                "deep_sleep": {"score": round(deep_score, 1), "weight": self.WEIGHTS["deep_sleep"]},
                "rem_sleep": {"score": round(rem_score, 1), "weight": self.WEIGHTS["rem_sleep"]},
                "consistency": {"score": round(consistency_score, 1), "weight": self.WEIGHTS["consistency"]},
                "interruptions": {"score": round(interruption_score, 1), "weight": self.WEIGHTS["interruptions"]},
            },
            "metrics": {
                "duration_hours": duration_hours,
                "deep_pct": round(deep_pct, 1),
                "rem_pct": round(rem_pct, 1),
                "efficiency_pct": round(efficiency, 1),
                "interruptions": interruptions,
            },
        }

    def get_recommendations(self, sleep_data: dict) -> list[dict]:
        """Generate personalized sleep improvement recommendations."""
        recommendations = []
        breakdown = sleep_data.get("breakdown", {})
        metrics = sleep_data.get("metrics", {})

        if breakdown.get("duration", {}).get("score", 100) < 70:
            duration = metrics.get("duration_hours", 0)
            if duration < 7:
                recommendations.append({
                    "category": "duration",
                    "priority": "high",
                    "title": "Increase Sleep Duration",
                    "description": f"You're averaging {duration:.1f}h. Aim for 7-9 hours.",
                    "tips": [
                        "Set a consistent bedtime alarm 30 min before target",
                        "Avoid screens 1 hour before bed",
                        "Limit caffeine after 2 PM",
                    ],
                })
            else:
                recommendations.append({
                    "category": "duration",
                    "priority": "medium",
                    "title": "Reduce Oversleeping",
                    "description": f"You're averaging {duration:.1f}h. Optimal is 7-9 hours.",
                    "tips": [
                        "Set a consistent wake time even on weekends",
                        "Get bright light exposure immediately on waking",
                    ],
                })

        if breakdown.get("deep_sleep", {}).get("score", 100) < 70:
            recommendations.append({
                "category": "deep_sleep",
                "priority": "high",
                "title": "Improve Deep Sleep",
                "description": f"Deep sleep is at {metrics.get('deep_pct', 0):.1f}% (target: 13-23%).",
                "tips": [
                    "Exercise regularly but not within 3 hours of bedtime",
                    "Keep bedroom temperature at 65-68°F (18-20°C)",
                    "Try progressive muscle relaxation before bed",
                    "Avoid alcohol within 3 hours of bedtime",
                ],
            })

        if breakdown.get("rem_sleep", {}).get("score", 100) < 70:
            recommendations.append({
                "category": "rem_sleep",
                "priority": "medium",
                "title": "Improve REM Sleep",
                "description": f"REM sleep is at {metrics.get('rem_pct', 0):.1f}% (target: 20-25%).",
                "tips": [
                    "Maintain a consistent sleep schedule",
                    "Avoid REM-suppressing medications when possible",
                    "Manage stress with meditation or journaling before bed",
                ],
            })

        if breakdown.get("consistency", {}).get("score", 100) < 70:
            recommendations.append({
                "category": "consistency",
                "priority": "medium",
                "title": "Improve Sleep Schedule Consistency",
                "description": "Your bedtime varies significantly. Consistency helps your circadian rhythm.",
                "tips": [
                    "Set a fixed bedtime and wake time, even on weekends",
                    "Create a pre-sleep routine that starts at the same time daily",
                    "Use dim lighting 1 hour before your target bedtime",
                ],
            })

        if breakdown.get("interruptions", {}).get("score", 100) < 70:
            recs_count = metrics.get("interruptions", 0)
            recommendations.append({
                "category": "interruptions",
                "priority": "high",
                "title": "Reduce Sleep Interruptions",
                "description": f"You had {recs_count} interruptions per night on average.",
                "tips": [
                    "Use blackout curtains to block light",
                    "Try white noise or earplugs",
                    "Limit fluid intake 2 hours before bed",
                    "Keep pets out of the bedroom",
                ],
            })

        if not recommendations:
            recommendations.append({
                "category": "general",
                "priority": "low",
                "title": "Keep It Up!",
                "description": "Your sleep quality is good. Maintain your current habits.",
                "tips": [
                    "Continue your consistent sleep schedule",
                    "Keep exercising regularly",
                    "Monitor changes during high-stress periods",
                ],
            })

        return sorted(recommendations, key=lambda r: {"high": 0, "medium": 1, "low": 2}[r["priority"]])

    def detect_trends(self, sleep_history: list[dict]) -> dict:
        """Detect trends in sleep history (last 7-30 days)."""
        if len(sleep_history) < 3:
            return {"trend": "insufficient_data", "data_points": len(sleep_history)}

        scores = [s.get("sleep_score", 0) for s in sleep_history]
        durations = [s.get("metrics", {}).get("duration_hours", 0) for s in sleep_history]

        # Simple linear trend
        n = len(scores)
        x_mean = (n - 1) / 2
        y_mean_scores = sum(scores) / n

        numerator = sum((i - x_mean) * (scores[i] - y_mean_scores) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / max(denominator, 1)

        if slope > 0.5:
            score_trend = "improving"
        elif slope < -0.5:
            score_trend = "declining"
        else:
            score_trend = "stable"

        avg_duration = sum(durations) / len(durations)
        avg_score = sum(scores) / len(scores)

        return {
            "trend": score_trend,
            "slope": round(slope, 2),
            "average_score": round(avg_score, 1),
            "average_duration": round(avg_duration, 1),
            "best_score": max(scores),
            "worst_score": min(scores),
            "data_points": len(sleep_history),
        }


# ── Endpoint-facing models ───────────────────────────────────────────────────
# SleepAnalyzer works on one night's numbers. The log/analysis endpoints work
# on a list of nights, so the models below are the wire format and the
# function below is the single entry point that spans several nights.

class StageMinutes(BaseModel):
    """Minutes spent in one sleep stage."""
    name: str
    minutes: float
    percentage: float


class SleepEntry(BaseModel):
    """One night of logged sleep."""
    date: str
    bedtime: str
    wake_time: str
    total_minutes: int
    efficiency_pct: float
    stages: list[StageMinutes] = Field(default_factory=list)
    interruptions: int = 0


class SleepAnalysis(BaseModel):
    """Aggregate analysis across the logged nights."""
    score: float
    grade: str
    avg_duration_hours: float
    avg_efficiency_pct: float
    stage_breakdown: list[StageMinutes]
    nights_analyzed: int
    quality_label: str
    recommendations: list[dict] = Field(default_factory=list)


GRADE_THRESHOLDS = [(90, "A"), (80, "B"), (70, "C"), (60, "D")]


def _grade_for(score: float) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"


def _bedtime_consistency_std(bedtimes: list[str]) -> float:
    """Standard deviation of bedtimes in minutes, wrapping over midnight.

    A 23:30 bedtime and a 00:30 bedtime differ by an hour, not by 23. Linear
    standard deviation gets that wrong, so the clock times are compared as
    angles on a 24-hour circle.
    """
    if len(bedtimes) < 2:
        return 0.0

    angles = []
    for value in bedtimes:
        try:
            hour, minute = (int(part) for part in value.split(":")[:2])
        except (ValueError, AttributeError):
            continue
        angles.append(2 * math.pi * ((hour * 60 + minute) % 1440) / 1440)

    if len(angles) < 2:
        return 0.0

    sin_mean = sum(math.sin(a) for a in angles) / len(angles)
    cos_mean = sum(math.cos(a) for a in angles) / len(angles)
    resultant = math.hypot(sin_mean, cos_mean)
    if resultant == 0:
        return 0.0

    # Circular standard deviation, converted from radians back to minutes.
    circular_std = math.sqrt(-2 * math.log(resultant))
    return circular_std * 1440 / (2 * math.pi)


def analyze_sleep(entries: list[SleepEntry]) -> SleepAnalysis:
    """Analyse a run of logged nights into a single scored summary."""
    if not entries:
        return SleepAnalysis(
            score=0.0,
            grade="F",
            avg_duration_hours=0.0,
            avg_efficiency_pct=0.0,
            stage_breakdown=[],
            nights_analyzed=0,
            quality_label="insufficient_data",
            recommendations=[{
                "category": "general",
                "priority": "low",
                "title": "Log Some Sleep",
                "description": "No sleep has been logged yet, so there is nothing to score.",
                "tips": ["Log last night's bedtime, wake time and total sleep."],
            }],
        )

    analyzer = SleepAnalyzer()

    nights = len(entries)
    avg_total_minutes = sum(e.total_minutes for e in entries) / nights
    duration_hours = avg_total_minutes / 60
    avg_efficiency = sum(e.efficiency_pct for e in entries) / nights
    avg_interruptions = sum(e.interruptions for e in entries) / nights

    stage_totals: dict[str, float] = {}
    for entry in entries:
        for stage in entry.stages:
            stage_totals[stage.name] = stage_totals.get(stage.name, 0.0) + stage.minutes

    breakdown = [
        StageMinutes(
            name=name,
            minutes=round(minutes / nights, 1),
            percentage=round(minutes / nights / max(avg_total_minutes, 1) * 100, 1),
        )
        for name, minutes in stage_totals.items()
    ]

    scored = analyzer.calculate_sleep_score(
        duration_hours=duration_hours,
        deep_minutes=stage_totals.get(SleepStage.DEEP, 0.0) / nights,
        rem_minutes=stage_totals.get(SleepStage.REM, 0.0) / nights,
        awake_minutes=stage_totals.get(SleepStage.AWAKE, 0.0) / nights,
        interruptions=round(avg_interruptions),
        bedtime_consistency_std=_bedtime_consistency_std([e.bedtime for e in entries]),
    )

    score = scored["sleep_score"]
    return SleepAnalysis(
        score=score,
        grade=_grade_for(score),
        avg_duration_hours=round(duration_hours, 2),
        avg_efficiency_pct=round(avg_efficiency, 1),
        stage_breakdown=breakdown,
        nights_analyzed=nights,
        quality_label=scored["quality_label"],
        recommendations=analyzer.get_recommendations(scored),
    )

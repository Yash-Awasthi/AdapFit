"""
Sleep Quality Analyzer — analyzes sleep patterns, calculates sleep scores,
and provides personalized recommendations for improving sleep quality.
"""

from datetime import datetime, timedelta
from typing import Optional
import math



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
        deep_minutes: Optional[float] = None,
        rem_minutes: Optional[float] = None,
        awake_minutes: Optional[float] = None,
        interruptions: Optional[int] = None,
        bedtime_consistency_std: Optional[float] = None,
        efficiency_pct: Optional[float] = None,
    ) -> dict:
        """Score 0-100 from whatever was measured.

        A component with no measurement is left out and the remaining weights
        are rescaled, so a manual log without stages is not scored as if its
        deep and REM sleep were zero or average.
        """
        components: dict[str, float] = {}

        if 7 <= duration_hours <= 9:
            components["duration"] = 100
        elif 6 <= duration_hours < 7:
            components["duration"] = 70 + (duration_hours - 6) * 30
        elif 9 < duration_hours <= 10:
            components["duration"] = 100 - (duration_hours - 9) * 30
        elif duration_hours < 6:
            components["duration"] = max(0, duration_hours * 11.67)
        else:
            components["duration"] = max(0, 100 - (duration_hours - 10) * 40)

        total_minutes = duration_hours * 60
        efficiency = efficiency_pct
        if efficiency is None and awake_minutes is not None:
            efficiency = (total_minutes - awake_minutes) / max(total_minutes, 1) * 100
        if efficiency is not None:
            components["efficiency"] = max(0.0, min(100.0, efficiency))

        deep_pct = rem_pct = None
        if deep_minutes is not None:
            deep_pct = deep_minutes / max(total_minutes, 1) * 100
            if 13 <= deep_pct <= 23:
                components["deep_sleep"] = 100
            elif deep_pct < 13:
                components["deep_sleep"] = max(0, deep_pct * (100 / 13))
            else:
                components["deep_sleep"] = max(0, 100 - (deep_pct - 23) * 10)

        if rem_minutes is not None:
            rem_pct = rem_minutes / max(total_minutes, 1) * 100
            if 20 <= rem_pct <= 25:
                components["rem_sleep"] = 100
            elif rem_pct < 20:
                components["rem_sleep"] = max(0, rem_pct * (100 / 20))
            else:
                components["rem_sleep"] = max(0, 100 - (rem_pct - 25) * 10)

        if bedtime_consistency_std is not None:
            components["consistency"] = max(0, 100 - bedtime_consistency_std * 2)

        if interruptions is not None:
            if interruptions <= 1:
                components["interruptions"] = 100
            elif interruptions <= 3:
                components["interruptions"] = 70 - (interruptions - 1) * 10
            else:
                components["interruptions"] = max(0, 50 - (interruptions - 3) * 15)

        weight_sum = sum(self.WEIGHTS[k] for k in components)
        total_score = sum(self.WEIGHTS[k] * v for k, v in components.items()) / weight_sum
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
                k: {"score": round(v, 1), "weight": self.WEIGHTS[k]} for k, v in components.items()
            },
            "measured": sorted(components),
            "metrics": {
                "duration_hours": duration_hours,
                "deep_pct": round(deep_pct, 1) if deep_pct is not None else None,
                "rem_pct": round(rem_pct, 1) if rem_pct is not None else None,
                "efficiency_pct": round(efficiency, 1) if efficiency is not None else None,
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


GRADE_THRESHOLDS = [(90, "A"), (80, "B"), (70, "C"), (60, "D")]


def grade_for(score: float) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"


def bedtime_consistency_std(bedtimes: list[str]) -> float:
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


def analyze_oximetry(readings: list[float], timestamps: list[datetime]) -> dict:
    """Overnight SpO2 summary: average, lowest, time under 90%, and dips per hour.

    A dip is a fall of 3 points or more below the mean of the preceding two
    minutes, counted once until the reading recovers. Counting every low
    sample instead turns one long dip into dozens.
    """
    if len(readings) != len(timestamps) or len(readings) < 2:
        raise ValueError("Need matching SpO2 readings and timestamps, at least two")
    pairs = sorted(zip(timestamps, readings))
    ts = [t for t, _ in pairs]
    vals = [v for _, v in pairs]

    minutes_below_90 = sum(
        (ts[i + 1] - ts[i]).total_seconds() / 60 for i in range(len(vals) - 1) if vals[i] < 90
    )
    dips, in_dip, start = 0, False, 0
    for i in range(1, len(vals)):
        while (ts[i] - ts[start]).total_seconds() > 120:
            start += 1
        window = vals[start:i] or [vals[i - 1]]
        baseline = sum(window) / len(window)
        if not in_dip and vals[i] <= baseline - 3:
            dips, in_dip = dips + 1, True
        elif in_dip and vals[i] > baseline - 3:
            in_dip = False

    hours = max((ts[-1] - ts[0]).total_seconds() / 3600, 1 / 60)
    dips_per_hour = round(dips / hours, 1)
    result = {
        "avg_spo2": round(sum(vals) / len(vals), 1),
        "min_spo2": round(min(vals), 1),
        "minutes_below_90": round(minutes_below_90, 1),
        "dips": dips,
        "dips_per_hour": dips_per_hour,
        "recording_hours": round(hours, 2),
    }
    if dips_per_hour >= 5 or minutes_below_90 >= 5:
        result["next_step"] = (
            "Your oxygen dipped repeatedly overnight. Share this recording with a doctor; "
            "a sleep study is how the cause is found."
        )
    return result


def analyze_pap_therapy(events_per_hour: float, leak_rate: float, pressure: float,
                        usage_hours: float, regime: str = "CPAP") -> dict:
    """Nightly PAP therapy summary from the machine's own report."""
    steps = []
    if usage_hours < 4:
        steps.append("Aim for at least 4 hours of use a night; comfort fixes with your provider help most.")
    if leak_rate > 24:
        steps.append("Leak is above 24 L/min. Refit the mask or ask your provider about a different size.")
    if events_per_hour >= 5:
        steps.append("The machine still records 5 or more events an hour. Tell your sleep doctor.")
    return {
        "regime": regime,
        "events_per_hour": round(events_per_hour, 1),
        "leak_rate": round(leak_rate, 1),
        "pressure": round(pressure, 1),
        "usage_hours": round(usage_hours, 1),
        "meets_usage_target": usage_hours >= 4,
        "next_steps": steps,
    }

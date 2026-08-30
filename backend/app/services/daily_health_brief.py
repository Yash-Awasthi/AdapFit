"""Daily Health Brief Service.

Extracted from applehealth (inspiration).
Generates daily health summaries combining steps, sleep,
heart rate, and workout data.

All pure functions — no DB, no async.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DailySteps:
    """Daily step count data."""
    date: str
    steps: int = 0
    distance_km: float = 0.0
    floors_climbed: int = 0


@dataclass
class DailySleep:
    """Daily sleep data."""
    date: str
    total_minutes: int = 0
    deep_minutes: int = 0
    rem_minutes: int = 0
    core_minutes: int = 0
    awake_minutes: int = 0
    sleep_start: str = ""
    sleep_end: str = ""
    quality_score: float = 0.0


@dataclass
class DailyHeartRate:
    """Daily heart rate data."""
    date: str
    resting_hr: int = 0
    max_hr: int = 0
    min_hr: int = 0
    avg_hr: int = 0
    hrv_rmssd: float = 0.0


@dataclass
class DailyWorkout:
    """Daily workout data."""
    date: str
    workout_type: str = ""
    duration_minutes: int = 0
    calories_burned: int = 0
    avg_heart_rate: int = 0
    max_heart_rate: int = 0


@dataclass
class HealthBrief:
    """Complete daily health brief."""
    date: str
    steps: Optional[DailySteps] = None
    sleep: Optional[DailySleep] = None
    heart_rate: Optional[DailyHeartRate] = None
    workouts: list[DailyWorkout] = field(default_factory=list)
    wellness_score: float = 0.0
    summary_text: str = ""
    recommendations: list[str] = field(default_factory=list)


# --- Data Loading ---

def parse_steps_data(rows: list[dict]) -> list[DailySteps]:
    """Parse step data from CSV rows.

    Args:
        rows: List of dicts with date, steps, distance, floors

    Returns:
        List of DailySteps
    """
    results = []
    for row in rows:
        try:
            results.append(DailySteps(
                date=str(row.get("date", "")),
                steps=int(float(row.get("steps", 0))),
                distance_km=float(row.get("distance_km", 0)),
                floors_climbed=int(float(row.get("floors_climbed", 0))),
            ))
        except (ValueError, TypeError):
            continue
    return results


def parse_sleep_data(rows: list[dict]) -> list[DailySleep]:
    """Parse sleep data from CSV rows.

    Args:
        rows: List of dicts with sleep metrics

    Returns:
        List of DailySleep
    """
    results = []
    for row in rows:
        try:
            results.append(DailySleep(
                date=str(row.get("date", "")),
                total_minutes=int(float(row.get("total_minutes", 0))),
                deep_minutes=int(float(row.get("deep_minutes", 0))),
                rem_minutes=int(float(row.get("rem_minutes", 0))),
                core_minutes=int(float(row.get("core_minutes", 0))),
                awake_minutes=int(float(row.get("awake_minutes", 0))),
                sleep_start=str(row.get("sleep_start", "")),
                sleep_end=str(row.get("sleep_end", "")),
            ))
        except (ValueError, TypeError):
            continue
    return results


def parse_heart_rate_data(rows: list[dict]) -> list[DailyHeartRate]:
    """Parse heart rate data from CSV rows.

    Args:
        rows: List of dicts with heart rate metrics

    Returns:
        List of DailyHeartRate
    """
    results = []
    for row in rows:
        try:
            results.append(DailyHeartRate(
                date=str(row.get("date", "")),
                resting_hr=int(float(row.get("resting_hr", 0))),
                max_hr=int(float(row.get("max_hr", 0))),
                min_hr=int(float(row.get("min_hr", 0))),
                avg_hr=int(float(row.get("avg_hr", 0))),
                hrv_rmssd=float(row.get("hrv_rmssd", 0)),
            ))
        except (ValueError, TypeError):
            continue
    return results


def parse_workout_data(rows: list[dict]) -> list[DailyWorkout]:
    """Parse workout data from CSV rows.

    Args:
        rows: List of dicts with workout metrics

    Returns:
        List of DailyWorkout
    """
    results = []
    for row in rows:
        try:
            results.append(DailyWorkout(
                date=str(row.get("date", "")),
                workout_type=str(row.get("workout_type", "")),
                duration_minutes=int(float(row.get("duration_minutes", 0))),
                calories_burned=int(float(row.get("calories_burned", 0))),
                avg_heart_rate=int(float(row.get("avg_heart_rate", 0))),
                max_heart_rate=int(float(row.get("max_heart_rate", 0))),
            ))
        except (ValueError, TypeError):
            continue
    return results


# --- Scoring ---

def calculate_wellness_score(
    steps: Optional[DailySteps],
    sleep: Optional[DailySleep],
    heart_rate: Optional[DailyHeartRate],
    workouts: list[DailyWorkout],
) -> float:
    """Calculate daily wellness score (0-100).

    Args:
        steps: Daily steps data
        sleep: Daily sleep data
        heart_rate: Daily heart rate data
        workouts: Daily workout data

    Returns:
        Wellness score 0-100
    """
    scores = []

    # Steps score (target: 10000)
    if steps:
        step_score = min(100, (steps.steps / 10000) * 100)
        scores.append(step_score)

    # Sleep score (target: 8 hours = 480 min)
    if sleep and sleep.total_minutes > 0:
        sleep_score = min(100, (sleep.total_minutes / 480) * 100)
        # Bonus for deep sleep (target: 20% of total)
        if sleep.total_minutes > 0:
            deep_pct = sleep.deep_minutes / sleep.total_minutes
            if deep_pct >= 0.15:
                sleep_score = min(100, sleep_score * 1.1)
        scores.append(sleep_score)

    # Heart rate score (lower resting = better, target: 60 bpm)
    if heart_rate and heart_rate.resting_hr > 0:
        if heart_rate.resting_hr <= 60:
            hr_score = 100
        elif heart_rate.resting_hr <= 70:
            hr_score = 80
        elif heart_rate.resting_hr <= 80:
            hr_score = 60
        else:
            hr_score = max(20, 100 - (heart_rate.resting_hr - 80))
        scores.append(hr_score)

    # Workout score
    if workouts:
        total_duration = sum(w.duration_minutes for w in workouts)
        workout_score = min(100, (total_duration / 60) * 100)  # Target: 60 min
        scores.append(workout_score)

    if not scores:
        return 0.0

    return round(sum(scores) / len(scores), 1)


# --- Recommendations ---

def generate_recommendations(
    steps: Optional[DailySteps],
    sleep: Optional[DailySleep],
    heart_rate: Optional[DailyHeartRate],
    workouts: list[DailyWorkout],
) -> list[str]:
    """Generate health recommendations based on daily data.

    Args:
        steps: Daily steps data
        sleep: Daily sleep data
        heart_rate: Daily heart rate data
        workouts: Daily workout data

    Returns:
        List of recommendation strings
    """
    recommendations = []

    # Steps recommendations
    if steps:
        if steps.steps < 5000:
            recommendations.append("You've been sedentary today. Try to walk more — aim for 10,000 steps.")
        elif steps.steps < 8000:
            recommendations.append("Good progress on steps! A bit more walking would reach the 10K target.")
        elif steps.steps >= 10000:
            recommendations.append("Great job hitting 10,000 steps today!")

    # Sleep recommendations
    if sleep:
        if sleep.total_minutes < 360:
            recommendations.append("Sleep was quite short last night. Aim for 7-9 hours for optimal recovery.")
        elif sleep.total_minutes < 420:
            recommendations.append("Sleep was a bit below target. Try to get 7+ hours tonight.")
        elif sleep.total_minutes > 540:
            recommendations.append("Oversleeping can also affect energy. 7-9 hours is the sweet spot.")

        if sleep.total_minutes > 0 and sleep.deep_minutes / sleep.total_minutes < 0.13:
            recommendations.append("Deep sleep was low. Avoid screens before bed and keep a cool room.")

    # Heart rate recommendations
    if heart_rate:
        if heart_rate.resting_hr > 80:
            recommendations.append("Resting heart rate is elevated. Consider stress management or cardio training.")
        if heart_rate.hrv_rmssd > 0 and heart_rate.hrv_rmssd < 20:
            recommendations.append("HRV is low, suggesting recovery might be needed. Consider a rest day.")

    # Workout recommendations
    if not workouts:
        recommendations.append("No workout today. Even a 30-minute walk counts toward your goals!")
    else:
        total = sum(w.duration_minutes for w in workouts)
        if total < 30:
            recommendations.append("Today's workout was short. Try to reach 30+ minutes for health benefits.")

    return recommendations


# --- Brief Generation ---

def generate_daily_brief(
    date: str,
    steps_data: list[DailySteps],
    sleep_data: list[DailySleep],
    heart_rate_data: list[DailyHeartRate],
    workout_data: list[DailyWorkout],
) -> HealthBrief:
    """Generate a complete daily health brief.

    Args:
        date: Target date (YYYY-MM-DD)
        steps_data: All steps data
        sleep_data: All sleep data
        heart_rate_data: All heart rate data
        workout_data: All workout data

    Returns:
        Complete health brief
    """
    steps = next((s for s in steps_data if s.date == date), None)
    sleep = next((s for s in sleep_data if s.date == date), None)
    heart_rate = next((h for h in heart_rate_data if h.date == date), None)
    workouts = [w for w in workout_data if w.date == date]

    wellness_score = calculate_wellness_score(steps, sleep, heart_rate, workouts)
    recommendations = generate_recommendations(steps, sleep, heart_rate, workouts)

    # Generate summary text
    parts = []
    if steps:
        parts.append(f"{steps.steps:,} steps")
    if sleep:
        hours = sleep.total_minutes // 60
        mins = sleep.total_minutes % 60
        parts.append(f"{hours}h {mins}m sleep")
    if heart_rate:
        parts.append(f"resting HR {heart_rate.resting_hr} bpm")
    if workouts:
        total_cal = sum(w.calories_burned for w in workouts)
        parts.append(f"{len(workouts)} workout(s), {total_cal} cal")

    summary_text = f"Today: {', '.join(parts)}" if parts else "No data recorded today."

    return HealthBrief(
        date=date,
        steps=steps,
        sleep=sleep,
        heart_rate=heart_rate,
        workouts=workouts,
        wellness_score=wellness_score,
        summary_text=summary_text,
        recommendations=recommendations,
    )

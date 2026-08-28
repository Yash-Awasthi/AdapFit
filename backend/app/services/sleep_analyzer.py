"""Sleep analysis: stage breakdown, consistency scoring, and recommendations."""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from statistics import mean, stdev


class SleepStage(BaseModel):
    name: str  # "awake", "light", "deep", "rem"
    minutes: int
    percentage: float


class SleepEntry(BaseModel):
    date: str
    bedtime: str  # HH:MM
    wake_time: str  # HH:MM
    total_minutes: int
    efficiency_pct: float
    stages: List[SleepStage]
    interruptions: int = 0
    notes: Optional[str] = None


class SleepAnalysis(BaseModel):
    score: float  # 0-100
    grade: str  # A, B, C, D, F
    consistency_score: float  # 0-100
    avg_duration_hours: float
    avg_efficiency: float
    deep_sleep_pct: float
    rem_sleep_pct: float
    consistency_trend: str  # "improving", "stable", "declining"
    recommendations: List[str]
    stage_breakdown: List[SleepStage]


# Sleep targets by age group
TARGETS = {
    "default": {"min_hours": 7, "max_hours": 9, "deep_pct": 15, "rem_pct": 20, "efficiency": 85},
}


def analyze_sleep(entries: List[SleepEntry], age_group: str = "default") -> SleepAnalysis:
    """Analyze sleep data and generate insights."""
    if not entries:
        return SleepAnalysis(
            score=0, grade="F", consistency_score=0,
            avg_duration_hours=0, avg_efficiency=0,
            deep_sleep_pct=0, rem_sleep_pct=0,
            consistency_trend="stable",
            recommendations=["Start tracking your sleep to get personalized insights."],
            stage_breakdown=[],
        )

    targets = TARGETS.get(age_group, TARGETS["default"])

    # Duration analysis
    durations = [e.total_minutes / 60 for e in entries]
    avg_duration = mean(durations)
    avg_efficiency = mean([e.efficiency_pct for e in entries])

    # Stage analysis
    all_deep = [s.percentage for e in entries for s in e.stages if s.name == "deep"]
    all_rem = [s.percentage for e in entries for s in e.stages if s.name == "rem"]
    avg_deep = mean(all_deep) if all_deep else 0
    avg_rem = mean(all_rem) if all_rem else 0

    # Consistency: coefficient of variation of bedtime and duration
    if len(durations) >= 2:
        dur_cv = stdev(durations) / mean(durations) if mean(durations) > 0 else 0
        consistency = max(0, 100 - dur_cv * 200)
    else:
        consistency = 50

    # Trend
    if len(durations) >= 3:
        recent = mean(durations[:len(durations)//2])
        older = mean(durations[len(durations)//2:])
        if recent > older + 0.3:
            trend = "improving"
        elif recent < older - 0.3:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"

    # Score calculation (weighted)
    duration_score = min(100, (avg_duration / targets["min_hours"]) * 100) if targets["min_hours"] else 50
    efficiency_score = avg_efficiency
    deep_score = min(100, (avg_deep / targets["deep_pct"]) * 100) if targets["deep_pct"] else 50
    rem_score = min(100, (avg_rem / targets["rem_pct"]) * 100) if targets["rem_pct"] else 50

    score = (
        duration_score * 0.3 +
        efficiency_score * 0.25 +
        deep_score * 0.2 +
        rem_score * 0.15 +
        consistency * 0.1
    )
    score = round(min(100, max(0, score)), 1)

    # Grade
    if score >= 90: grade = "A"
    elif score >= 80: grade = "B"
    elif score >= 70: grade = "C"
    elif score >= 60: grade = "D"
    else: grade = "F"

    # Recommendations
    recs = []
    if avg_duration < targets["min_hours"]:
        recs.append(f"Average sleep is {avg_duration:.1f}h — aim for {targets['min_hours']}+ hours.")
    if avg_efficiency < targets["efficiency"]:
        recs.append(f"Sleep efficiency is {avg_efficiency:.0f}% — reduce screen time before bed.")
    if avg_deep < targets["deep_pct"]:
        recs.append(f"Deep sleep is low ({avg_deep:.0f}%) — try cooler room temperature.")
    if avg_rem < targets["rem_pct"]:
        recs.append(f"REM sleep is low ({avg_rem:.0f}%) — maintain consistent sleep schedule.")
    if consistency < 70:
        recs.append("Sleep timing is irregular — go to bed at the same time daily.")
    if trend == "declining":
        recs.append("Sleep quality is declining — consider reducing caffeine after 2pm.")
    if not recs:
        recs.append("Great sleep habits! Keep up the consistency.")

    # Stage breakdown (averaged)
    stage_names = ["awake", "light", "deep", "rem"]
    breakdown = []
    for name in stage_names:
        vals = [s.percentage for e in entries for s in e.stages if s.name == name]
        avg_val = mean(vals) if vals else 0
        avg_min = sum(s.minutes for e in entries for s in e.stages if s.name == name) / len(entries)
        breakdown.append(SleepStage(name=name, minutes=round(avg_min), percentage=round(avg_val, 1)))

    return SleepAnalysis(
        score=score,
        grade=grade,
        consistency_score=round(consistency, 1),
        avg_duration_hours=round(avg_duration, 1),
        avg_efficiency=round(avg_efficiency, 1),
        deep_sleep_pct=round(avg_deep, 1),
        rem_sleep_pct=round(avg_rem, 1),
        consistency_trend=trend,
        recommendations=recs,
        stage_breakdown=breakdown,
    )

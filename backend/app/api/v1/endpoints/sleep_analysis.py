"""TRACK: Advanced sleep analysis with stage breakdown, consistency scoring, and recommendations."""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from app.core.storage import storage

router = APIRouter()


class SleepStage(BaseModel):
    name: str
    minutes: int
    percentage: float
    optimal_range: str
    status: str  # optimal, low, high


class SleepConsistency(BaseModel):
    bedtime_consistency: float  # 0-100
    wake_time_consistency: float  # 0-100
    duration_consistency: float  # 0-100
    overall_score: float  # 0-100
    trend: str  # improving, stable, declining


class SleepRecommendation(BaseModel):
    category: str
    title: str
    description: str
    priority: str  # high, medium, low


class SleepAnalysis(BaseModel):
    user_id: str
    analysis_period_days: int
    avg_duration_hours: float
    avg_quality_score: float
    sleep_stages: list[SleepStage]
    consistency: SleepConsistency
    recommendations: list[SleepRecommendation]
    sleep_debt_hours: float
    recovery_impact: str
    hrv_correlation: Optional[float]


def _analyze_stages(logs: list[dict]) -> list[SleepStage]:
    """Analyze sleep stage averages from log data."""
    if not logs:
        return []

    avg_deep = sum(l.get("deep_sleep_minutes", 0) for l in logs) / len(logs)
    avg_rem = sum(l.get("rem_sleep_minutes", 0) for l in logs) / len(logs)
    avg_total = sum(l.get("duration_hours", 7) * 60 for l in logs) / len(logs)
    avg_light = max(0, avg_total - avg_deep - avg_rem)

    stages = [
        SleepStage(
            name="Deep Sleep",
            minutes=round(avg_deep),
            percentage=round(avg_deep / avg_total * 100, 1) if avg_total > 0 else 0,
            optimal_range="60-120 min",
            status="optimal" if 60 <= avg_deep <= 120 else ("low" if avg_deep < 60 else "high"),
        ),
        SleepStage(
            name="REM Sleep",
            minutes=round(avg_rem),
            percentage=round(avg_rem / avg_total * 100, 1) if avg_total > 0 else 0,
            optimal_range="90-120 min",
            status="optimal" if 90 <= avg_rem <= 120 else ("low" if avg_rem < 90 else "high"),
        ),
        SleepStage(
            name="Light Sleep",
            minutes=round(avg_light),
            percentage=round(avg_light / avg_total * 100, 1) if avg_total > 0 else 0,
            optimal_range="270-360 min",
            status="optimal",
        ),
    ]
    return stages


def _compute_consistency(logs: list[dict]) -> SleepConsistency:
    """Compute sleep schedule consistency from log data."""
    if len(logs) < 3:
        return SleepConsistency(
            bedtime_consistency=0, wake_time_consistency=0,
            duration_consistency=0, overall_score=0, trend="insufficient_data",
        )

    durations = [l.get("duration_hours", 7) for l in logs]
    avg_dur = sum(durations) / len(durations)
    dur_std = (sum((d - avg_dur) ** 2 for d in durations) / len(durations)) ** 0.5

    # Consistency = 100 - (std_dev / mean * 100), clamped
    dur_consistency = max(0, min(100, 100 - (dur_std / avg_dur * 100) if avg_dur > 0 else 0))

    # Bedtime consistency (based on sleep efficiency variance)
    efficiencies = [l.get("sleep_efficiency_pct", 85) for l in logs]
    eff_avg = sum(efficiencies) / len(efficiencies)
    eff_std = (sum((e - eff_avg) ** 2 for e in efficiencies) / len(efficiencies)) ** 0.5
    bedtime_consistency = max(0, min(100, 100 - eff_std))

    # Trend detection
    recent = durations[:len(durations)//2]
    older = durations[len(durations)//2:]
    recent_avg = sum(recent) / len(recent) if recent else avg_dur
    older_avg = sum(older) / len(older) if older else avg_dur
    trend = "stable"
    if recent_avg > older_avg + 0.3:
        trend = "improving"
    elif recent_avg < older_avg - 0.3:
        trend = "declining"

    overall = (bedtime_consistency + bedtime_consistency + dur_consistency) / 3

    return SleepConsistency(
        bedtime_consistency=round(bedtime_consistency),
        wake_time_consistency=round(bedtime_consistency),
        duration_consistency=round(dur_consistency),
        overall_score=round(overall),
        trend=trend,
    )


def _generate_recommendations(
    avg_duration: float, avg_quality: float, stages: list[SleepStage], consistency: SleepConsistency
) -> list[SleepRecommendation]:
    """Generate personalized sleep recommendations."""
    recs = []

    if avg_duration < 7:
        recs.append(SleepRecommendation(
            category="duration",
            title="Increase Sleep Duration",
            description=f"You're averaging {avg_duration:.1f}h. Aim for 7-9h for optimal recovery.",
            priority="high",
        ))

    if avg_quality < 70:
        recs.append(SleepRecommendation(
            category="quality",
            title="Improve Sleep Quality",
            description="Low sleep quality detected. Try reducing screen time 1h before bed.",
            priority="high",
        ))

    deep = next((s for s in stages if s.name == "Deep Sleep"), None)
    if deep and deep.status == "low":
        recs.append(SleepRecommendation(
            category="deep_sleep",
            title="Boost Deep Sleep",
            description="Deep sleep is below optimal. Avoid alcohol and maintain consistent bedtime.",
            priority="medium",
        ))

    rem = next((s for s in stages if s.name == "REM Sleep"), None)
    if rem and rem.status == "low":
        recs.append(SleepRecommendation(
            category="rem_sleep",
            title="Increase REM Sleep",
            description="REM sleep is low. Regular exercise and stress management can help.",
            priority="medium",
        ))

    if consistency.overall_score < 60:
        recs.append(SleepRecommendation(
            category="consistency",
            title="Maintain Consistent Schedule",
            description="Your sleep schedule varies significantly. Try going to bed within 30min of the same time.",
            priority="high",
        ))

    if avg_duration > 9:
        recs.append(SleepRecommendation(
            category="duration",
            title="Consider Reducing Sleep Duration",
            description=f" averaging {avg_duration:.1f}h. Oversleeping can cause grogginess.",
            priority="low",
        ))

    if not recs:
        recs.append(SleepRecommendation(
            category="maintenance",
            title="Keep It Up",
            description="Your sleep habits look great! Maintain your current routine.",
            priority="low",
        ))

    return recs


@router.get("/{user_id}", response_model=SleepAnalysis)
async def get_sleep_analysis(user_id: str, days: int = Query(14, ge=7, le=90)):
    """Get comprehensive sleep analysis with stages, consistency, and recommendations."""
    logs = await storage.get_sleep_logs(user_id, days)

    if not logs:
        return SleepAnalysis(
            user_id=user_id,
            analysis_period_days=days,
            avg_duration_hours=0,
            avg_quality_score=0,
            sleep_stages=[],
            consistency=SleepConsistency(
                bedtime_consistency=0, wake_time_consistency=0,
                duration_consistency=0, overall_score=0, trend="no_data",
            ),
            recommendations=[SleepRecommendation(
                category="data",
                title="Start Logging Sleep",
                description="Track your sleep for personalized analysis.",
                priority="high",
            )],
            sleep_debt_hours=0,
            recovery_impact="No data available",
            hrv_correlation=None,
        )

    avg_duration = sum(l.get("duration_hours", 7) for l in logs) / len(logs)
    avg_quality = sum(l.get("quality_score", 80) for l in logs) / len(logs)

    stages = _analyze_stages(logs)
    consistency = _compute_consistency(logs)
    recs = _generate_recommendations(avg_duration, avg_quality, stages, consistency)

    # Sleep debt: target 8h minus actual
    sleep_debt = max(0, (8 - avg_duration) * len(logs))

    # Recovery impact description
    if avg_quality >= 85:
        recovery = "Excellent — sleep is strongly supporting your recovery"
    elif avg_quality >= 70:
        recovery = "Good — sleep is adequately supporting recovery"
    elif avg_quality >= 50:
        recovery = "Fair — sleep quality may be limiting recovery"
    else:
        recovery = "Poor — sleep is significantly impacting recovery"

    return SleepAnalysis(
        user_id=user_id,
        analysis_period_days=days,
        avg_duration_hours=round(avg_duration, 1),
        avg_quality_score=round(avg_quality, 1),
        sleep_stages=stages,
        consistency=consistency,
        recommendations=recs,
        sleep_debt_hours=round(sleep_debt, 1),
        recovery_impact=recovery,
        hrv_correlation=None,
    )

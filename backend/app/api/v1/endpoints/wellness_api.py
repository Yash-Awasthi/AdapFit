"""
Wellness API — Unified endpoints for the wellness scoring system.

5 endpoints:
- GET /wellness/score — current unified score
- GET /wellness/report — detailed daily report
- GET /wellness/trends — weekly/monthly trends
- GET /wellness/recommendations — personalized suggestions
- GET /wellness/alerts — active health alerts
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

from app.services.wellness_score import (
    calculate_wellness_score,
    generate_daily_report,
    generate_alerts,
    generate_recommendations,
    analyze_weekly_trend,
    score_sleep,
    score_recovery,
    score_activity,
    score_nutrition,
    score_stress,
    score_cardiovascular,
    AlertSeverity,
    TrendDirection,
)


router = APIRouter(prefix="/wellness", tags=["Wellness"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class ComponentScoreResponse(BaseModel):
    name: str
    score: float = Field(..., ge=0, le=100)
    weight: float
    status: str
    details: Dict[str, float] = {}


class WellnessScoreResponse(BaseModel):
    overall: float = Field(..., ge=0, le=100)
    grade: str
    components: List[ComponentScoreResponse]
    confidence: float = Field(..., ge=0, le=1)
    timestamp: str


class AlertResponse(BaseModel):
    severity: str
    component: str
    message: str
    score: float
    threshold: float
    recommendation: str


class RecommendationResponse(BaseModel):
    category: str
    priority: int
    title: str
    description: str
    impact: str
    action: str


class DailyReportResponse(BaseModel):
    date: str
    overall_score: float
    grade: str
    components: List[ComponentScoreResponse]
    alerts: List[AlertResponse]
    recommendations: List[RecommendationResponse]
    highlights: List[str]
    compare_to_yesterday: float


class TrendPoint(BaseModel):
    date: str
    score: float


class WeeklyTrendResponse(BaseModel):
    period: str
    average_score: float
    trend: str
    trend_strength: float
    best_day: Optional[TrendPoint] = None
    worst_day: Optional[TrendPoint] = None
    scores: List[TrendPoint]
    insights: List[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/score", response_model=WellnessScoreResponse)
async def get_wellness_score(
    sleep_hours: float = Query(7.5, ge=0, le=24),
    sleep_quality: float = Query(70, ge=0, le=100),
    steps: int = Query(8000, ge=0),
    active_minutes: int = Query(25, ge=0),
    hrv_score: float = Query(60, ge=0, le=100),
    resting_hr: float = Query(62, ge=30, le=200),
    calorie_intake: int = Query(2000, ge=0),
    water_ml: int = Query(2000, ge=0),
):
    """
    Get the current unified wellness score.
    
    Combines sleep, recovery, activity, nutrition, stress, and
    cardiovascular metrics into a single 0-100 score.
    """
    components = [
        score_sleep(sleep_hours, sleep_quality),
        score_recovery(hrv_score, 0, 65, 3),
        score_activity(steps, active_minutes, 2200),
        score_nutrition(calorie_intake, 45, water_ml),
        score_stress(hrv_score * 0.6, resting_hr, sleep_quality, min(100, active_minutes * 3)),
        score_cardiovascular(resting_hr, 180, 15, 118, 76),
    ]
    
    from datetime import datetime
    wellness = calculate_wellness_score(components, datetime.now().isoformat())
    
    return WellnessScoreResponse(
        overall=wellness.overall,
        grade=wellness.grade,
        components=[
            ComponentScoreResponse(
                name=c.name, score=c.score, weight=c.weight,
                status=c.status, details=c.details,
            )
            for c in wellness.components
        ],
        confidence=wellness.confidence,
        timestamp=wellness.timestamp,
    )


@router.get("/report", response_model=DailyReportResponse)
async def get_daily_report(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    sleep_hours: float = Query(7.5),
    sleep_quality: float = Query(70),
    steps: int = Query(8000),
    hrv_score: float = Query(60),
    resting_hr: float = Query(62),
    prev_score: float = Query(0),
):
    """Get detailed daily wellness report with alerts and recommendations."""
    from datetime import datetime
    report_date = date or datetime.now().strftime("%Y-%m-%d")
    
    report = generate_daily_report(
        date=report_date,
        sleep_hours=sleep_hours,
        sleep_quality=sleep_quality,
        hrv_score=hrv_score,
        resting_hr=resting_hr,
        steps=steps,
        prev_score=prev_score,
    )
    
    return DailyReportResponse(
        date=report.date,
        overall_score=report.score.overall,
        grade=report.score.grade,
        components=[
            ComponentScoreResponse(
                name=c.name, score=c.score, weight=c.weight,
                status=c.status, details=c.details,
            )
            for c in report.score.components
        ],
        alerts=[
            AlertResponse(
                severity=a.severity.value, component=a.component,
                message=a.message, score=a.score, threshold=a.threshold,
                recommendation=a.recommendation,
            )
            for a in report.alerts
        ],
        recommendations=[
            RecommendationResponse(
                category=r.category, priority=r.priority, title=r.title,
                description=r.description, impact=r.impact, action=r.action,
            )
            for r in report.recommendations
        ],
        highlights=report.highlights,
        compare_to_yesterday=report.compare_to_yesterday,
    )


@router.get("/trends", response_model=WeeklyTrendResponse)
async def get_trends(
    period: str = Query("7d", regex="^(7d|30d|90d)$"),
    scores: Optional[str] = Query(None, description="Comma-separated daily scores"),
):
    """Get wellness trend analysis over time."""
    # Parse provided scores or generate defaults
    if scores:
        score_list = [float(s) for s in scores.split(",")]
        daily_data = [
            {"date": f"day_{i+1}", "score": s}
            for i, s in enumerate(score_list)
        ]
    else:
        # Default sample trend
        daily_data = [
            {"date": f"2024-01-{i+1:02d}", "score": 65 + (i * 2) - (i % 3) * 5}
            for i in range(7)
        ]
    
    trend = analyze_weekly_trend(daily_data)
    
    return WeeklyTrendResponse(
        period=trend.period,
        average_score=trend.average_score,
        trend=trend.trend.value,
        trend_strength=trend.trend_strength,
        best_day=TrendPoint(**trend.best_day) if trend.best_day else None,
        worst_day=TrendPoint(**trend.worst_day) if trend.worst_day else None,
        scores=[TrendPoint(date=d["date"], score=d["score"]) for d in trend.scores],
        insights=trend.insights,
    )


@router.get("/recommendations", response_model=List[RecommendationResponse])
async def get_recommendations(
    sleep_score: float = Query(60, ge=0, le=100),
    recovery_score: float = Query(55, ge=0, le=100),
    activity_score: float = Query(50, ge=0, le=100),
    nutrition_score: float = Query(65, ge=0, le=100),
    stress_score: float = Query(45, ge=0, le=100),
    cardio_score: float = Query(70, ge=0, le=100),
):
    """Get personalized wellness recommendations."""
    from app.services.wellness_score import ComponentScore
    
    components = [
        ComponentScore(name="sleep", score=sleep_score, weight=0.25),
        ComponentScore(name="recovery", score=recovery_score, weight=0.20),
        ComponentScore(name="activity", score=activity_score, weight=0.20),
        ComponentScore(name="nutrition", score=nutrition_score, weight=0.15),
        ComponentScore(name="stress", score=stress_score, weight=0.10),
        ComponentScore(name="cardiovascular", score=cardio_score, weight=0.10),
    ]
    
    recs = generate_recommendations(components)
    
    return [
        RecommendationResponse(
            category=r.category, priority=r.priority, title=r.title,
            description=r.description, impact=r.impact, action=r.action,
        )
        for r in recs
    ]


@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    sleep_score: float = Query(60, ge=0, le=100),
    recovery_score: float = Query(55, ge=0, le=100),
    activity_score: float = Query(50, ge=0, le=100),
    overall_score: float = Query(55, ge=0, le=100),
):
    """Get active health alerts."""
    from app.services.wellness_score import ComponentScore
    
    components = [
        ComponentScore(name="sleep", score=sleep_score, weight=0.25),
        ComponentScore(name="recovery", score=recovery_score, weight=0.20),
        ComponentScore(name="activity", score=activity_score, weight=0.20),
        ComponentScore(name="nutrition", score=65, weight=0.15),
        ComponentScore(name="stress", score=50, weight=0.10),
        ComponentScore(name="cardiovascular", score=70, weight=0.10),
    ]
    
    alerts = generate_alerts(components, overall_score)
    
    return [
        AlertResponse(
            severity=a.severity.value, component=a.component,
            message=a.message, score=a.score, threshold=a.threshold,
            recommendation=a.recommendation,
        )
        for a in alerts
    ]

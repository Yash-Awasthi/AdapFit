"""
Sleep Analysis API — endpoints for sleep quality scoring,
recommendations, and trend analysis.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter(
    prefix="/sleep",
    tags=["Sleep Analysis"],
    responses={
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"},
    },
)


class SleepInput(BaseModel):
    duration_hours: float = Field(..., ge=0, le=24, description="Total sleep duration in hours")
    deep_minutes: float = Field(..., ge=0, description="Deep sleep minutes")
    rem_minutes: float = Field(..., ge=0, description="REM sleep minutes")
    awake_minutes: float = Field(0, ge=0, description="Time awake during the night")
    interruptions: int = Field(0, ge=0, description="Number of sleep interruptions")
    bedtime_consistency_std: float = Field(30.0, ge=0, description="Standard deviation of bedtime in minutes")


class SleepHistoryInput(BaseModel):
    history: list[SleepInput] = Field(..., min_length=1, description="List of nightly sleep records")


@router.post(
    "/score",
    summary="Calculate sleep quality score",
    description="Analyzes 6 sleep factors (duration, efficiency, deep/REM %, consistency, interruptions) to produce a 0-100 quality score with personalized recommendations.",
    responses={
        200: {
            "description": "Sleep quality score with breakdown and recommendations",
            "content": {
                "application/json": {
                    "example": {
                        "sleep_score": 78.5,
                        "quality_label": "good",
                        "breakdown": {
                            "duration": {"score": 100, "weight": 0.25},
                            "efficiency": {"score": 91.7, "weight": 0.2},
                            "deep_sleep": {"score": 85.0, "weight": 0.2},
                            "rem_sleep": {"score": 90.0, "weight": 0.15},
                            "consistency": {"score": 66.7, "weight": 0.1},
                            "interruptions": {"score": 50.0, "weight": 0.1},
                        },
                        "metrics": {
                            "duration_hours": 7.5,
                            "deep_pct": 20.0,
                            "rem_pct": 22.2,
                            "efficiency_pct": 91.7,
                            "interruptions": 2,
                        },
                        "recommendations": [
                            {
                                "category": "interruptions",
                                "priority": "high",
                                "title": "Reduce Sleep Interruptions",
                                "description": "You had 2 interruptions per night on average.",
                                "tips": ["Use blackout curtains", "Try white noise"],
                            }
                        ],
                    }
                }
            },
        }
    },
)
async def calculate_sleep_score(input: SleepInput):
    """Calculate comprehensive sleep quality score."""
    from app.services.sleep_analyzer import SleepAnalyzer
    analyzer = SleepAnalyzer()
    result = analyzer.calculate_sleep_score(
        duration_hours=input.duration_hours,
        deep_minutes=input.deep_minutes,
        rem_minutes=input.rem_minutes,
        awake_minutes=input.awake_minutes,
        interruptions=input.interruptions,
        bedtime_consistency_std=input.bedtime_consistency_std,
    )
    recommendations = analyzer.get_recommendations(result)
    result["recommendations"] = recommendations
    return result


@router.post(
    "/recommendations",
    summary="Get personalized sleep recommendations",
    description="Returns prioritized sleep improvement recommendations based on the weakest sleep factors.",
    responses={
        200: {
            "description": "Recommendations and current score",
            "content": {
                "application/json": {
                    "example": {
                        "recommendations": [
                            {
                                "category": "deep_sleep",
                                "priority": "high",
                                "title": "Improve Deep Sleep",
                                "description": "Deep sleep is at 10.5% (target: 13-23%).",
                                "tips": [
                                    "Exercise regularly but not within 3 hours of bedtime",
                                    "Keep bedroom temperature at 65-68°F",
                                ],
                            }
                        ],
                        "current_score": 78.5,
                    }
                }
            },
        }
    },
)
async def get_recommendations(input: SleepInput):
    """Get personalized sleep improvement recommendations."""
    from app.services.sleep_analyzer import SleepAnalyzer
    analyzer = SleepAnalyzer()
    result = analyzer.calculate_sleep_score(
        duration_hours=input.duration_hours,
        deep_minutes=input.deep_minutes,
        rem_minutes=input.rem_minutes,
        awake_minutes=input.awake_minutes,
        interruptions=input.interruptions,
        bedtime_consistency_std=input.bedtime_consistency_std,
    )
    recommendations = analyzer.get_recommendations(result)
    return {"recommendations": recommendations, "current_score": result["sleep_score"]}


@router.post(
    "/trends",
    summary="Detect sleep trends over time",
    description="Analyzes a history of sleep records to detect improving, declining, or stable trends with statistical measures.",
    responses={
        200: {
            "description": "Trend analysis",
            "content": {
                "application/json": {
                    "example": {
                        "trend": "improving",
                        "slope": 0.8,
                        "average_score": 75.0,
                        "average_duration": 7.2,
                        "best_score": 92.0,
                        "worst_score": 45.0,
                        "data_points": 14,
                    }
                }
            },
        }
    },
)
async def detect_trends(input: SleepHistoryInput):
    """Detect trends in sleep history."""
    from app.services.sleep_analyzer import SleepAnalyzer
    analyzer = SleepAnalyzer()
    history_scores = []
    for record in input.history:
        score = analyzer.calculate_sleep_score(
            duration_hours=record.duration_hours,
            deep_minutes=record.deep_minutes,
            rem_minutes=record.rem_minutes,
            awake_minutes=record.awake_minutes,
            interruptions=record.interruptions,
            bedtime_consistency_std=record.bedtime_consistency_std,
        )
        history_scores.append(score)
    trends = analyzer.detect_trends(history_scores)
    return trends

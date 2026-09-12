"""
OpenAPI schemas for ZFIT new API endpoints.
Provides request/response models with full documentation for Swagger UI.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ── Workout Plans Schemas ─────────────────────────────────────────────────────

class WorkoutPlanGenerateRequest(BaseModel):
    """Request body for generating an AI workout plan."""
    goal: str = Field(
        ...,
        description="Training goal",
        examples=["strength", "hypertrophy", "endurance", "fat_loss", "flexibility"],
    )
    experience: str = Field(
        default="intermediate",
        description="Experience level",
        examples=["beginner", "intermediate", "advanced"],
    )
    days_per_week: int = Field(
        default=4,
        ge=1,
        le=7,
        description="Number of training days per week",
    )
    minutes_per_session: int = Field(
        default=60,
        ge=15,
        le=180,
        description="Available time per session in minutes",
    )
    equipment: list[str] = Field(
        default_factory=lambda: ["barbell", "dumbbells", "bench"],
        description="Available equipment",
    )
    split: Optional[str] = Field(
        default=None,
        description="Preferred training split (push/pull/legs, upper/lower, full_body, auto)",
    )


class WorkoutPlanResponse(BaseModel):
    """Response containing a generated workout plan."""
    name: str = Field(..., description="Plan name", example="Strength Builder 4-Day")
    goal: str = Field(..., description="Training goal", example="strength")
    duration_weeks: int = Field(..., description="Plan duration in weeks", example=8)
    days_per_week: int = Field(..., example=4)
    deload_weeks: list[int] = Field(
        default_factory=list,
        description="Week numbers for deload",
        example=[4, 8],
    )
    days: list[dict] = Field(
        default_factory=list,
        description="Weekly training days with exercises",
    )


class RecoveryScoreResponse(BaseModel):
    """Response containing HRV-based recovery score."""
    recovery_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Overall recovery score (0-100)",
        example=72.5,
    )
    readiness: str = Field(
        ...,
        description="Readiness label",
        example="good",
    )
    hrv_rmssd: float = Field(..., description="HRV RMSSD in ms", example=55.0)
    resting_hr: int = Field(..., description="Resting heart rate in bpm", example=62)
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recovery recommendations",
    )


class NutritionAnalysisRequest(BaseModel):
    """Request body for nutrition analysis."""
    weight_kg: float = Field(..., gt=0, description="Body weight in kg", example=75.0)
    goal: str = Field(
        ...,
        description="Nutrition goal",
        examples=["muscle_gain", "fat_loss", "maintenance", "performance"],
    )
    activity_level: str = Field(
        default="moderate",
        description="Activity level",
        examples=["sedentary", "light", "moderate", "active", "very_active"],
    )


class NutritionAnalysisResponse(BaseModel):
    """Response containing macro/micronutrient analysis."""
    calories: int = Field(..., description="Daily calorie target", example=2400)
    protein_g: int = Field(..., description="Daily protein in grams", example=150)
    carbs_g: int = Field(..., description="Daily carbs in grams", example=300)
    fat_g: int = Field(..., description="Daily fat in grams", example=80)
    fiber_g: int = Field(..., description="Daily fiber in grams", example=35)
    water_ml: int = Field(..., description="Daily water in ml", example=3000)
    meal_timing: list[dict] = Field(
        default_factory=list,
        description="Suggested meal timing",
    )


# ── Sleep Analysis Schemas ────────────────────────────────────────────────────

class SleepInput(BaseModel):
    """Input for sleep quality scoring."""
    duration_hours: float = Field(
        ...,
        ge=0,
        le=24,
        description="Total sleep duration in hours",
        example=7.5,
    )
    deep_minutes: float = Field(
        ...,
        ge=0,
        description="Deep sleep in minutes",
        example=90,
    )
    rem_minutes: float = Field(
        ...,
        ge=0,
        description="REM sleep in minutes",
        example=100,
    )
    awake_minutes: float = Field(
        default=0,
        ge=0,
        description="Time awake during the night in minutes",
        example=15,
    )
    interruptions: int = Field(
        default=0,
        ge=0,
        description="Number of sleep interruptions",
        example=2,
    )
    bedtime_consistency_std: float = Field(
        default=30.0,
        ge=0,
        description="Standard deviation of bedtime in minutes",
        example=20.0,
    )


class SleepScoreBreakdown(BaseModel):
    """Breakdown of individual sleep score components."""
    score: float = Field(..., ge=0, le=100, example=85.0)
    weight: float = Field(..., description="Weight in composite score", example=0.25)


class SleepScoreResponse(BaseModel):
    """Response containing comprehensive sleep quality score."""
    sleep_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Overall sleep quality score",
        example=78.5,
    )
    quality_label: str = Field(
        ...,
        description="Quality label",
        example="good",
    )
    breakdown: dict[str, SleepScoreBreakdown] = Field(
        ...,
        description="Score breakdown by component (duration, efficiency, deep_sleep, rem_sleep, consistency, interruptions)",
    )
    metrics: dict[str, float] = Field(
        ...,
        description="Raw sleep metrics",
        example={
            "duration_hours": 7.5,
            "deep_pct": 20.0,
            "rem_pct": 22.2,
            "efficiency_pct": 91.7,
            "interruptions": 2,
        },
    )
    recommendations: list[dict] = Field(
        default_factory=list,
        description="Personalized sleep improvement recommendations",
    )


class RecommendationItem(BaseModel):
    """A single sleep improvement recommendation."""
    category: str = Field(..., example="deep_sleep")
    priority: str = Field(..., description="Priority level", example="high")
    title: str = Field(..., example="Improve Deep Sleep")
    description: str = Field(..., example="Deep sleep is at 10.5% (target: 13-23%).")
    tips: list[str] = Field(
        default_factory=list,
        description="Actionable tips",
    )


class SleepRecommendationsResponse(BaseModel):
    """Response with sleep recommendations."""
    recommendations: list[RecommendationItem]
    current_score: float = Field(..., ge=0, le=100)


class SleepHistoryInput(BaseModel):
    """Input for sleep trend analysis."""
    history: list[SleepInput] = Field(
        ...,
        min_length=1,
        description="List of nightly sleep records",
    )


class SleepTrendResponse(BaseModel):
    """Response with sleep trend analysis."""
    trend: str = Field(
        ...,
        description="Trend direction",
        example="improving",
    )
    slope: float = Field(..., description="Linear trend slope", example=0.8)
    average_score: float = Field(..., example=75.0)
    average_duration: float = Field(..., example=7.2)
    best_score: float = Field(..., example=92.0)
    worst_score: float = Field(..., example=45.0)
    data_points: int = Field(..., example=14)

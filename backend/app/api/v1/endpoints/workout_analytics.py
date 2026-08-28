"""Advanced workout analytics: periodization insights, trend predictions, muscle balance."""
from fastapi import APIRouter, Query
from app.services.workout_analytics import (
    analyze_volume_trends, analyze_muscle_balance,
    generate_periodization_insight, generate_predictions,
    WorkoutAnalytics, VolumeTrend, MuscleBalance,
    PeriodizationInsight, TrendPrediction,
)

router = APIRouter()


@router.get("", response_model=WorkoutAnalytics)
async def get_analytics(user_id: str = Query("default")):
    """Get comprehensive workout analytics with ML insights."""
    # Get workout data from in-memory store
    try:
        from app.api.v1.endpoints.workouts import workout_history
        workouts = workout_history.get(user_id, [])
    except (ImportError, AttributeError):
        workouts = []

    try:
        from app.api.v1.endpoints.recovery import recovery_logs
        logs = recovery_logs.get(user_id, [])
    except (ImportError, AttributeError):
        logs = []

    # Generate analytics
    vol_trends = analyze_volume_trends(workouts)
    muscle_bal = analyze_muscle_balance(workouts)
    period_insight = generate_periodization_insight(workouts, logs)
    predictions = generate_predictions(workouts)

    # Overall score
    balance_score = mean([m.balance_score for m in muscle_bal]) if muscle_bal else 50
    trend_score = 70 if period_insight.current_phase != "unknown" else 30
    overall = round((balance_score + trend_score) / 2, 1)

    # Actionable insights
    insights = []
    for t in vol_trends:
        if t.direction != "stable":
            insights.append(f"Volume {t.direction}: {t.recommendation}")
    for m in muscle_bal:
        if m.status != "balanced":
            insights.append(f"{m.muscle_group}: {m.recommendation}")
    if period_insight.fatigue_accumulation > 70:
        insights.append("High fatigue detected. Consider a deload week.")
    if not insights:
        insights.append("Training is well-balanced. Keep up the consistency!")

    return WorkoutAnalytics(
        summary={
            "total_workouts": len(workouts),
            "total_volume_load": sum(
                sum(s.get("weight_kg", 0) * s.get("reps_completed", 0)
                    for ex in w.get("exercises", [])
                    for s in ex.get("sets", []))
                for w in workouts
            ),
            "avg_session_duration": 45,  # Placeholder
            "muscles_tracked": len(set(
                ex.get("target_muscle", "")
                for w in workouts
                for ex in w.get("exercises", [])
            )),
        },
        volume_trends=vol_trends,
        muscle_balance=muscle_bal,
        periodization_insights=period_insight,
        predictions=predictions,
        overall_score=overall,
        actionable_insights=insights,
    )


@router.get("/volume-trends", response_model=list[VolumeTrend])
async def get_volume_trends(user_id: str = Query("default")):
    """Get volume trend analysis."""
    try:
        from app.api.v1.endpoints.workouts import workout_history
        workouts = workout_history.get(user_id, [])
    except (ImportError, AttributeError):
        workouts = []
    return analyze_volume_trends(workouts)


@router.get("/muscle-balance", response_model=list[MuscleBalance])
async def get_muscle_balance(user_id: str = Query("default")):
    """Get muscle group balance analysis."""
    try:
        from app.api.v1.endpoints.workouts import workout_history
        workouts = workout_history.get(user_id, [])
    except (ImportError, AttributeError):
        workouts = []
    return analyze_muscle_balance(workouts)


@router.get("/predictions", response_model=list[TrendPrediction])
async def get_predictions(user_id: str = Query("default")):
    """Get trend predictions (30d and 90d)."""
    try:
        from app.api.v1.endpoints.workouts import workout_history
        workouts = workout_history.get(user_id, [])
    except (ImportError, AttributeError):
        workouts = []
    return generate_predictions(workouts)

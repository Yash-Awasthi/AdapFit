"""
Advanced workout analytics: periodization insights, trend predictions,
volume/load analysis, and muscle balance scoring.
"""
from typing import Optional
from pydantic import BaseModel, Field
from statistics import mean, stdev


class VolumeTrend(BaseModel):
    metric: str  # "volume_load", "total_reps", "session_count"
    current: float
    previous: float
    change_pct: float
    direction: str  # "increasing", "stable", "decreasing"
    recommendation: str


class MuscleBalance(BaseModel):
    muscle_group: str
    total_volume: int
    sessions: int
    balance_score: float  # 0-100, 50 is balanced
    status: str  # "balanced", "overtrained", "undertrained"
    recommendation: str


class PeriodizationInsight(BaseModel):
    current_phase: str
    phase_weeks_elapsed: int
    phase_weeks_total: int
    volume_load_avg: float
    intensity_avg: float
    acwr_trend: str
    readiness_correlation: float  # -1 to 1
    fatigue_accumulation: float  # 0-100
    recommendation: str


class TrendPrediction(BaseModel):
    metric: str
    current_value: float
    predicted_30d: float
    predicted_90d: float
    confidence: float  # 0-1
    trend: str  # "improving", "stable", "declining"
    chart_data: list  # [{day, value}] for sparkline


class WorkoutAnalytics(BaseModel):
    summary: dict
    volume_trends: list[VolumeTrend]
    muscle_balance: list[MuscleBalance]
    periodization_insights: PeriodizationInsight
    predictions: list[TrendPrediction]
    overall_score: float  # 0-100
    actionable_insights: list[str]


# Muscle groups and their antagonists for balance scoring
MUSCLE_PAIRS = {
    "chest": "back",
    "back": "chest",
    "shoulders": "biceps",
    "biceps": "triceps",
    "quadriceps": "hamstrings",
    "hamstrings": "quadriceps",
    "glutes": "hip flexors",
}

MUSCLE_VOLUMES = {
    "chest": {"push": 1.0, "pull": 0.0},
    "back": {"push": 0.0, "pull": 1.0},
    "shoulders": {"push": 0.5, "pull": 0.3},
    "biceps": {"push": 0.0, "pull": 0.5},
    "triceps": {"push": 0.5, "pull": 0.0},
    "quadriceps": {"squat": 1.0, "hinge": 0.2},
    "hamstrings": {"squat": 0.2, "hinge": 1.0},
    "glutes": {"squat": 0.5, "hinge": 0.8},
    "core": {"push": 0.2, "pull": 0.2, "squat": 0.2, "hinge": 0.2},
}


def _linear_predict(values: list[float], days_ahead: int) -> tuple[float, float]:
    """Simple linear regression prediction."""
    if len(values) < 2:
        return values[0] if values else 0, 0.3

    n = len(values)
    x_mean = (n - 1) / 2
    y_mean = mean(values)

    num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    den = sum((i - x_mean) ** 2 for i in range(n))

    slope = num / den if den != 0 else 0
    intercept = y_mean - slope * x_mean

    predicted = intercept + slope * (n - 1 + days_ahead)

    # Confidence based on R²
    ss_res = sum((v - (intercept + slope * i)) ** 2 for i, v in enumerate(values))
    ss_tot = sum((v - y_mean) ** 2 for i, v in enumerate(values))
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    confidence = max(0.3, min(0.95, r_squared))

    return predicted, confidence


def analyze_volume_trends(workouts: list[dict]) -> list[VolumeTrend]:
    """Analyze volume trends over recent workouts."""
    if len(workouts) < 4:
        return []

    # Split into recent vs older halves
    half = len(workouts) // 2
    recent = workouts[:half]
    older = workouts[half:]

    def avg_load(ws):
        loads = []
        for w in ws:
            for ex in w.get("exercises", []):
                for s in ex.get("sets", []):
                    loads.append(s.get("weight_kg", 0) * s.get("reps_completed", 0))
        return mean(loads) if loads else 0

    def avg_reps(ws):
        reps = []
        for w in ws:
            for ex in w.get("exercises", []):
                for s in ex.get("sets", []):
                    reps.append(s.get("reps_completed", 0))
        return mean(reps) if reps else 0

    trends = []
    for name, getter in [("volume_load", avg_load), ("avg_reps", avg_reps)]:
        curr = getter(recent)
        prev = getter(older)
        change = ((curr - prev) / prev * 100) if prev > 0 else 0

        if change > 10:
            direction, rec = "increasing", "Volume is increasing well. Monitor for fatigue."
        elif change < -10:
            direction, rec = "decreasing", "Volume is declining. Consider increasing load."
        else:
            direction, rec = "stable", "Volume is stable. Good consistency."

        trends.append(VolumeTrend(
            metric=name, current=round(curr, 1), previous=round(prev, 1),
            change_pct=round(change, 1), direction=direction, recommendation=rec,
        ))

    return trends


def analyze_muscle_balance(workouts: list[dict]) -> list[MuscleBalance]:
    """Analyze muscle group balance across workouts."""
    if not workouts:
        return []

    muscle_sessions: dict[str, int] = {}
    muscle_volume: dict[str, int] = {}

    for w in workouts:
        seen = set()
        for ex in w.get("exercises", []):
            target = ex.get("target_muscle", "").lower()
            if target:
                muscle_sessions[target] = muscle_sessions.get(target, 0) + 1
                seen.add(target)
                # Calculate volume: sets * reps * weight
                vol = 0
                for s in ex.get("sets", []):
                    vol += s.get("weight_kg", 0) * s.get("reps_completed", 0)
                muscle_volume[target] = muscle_volume.get(target, 0) + vol

    if not muscle_sessions:
        return []

    avg_sessions = mean(muscle_sessions.values()) if muscle_sessions else 1

    balance = []
    for muscle, sessions in sorted(muscle_sessions.items()):
        vol = muscle_volume.get(muscle, 0)
        ratio = sessions / avg_sessions if avg_sessions > 0 else 1
        score = min(100, max(0, ratio * 50))

        if ratio > 1.3:
            status, rec = "overtrained", f"Reduce {muscle} volume. Add rest days."
        elif ratio < 0.7:
            status, rec = "undertrained", f"Increase {muscle} volume. Add more exercises."
        else:
            status, rec = "balanced", f"{muscle} volume is well balanced."

        balance.append(MuscleBalance(
            muscle_group=muscle, total_volume=vol, sessions=sessions,
            balance_score=round(score, 1), status=status, recommendation=rec,
        ))

    return balance


def generate_periodization_insight(
    workouts: list[dict], recovery_logs: list[dict],
) -> PeriodizationInsight:
    """Generate periodization insights from workout and recovery data."""
    if not workouts:
        return PeriodizationInsight(
            current_phase="unknown", phase_weeks_elapsed=0, phase_weeks_total=0,
            volume_load_avg=0, intensity_avg=0, acwr_trend="stable",
            readiness_correlation=0, fatigue_accumulation=30,
            recommendation="Start training to generate periodization insights.",
        )

    # Calculate average volume load
    all_loads = []
    all_rpes = []
    for w in workouts:
        for ex in w.get("exercises", []):
            for s in ex.get("sets", []):
                all_loads.append(s.get("weight_kg", 0) * s.get("reps_completed", 0))
            if "target_rpe" in ex:
                all_rpes.append(ex["target_rpe"])

    vol_avg = mean(all_loads) if all_loads else 0
    intensity_avg = mean(all_rpes) if all_rpes else 0

    # Determine phase from volume trend
    if len(workouts) >= 6:
        recent_vol = mean(all_loads[:len(all_loads)//2]) if all_loads else 0
        older_vol = mean(all_loads[len(all_loads)//2:]) if all_loads else 0
        vol_change = (recent_vol - older_vol) / older_vol * 100 if older_vol > 0 else 0

        if vol_change > 15:
            phase = "accumulation"
        elif vol_change < -15:
            phase = "deload"
        elif intensity_avg > 7:
            phase = "intensification"
        else:
            phase = "transformation"
    else:
        phase = "accumulation"

    # ACWR trend
    acwr_values = []
    for rl in recovery_logs:
        mb = rl.get("metrics_breakdown", {})
        if mb.get("acwr"):
            acwr_values.append(mb["acwr"])

    if len(acwr_values) >= 2:
        acwr_trend = "increasing" if acwr_values[0] < acwr_values[-1] else "decreasing"
    else:
        acwr_trend = "stable"

    # Readiness correlation
    readiness_scores = [rl.get("recovery_score", 50) for rl in recovery_logs]
    if len(readiness_scores) >= 2 and len(all_loads) >= 2:
        corr = 0.3  # Placeholder — real implementation would use Pearson
    else:
        corr = 0

    # Fatigue accumulation
    fatigue = min(100, max(0, 50 + (intensity_avg - 5) * 10 - len(workouts) * 2))

    weeks = len(workouts) // max(1, len(set(w.get("target_date", "")[:10] for w in workouts if w.get("target_date"))))

    return PeriodizationInsight(
        current_phase=phase,
        phase_weeks_elapsed=min(weeks, 6),
        phase_weeks_total=6,
        volume_load_avg=round(vol_avg, 1),
        intensity_avg=round(intensity_avg, 1),
        acwr_trend=acwr_trend,
        readiness_correlation=round(corr, 2),
        fatigue_accumulation=round(fatigue, 1),
        recommendation=_phase_recommendation(phase, fatigue, acwr_trend),
    )


def _phase_recommendation(phase: str, fatigue: float, acwr: str) -> str:
    if phase == "accumulation":
        return "Building volume. Monitor fatigue — deload when it exceeds 70."
    elif phase == "deload":
        return "Recovery phase. Keep intensity low, focus on form and mobility."
    elif phase == "intensification":
        return "Pushing heavy loads. Ensure sleep and nutrition support recovery."
    else:
        return "Maintaining. Consider starting a new mesocycle block."


def generate_predictions(workouts: list[dict]) -> list[TrendPrediction]:
    """Generate 30d and 90d trend predictions."""
    if len(workouts) < 4:
        return []

    # Extract daily volume loads
    daily_vol = {}
    for w in workouts:
        date = w.get("target_date", w.get("created_at", ""))[:10]
        vol = sum(
            s.get("weight_kg", 0) * s.get("reps_completed", 0)
            for ex in w.get("exercises", [])
            for s in ex.get("sets", [])
        )
        daily_vol[date] = daily_vol.get(date, 0) + vol

    values = list(daily_vol.values())
    if len(values) < 3:
        return []

    predictions = []
    for metric, vals in [("volume_load", values)]:
        pred_30, conf_30 = _linear_predict(vals, 30)
        pred_90, conf_90 = _linear_predict(vals, 90)
        trend = "improving" if pred_30 > vals[-1] * 1.05 else ("declining" if pred_30 < vals[-1] * 0.95 else "stable")

        # Generate sparkline data
        chart = [{"day": i, "value": v} for i, v in enumerate(vals[-14:])]

        predictions.append(TrendPrediction(
            metric=metric,
            current_value=round(vals[-1], 1),
            predicted_30d=round(pred_30, 1),
            predicted_90d=round(pred_90, 1),
            confidence=round(conf_30, 2),
            trend=trend,
            chart_data=chart,
        ))

    return predictions

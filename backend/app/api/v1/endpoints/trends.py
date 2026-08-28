from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.services.recovery_engine import RecoveryEngine
from app.services.ml_engine import ml_engine
from app.services.nlp_pipeline import nlp_pipeline
from app.services.agent.evolution_engine import evolution_engine
from app.services.agent.orchestrator import agent_orchestrator
from app.services.spark_processor import spark_analytics
from app.services.vector_store import vector_store
from app.models.schemas import SentimentRequest, GoalParsingRequest, NLPFeedbackRequest
from app.core.config import settings
from app.core.storage import storage
from app.core.background import task_manager
from core_engine import is_rust_available

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/acwr")
async def get_acwr_status(user_id: str):
    history = await storage.get_workload_history(user_id, 28)
    loads = [h.get("session_load", 0) for h in history]

    if loads:
        from core_engine import compute_ewma
        acute_ewma = compute_ewma(loads[-7:], 7)
        chronic_ewma = compute_ewma(loads[-28:], 28)
        acute = acute_ewma[-1] if acute_ewma else 500
        chronic = chronic_ewma[-1] if chronic_ewma else 500
    else:
        acute = 480.0
        chronic = settings.DEFAULT_CHRONIC_LOAD

    acwr_val, acwr_status, penalty = RecoveryEngine.evaluate_acwr(acute, chronic)

    return {
        "user_id": user_id,
        "acute_workload_7d": round(acute, 1),
        "chronic_workload_28d": round(chronic, 1),
        "acwr": acwr_val,
        "acwr_status": acwr_status,
        "recovery_penalty": penalty,
        "history_count": len(history),
    }

@router.get("/hrv")
async def get_hrv_trend(user_id: str, days: int = 28):
    logs = await storage.get_recovery_logs(user_id, days)
    hrv_values = [r.get("hrv_rmssd") for r in logs if r.get("hrv_rmssd")]

    forecast = ml_engine.forecast_hrv(hrv_values, days_ahead=7) if hrv_values else {"trend": "no_data"}
    anomalies = ml_engine.detect_anomalies(hrv_values) if len(hrv_values) >= 3 else {"anomalies": []}

    return {
        "user_id": user_id,
        "hrv_history": hrv_values,
        "dates": [r.get("log_date", "") for r in logs if r.get("hrv_rmssd")],
        "forecast": forecast,
        "anomalies": anomalies,
    }

@router.get("/sleep")
async def get_sleep_trend(user_id: str, days: int = 28):
    logs = await storage.get_recovery_logs(user_id, days)
    sleep_data = [{"hours": r.get("sleep_duration_hours"), "efficiency": r.get("sleep_efficiency_pct"), "date": r.get("log_date")} for r in logs if r.get("sleep_duration_hours")]
    return {"user_id": user_id, "items": sleep_data, "count": len(sleep_data)}

@router.get("/ml-insights")
async def get_ml_insights(user_id: str):
    recovery_logs = await storage.get_recovery_logs(user_id, 28)
    workout_logs = await storage.get_workout_logs(user_id, 28)

    features = ml_engine.extract_features(recovery_logs, workout_logs)
    predictions = ml_engine.predict_readiness(features)

    hrv_values = [r.get("hrv_rmssd", 50) for r in recovery_logs if r.get("hrv_rmssd")]
    hrv_forecast = ml_engine.forecast_hrv(hrv_values) if hrv_values else {"trend": "no_data"}

    recovery_scores = [r.get("recovery_score", 70) for r in recovery_logs]
    anomalies = ml_engine.detect_anomalies(recovery_scores) if len(recovery_scores) >= 3 else {"anomalies": []}

    return {
        "user_id": user_id,
        "readiness_prediction": predictions,
        "hrv_forecast": hrv_forecast,
        "recovery_anomalies": anomalies,
        "model_status": ml_engine.get_status(),
        "core_engine_rust": is_rust_available(),
    }

@router.get("/alerts")
async def get_anomaly_alerts(user_id: str):
    """Consolidated anomaly alerts across all metrics."""
    recovery_logs = await storage.get_recovery_logs(user_id, 28)
    workout_logs = await storage.get_workout_logs(user_id, 28)

    alerts = []

    # Check recovery score anomalies
    recovery_scores = [r.get("recovery_score", 70) for r in recovery_logs]
    if len(recovery_scores) >= 3:
        r_anomalies = ml_engine.detect_anomalies(recovery_scores)
        for a in r_anomalies.get("anomalies", []):
            alerts.append({"type": "recovery_score", "severity": "high", "detail": f"Recovery score {a['value']} (z={a['z_score']}) is anomalous"})

    # Check HRV anomalies
    hrv_values = [r.get("hrv_rmssd") for r in recovery_logs if r.get("hrv_rmssd")]
    if len(hrv_values) >= 3:
        h_anomalies = ml_engine.detect_anomalies(hrv_values)
        for a in h_anomalies.get("anomalies", []):
            alerts.append({"type": "hrv", "severity": "high", "detail": f"HRV {a['value']}ms (z={a['z_score']}) is anomalous"})

    # Check ACWR danger
    if workout_logs:
        last_log = workout_logs[-1]
        acwr = last_log.get("acwr", 1.0)
        if acwr > 1.5:
            alerts.append({"type": "acwr", "severity": "critical", "detail": f"ACWR {acwr:.2f} exceeds danger threshold (1.5). Deload recommended."})
        elif acwr > 1.3:
            alerts.append({"type": "acwr", "severity": "warning", "detail": f"ACWR {acwr:.2f} in caution zone. Reduce volume."})

    # Check sleep debt
    sleep_hours = [r.get("sleep_duration_hours") for r in recovery_logs[-3:] if r.get("sleep_duration_hours")]
    if sleep_hours:
        avg_sleep = sum(sleep_hours) / len(sleep_hours)
        if avg_sleep < 6.0:
            alerts.append({"type": "sleep", "severity": "warning", "detail": f"Average sleep {avg_sleep:.1f}h is below recommended 7h."})

    # Check consecutive high RPE
    high_rpe_count = 0
    for wl in reversed(workout_logs):
        if wl.get("session_rpe", 0) >= 7:
            high_rpe_count += 1
        else:
            break
    if high_rpe_count >= 5:
        alerts.append({"type": "overtraining", "severity": "critical", "detail": f"{high_rpe_count} consecutive high-RPE sessions. Risk of overtraining."})
    elif high_rpe_count >= 3:
        alerts.append({"type": "overtraining", "severity": "warning", "detail": f"{high_rpe_count} consecutive high-RPE sessions. Monitor fatigue."})

    return {
        "user_id": user_id,
        "alerts": alerts,
        "alert_count": len(alerts),
        "has_critical": any(a["severity"] == "critical" for a in alerts),
    }


@router.get("/tasks")
async def get_background_tasks():
    """Get background task manager status."""
    return task_manager.get_status()


@router.get("/agent-status")
async def get_agent_status():
    return {
        "orchestrator": agent_orchestrator.get_status(),
        "spark": spark_analytics.get_status(),
        "vector_store": vector_store.get_status(),
        "nlp": nlp_pipeline.get_status(),
        "ml_engine": ml_engine.get_status(),
        "core_engine_rust": is_rust_available(),
    }

@router.get("/agent/preferences/{user_id}")
async def get_agent_preferences(user_id: str):
    return await evolution_engine.generate_personalization_report(user_id)

@router.get("/agent/insights/{user_id}")
async def get_agent_insights(user_id: str):
    recovery_logs = await storage.get_recovery_logs(user_id, 28)
    workout_logs = await storage.get_workout_logs(user_id, 7)
    user = await storage.get_user(user_id)

    summary = await nlp_pipeline.generate_weekly_summary(user or {}, recovery_logs, workout_logs)
    personalization = await evolution_engine.generate_personalization_report(user_id)
    strategy = await evolution_engine.detect_strategy_shifts(user_id)

    return {
        "user_id": user_id,
        "weekly_summary": summary,
        "personalization": personalization,
        "strategy_shift": strategy,
    }

@router.post("/nlp/sentiment")
@limiter.limit("30/minute")
async def analyze_sentiment(request: Request, req: SentimentRequest):
    return nlp_pipeline.analyze_sentiment(req.text)

@router.post("/nlp/parse-goals")
@limiter.limit("10/minute")
async def parse_goals(request: Request, req: GoalParsingRequest):
    return await nlp_pipeline.parse_goals_from_text(req.text)

@router.post("/nlp/feedback")
@limiter.limit("30/minute")
async def analyze_feedback(request: Request, req: NLPFeedbackRequest):
    result = nlp_pipeline.extract_exercise_feedback(req.text)
    if req.exercise_id:
        result["mentioned_muscles"] = nlp_pipeline.extract_mentioned_muscles(req.text)
    return result


@router.get("/correlations/{user_id}")
async def get_metric_correlations(user_id: str):
    """Analyze correlations between fitness metrics (sleep vs HRV, workload vs recovery, etc.)."""
    recovery_logs = await storage.get_recovery_logs(user_id, 28)
    workout_logs = await storage.get_workload_history(user_id, 28)

    result = ml_engine.correlation.analyze_metric_correlations(recovery_logs, workout_logs)
    result["user_id"] = user_id
    return result


@router.get("/fatigue-forecast/{user_id}")
async def get_fatigue_forecast(user_id: str):
    """Forecast fatigue trajectory and suggest deload timing."""
    workout_logs = await storage.get_workout_logs(user_id, 28)
    recovery_logs = await storage.get_recovery_logs(user_id, 28)

    result = ml_engine.fatigue_forecaster.forecast_fatigue_trajectory(workout_logs, recovery_logs)
    result["user_id"] = user_id
    return result


@router.get("/volume-capacity/{user_id}")
async def get_volume_capacity(user_id: str):
    """Estimate today's training volume capacity based on recovery state."""
    recovery_logs = await storage.get_recovery_logs(user_id, 28)
    workout_logs = await storage.get_workout_logs(user_id, 14)

    recovery_score = recovery_logs[-1].get("recovery_score", 70) if recovery_logs else 70
    acwr = workout_logs[-1].get("acwr", 1.0) if workout_logs else 1.0
    sleep_hours = recovery_logs[-1].get("sleep_duration_hours", 7) if recovery_logs else 7

    avg_volume = 0
    if workout_logs:
        volumes = [w.get("session_load", 500) for w in workout_logs[-7:]]
        avg_volume = sum(volumes) / max(len(volumes), 1)

    result = ml_engine.performance_predictor.predict_volume_capacity(
        recovery_score, avg_volume, acwr, sleep_hours
    )
    result["user_id"] = user_id
    return result

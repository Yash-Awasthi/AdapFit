import uuid
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import (
    WorkoutGenerateRequest, WorkoutGenerateResponse,
    WorkoutCompleteRequest, WorkoutCompleteResponse,
    ReadinessState, ACWRStatus, SemanticSearchRequest, ExerciseSubstitutionRequest,
)
from app.services.recommendation_engine import recommendation_engine
from app.services.recovery_engine import RecoveryEngine
from app.services.vector_store import vector_store
from app.services.agent.evolution_engine import evolution_engine
from app.services.ml_engine import ml_engine
from app.services.nlp_pipeline import nlp_pipeline
from app.core.config import settings
from app.core.storage import storage

router = APIRouter()

@router.post("", response_model=WorkoutGenerateResponse, status_code=status.HTTP_201_CREATED)
async def create_workout(req: WorkoutGenerateRequest):
    """Generate an adaptive workout based on recovery state and user preferences."""
    try:
        latest_recovery = await storage.get_recovery_logs(req.user_id, 1)
        readiness = ReadinessState.MODERATE
        recovery_score = 75
        sore_muscles = []

        if latest_recovery:
            last = latest_recovery[-1]
            readiness = ReadinessState(last.get("readiness_state", "MODERATE"))
            recovery_score = last.get("recovery_score", 75)
            sore_muscles = last.get("sore_muscle_groups", [])

        user = await storage.get_user(req.user_id)
        equipment = user.get("equipment_access", ["bodyweight", "dumbbells"]) if user else ["bodyweight", "dumbbells"]
        goal = user.get("primary_goal", "hypertrophy") if user else "hypertrophy"

        prefs = await evolution_engine.get_personalization_vector(req.user_id)

        response = await recommendation_engine.generate_workout(
            user_id=req.user_id,
            target_date=req.target_date,
            readiness_state=readiness,
            recovery_score=recovery_score,
            sore_muscles=sore_muscles,
            equipment_access=equipment,
            target_duration=req.target_duration_minutes,
            goal=goal,
        )

        await storage.save_workout(req.user_id, response.model_dump())

        recovery_logs = await storage.get_recovery_logs(req.user_id, 28)
        workout_logs = await storage.get_workout_logs(req.user_id, 28)
        features = ml_engine.extract_features(recovery_logs, workout_logs)
        ml_predictions = ml_engine.predict_readiness(features)

        memory = await storage.get_agent_memory(req.user_id)

        return WorkoutGenerateResponse(
            workout_id=response.workout_id,
            title=response.title,
            readiness_state=response.readiness_state,
            adaptation_rationale=response.adaptation_rationale,
            target_duration_minutes=response.target_duration_minutes,
            warmup=response.warmup,
            exercises=response.exercises,
            cooldown=response.cooldown,
            ml_insights=ml_predictions,
            agent_memory_insights={"exercise_preferences": dict(list(prefs.items())[:10]), "accepted_count": memory.get("accepted_workouts", 0)},
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Workout generation failed")

@router.patch("/{workout_id}", response_model=WorkoutCompleteResponse)
async def complete_workout(workout_id: str, req: WorkoutCompleteRequest):
    """Mark a workout as completed and log performance data."""
    try:
        session_load = float(req.actual_duration_minutes * req.session_rpe)

        history = await storage.get_workload_history(req.user_id, 28)
        existing_loads = [h.get("session_load", 0) for h in history]

        from core_engine import compute_ewma
        all_loads = existing_loads + [session_load]
        acute_ewma = compute_ewma(all_loads[-7:], 7)
        chronic_ewma = compute_ewma(all_loads[-28:], 28)

        acute_load = acute_ewma[-1] if acute_ewma else session_load * 7
        chronic_load = chronic_ewma[-1] if chronic_ewma else settings.DEFAULT_CHRONIC_LOAD

        acwr_val, acwr_status, _ = RecoveryEngine.evaluate_acwr(acute_load, chronic_load)
        acwr = acwr_val or 1.0

        await storage.add_workload_entry(req.user_id, {
            "session_load": session_load,
            "acute_load": round(acute_load, 1),
            "chronic_load": round(chronic_load, 1),
            "acwr": acwr,
            "session_rpe": req.session_rpe,
        })

        log_id = str(uuid.uuid4())
        await storage.add_workout_log(req.user_id, {
            "id": log_id,
            "workout_id": workout_id,
            "actual_duration_minutes": req.actual_duration_minutes,
            "session_rpe": req.session_rpe,
            "session_load": session_load,
            "acute_load_7d": round(acute_load, 1),
            "chronic_load_28d": round(chronic_load, 1),
            "acwr": acwr,
            "acwr_status": acwr_status,
            "logged_exercises": [ex.model_dump() for ex in req.logged_exercises],
            "user_feedback_notes": req.user_feedback_notes,
        })

        nlp_sentiment = None
        if req.user_feedback_notes:
            nlp_sentiment = nlp_pipeline.analyze_sentiment(req.user_feedback_notes)
            feedback_extract = nlp_pipeline.extract_exercise_feedback(req.user_feedback_notes)
            if feedback_extract.get("pain_flagged"):
                for ex in req.logged_exercises:
                    await evolution_engine.record_exercise_feedback(req.user_id, ex.exercise_id, "pain", req.user_feedback_notes)

        await evolution_engine.record_workout_accepted(req.user_id, [ex.model_dump() for ex in req.logged_exercises])

        recovery_logs = await storage.get_recovery_logs(req.user_id, 28)
        workout_logs = await storage.get_workout_logs(req.user_id, 7)
        features = ml_engine.extract_features(recovery_logs, workout_logs)
        hrv_forecast = ml_engine.forecast_hrv(
            [r.get("hrv_rmssd", 50) for r in recovery_logs if r.get("hrv_rmssd")]
        ) if any(r.get("hrv_rmssd") for r in recovery_logs) else {"slope": 0.0}

        consecutive_high = 0
        for wl in reversed(workout_logs):
            if wl.get("session_rpe", 0) >= 7:
                consecutive_high += 1
            else:
                break

        injury_risk = ml_engine.compute_injury_risk(acwr, hrv_forecast.get("slope", 0.0), 0.0, consecutive_high)

        deload = acwr_status == ACWRStatus.DANGER_ZONE
        msg = "Workout logged. ACWR and workload indexed."
        if deload:
            msg += " WARNING: ACWR > 1.5 — deload recommended."

        return WorkoutCompleteResponse(
            log_id=log_id,
            session_load=session_load,
            acute_load_7d=round(acute_load, 1),
            chronic_load_28d=round(chronic_load, 1),
            acwr=acwr,
            acwr_status=acwr_status,
            deload_recommended=deload,
            message=msg,
            nlp_sentiment=nlp_sentiment,
            injury_risk=injury_risk,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Workout completion failed")

@router.get("")
async def list_workouts(user_id: str, days: int = 14):
    """List workout history."""
    workouts = await storage.get_workouts(user_id, days)
    return {"user_id": user_id, "items": workouts, "count": len(workouts)}

import uuid
from datetime import datetime, timezone
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
from app.services.nlp_pipeline import nlp_pipeline
from app.core.config import settings
from app.core import workout_metrics
from app.core.storage import storage

router = APIRouter()

@router.post("", response_model=WorkoutGenerateResponse, status_code=status.HTTP_201_CREATED)
async def create_workout(req: WorkoutGenerateRequest):
    """Generate an adaptive workout based on recovery state and user preferences."""
    try:
        # Only the check-in for the day being planned counts; without one the session is a standard one, and says so.
        latest = await storage.get_recovery_logs(req.user_id, 1)
        today = latest[-1] if latest and str(latest[-1].get("log_date", ""))[:10] == str(req.target_date)[:10] else None
        readiness = ReadinessState(today["readiness_state"]) if today and today.get("readiness_state") else ReadinessState.MODERATE
        recovery_score = today.get("recovery_score") if today else None
        sore_muscles = (today.get("sore_muscle_groups") or []) if today else []

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

        if today is None:
            response.adaptation_rationale = ("No check-in for this day, so this is a standard session. "
                                             + response.adaptation_rationale)
        await storage.save_workout(req.user_id, response.model_dump())

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
            agent_memory_insights={"exercise_preferences": dict(list(prefs.items())[:10]), "accepted_count": memory.get("accepted_workouts", 0)},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Workout generation failed") from e

@router.patch("/{workout_id}", response_model=WorkoutCompleteResponse)
async def complete_workout(workout_id: str, req: WorkoutCompleteRequest):
    """Mark a workout as completed and log performance data."""
    try:
        session_load = float(req.actual_duration_minutes * req.session_rpe)
        entry = {"session_load": session_load, "session_rpe": req.session_rpe,
                 "recorded_at": datetime.now(timezone.utc).isoformat()}
        history = await storage.get_workload_history(req.user_id, workout_metrics.HISTORY_ENTRIES)
        acute_load, chronic_load = workout_metrics.acwr(history + [entry])
        acwr, acwr_status, _ = RecoveryEngine.evaluate_acwr(acute_load, chronic_load)
        if acwr is None:
            acwr_status = None
        await storage.add_workload_entry(req.user_id, {
            **entry, "acute_load": acute_load, "chronic_load": chronic_load, "acwr": acwr,
        })

        log_id = str(uuid.uuid4())
        await storage.add_workout_log(req.user_id, {
            "id": log_id,
            "workout_id": workout_id,
            "actual_duration_minutes": req.actual_duration_minutes,
            "session_rpe": req.session_rpe,
            "session_load": session_load,
            "acute_load_7d": acute_load,
            "chronic_load_28d": chronic_load,
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

        deload = acwr_status == ACWRStatus.DANGER_ZONE
        msg = "Workout logged." if acwr is not None else "Workout logged. Training load needs 4 weeks of sessions."
        if deload:
            msg += " WARNING: ACWR > 1.5 — deload recommended."

        return WorkoutCompleteResponse(
            log_id=log_id,
            session_load=session_load,
            acute_load_7d=acute_load,
            chronic_load_28d=chronic_load,
            acwr=acwr,
            acwr_status=acwr_status,
            deload_recommended=deload,
            message=msg,
            nlp_sentiment=nlp_sentiment,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Workout completion failed") from e

@router.get("")
async def list_workouts(user_id: str, days: int = 14):
    """List workout history."""
    workouts = await storage.get_workouts(user_id, days)
    return {"user_id": user_id, "items": workouts, "count": len(workouts)}

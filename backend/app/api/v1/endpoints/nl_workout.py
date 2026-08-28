"""
Natural Language Workout Logging
Parse free-text workout descriptions into structured data.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.services.nl_workout_logger import nl_workout_logger
from app.services.intent_classifier import intent_classifier, entity_extractor
from app.services.rag_knowledge import rag_retriever
from app.core.storage import storage

router = APIRouter()


class NLWorkoutRequest(BaseModel):
    user_id: str
    text: str = Field(min_length=3, max_length=2000, description="Natural language workout description")
    auto_log: bool = Field(default=False, description="Auto-log if parse confidence is high")


class ParsedExercise(BaseModel):
    exercise_id: str
    name: str
    sets: int
    reps: int
    weight_kg: float = 0.0
    rpe: Optional[float] = None
    volume_kg: float = 0.0


class NLWorkoutResponse(BaseModel):
    raw_text: str
    parsed_exercises: List[Dict[str, Any]]
    cardio: List[Dict[str, Any]]
    duration_minutes: Optional[int]
    global_rpe: Optional[float]
    total_sets: int
    total_reps: int
    total_volume_kg: float
    parse_confidence: float
    logged: bool
    intent: Dict[str, Any]
    entities: Dict[str, Any]
    coaching_tip: Optional[str] = None


@router.post("", response_model=NLWorkoutResponse)
async def parse_workout_text(req: NLWorkoutRequest):
    """Parse a natural language workout description into structured data."""
    # Classify intent
    intent = intent_classifier.classify(req.text)

    # Extract entities
    entities = entity_extractor.extract_all(req.text)

    # Parse the workout
    parsed = nl_workout_logger.parse(req.text)

    # Determine if auto-logged
    logged = False
    if parsed["parse_confidence"] >= 0.7 and req.auto_log:
        try:
            workout_log = {
                "exercises": parsed["exercises"],
                "cardio": parsed["cardio"],
                "duration_minutes": parsed["duration_minutes"],
                "session_rpe": parsed["global_rpe"] or 5,
                "user_feedback_notes": parsed["notes"],
                "source": "nl_parser",
            }
            await storage.add_workout_log(req.user_id, workout_log)
            logged = True
        except Exception:
            pass

    # Get coaching tip based on parsed data
    coaching_tip = None
    if parsed["exercises"]:
        total_vol = parsed["total_volume_kg"]
        if total_vol > 10000:
            coaching_tip = "High volume session — ensure adequate protein intake and sleep tonight."
        elif total_vol > 5000:
            coaching_tip = "Solid training volume. Track RPE trends to monitor fatigue accumulation."
        if parsed["global_rpe"] and parsed["global_rpe"] >= 9:
            coaching_tip = "High RPE session. Consider a lighter session tomorrow to manage fatigue."
        if parsed["global_rpe"] and parsed["global_rpe"] <= 4:
            coaching_tip = "Low RPE — this looks like a technique/mobility session. Good for recovery days."

    return NLWorkoutResponse(
        raw_text=req.text,
        parsed_exercises=parsed["exercises"],
        cardio=parsed["cardio"],
        duration_minutes=parsed["duration_minutes"],
        global_rpe=parsed["global_rpe"],
        total_sets=parsed["total_sets"],
        total_reps=parsed["total_reps"],
        total_volume_kg=parsed["total_volume_kg"],
        parse_confidence=parsed["parse_confidence"],
        logged=logged,
        intent=intent,
        entities=entities,
        coaching_tip=coaching_tip,
    )


@router.post("/batch")
async def batch_parse_workouts(user_id: str, texts: List[str]):
    """Parse multiple workout entries at once."""
    results = []
    for text in texts[:10]:  # Max 10 per batch
        parsed = nl_workout_logger.parse(text)
        results.append({
            "text": text,
            "exercises": parsed["exercises"],
            "confidence": parsed["parse_confidence"],
        })
    return {"user_id": user_id, "results": results, "count": len(results)}


@router.get("/context/{user_id}")
async def get_coaching_context(user_id: str):
    """Get contextual knowledge for coaching based on user's recent activity."""
    recovery_logs = await storage.get_recovery_logs(user_id, 7)
    workout_logs = await storage.get_workout_logs(user_id, 7)

    # Build a composite query from recent data
    query_parts = []
    if recovery_logs:
        last = recovery_logs[-1]
        if last.get("recovery_score", 70) < 50:
            query_parts.append("low recovery fatigue")
        if last.get("sleep_duration_hours", 7) < 6:
            query_parts.append("sleep deprivation")
    if workout_logs:
        avg_rpe = sum(w.get("session_rpe", 5) for w in workout_logs) / max(len(workout_logs), 1)
        if avg_rpe > 7:
            query_parts.append("high intensity training")

    query = " ".join(query_parts) if query_parts else "fitness recovery"

    knowledge = rag_retriever.retrieve(query, top_k=3)

    return {
        "user_id": user_id,
        "knowledge_entries": knowledge,
        "query": query,
    }

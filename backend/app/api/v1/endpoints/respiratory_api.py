"""Respiratory Training API — Breathing exercises, COPD, asthma"""
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.services.respiratory_training import respiratory_training_service

router = APIRouter()


class SessionRequest(BaseModel):
    exercise_id: str
    user_id: str = "default"


@router.get("/exercises")
async def get_exercises(category: str = "", difficulty: str = ""):
    return {"exercises": respiratory_training_service.get_exercises(category, difficulty)}


@router.get("/exercises/{exercise_id}")
async def get_exercise(exercise_id: str):
    exercise = respiratory_training_service.get_exercise(exercise_id)
    if not exercise:
        return {"error": "Exercise not found"}
    return {"exercise": exercise}


@router.post("/session/start")
async def start_session(request: SessionRequest):
    return respiratory_training_service.start_session(request.exercise_id, request.user_id)


@router.post("/session/complete/{session_id}")
async def complete_session(session_id: str, breaths: int = 10, rate: float = 6.0):
    return respiratory_training_service.complete_session(session_id, breaths, rate)


@router.post("/breath-hold")
async def log_breath_hold(hold_time: float = 30):
    return respiratory_training_service.log_breath_hold(hold_time)


@router.get("/lung-capacity")
async def estimate_lung_capacity(
    height: Optional[float] = Query(None, ge=100, le=250),
    age: Optional[int] = Query(None, ge=13, le=100),
    gender: Optional[str] = None,
):
    """
    Predicted vital capacity from height, age and sex.

    All three are required: they defaulted to a 175 cm thirty-year-old man, so
    the app returned a lung capacity for someone whose height it did not know.
    """
    if height is None or age is None or not gender:
        return {
            "status": "insufficient_data",
            "needs": ["height", "age", "gender"],
            "message": "Add your height, age and sex to your profile to see a predicted capacity.",
        }
    result = respiratory_training_service.estimate_lung_capacity(height, age, gender)
    return {"status": "ok", **result}


@router.get("/copd-program")
async def get_copd_program():
    return respiratory_training_service.get_copd_program()


@router.get("/asthma-program")
async def get_asthma_program():
    return respiratory_training_service.get_asthma_program()


@router.get("/history")
async def get_history(user_id: str = "default"):
    return {"history": respiratory_training_service.get_session_history(user_id)}

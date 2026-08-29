"""Workout Engine API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.workout_engine import workout_engine_service

router = APIRouter()

class PlanRequest(BaseModel):
    goal: str = "general_fitness"; fitness_level: str = "beginner"; equipment: list[str] = ["bodyweight", "barbell", "dumbbell"]
    duration_minutes: int = 45; days_per_week: int = 3

class SetLogRequest(BaseModel):
    session_id: str; exercise_name: str; set_num: int; reps: int; weight: float = 0; rpe: int = 5

@router.get("/exercises")
async def get_exercises(muscle_group: Optional[str] = None, difficulty: Optional[str] = None, equipment: Optional[str] = None, page: int = 1):
    return workout_engine_service.get_exercises(muscle_group, difficulty, equipment, page)

@router.get("/exercises/{exercise_id}")
async def get_exercise(exercise_id: str):
    return workout_engine_service.get_exercise(exercise_id) or {"error": "Not found"}

@router.post("/generate-plan")
async def generate_plan(request: PlanRequest):
    return workout_engine_service.generate_workout_plan(request.goal, request.fitness_level, request.equipment, request.duration_minutes, request.days_per_week)

@router.get("/plans")
async def get_plans():
    return {"plans": workout_engine_service.get_plans()}

@router.post("/session/start")
async def start_session(plan_id: str = "custom"):
    return workout_engine_service.start_session(plan_id)

@router.post("/session/log-set")
async def log_set(request: SetLogRequest):
    return workout_engine_service.log_set(request.session_id, request.exercise_name, request.set_num, request.reps, request.weight, request.rpe)

@router.post("/session/complete/{session_id}")
async def complete_session(session_id: str):
    return workout_engine_service.complete_session(session_id)

@router.get("/history")
async def get_history(limit: int = 20):
    return {"history": workout_engine_service.get_history(limit)}

@router.get("/prs")
async def get_prs():
    return {"personal_records": workout_engine_service.get_prs()}

@router.get("/stats")
async def get_stats():
    return workout_engine_service.get_workout_stats()

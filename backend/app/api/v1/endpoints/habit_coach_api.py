"""AI Habit Coach API — Behavioral science-based behavior change"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.habit_coach import habit_coach_service

router = APIRouter()


class AddHabitRequest(BaseModel):
    user_id: str
    habit_id: str


class SuggestRequest(BaseModel):
    goals: list[str] = []
    fitness_level: str = "beginner"


@router.get("/habits")
async def get_habits(category: str = "", difficulty: str = ""):
    return {"habits": habit_coach_service.get_habits(category, difficulty)}


@router.post("/suggest")
async def suggest_habits(request: SuggestRequest):
    return {"suggestions": habit_coach_service.suggest_habits(request.goals, request.fitness_level)}


@router.post("/add")
async def add_habit(request: AddHabitRequest):
    return habit_coach_service.add_habit(request.user_id, request.habit_id)


@router.post("/complete/{habit_id}")
async def complete_habit(habit_id: str, user_id: str = "default"):
    return habit_coach_service.log_habit_completion(user_id, habit_id)


@router.get("/user/{user_id}")
async def get_user_habits(user_id: str):
    return {"habits": habit_coach_service.get_user_habits(user_id)}


@router.get("/stats/{user_id}")
async def get_stats(user_id: str):
    return habit_coach_service.get_habit_stats(user_id)


@router.post("/com-b")
async def assess_com_b(user_id: str = "default", habit_id: str = "h001"):
    return habit_coach_service.assess_com_b(user_id, habit_id)


@router.get("/nudge/{user_id}")
async def get_nudge(user_id: str):
    return habit_coach_service.get_nudge(user_id)


@router.get("/relapse-prevention")
async def get_relapse_prevention(user_id: str = "default"):
    return habit_coach_service.get_relapse_prevention(user_id)

"""AI Habit Coach API — Behavioral science-based behavior change"""
from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.services.habit_coach import habit_coach_service

router = APIRouter()


class AddHabitRequest(BaseModel):
    user_id: str
    habit_id: str


class CustomHabitRequest(BaseModel):
    user_id: str
    name: str = Field(min_length=1, max_length=60)
    category: str = Field("other", max_length=30)
    cue: str = Field("", max_length=80)


class SuggestRequest(BaseModel):
    goals: list[str] = []
    fitness_level: str = "beginner"


@router.get("/")
async def get_habits(category: str = "", difficulty: str = ""):
    return {"habits": habit_coach_service.get_habits(category, difficulty)}


@router.get("/suggest")
async def suggest_habits_get(fitness_level: str = "beginner"):
    return {"suggestions": habit_coach_service.suggest_habits([], fitness_level)}


@router.post("/suggest")
async def suggest_habits(request: SuggestRequest):
    return {"suggestions": habit_coach_service.suggest_habits(request.goals, request.fitness_level)}


@router.post("/add")
async def add_habit(request: AddHabitRequest):
    return habit_coach_service.add_habit(request.user_id, request.habit_id)


@router.post("/custom")
async def add_custom_habit(request: CustomHabitRequest):
    return habit_coach_service.add_custom_habit(request.user_id, request.name, request.category, request.cue)


@router.delete("/{habit_id}")
async def remove_habit(habit_id: str, user_id: str = "default"):
    if not habit_coach_service.remove_habit(user_id, habit_id):
        raise HTTPException(status_code=404, detail="Not tracking this habit")
    return {"removed": True}


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

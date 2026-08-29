"""Adaptive workouts — difficulty adjustment, accessible alternatives, progression."""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from app.services.adaptive_workouts import (
    Exercise, WorkoutPerformance, UserFitnessProfile,
    select_adaptive_workout, get_accessible_alternatives,
    score_exercise_accessibility, suggest_progression,
)

router = APIRouter()


class ExerciseInput(BaseModel):
    id: str
    name: str
    muscle_group: str
    difficulty: int = Field(..., ge=1, le=10)
    equipment: list[str] = []
    accessibility: list[str] = ["standing"]
    alternatives: list[str] = []


class PerformanceInput(BaseModel):
    exercise_id: str
    sets_completed: int
    reps_completed: list[int] = []
    weight_kg: Optional[float] = None
    rpe: Optional[int] = Field(None, ge=1, le=10)
    completed: bool = True


class ProfileInput(BaseModel):
    fitness_level: str = "intermediate"
    limitations: list[str] = []
    max_heart_rate: int = 190
    preferred_intensity: str = "moderate"


class WorkoutSelectInput(BaseModel):
    exercises: list[ExerciseInput]
    profile: ProfileInput
    performance_history: list[PerformanceInput] = []
    target_exercises: int = 8


class AlternativesInput(BaseModel):
    exercise_id: str
    limitations: list[str] = []
    exercises: list[ExerciseInput] = []


@router.post("/adaptive")
async def adaptive_workout(req: WorkoutSelectInput):
    """Select exercises adapted to user's fitness level and limitations."""
    exercises = [Exercise(**e.model_dump()) for e in req.exercises]
    profile = UserFitnessProfile(**req.profile.model_dump())
    history = [WorkoutPerformance(**p.model_dump()) for p in req.performance_history]
    return select_adaptive_workout(exercises, profile, history, req.target_exercises)


@router.post("/accessible-alternatives")
async def accessible_alternatives(req: AlternativesInput):
    """Get accessible alternatives for an exercise."""
    exercises = [Exercise(**e.model_dump()) for e in req.exercises]
    return get_accessible_alternatives(req.exercise_id, req.limitations, exercises)


@router.post("/accessibility/score")
async def accessibility_score(exercise: ExerciseInput):
    """Score how accessible an exercise is (0-100)."""
    return score_exercise_accessibility(Exercise(**exercise.model_dump()))


@router.post("/progression")
async def progression_suggestion(history: list[PerformanceInput], profile: ProfileInput):
    """Suggest next workout progression based on history."""
    perf = [WorkoutPerformance(**p.model_dump()) for p in history]
    prof = UserFitnessProfile(**profile.model_dump())
    return suggest_progression(perf, prof)

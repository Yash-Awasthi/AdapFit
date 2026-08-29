"""Physical Therapy & Rehabilitation API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.rehabilitation import rehabilitation_service

router = APIRouter()


class StartProgramRequest(BaseModel):
    injury_type: str
    user_id: str = "default"


class LogExerciseRequest(BaseModel):
    program_id: str
    exercise_name: str
    reps_done: int = 0
    pain_level: int = 0
    notes: str = ""


class LogProgressRequest(BaseModel):
    program_id: str
    pain_level: int = 0
    rom_degrees: int = 0
    strength_score: int = 0
    notes: str = ""


@router.get("/programs")
async def get_programs():
    return {"programs": rehabilitation_service.get_injury_programs()}


@router.get("/programs/{injury_type}")
async def get_program(injury_type: str):
    program = rehabilitation_service.get_program(injury_type)
    if not program:
        return {"error": "Program not found"}
    return {"program": program}


@router.post("/program/start")
async def start_program(request: StartProgramRequest):
    return rehabilitation_service.start_program(request.injury_type, request.user_id)


@router.post("/exercise/log")
async def log_exercise(request: LogExerciseRequest):
    return rehabilitation_service.log_exercise(request.program_id, request.exercise_name, request.reps_done, request.pain_level, request.notes)


@router.get("/exercise-library")
async def get_exercise_library(body_part: str = "", difficulty: str = ""):
    return {"exercises": rehabilitation_service.get_exercise_library(body_part, difficulty)}


@router.post("/progress")
async def log_progress(request: LogProgressRequest):
    return rehabilitation_service.log_progress(request.program_id, request.pain_level, request.rom_degrees, request.strength_score, request.notes)


@router.get("/progress/{program_id}")
async def get_progress(program_id: str):
    return {"progress": rehabilitation_service.get_progress_chart(program_id)}


@router.get("/milestones/{injury_type}")
async def get_milestones(injury_type: str):
    return {"milestones": rehabilitation_service.get_milestones(injury_type)}


@router.get("/pain-trend")
async def get_pain_trend(days: int = 14):
    return {"trend": rehabilitation_service.get_pain_trend(days)}


@router.get("/recovery-estimate/{injury_type}")
async def get_recovery_estimate(injury_type: str):
    return rehabilitation_service.get_recovery_estimate(injury_type)

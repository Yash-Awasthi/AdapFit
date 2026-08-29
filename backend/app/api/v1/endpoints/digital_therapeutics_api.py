"""
Digital Therapeutics API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/dtx", tags=["Digital Therapeutics"])


class EnrollRequest(BaseModel):
    user_id: str
    program_key: str
    prescriber: str = "system"
    notes: str = ""


class LogSessionRequest(BaseModel):
    enrollment_id: str
    module_name: str
    duration_min: int
    completion: float
    mood_before: int
    mood_after: int
    notes: str = ""


class OutcomeRequest(BaseModel):
    enrollment_id: str
    metric_key: str
    score: float
    notes: str = ""


@router.post("/enroll")
async def enroll_patient(req: EnrollRequest):
    from app.services.digital_therapeutics import dtx_service
    return dtx_service.enroll_patient(req.user_id, req.program_key, req.prescriber, req.notes)


@router.post("/session/log")
async def log_session(req: LogSessionRequest):
    from app.services.digital_therapeutics import dtx_service
    return dtx_service.log_session(req.enrollment_id, req.module_name, req.duration_min, req.completion, req.mood_before, req.mood_after, req.notes)


@router.post("/outcome/record")
async def record_outcome(req: OutcomeRequest):
    from app.services.digital_therapeutics import dtx_service
    return dtx_service.record_outcome(req.enrollment_id, req.metric_key, req.score, req.notes)


@router.get("/progress/{enrollment_id}")
async def get_progress(enrollment_id: str):
    from app.services.digital_therapeutics import dtx_service
    return dtx_service.get_enrollment_progress(enrollment_id)


@router.get("/programs")
async def get_programs():
    from app.services.digital_therapeutics import dtx_service
    return dtx_service.get_programs()


@router.get("/enrollments/{user_id}")
async def get_enrollments(user_id: str):
    from app.services.digital_therapeutics import dtx_service
    return dtx_service.get_user_enrollments(user_id)


@router.get("/outcomes")
async def get_outcomes():
    from app.services.digital_therapeutics import dtx_service
    return dtx_service.OUTCOME_METRICS

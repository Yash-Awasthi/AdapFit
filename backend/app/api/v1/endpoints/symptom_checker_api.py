"""Symptom triage: how soon to get care, with red-flag checks. Never a diagnosis."""
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.safety_policy import triage
from app.services.symptom_checker import symptom_checker_service

router = APIRouter()


class SymptomCheckRequest(BaseModel):
    symptom: str = Field(min_length=2, max_length=40)
    severity: int = Field(ge=1, le=10)
    days: float = Field(0, ge=0, le=3650)
    red_flags: List[str] = Field(default_factory=list, max_length=10)
    note: str = Field("", max_length=300)


@router.get("/symptoms")
async def list_symptoms():
    return {"symptoms": symptom_checker_service.get_symptoms()}


@router.post("/check")
async def check_symptom(req: SymptomCheckRequest):
    flagged = triage(req.note) if req.note else None
    result = symptom_checker_service.check_symptom(req.symptom, req.severity, req.days, req.red_flags)
    if flagged and "error" not in result:
        result.update(level="emergency", message=flagged["reply"].split("\n")[0], safety=flagged)
    return result


@router.get("/history")
async def get_history(limit: int = 10):
    return {"history": symptom_checker_service.get_history(limit)}

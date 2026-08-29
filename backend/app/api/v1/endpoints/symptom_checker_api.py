"""AI Symptom Checker & Triage API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.symptom_checker import symptom_checker_service

router = APIRouter()


class SymptomCheckRequest(BaseModel):
    symptom: str
    severity: int = 5
    duration: str = ""
    additional_info: str = ""


class MultiSymptomRequest(BaseModel):
    symptoms: list[dict]


@router.get("/body-systems")
async def get_body_systems():
    return {"systems": symptom_checker_service.get_body_systems()}


@router.post("/check")
async def check_symptom(request: SymptomCheckRequest):
    return symptom_checker_service.check_symptom(request.symptom, request.severity, request.duration, request.additional_info)


@router.post("/check-multi")
async def multi_symptom_check(request: MultiSymptomRequest):
    return symptom_checker_service.multi_symptom_check(request.symptoms)


@router.get("/tips")
async def get_health_tips(symptom: str = ""):
    return {"tips": symptom_checker_service.get_health_tips(symptom)}


@router.get("/history")
async def get_history(user_id: str = "default", limit: int = 10):
    return {"history": symptom_checker_service.get_assessment_history(user_id, limit)}

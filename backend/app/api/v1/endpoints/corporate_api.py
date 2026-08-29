"""Corporate Health Program API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.corporate_health import corporate_health_service

router = APIRouter()


class RegisterCompanyRequest(BaseModel):
    name: str
    domain: str
    employee_count: int


class JoinChallengeRequest(BaseModel):
    employee_id: str
    challenge_id: str


@router.post("/register")
async def register_company(request: RegisterCompanyRequest):
    return corporate_health_service.register_company(request.name, request.domain, request.employee_count)


@router.get("/challenges")
async def get_challenges(company_id: str = ""):
    return {"challenges": corporate_health_service.get_challenges(company_id)}


@router.post("/challenges/join")
async def join_challenge(request: JoinChallengeRequest):
    return corporate_health_service.join_challenge(request.employee_id, request.challenge_id)


@router.get("/wellness/{employee_id}")
async def get_wellness_score(employee_id: str):
    return corporate_health_service.get_employee_wellness_score(employee_id)


@router.get("/dashboard/{company_id}")
async def get_company_dashboard(company_id: str):
    return corporate_health_service.get_company_dashboard(company_id)


@router.get("/insurance/{employee_id}")
async def get_insurance_rewards(employee_id: str):
    return corporate_health_service.get_insurance_rewards(employee_id)


@router.post("/screening/{employee_id}")
async def schedule_screening(employee_id: str, screening_type: str = "annual"):
    return corporate_health_service.schedule_health_screening(employee_id, screening_type)

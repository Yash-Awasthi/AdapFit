"""Health Risk Assessment API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.health_risk_engine import health_risk_engine

router = APIRouter()


class RiskAssessmentRequest(BaseModel):
    age: int = 30
    gender: str = "male"
    bmi: float = 25
    systolic_bp: int = 120
    total_cholesterol: int = 200
    hdl_cholesterol: int = 50
    triglycerides: int = 150
    fasting_glucose: int = 95
    waist_circumference: int = 90
    smoking: bool = False
    diabetes: bool = False
    family_history: bool = False
    physical_activity: str = "moderate"
    high_glucose: bool = False


@router.post("/cardiovascular")
async def assess_cardiovascular(data: RiskAssessmentRequest = RiskAssessmentRequest()):
    return health_risk_engine.assess_cardiovascular_risk(data.model_dump())


@router.post("/diabetes")
async def assess_diabetes(data: RiskAssessmentRequest = RiskAssessmentRequest()):
    return health_risk_engine.assess_diabetes_risk(data.model_dump())


@router.post("/metabolic")
async def assess_metabolic(data: RiskAssessmentRequest = RiskAssessmentRequest()):
    return health_risk_engine.assess_metabolic_syndrome(data.model_dump())


@router.post("/comprehensive")
async def comprehensive_report(data: RiskAssessmentRequest = RiskAssessmentRequest()):
    return health_risk_engine.get_comprehensive_risk_report(data.model_dump())


@router.get("/trends")
async def get_trends(user_id: str = "default"):
    return {"trends": health_risk_engine.get_risk_trends(user_id)}

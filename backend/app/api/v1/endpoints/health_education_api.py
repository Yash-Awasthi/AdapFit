"""Health Education API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.health_education import health_education_service

router = APIRouter(prefix="/health-education", tags=["Health Literacy & Education"])

class LiteracyAssessmentRequest(BaseModel):
    data: Dict[str, Any]

@router.get("/glossary")
async def search_glossary(query: str = ""):
    result = health_education_service.search_glossary(query) if query else list(health_education_service.glossary.values())[:20]
    return {"success": True, "data": result}

@router.get("/condition/{condition}")
async def get_condition(condition: str):
    result = health_education_service.get_condition_info(condition)
    return {"success": True, "data": result}

@router.get("/treatment/{treatment}")
async def get_treatment(treatment: str):
    result = health_education_service.get_treatment_info(treatment)
    return {"success": True, "data": result}

@router.post("/literacy-assessment")
async def assess_literacy(req: LiteracyAssessmentRequest):
    result = health_education_service.assess_literacy(req.data)
    return {"success": True, "data": result}

@router.get("/conditions")
async def list_conditions():
    return {"success": True, "data": list(health_education_service.conditions.keys())}

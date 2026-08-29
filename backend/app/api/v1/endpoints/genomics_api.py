"""Genomics Insights API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List
from app.services.genomics_insights import genomics_insights_service

router = APIRouter(prefix="/genomics", tags=["Genomics & Pharmacogenomics"])


class GeneticAnalysisRequest(BaseModel):
    user_id: str
    genetic_data: Dict[str, Any]


class DrugSafetyRequest(BaseModel):
    user_id: str
    medications: List[str]


@router.post("/analyze")
async def analyze_genetics(req: GeneticAnalysisRequest):
    result = genomics_insights_service.analyze_genetic_data(req.user_id, req.genetic_data)
    return {"success": True, "data": result}


@router.post("/drug-safety")
async def check_drug_safety(req: DrugSafetyRequest):
    result = genomics_insights_service.check_drug_safety(req.user_id, req.medications)
    return {"success": True, "data": result}


@router.get("/genes")
async def list_genetic_risks():
    risks = [
        {"disease": k, "genes": v["genes"], "risk_variants": list(v["risk_variants"].keys())}
        for k, v in genomics_insights_service.genetic_risks.items()
    ]
    return {"success": True, "data": risks}

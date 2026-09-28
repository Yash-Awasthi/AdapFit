"""
Government Health Schemes API — Discover and Check Eligibility for Health Benefits

Provides information about national/state health schemes, insurance programs,
and public health benefits with personalized eligibility checking.

IMPORTANT: All benefit amounts and eligibility criteria should be re-verified
with official sources. The system always shows disclaimers about verification.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
from app.services.government_schemes import government_schemes_service
from app.core.dependencies import require_user

router = APIRouter()


class EligibilityCheckRequest(BaseModel):
    country: str = "IN"
    age: Optional[int] = Field(None, ge=0, le=120)
    is_pregnant: Optional[bool] = None
    formal_employee: Optional[bool] = Field(None, description="Salaried with an employer")
    monthly_wage: Optional[float] = Field(None, ge=0)
    central_govt: Optional[bool] = Field(None, description="Central government employee or pensioner")
    in_secc_list: Optional[bool] = Field(None, description="Family named on the PM-JAY (SECC 2011) list")


@router.get("/list")
async def list_schemes(country: str = "IN"):
    """List all health schemes for a country."""
    schemes = government_schemes_service.get_all_schemes(country)
    return {"schemes": schemes, "count": len(schemes), "country": country}


@router.get("/categories")
async def get_categories():
    """List scheme categories."""
    return {"categories": government_schemes_service.get_categories()}


@router.get("/{scheme_id}")
async def get_scheme(scheme_id: str):
    """Get details of a specific scheme."""
    scheme = government_schemes_service.get_scheme(scheme_id)
    if not scheme:
        return {"error": "Scheme not found"}
    return scheme


@router.post("/search")
async def search_schemes(query: str = "", country: str = "IN"):
    """Search schemes by name, category, or keyword."""
    schemes = government_schemes_service.search_schemes(query, country)
    return {"schemes": schemes, "count": len(schemes), "query": query}


@router.post("/eligibility")
async def check_eligibility(request: EligibilityCheckRequest, user: dict = Depends(require_user)):
    """Schemes the answers point to, with reasons. Always 'confirm on the official portal'."""
    return {"schemes": government_schemes_service.check_eligibility(**request.model_dump())}

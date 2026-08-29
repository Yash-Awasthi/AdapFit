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
    income_annual: Optional[float] = Field(None, ge=0, description="Annual income in local currency")
    is_bpl: Optional[bool] = Field(None, description="Below Poverty Line card holder")
    age: Optional[int] = Field(None, ge=0, le=120)
    has_insurance: Optional[bool] = None
    is_pregnant: Optional[bool] = None
    is_employee: Optional[bool] = None
    has_children_under_5: Optional[bool] = None


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
    """
    Check which schemes the user might be eligible for.
    
    Provide any combination of the eligibility parameters — more data means
    better eligibility matching. Always shows "verify with official source".
    """
    results = government_schemes_service.check_eligibility(
        country=request.country,
        income_annual=request.income_annual,
        is_bpl=request.is_bpl,
        age=request.age,
        has_insurance=request.has_insurance,
        is_pregnant=request.is_pregnant,
        is_employee=request.is_employee,
        has_children_under_5=request.has_children_under_5,
    )
    return {
        "user_id": user["id"],
        "eligible_schemes": results,
        "count": len(results),
        "disclaimer": "All eligibility determinations are estimates. Please verify with the official scheme portal or helpline before applying.",
    }

"""
Nutrigenomics & DNA-Based Personalized Nutrition API Endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/nutrigenomics", tags=["Nutrigenomics"])


class GeneticProfileRequest(BaseModel):
    genetic_data: Dict
    dietary_restrictions: Optional[List[str]] = None
    calorie_target: int = 2000


class MealPlanRequest(BaseModel):
    genetic_data: Dict
    dietary_restrictions: Optional[List[str]] = None
    calorie_target: int = 2000


@router.post("/analyze")
async def analyze_genetic_profile(request: GeneticProfileRequest):
    """Analyze genetic data and provide personalized nutrition recommendations"""
    from app.services.nutrigenomics import nutrigenomics_service
    profile = nutrigenomics_service.analyze_genetic_profile(request.genetic_data)
    return {"success": True, "data": profile}


@router.post("/meal-plan")
async def get_meal_plan(request: MealPlanRequest):
    """Generate personalized meal plan based on genetics"""
    from app.services.nutrigenomics import nutrigenomics_service
    plan = nutrigenomics_service.get_meal_plan(
        genetic_data=request.genetic_data,
        dietary_restrictions=request.dietary_restrictions,
        calorie_target=request.calorie_target
    )
    return {"success": True, "data": plan}


@router.post("/supplements")
async def get_supplement_guide(request: GeneticProfileRequest):
    """Get personalized supplement recommendations"""
    from app.services.nutrigenomics import nutrigenomics_service
    supplements = nutrigenomics_service.get_supplement_guide(request.genetic_data)
    return {"success": True, "data": supplements, "count": len(supplements)}


@router.get("/genes")
async def get_gene_database():
    """Get all available gene variants and their dietary implications"""
    from app.services.nutrigenomics import nutrigenomics_service
    return {"success": True, "data": nutrigenomics_service.gene_variants}


@router.get("/genes/{gene_name}")
async def get_gene_info(gene_name: str):
    """Get specific gene variant information"""
    from app.services.nutrigenomics import nutrigenomics_service
    if gene_name in nutrigenomics_service.gene_variants:
        return {"success": True, "data": nutrigenomics_service.gene_variants[gene_name]}
    return {"success": False, "error": f"Gene {gene_name} not found"}


@router.get("/diet-patterns")
async def get_diet_patterns():
    """Get recommended dietary patterns"""
    from app.services.nutrigenomics import nutrigenomics_service
    return {"success": True, "data": nutrigenomics_service.dietary_patterns}


@router.get("/food-interactions")
async def get_food_gene_interactions():
    """Get food-gene interaction database"""
    from app.services.nutrigenomics import nutrigenomics_service
    return {"success": True, "data": nutrigenomics_service.food_gene_interactions}

"""
Health Equity API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Optional

router = APIRouter(prefix="/health-equity", tags=["Health Equity"])


class CreateCommunityRequest(BaseModel):
    community_id: str
    name: str
    population: int
    demographics: dict = {}


class SDOHScoreRequest(BaseModel):
    community_id: str
    category_scores: Dict[str, float]


class AddResourceRequest(BaseModel):
    community_id: str
    name: str
    resource_type: str
    address: str
    phone: str
    hours: str = ""


class OutcomeRequest(BaseModel):
    community_id: str
    intervention_name: str
    metric: str
    before: float
    after: float


@router.post("/community/create")
async def create_community(req: CreateCommunityRequest):
    from app.services.health_equity import health_equity
    return health_equity.create_community_profile(req.community_id, req.name, req.population, req.demographics)


@router.post("/sdoh/score")
async def calculate_sdoh(req: SDOHScoreRequest):
    from app.services.health_equity import health_equity
    return health_equity.calculate_sdoh_score(req.community_id, req.category_scores)


@router.get("/interventions")
async def get_interventions(category: Optional[str] = None):
    from app.services.health_equity import health_equity
    return health_equity.get_interventions(category)


@router.get("/recommendations/{community_id}")
async def get_recommendations(community_id: str):
    from app.services.health_equity import health_equity
    return health_equity.recommend_interventions(community_id)


@router.post("/resource/add")
async def add_resource(req: AddResourceRequest):
    from app.services.health_equity import health_equity
    return health_equity.add_resource(req.community_id, req.name, req.resource_type, req.address, req.phone, req.hours)


@router.get("/resources/{community_id}")
async def get_resources(community_id: str, type: Optional[str] = None):
    from app.services.health_equity import health_equity
    return health_equity.get_resources(community_id, type)


@router.post("/outcome/log")
async def log_outcome(req: OutcomeRequest):
    from app.services.health_equity import health_equity
    return health_equity.log_intervention_outcome(req.community_id, req.intervention_name, req.metric, req.before, req.after)


@router.get("/sdoh-categories")
async def get_sdoh_categories():
    from app.services.health_equity import health_equity
    return health_equity.SDOH_CATEGORIES

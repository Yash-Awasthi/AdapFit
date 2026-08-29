"""
Health Recommendations V2 API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/recommendations-v2", tags=["AI Health Recommendations"])


class GetRecommendationsRequest(BaseModel):
    user_id: str
    health_data: dict = {}
    count: int = 5


class DismissRequest(BaseModel):
    user_id: str
    recommendation_id: str


class FeedbackRequest(BaseModel):
    user_id: str
    recommendation_id: str
    helpful: bool
    notes: str = ""


@router.post("/get")
async def get_recommendations(req: GetRecommendationsRequest):
    from app.services.health_recommendations_v2 import health_recommendations_v2
    return health_recommendations_v2.get_recommendations(req.user_id, req.health_data, req.count)


@router.post("/dismiss")
async def dismiss(req: DismissRequest):
    from app.services.health_recommendations_v2 import health_recommendations_v2
    return health_recommendations_v2.dismiss_recommendation(req.user_id, req.recommendation_id)


@router.post("/feedback")
async def provide_feedback(req: FeedbackRequest):
    from app.services.health_recommendations_v2 import health_recommendations_v2
    return health_recommendations_v2.provide_feedback(req.user_id, req.recommendation_id, req.helpful, req.notes)


@router.get("/stats/{user_id}")
async def get_stats(user_id: str):
    from app.services.health_recommendations_v2 import health_recommendations_v2
    return health_recommendations_v2.get_recommendation_stats(user_id)


@router.get("/categories")
async def get_categories():
    from app.services.health_recommendations_v2 import health_recommendations_v2
    return health_recommendations_v2.RECOMMENDATION_CATEGORIES


@router.get("/all")
async def get_all_recommendations():
    from app.services.health_recommendations_v2 import health_recommendations_v2
    all_recs = []
    for cat, recs in health_recommendations_v2.RECOMMENDATION_DATABASE.items():
        for r in recs:
            all_recs.append({**r, "category": cat})
    return all_recs

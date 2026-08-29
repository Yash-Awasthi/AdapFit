"""
Health Misinformation Detection API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/misinformation", tags=["Health Misinformation"])


class VerifyClaimRequest(BaseModel):
    claim: str
    source: Optional[str] = None
    context: str = ""


class RateSourceRequest(BaseModel):
    source_name: str
    source_url: Optional[str] = None


class CheckArticleRequest(BaseModel):
    url: Optional[str] = None
    text: str


@router.post("/verify")
async def verify_claim(req: VerifyClaimRequest):
    from app.services.health_misinformation import health_misinformation_service
    return health_misinformation_service.verify_claim(req.claim, req.source, req.context)


@router.post("/rate-source")
async def rate_source(req: RateSourceRequest):
    from app.services.health_misinformation import health_misinformation_service
    return health_misinformation_service.rate_source(req.source_name, req.source_url)


@router.post("/check-article")
async def check_article(req: CheckArticleRequest):
    from app.services.health_misinformation import health_misinformation_service
    return health_misinformation_service.check_article(req.text, req.url)


@router.get("/misinformation-categories")
async def get_categories():
    from app.services.health_misinformation import health_misinformation_service
    return health_misinformation_service.MISINFO_CATEGORIES


@router.get("/red-flags")
async def get_red_flags():
    from app.services.health_misinformation import health_misinformation_service
    return health_misinformation_service.RED_FLAGS


@router.get("/trusted-sources")
async def get_trusted_sources():
    from app.services.health_misinformation import health_misinformation_service
    return health_misinformation_service.TRUSTED_SOURCES

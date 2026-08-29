"""
Health News & Evidence Feed API — Categorized Health Content with Source Attribution

Every article includes source, evidence level, "why this matters," and clear
separation between news, education, research, and medical guidance.
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.services.health_news_feed import health_news_feed_service
from app.core.dependencies import require_user

router = APIRouter()


@router.get("/feed")
async def get_feed(
    category: Optional[str] = None,
    content_type: Optional[str] = None,
    evidence_level: Optional[str] = None,
    limit: int = Query(20, ge=1, le=50),
):
    """Get the health news feed with optional filtering."""
    return {"articles": health_news_feed_service.get_feed(category, content_type, evidence_level, limit)}


@router.get("/personalized")
async def get_personalized_feed(user: dict = Depends(require_user), limit: int = Query(10, ge=1, le=30)):
    """Get content personalized based on user's current health state."""
    # In a real implementation, this would pull user's health state tags
    # For now, return general feed
    return {"articles": health_news_feed_service.get_feed(limit=limit), "personalized": False}


@router.get("/categories")
async def get_categories():
    """List all content categories."""
    return {"categories": health_news_feed_service.get_categories()}


@router.get("/{article_id}")
async def get_article(article_id: str):
    """Get a specific article."""
    article = health_news_feed_service.get_article(article_id)
    if not article:
        return {"error": "Article not found"}
    return article

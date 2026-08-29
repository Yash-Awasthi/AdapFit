"""
Content Hub API — YouTube-like Health Video/GIF Feed
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from app.services.content_platform import content_platform_service

router = APIRouter()


class BookmarkRequest(BaseModel):
    content_id: str


class EngagementRequest(BaseModel):
    content_id: str
    action: str  # view, bookmark, like, complete


class RecommendationRequest(BaseModel):
    user_goals: list[str] = ["general_fitness"]
    fitness_level: str = "beginner"
    health_conditions: list[str] = []


@router.get("/feed")
async def get_content_feed(
    category: Optional[str] = None,
    content_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    """Get personalized content feed with filtering."""
    feed = content_platform_service.get_content_feed(
        category=category, content_type=content_type,
        page=page, page_size=page_size, difficulty=difficulty,
    )
    return {
        "items": [
            {
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "content_type": item.content_type.value,
                "category": item.category.value,
                "difficulty": item.difficulty.value,
                "duration_seconds": item.duration_seconds,
                "thumbnail_url": item.thumbnail_url,
                "muscles_targeted": item.muscles_targeted,
                "rating": item.rating,
                "view_count": item.view_count,
            }
            for item in feed.items
        ],
        "total_count": feed.total_count,
        "page": feed.page,
        "page_size": feed.page_size,
    }


@router.get("/item/{content_id}")
async def get_content_item(content_id: str):
    """Get detailed content item."""
    result = content_platform_service.get_content_by_id(content_id)
    if not result:
        return {"error": "Content not found"}
    return result


@router.get("/search")
async def search_content(q: str, limit: int = 20):
    """Search content by keyword."""
    return {"results": content_platform_service.search_content(q, limit)}


@router.get("/trending")
async def get_trending(limit: int = 20):
    """Get trending health content."""
    return {"trending": content_platform_service.get_trending(limit)}


@router.get("/playlist/{workout_type}")
async def get_workout_playlist(workout_type: str, level: str = "all_levels"):
    """Get a curated workout playlist."""
    playlist = content_platform_service.get_workout_playlist(workout_type, level)
    return {
        "title": playlist["title"],
        "description": playlist["description"],
        "total_duration_minutes": playlist["total_duration_minutes"],
        "exercises": playlist["exercises"],
        "level": playlist["level"],
    }


@router.get("/knowledge")
async def get_health_knowledge(topic: Optional[str] = None):
    """Get health knowledge articles and tips."""
    return {"articles": content_platform_service.get_health_knowledge(topic)}


@router.post("/bookmark")
async def bookmark_content(request: BookmarkRequest):
    """Bookmark a content item."""
    return content_platform_service.bookmark_content("default", request.content_id)


@router.get("/bookmarks")
async def get_bookmarks():
    """Get user's bookmarked content."""
    return {"bookmarks": content_platform_service.get_user_bookmarks("default")}


@router.post("/recommendations")
async def get_recommendations(request: RecommendationRequest):
    """Get personalized content recommendations."""
    return {
        "recommendations": content_platform_service.get_personalized_recommendations(
            request.user_goals, request.fitness_level, request.health_conditions,
        )
    }


@router.post("/engage")
async def track_engagement(request: EngagementRequest):
    """Track user engagement with content."""
    return content_platform_service.track_engagement("default", request.content_id, request.action)

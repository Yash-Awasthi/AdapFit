"""
Content Hub API — YouTube-like Health Video/GIF Feed
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from urllib.parse import quote_plus

from app.services.content_platform import content_platform_service
from app.services.content_media import media_for, SEARCH_TEMPLATE
from app.services import youtube_search as youtube

router = APIRouter()

# Search phrasing per category, tuned to return instructional videos rather
# than vlogs. Editing a line here changes what that category's feed shows.
CATEGORY_QUERIES = {
    "all": "evidence based fitness and health explained",
    "strength": "proper lifting technique tutorial barbell",
    "cardio": "cardio workout follow along no equipment",
    "flexibility": "mobility and stretching routine follow along",
    "mental_wellness": "guided meditation and breathing exercise",
    "nutrition": "evidence based nutrition for muscle and fat loss",
    "sleep": "sleep science how to sleep better",
    "general_health": "heart rate variability and recovery explained",
}


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
                "muscles_targeted": item.muscles_targeted,
                "rating": item.rating,
                "view_count": item.view_count,
                # The seeded media_url is a placeholder path until a real asset
                # host is configured, so only absolute URLs are handed to clients.
                "gif_url": item.media_url if item.media_url.startswith("http") else None,
                **media_for(item.title, item.category.value),
            }
            for item in feed.items
        ],
        "total_count": feed.total_count,
        "page": feed.page,
        "page_size": feed.page_size,
    }


@router.get("/youtube/search")
async def youtube_search(
    q: str = Query(..., min_length=2, max_length=120),
    limit: int = Query(12, ge=1, le=25),
):
    """Search YouTube for playable content matching a query."""
    results = await youtube.search(q, limit)
    return {
        "query": q,
        "available": youtube.search_available(),
        "results": results,
        "fallback_url": SEARCH_TEMPLATE.format(query=quote_plus(q)),
    }


@router.get("/youtube/category/{category}")
async def youtube_category(category: str, limit: int = Query(12, ge=1, le=25)):
    """Curated YouTube feed for one content category."""
    query = CATEGORY_QUERIES.get(category, CATEGORY_QUERIES["all"])
    results = await youtube.search(query, limit)
    return {
        "category": category,
        "query": query,
        "available": youtube.search_available(),
        "results": results,
        "fallback_url": SEARCH_TEMPLATE.format(query=quote_plus(query)),
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

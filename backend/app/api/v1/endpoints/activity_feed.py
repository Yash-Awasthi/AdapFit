"""Social Activity Feed — vertical feed with workout posts, likes, comments, shares."""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from app.core.storage import storage

router = APIRouter()

# In-memory feed storage (would be DB in production)
_activity_feed: list[dict] = []


class PostWorkoutRequest(BaseModel):
    user_id: str
    workout_id: str
    caption: str = Field(max_length=500, default="")
    is_public: bool = True


class CommentRequest(BaseModel):
    user_id: str
    content: str = Field(min_length=1, max_length=300)


class FeedItem(BaseModel):
    post_id: str
    user_id: str
    user_name: str
    workout_id: str
    workout_title: str
    exercises_summary: str
    duration_minutes: int
    total_volume: float
    recovery_score: Optional[float]
    readiness_state: Optional[str]
    caption: str
    likes_count: int
    comments_count: int
    is_public: bool
    created_at: str


@router.post("/post")
async def post_workout_to_feed(req: PostWorkoutRequest):
    """Post a completed workout to the activity feed."""
    # Get workout details
    workouts = await storage.get_workouts(req.user_id, 30)
    workout = next((w for w in workouts if w.get("workout_id") == req.workout_id), None)

    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    exercises = workout.get("exercises", [])
    ex_summary = ", ".join(e.get("name", e.get("exercise_id", "")) for e in exercises[:4])
    if len(exercises) > 4:
        ex_summary += f" +{len(exercises) - 4} more"

    total_volume = sum(
        (e.get("actual_weight", 0) or 0) * (e.get("actual_reps", 0) or 0) * (e.get("sets", 0) or 0)
        for e in exercises
    )

    post = {
        "post_id": str(uuid.uuid4()),
        "user_id": req.user_id,
        "user_name": req.user_id[:8].capitalize(),
        "workout_id": req.workout_id,
        "workout_title": workout.get("title", "Workout"),
        "exercises_summary": ex_summary,
        "duration_minutes": workout.get("actual_duration_minutes", 0) or 0,
        "total_volume": round(total_volume, 0),
        "recovery_score": None,
        "readiness_state": workout.get("readiness_state"),
        "caption": req.caption,
        "likes": set(),
        "likes_count": 0,
        "comments": [],
        "comments_count": 0,
        "is_public": req.is_public,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    _activity_feed.insert(0, post)
    # Keep feed manageable
    if len(_activity_feed) > 500:
        _activity_feed.pop()

    return {"post_id": post["post_id"], "created": True}


@router.get("")
async def get_activity_feed(
    user_id: str = Query("default"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    """Get the activity feed with posts from all users."""
    public_posts = [p for p in _activity_feed if p["is_public"]]
    items = public_posts[offset:offset + limit]

    return {
        "items": [
            {
                "post_id": p["post_id"],
                "user_id": p["user_id"],
                "user_name": p["user_name"],
                "workout_title": p["workout_title"],
                "exercises_summary": p["exercises_summary"],
                "duration_minutes": p["duration_minutes"],
                "total_volume": p["total_volume"],
                "caption": p["caption"],
                "likes_count": p["likes_count"],
                "comments_count": p["comments_count"],
                "is_liked": user_id in p["likes"],
                "created_at": p["created_at"],
            }
            for p in items
        ],
        "total": len(public_posts),
        "has_more": offset + limit < len(public_posts),
    }


@router.post("/{post_id}/like")
async def like_post(post_id: str, user_id: str = Query(...)):
    """Like or unlike a post."""
    post = next((p for p in _activity_feed if p["post_id"] == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if user_id in post["likes"]:
        post["likes"].discard(user_id)
        post["likes_count"] = max(0, post["likes_count"] - 1)
        return {"liked": False, "likes_count": post["likes_count"]}
    else:
        post["likes"].add(user_id)
        post["likes_count"] += 1
        return {"liked": True, "likes_count": post["likes_count"]}


@router.post("/{post_id}/comment")
async def comment_on_post(post_id: str, req: CommentRequest):
    """Add a comment to a post."""
    post = next((p for p in _activity_feed if p["post_id"] == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comment = {
        "comment_id": str(uuid.uuid4()),
        "user_id": req.user_id,
        "user_name": req.user_id[:8].capitalize(),
        "content": req.content,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    post["comments"].append(comment)
    post["comments_count"] += 1

    return {"comment_id": comment["comment_id"], "created": True}


@router.get("/{post_id}/comments")
async def get_comments(post_id: str, limit: int = Query(20, ge=1, le=100)):
    """Get comments for a post."""
    post = next((p for p in _activity_feed if p["post_id"] == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return {"comments": post["comments"][:limit], "total": len(post["comments"])}

"""Workout sharing community: share workouts, like, comment, browse feed."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter()


class WorkoutShareRequest(BaseModel):
    workout_id: str
    title: str = Field(min_length=1, max_length=200)
    caption: str = Field(max_length=1000, default="")
    is_public: bool = True


class CommentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class ShareResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    workout_id: str
    title: str
    caption: str
    exercises_summary: str
    duration_minutes: int
    readiness_state: str
    likes: int
    comments_count: int
    is_public: bool
    shared_at: str


class CommentResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    text: str
    created_at: str


# In-memory storage
shared_workouts: dict = {}  # share_id -> share data
community_comments: dict = {}  # share_id -> list of comments
community_likes: dict = {}  # share_id -> set of user_ids


@router.get("/feed", response_model=List[ShareResponse])
async def get_community_feed(
    user_id: str = Query("default"),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("recent", pattern="^(recent|popular|following)$"),
):
    """Get the community feed of shared workouts."""
    public_shares = [s for s in shared_workouts.values() if s["is_public"]]

    if sort == "popular":
        public_shares.sort(key=lambda s: len(community_likes.get(s["id"], set())), reverse=True)
    else:
        public_shares.sort(key=lambda s: s["shared_at"], reverse=True)

    results = []
    for s in public_shares[:limit]:
        sid = s["id"]
        results.append(ShareResponse(
            id=sid,
            user_id=s["user_id"],
            user_name=s["user_name"],
            workout_id=s["workout_id"],
            title=s["title"],
            caption=s["caption"],
            exercises_summary=s["exercises_summary"],
            duration_minutes=s["duration_minutes"],
            readiness_state=s["readiness_state"],
            likes=len(community_likes.get(sid, set())),
            comments_count=len(community_comments.get(sid, [])),
            is_public=s["is_public"],
            shared_at=s["shared_at"],
        ))
    return results


@router.post("/share", response_model=ShareResponse, status_code=201)
async def share_workout(request: WorkoutShareRequest, user_id: str = Query("default")):
    """Share a completed workout to the community."""
    # Get workout details from storage
    try:
        from app.core.storage import storage
        workouts = await storage.get_workouts(user_id, 90)
    except Exception:
        workouts = []

    workout = next((w for w in workouts if w.get("workout_id") == request.workout_id), None)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    exercises = workout.get("exercises", [])
    ex_summary = ", ".join(e.get("name", "") for e in exercises[:3])
    if len(exercises) > 3:
        ex_summary += f" +{len(exercises) - 3} more"

    sid = str(uuid.uuid4())[:8]
    share = {
        "id": sid,
        "user_id": user_id,
        "user_name": user_id,  # Would be real user name in production
        "workout_id": request.workout_id,
        "title": request.title,
        "caption": request.caption,
        "exercises_summary": ex_summary,
        "duration_minutes": workout.get("target_duration_minutes", 0),
        "readiness_state": workout.get("readiness_state", "unknown"),
        "is_public": request.is_public,
        "shared_at": datetime.now(timezone.utc).isoformat(),
    }
    shared_workouts[sid] = share
    community_likes[sid] = set()
    community_comments[sid] = []

    return ShareResponse(
        id=sid, user_id=user_id, user_name=user_id,
        workout_id=request.workout_id, title=request.title,
        caption=request.caption, exercises_summary=ex_summary,
        duration_minutes=share["duration_minutes"],
        readiness_state=share["readiness_state"],
        likes=0, comments_count=0, is_public=request.is_public,
        shared_at=share["shared_at"],
    )


@router.post("/{share_id}/like")
async def like_workout(share_id: str, user_id: str = Query("default")):
    """Like or unlike a shared workout."""
    if share_id not in shared_workouts:
        raise HTTPException(status_code=404, detail="Shared workout not found")

    likes = community_likes.setdefault(share_id, set())
    if user_id in likes:
        likes.discard(user_id)
        return {"liked": False, "total_likes": len(likes)}
    else:
        likes.add(user_id)
        return {"liked": True, "total_likes": len(likes)}


@router.get("/{share_id}/comments", response_model=List[CommentResponse])
async def get_comments(share_id: str, limit: int = Query(20, ge=1, le=100)):
    """Get comments on a shared workout."""
    if share_id not in shared_workouts:
        raise HTTPException(status_code=404, detail="Shared workout not found")

    comments = community_comments.get(share_id, [])
    return [
        CommentResponse(id=c["id"], user_id=c["user_id"], user_name=c["user_name"],
                        text=c["text"], created_at=c["created_at"])
        for c in comments[:limit]
    ]


@router.post("/{share_id}/comments", response_model=CommentResponse, status_code=201)
async def add_comment(share_id: str, request: CommentRequest, user_id: str = Query("default")):
    """Add a comment to a shared workout."""
    if share_id not in shared_workouts:
        raise HTTPException(status_code=404, detail="Shared workout not found")

    comment = {
        "id": str(uuid.uuid4())[:8],
        "user_id": user_id,
        "user_name": user_id,
        "text": request.text,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    community_comments.setdefault(share_id, []).append(comment)

    return CommentResponse(**comment)


@router.delete("/{share_id}")
async def delete_share(share_id: str, user_id: str = Query("default")):
    """Delete a shared workout (owner only)."""
    share = shared_workouts.get(share_id)
    if not share:
        raise HTTPException(status_code=404, detail="Not found")
    if share["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not your share")

    del shared_workouts[share_id]
    community_likes.pop(share_id, None)
    community_comments.pop(share_id, None)
    return {"deleted": True}


@router.get("/my-shares", response_model=List[ShareResponse])
async def my_shares(user_id: str = Query("default"), limit: int = Query(20, ge=1, le=50)):
    """Get user's own shared workouts."""
    my = [s for s in shared_workouts.values() if s["user_id"] == user_id]
    my.sort(key=lambda s: s["shared_at"], reverse=True)

    return [
        ShareResponse(
            id=s["id"], user_id=s["user_id"], user_name=s["user_name"],
            workout_id=s["workout_id"], title=s["title"], caption=s["caption"],
            exercises_summary=s["exercises_summary"],
            duration_minutes=s["duration_minutes"],
            readiness_state=s["readiness_state"],
            likes=len(community_likes.get(s["id"], set())),
            comments_count=len(community_comments.get(s["id"], [])),
            is_public=s["is_public"], shared_at=s["shared_at"],
        )
        for s in my[:limit]
    ]

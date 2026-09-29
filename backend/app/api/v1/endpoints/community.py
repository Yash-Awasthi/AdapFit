"""Workout sharing community: share workouts, like, comment, browse feed."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.durable import durable_dict

router = APIRouter()


class WorkoutShareRequest(BaseModel):
    # Omitted for a plain discussion post, which shares the same feed,
    # like, and comment machinery as a shared workout.
    workout_id: Optional[str] = None
    title: str = Field(min_length=1, max_length=200)
    caption: str = Field(max_length=1000, default="")
    category: str = Field(max_length=40, default="general")
    is_public: bool = True


class CommentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class ShareResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    workout_id: Optional[str] = None
    category: str = "general"
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
shared_workouts = durable_dict("app.api.v1.endpoints.community.shared_workouts")  # share_id -> share data
community_comments = durable_dict("app.api.v1.endpoints.community.community_comments")  # share_id -> list of comments
community_likes = durable_dict("app.api.v1.endpoints.community.community_likes")  # share_id -> set of user_ids
# Google Play requires reporting and blocking wherever users post.
community_reports = durable_dict("app.api.v1.endpoints.community.reports")  # share_id -> {reporter id: report}
community_blocks = durable_dict("app.api.v1.endpoints.community.blocks")  # user_id -> list of blocked user ids
# ponytail: a post three people report is hidden from everyone until reviewed; a moderator queue replaces this.
HIDE_AFTER_REPORTS = 3


class ReportRequest(BaseModel):
    reason: str = Field(pattern="^(spam|abuse|harmful_health_advice|sexual|other)$")
    comment_id: Optional[str] = None
    detail: str = Field("", max_length=500)


def _visible_to(user_id: str, author_id: str, share_id: Optional[str] = None) -> bool:
    if author_id in (community_blocks.get(user_id) or []):
        return False
    if share_id is None:
        return True
    post_reports = {r for r, rep in (community_reports.get(share_id) or {}).items() if not rep.get("comment_id")}
    return user_id not in post_reports and len(post_reports) < HIDE_AFTER_REPORTS


@router.post("/{share_id}/report", status_code=201)
async def report_share(share_id: str, request: ReportRequest, user_id: str = Query("default")):
    """Report a post or one of its comments. The reporter stops seeing the post at once."""
    if share_id not in shared_workouts:
        raise HTTPException(status_code=404, detail="Shared workout not found")
    reports = dict(community_reports.get(share_id) or {})
    reports[user_id] = {"reason": request.reason, "comment_id": request.comment_id, "detail": request.detail,
                        "at": datetime.now(timezone.utc).isoformat()}
    community_reports[share_id] = reports
    from app.core import audit
    await audit.record("community_report", user_id=shared_workouts[share_id]["user_id"], actor_id=user_id,
                       share_id=share_id, reason=request.reason, comment_id=request.comment_id)
    return {"reported": True, "hidden_for_everyone": not _visible_to("", "", share_id)}


@router.post("/block/{blocked_id}")
async def block_user(blocked_id: str, user_id: str = Query("default")):
    """Hide everything this person posts or comments, for the caller only."""
    if blocked_id == user_id:
        raise HTTPException(status_code=400, detail="You cannot block yourself")
    blocked = list(community_blocks.get(user_id) or [])
    if blocked_id not in blocked:
        blocked.append(blocked_id)
    community_blocks[user_id] = blocked
    return {"blocked": blocked}


@router.delete("/block/{blocked_id}")
async def unblock_user(blocked_id: str, user_id: str = Query("default")):
    community_blocks[user_id] = [b for b in (community_blocks.get(user_id) or []) if b != blocked_id]
    return {"blocked": community_blocks[user_id]}


@router.get("/feed", response_model=List[ShareResponse])
async def get_community_feed(
    user_id: str = Query("default"),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("recent", pattern="^(recent|popular|following)$"),
):
    """Get the community feed of shared workouts."""
    public_shares = [s for s in shared_workouts.values()
                     if s["is_public"] and _visible_to(user_id, s["user_id"], s["id"])]

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
            category=s.get("category", "general"),
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

    workout = None
    if request.workout_id:
        workout = next((w for w in workouts if w.get("workout_id") == request.workout_id), None)
        if not workout:
            raise HTTPException(status_code=404, detail="Workout not found")

    exercises = (workout or {}).get("exercises", [])
    ex_summary = ", ".join(e.get("name", "") for e in exercises[:3])
    if len(exercises) > 3:
        ex_summary += f" +{len(exercises) - 3} more"

    sid = str(uuid.uuid4())[:8]
    share = {
        "id": sid,
        "user_id": user_id,
        "user_name": user_id,  # Would be real user name in production
        "workout_id": request.workout_id,
        "category": request.category,
        "title": request.title,
        "caption": request.caption,
        "exercises_summary": ex_summary,
        "duration_minutes": (workout or {}).get("target_duration_minutes", 0),
        "readiness_state": (workout or {}).get("readiness_state", "unknown"),
        "is_public": request.is_public,
        "shared_at": datetime.now(timezone.utc).isoformat(),
    }
    shared_workouts[sid] = share
    community_likes[sid] = set()
    community_comments[sid] = []

    return ShareResponse(
        id=sid, user_id=user_id, user_name=user_id,
        workout_id=request.workout_id, category=request.category,
        title=request.title,
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
async def get_comments(share_id: str, limit: int = Query(20, ge=1, le=100), user_id: str = Query("default")):
    """Get comments on a shared workout."""
    if share_id not in shared_workouts:
        raise HTTPException(status_code=404, detail="Shared workout not found")

    mine = (community_reports.get(share_id) or {}).get(user_id) or {}
    comments = [c for c in community_comments.get(share_id, [])
                if _visible_to(user_id, c["user_id"]) and c["id"] != mine.get("comment_id")]
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
            workout_id=s["workout_id"], category=s.get("category", "general"),
            title=s["title"], caption=s["caption"],
            exercises_summary=s["exercises_summary"],
            duration_minutes=s["duration_minutes"],
            readiness_state=s["readiness_state"],
            likes=len(community_likes.get(s["id"], set())),
            comments_count=len(community_comments.get(s["id"], [])),
            is_public=s["is_public"], shared_at=s["shared_at"],
        )
        for s in my[:limit]
    ]

"""Social features: challenges, leaderboard, activity feed."""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from app.services.websocket_manager import ws_manager

router = APIRouter()


# --- Schemas ---
class ChallengeCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100, examples=["30-Day Plank Challenge"])
    description: str = Field(min_length=10, max_length=500, examples=["Hold a plank for 5 minutes total each day"])
    challenge_type: str = Field(default="duration", examples=["duration", "reps", "streak", "custom"])
    target_value: int = Field(ge=1, examples=[30])
    target_unit: str = Field(default="days", examples=["days", "reps", "minutes", "km"])
    duration_days: int = Field(ge=1, le=365, default=30, examples=[30])


class ChallengeResponse(BaseModel):
    id: str
    name: str
    description: str
    challenge_type: str
    target_value: int
    target_unit: str
    duration_days: int
    created_by: str
    created_at: str
    ends_at: str
    participant_count: int = 0
    is_active: bool = True


class ChallengeJoinResponse(BaseModel):
    message: str
    challenge_id: str
    participant_id: str


class ProgressUpdate(BaseModel):
    value: float = Field(ge=0, examples=[5])
    note: Optional[str] = Field(None, max_length=200, examples=["Held plank for 5 min today"])


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    user_name: str
    score: float
    progress_pct: float
    is_current_user: bool = False


class ActivityFeedItem(BaseModel):
    id: str
    user_name: str
    action: str
    detail: str
    timestamp: str


# --- In-memory storage ---
challenges: dict = {}
participants: dict = {}  # challenge_id -> {user_id -> {progress, joined_at}}
activity_feed: list = []


@router.get("", response_model=List[ChallengeResponse])
async def list_challenges(
    user_id: str = Query("default"),
    active_only: bool = Query(True),
):
    """List available challenges."""
    now = datetime.now(timezone.utc)
    results = []
    for c in challenges.values():
        if active_only and datetime.fromisoformat(c["ends_at"]) < now:
            continue
        cid = c["id"]
        results.append(ChallengeResponse(
            id=cid,
            name=c["name"],
            description=c["description"],
            challenge_type=c["challenge_type"],
            target_value=c["target_value"],
            target_unit=c["target_unit"],
            duration_days=c["duration_days"],
            created_by=c["created_by"],
            created_at=c["created_at"],
            ends_at=c["ends_at"],
            participant_count=len(participants.get(cid, {})),
        ))
    return results


@router.post("", response_model=ChallengeResponse, status_code=201)
async def create_challenge(challenge: ChallengeCreate, user_id: str = Query("default")):
    """Create a new challenge."""
    now = datetime.now(timezone.utc)
    cid = str(uuid.uuid4())[:8]
    c = {
        "id": cid,
        **challenge.model_dump(),
        "created_by": user_id,
        "created_at": now.isoformat(),
        "ends_at": (now + timedelta(days=challenge.duration_days)).isoformat(),
    }
    challenges[cid] = c
    participants[cid] = {}
    activity_feed.append({
        "id": str(uuid.uuid4())[:8],
        "user_name": user_id,
        "action": "created challenge",
        "detail": challenge.name,
        "timestamp": now.isoformat(),
    })
    return ChallengeResponse(
        id=cid, name=c["name"], description=c["description"],
        challenge_type=c["challenge_type"], target_value=c["target_value"],
        target_unit=c["target_unit"], duration_days=c["duration_days"],
        created_by=c["created_by"], created_at=c["created_at"],
        ends_at=c["ends_at"], participant_count=0,
    )


@router.post("/{challenge_id}/join", response_model=ChallengeJoinResponse)
async def join_challenge(challenge_id: str, user_id: str = Query("default")):
    """Join a challenge."""
    if challenge_id not in challenges:
        raise HTTPException(status_code=404, detail="Challenge not found")
    c = participants.setdefault(challenge_id, {})
    if user_id in c:
        raise HTTPException(status_code=409, detail="Already joined")
    pid = str(uuid.uuid4())[:8]
    c[user_id] = {"progress": 0, "joined_at": datetime.now(timezone.utc).isoformat(), "pid": pid}
    activity_feed.append({
        "id": str(uuid.uuid4())[:8],
        "user_name": user_id,
        "action": "joined challenge",
        "detail": challenges[challenge_id]["name"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    # Broadcast live update to all connected users
    asyncio.create_task(ws_manager.push_social_update("challenge_joined", {
        "challenge_id": challenge_id,
        "challenge_name": challenges[challenge_id]["name"],
        "user_name": user_id,
        "participant_count": len(c),
    }))
    return ChallengeJoinResponse(message="Joined!", challenge_id=challenge_id, participant_id=pid)


@router.post("/{challenge_id}/progress", response_model=ChallengeResponse)
async def update_progress(challenge_id: str, update: ProgressUpdate, user_id: str = Query("default")):
    """Update progress for a challenge."""
    if challenge_id not in challenges:
        raise HTTPException(status_code=404, detail="Challenge not found")
    c = participants.get(challenge_id, {})
    if user_id not in c:
        raise HTTPException(status_code=400, detail="Not joined")
    c[user_id]["progress"] = update.value
    activity_feed.append({
        "id": str(uuid.uuid4())[:8],
        "user_name": user_id,
        "action": "logged progress",
        "detail": f"{update.value} on {challenges[challenge_id]['name']}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    # Broadcast progress update
    asyncio.create_task(ws_manager.push_social_update("progress_updated", {
        "challenge_id": challenge_id,
        "challenge_name": challenges[challenge_id]["name"],
        "user_name": user_id,
        "progress": update.value,
    }))
    ch = challenges[challenge_id]
    return ChallengeResponse(
        id=challenge_id, name=ch["name"], description=ch["description"],
        challenge_type=ch["challenge_type"], target_value=ch["target_value"],
        target_unit=ch["target_unit"], duration_days=ch["duration_days"],
        created_by=ch["created_by"], created_at=ch["created_at"],
        ends_at=ch["ends_at"], participant_count=len(c),
    )


@router.get("/{challenge_id}/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(challenge_id: str, user_id: str = Query("default")):
    """Get leaderboard for a challenge."""
    if challenge_id not in challenges:
        raise HTTPException(status_code=404, detail="Challenge not found")
    ch = challenges[challenge_id]
    target = ch["target_value"]
    p = participants.get(challenge_id, {})
    entries = []
    for uid, data in sorted(p.items(), key=lambda x: -x[1]["progress"]):
        progress_pct = min((data["progress"] / target) * 100, 100) if target else 0
        entries.append(LeaderboardEntry(
            rank=len(entries) + 1, user_id=uid, user_name=uid,
            score=data["progress"], progress_pct=progress_pct,
            is_current_user=(uid == user_id),
        ))
    return entries


@router.get("/feed", response_model=List[ActivityFeedItem])
async def get_activity_feed(limit: int = Query(20, ge=1, le=100)):
    """Get recent activity feed across all challenges."""
    return [
        ActivityFeedItem(**item)
        for item in sorted(activity_feed, key=lambda x: x["timestamp"], reverse=True)[:limit]
    ]

"""Fitness challenges: pre-built challenges, daily progress, enhanced leaderboards."""
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter()


class ChallengeTemplate(BaseModel):
    id: str
    name: str
    description: str
    category: str  # "strength", "endurance", "flexibility", "consistency"
    target_value: int
    target_unit: str
    duration_days: int
    difficulty: str  # "beginner", "intermediate", "advanced"
    daily_goal: float
    icon: str


class FitnessChallengeResponse(BaseModel):
    id: str
    template_id: Optional[str] = None
    name: str
    description: str
    category: str
    target_value: int
    target_unit: str
    duration_days: int
    daily_goal: float
    difficulty: str
    created_by: str
    created_at: str
    starts_at: str
    ends_at: str
    participant_count: int = 0
    is_active: bool = True
    is_builtin: bool = False


class DailyLogRequest(BaseModel):
    value: float = Field(ge=0, examples=[50])
    note: Optional[str] = Field(None, max_length=200)


class ParticipantProgress(BaseModel):
    user_id: str
    user_name: str
    total_progress: float
    progress_pct: float
    daily_logs: int
    current_streak: int
    best_streak: int
    completed: bool
    rank: int


class LeaderboardResponse(BaseModel):
    challenge_name: str
    target: int
    unit: str
    entries: List[ParticipantProgress]
    total_participants: int


# --- Pre-built challenges ---
BUILTIN_CHALLENGES = [
    ChallengeTemplate(
        id="pushup_30", name="30-Day Push-Up Challenge",
        description="Build upper body strength with progressive push-ups. Start at 10, finish at 100!",
        category="strength", target_value=1500, target_unit="reps", duration_days=30,
        difficulty="beginner", daily_goal=50, icon="💪",
    ),
    ChallengeTemplate(
        id="running_100k", name="100km Running Month",
        description="Run 100km this month. That's about 3.3km per day!",
        category="endurance", target_value=100, target_unit="km", duration_days=30,
        difficulty="intermediate", daily_goal=3.3, icon="🏃",
    ),
    ChallengeTemplate(
        id="plank_30", name="30-Day Plank Challenge",
        description="Hold a plank every day. Start at 20s, work up to 5 minutes.",
        category="strength", target_value=9000, target_unit="seconds", duration_days=30,
        difficulty="beginner", daily_goal=300, icon="🏋️",
    ),
    ChallengeTemplate(
        id="steps_million", name="Million Steps Month",
        description="Walk 1,000,000 steps in a month. That's about 33,333 per day.",
        category="endurance", target_value=1000000, target_unit="steps", duration_days=30,
        difficulty="intermediate", daily_goal=33333, icon="🚶",
    ),
    ChallengeTemplate(
        id="squat_1000", name="1000 Squats in a Week",
        description="Complete 1000 bodyweight squats in 7 days. About 143 per day.",
        category="strength", target_value=1000, target_unit="reps", duration_days=7,
        difficulty="advanced", daily_goal=143, icon="🦵",
    ),
    ChallengeTemplate(
        id="yoga_30", name="30-Day Yoga Streak",
        description="Practice yoga for at least 20 minutes every day for 30 days.",
        category="flexibility", target_value=600, target_unit="minutes", duration_days=30,
        difficulty="beginner", daily_goal=20, icon="🧘",
    ),
    ChallengeTemplate(
        id="consistency_21", name="21-Day Training Streak",
        description="Work out every single day for 21 days. Any workout counts!",
        category="consistency", target_value=21, target_unit="sessions", duration_days=21,
        difficulty="intermediate", daily_goal=1, icon="🔥",
    ),
    ChallengeTemplate(
        id="bench_100k", name="Bench Press 100kg Club",
        description="Work up to a 100kg bench press. Log your working sets.",
        category="strength", target_value=100, target_unit="kg", duration_days=60,
        difficulty="advanced", daily_goal=1.7, icon="🏆",
    ),
]


# In-memory storage
fitness_challenges: dict = {}  # challenge_id -> challenge data
fitness_participants: dict = {}  # challenge_id -> {user_id -> participant data}
fitness_daily_logs: dict = {}  # challenge_id -> {user_id -> [{date, value, note}]}
builtin_used: set = set()  # track which builtins have been instantiated


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("", response_model=List[FitnessChallengeResponse])
async def list_challenges(
    user_id: str = Query("default"),
    category: Optional[str] = Query(None),
    include_builtin: bool = Query(True),
    active_only: bool = Query(True),
):
    """List available fitness challenges."""
    now = datetime.now(timezone.utc)
    results = []

    if include_builtin:
        for t in BUILTIN_CHALLENGES:
            if category and t.category != category:
                continue
            results.append(FitnessChallengeResponse(
                id=t.id, template_id=t.id, name=t.name, description=t.description,
                category=t.category, target_value=t.target_value, target_unit=t.target_unit,
                duration_days=t.duration_days, daily_goal=t.daily_goal, difficulty=t.difficulty,
                created_by="system", created_at="2026-01-01T00:00:00Z",
                starts_at="2026-01-01T00:00:00Z", ends_at="2026-12-31T23:59:59Z",
                participant_count=len(fitness_participants.get(t.id, {})),
                is_active=True, is_builtin=True,
            ))

    for c in fitness_challenges.values():
        if active_only and datetime.fromisoformat(c["ends_at"]) < now:
            continue
        if category and c["category"] != category:
            continue
        cid = c["id"]
        results.append(FitnessChallengeResponse(
            id=cid, template_id=c.get("template_id"), name=c["name"],
            description=c["description"], category=c["category"],
            target_value=c["target_value"], target_unit=c["target_unit"],
            duration_days=c["duration_days"], daily_goal=c["daily_goal"],
            difficulty=c["difficulty"], created_by=c["created_by"],
            created_at=c["created_at"], starts_at=c["starts_at"],
            ends_at=c["ends_at"],
            participant_count=len(fitness_participants.get(cid, {})),
            is_active=True, is_builtin=False,
        ))

    return results


@router.get("/categories")
async def list_categories():
    """List challenge categories."""
    return {
        "categories": [
            {"id": "strength", "name": "Strength", "icon": "💪"},
            {"id": "endurance", "name": "Endurance", "icon": "🏃"},
            {"id": "flexibility", "name": "Flexibility", "icon": "🧘"},
            {"id": "consistency", "name": "Consistency", "icon": "🔥"},
        ]
    }


@router.get("/builtin", response_model=List[ChallengeTemplate])
async def get_builtin_challenges():
    """Get all pre-built challenge templates."""
    return BUILTIN_CHALLENGES


@router.post("/join/{challenge_id}")
async def join_challenge(challenge_id: str, user_id: str = Query("default")):
    """Join a fitness challenge."""
    # Check builtins
    template = next((t for t in BUILTIN_CHALLENGES if t.id == challenge_id), None)

    if not template and challenge_id not in fitness_challenges:
        raise HTTPException(status_code=404, detail="Challenge not found")

    participants = fitness_participants.setdefault(challenge_id, {})
    if user_id in participants:
        raise HTTPException(status_code=409, detail="Already joined this challenge")

    now = datetime.now(timezone.utc)
    if template and challenge_id not in fitness_challenges:
        # Instantiate the builtin
        fitness_challenges[challenge_id] = {
            "id": challenge_id, "template_id": template.id,
            "name": template.name, "description": template.description,
            "category": template.category, "target_value": template.target_value,
            "target_unit": template.target_unit, "duration_days": template.duration_days,
            "daily_goal": template.daily_goal, "difficulty": template.difficulty,
            "created_by": "system", "created_at": "2026-01-01T00:00:00Z",
            "starts_at": now.isoformat(),
            "ends_at": (now + timedelta(days=template.duration_days)).isoformat(),
        }

    participants[user_id] = {
        "joined_at": now.isoformat(),
        "total_progress": 0,
        "daily_logs_count": 0,
        "current_streak": 0,
        "best_streak": 0,
    }
    fitness_daily_logs.setdefault(challenge_id, {})[user_id] = []

    ch = fitness_challenges.get(challenge_id, {})
    return {
        "message": f"Joined '{ch.get('name', challenge_id)}'!",
        "challenge_id": challenge_id,
        "participants": len(participants),
    }


@router.post("/{challenge_id}/log")
async def log_daily_progress(
    challenge_id: str, request: DailyLogRequest, user_id: str = Query("default"),
):
    """Log daily progress for a challenge."""
    if challenge_id not in fitness_participants:
        raise HTTPException(status_code=404, detail="Not joined this challenge")

    participants = fitness_participants[challenge_id]
    if user_id not in participants:
        raise HTTPException(status_code=404, detail="Not joined this challenge")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    logs = fitness_daily_logs.setdefault(challenge_id, {}).setdefault(user_id, [])

    # Check for duplicate day
    if any(l["date"] == today for l in logs):
        raise HTTPException(status_code=409, detail="Already logged today")

    logs.append({"date": today, "value": request.value, "note": request.note})

    # Update participant stats
    p = participants[user_id]
    p["total_progress"] = sum(l["value"] for l in logs)
    p["daily_logs_count"] = len(logs)

    # Update streak
    dates = sorted(set(l["date"] for l in logs))
    streak = 1
    for i in range(len(dates) - 1, 0, -1):
        d1 = datetime.strptime(dates[i], "%Y-%m-%d")
        d2 = datetime.strptime(dates[i - 1], "%Y-%m-%d")
        if (d1 - d2).days == 1:
            streak += 1
        else:
            break
    p["current_streak"] = streak
    p["best_streak"] = max(p.get("best_streak", 0), streak)

    ch = fitness_challenges.get(challenge_id, {})
    target = ch.get("target_value", 1)
    progress_pct = min(100, (p["total_progress"] / target) * 100) if target > 0 else 0
    p["completed"] = progress_pct >= 100

    return {
        "logged": True, "date": today, "value": request.value,
        "total_progress": p["total_progress"],
        "progress_pct": round(progress_pct, 1),
        "current_streak": streak,
        "completed": p["completed"],
    }


@router.get("/{challenge_id}/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(challenge_id: str, user_id: str = Query("default")):
    """Get the leaderboard for a challenge."""
    ch = fitness_challenges.get(challenge_id)
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found")

    participants = fitness_participants.get(challenge_id, {})
    target = ch["target_value"]

    entries = []
    for uid, data in sorted(participants.items(), key=lambda x: -x[1]["total_progress"]):
        progress_pct = min(100, (data["total_progress"] / target) * 100) if target > 0 else 0
        entries.append(ParticipantProgress(
            user_id=uid, user_name=uid,
            total_progress=data["total_progress"],
            progress_pct=round(progress_pct, 1),
            daily_logs=data.get("daily_logs_count", 0),
            current_streak=data.get("current_streak", 0),
            best_streak=data.get("best_streak", 0),
            completed=data.get("completed", False),
            rank=len(entries) + 1,
        ))

    return LeaderboardResponse(
        challenge_name=ch["name"], target=target,
        unit=ch["target_unit"], entries=entries,
        total_participants=len(participants),
    )


@router.get("/{challenge_id}/my-progress")
async def my_progress(challenge_id: str, user_id: str = Query("default")):
    """Get my progress in a challenge."""
    participants = fitness_participants.get(challenge_id, {})
    if user_id not in participants:
        raise HTTPException(status_code=404, detail="Not joined this challenge")

    p = participants[user_id]
    logs = fitness_daily_logs.get(challenge_id, {}).get(user_id, [])
    ch = fitness_challenges.get(challenge_id, {})
    target = ch.get("target_value", 1)

    return {
        "total_progress": p["total_progress"],
        "progress_pct": round(min(100, (p["total_progress"] / target) * 100), 1),
        "daily_logs_count": p.get("daily_logs_count", 0),
        "current_streak": p.get("current_streak", 0),
        "best_streak": p.get("best_streak", 0),
        "completed": p.get("completed", False),
        "recent_logs": logs[-7:],
        "target": target,
        "unit": ch.get("target_unit", ""),
    }


@router.delete("/{challenge_id}")
async def leave_challenge(challenge_id: str, user_id: str = Query("default")):
    """Leave a challenge."""
    participants = fitness_participants.get(challenge_id, {})
    if user_id not in participants:
        raise HTTPException(status_code=404, detail="Not joined")

    del participants[user_id]
    fitness_daily_logs.get(challenge_id, {}).pop(user_id, None)
    return {"left": True}

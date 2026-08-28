"""Goal tracking: set goals, track progress, milestones, and celebrations."""
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter()


class GoalCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100, examples=["Squat 1.5x Bodyweight"])
    description: str = Field(max_length=500, default="")
    goal_type: str = Field(examples=["strength", "body_composition", "consistency", "habit", "custom"])
    target_value: float = Field(ge=0, examples=[120])
    target_unit: str = Field(default="kg", examples=["kg", "reps", "minutes", "days", "sessions"])
    deadline_days: int = Field(ge=1, le=365, default=90)
    milestones: List[float] = Field(default_factory=list, description="Intermediate milestone values")


class GoalUpdate(BaseModel):
    current_value: Optional[float] = None
    name: Optional[str] = None
    notes: Optional[str] = None


class GoalResponse(BaseModel):
    id: str
    name: str
    description: str
    goal_type: str
    target_value: float
    target_unit: str
    current_value: float
    progress_pct: float
    status: str  # "active", "achieved", "expired", "paused"
    milestones_achieved: List[float]
    streak_days: int
    best_streak: int
    created_at: str
    deadline: str
    celebration: Optional[str] = None


class MilestoneResponse(BaseModel):
    goal_id: str
    milestone_value: float
    achieved_at: Optional[str]
    is_achieved: bool
    celebration_message: str


# In-memory storage
user_goals: dict = {}  # user_id -> list of goals
goal_logs: dict = {}  # goal_id -> list of {date, value}
goal_streaks: dict = {}  # goal_id -> {current, best, last_date}


CELEBRATIONS = {
    25: "Quarter way there! Keep pushing!",
    50: "Halfway to your goal! You're crushing it!",
    75: "Three quarters done! The finish line is in sight!",
    100: "GOAL ACHIEVED! You did it! Incredible work!",
}


def _update_streak(goal_id: str):
    """Update streak tracking for a goal."""
    logs = goal_logs.get(goal_id, [])
    if not logs:
        return

    dates = sorted(set(l["date"] for l in logs))
    streak = goal_streaks.setdefault(goal_id, {"current": 0, "best": 0, "last_date": ""})

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    if dates:
        last = dates[-1]
        if last == today:
            # Check consecutive days
            consecutive = 1
            for i in range(len(dates) - 2, -1, -1):
                d1 = datetime.strptime(dates[i + 1], "%Y-%m-%d")
                d2 = datetime.strptime(dates[i], "%Y-%m-%d")
                if (d1 - d2).days == 1:
                    consecutive += 1
                else:
                    break
            streak["current"] = consecutive
        elif last == yesterday:
            streak["current"] = streak.get("current", 1)
        else:
            streak["current"] = 1

        streak["best"] = max(streak.get("best", 0), streak["current"])
        streak["last_date"] = last


@router.get("", response_model=List[GoalResponse])
async def list_goals(user_id: str = Query("default"), status: Optional[str] = Query(None)):
    """List user goals."""
    goals = user_goals.get(user_id, [])

    now = datetime.now(timezone.utc)
    results = []
    for g in goals:
        # Check if expired
        deadline = datetime.fromisoformat(g["deadline"].replace("Z", "+00:00"))
        if deadline < now and g["status"] == "active":
            g["status"] = "expired"

        progress = (g["current_value"] / g["target_value"] * 100) if g["target_value"] > 0 else 0
        progress = min(100, max(0, progress))

        _update_streak(g["id"])
        streak_info = goal_streaks.get(g["id"], {"current": 0, "best": 0})

        # Check milestones
        achieved = [m for m in g.get("milestones", []) if g["current_value"] >= m]

        # Celebration check
        celebration = None
        if progress >= 100 and g["status"] != "achieved":
            g["status"] = "achieved"
            celebration = CELEBRATIONS[100]
        elif progress >= 75:
            celebration = CELEBRATIONS[75]
        elif progress >= 50:
            celebration = CELEBRATIONS[50]
        elif progress >= 25:
            celebration = CELEBRATIONS[25]

        results.append(GoalResponse(
            id=g["id"], name=g["name"], description=g["description"],
            goal_type=g["goal_type"], target_value=g["target_value"],
            target_unit=g["target_unit"], current_value=g["current_value"],
            progress_pct=round(progress, 1), status=g["status"],
            milestones_achieved=achieved, streak_days=streak_info["current"],
            best_streak=streak_info["best"], created_at=g["created_at"],
            deadline=g["deadline"], celebration=celebration,
        ))

    if status:
        results = [r for r in results if r.status == status]

    return results


@router.post("", response_model=GoalResponse, status_code=201)
async def create_goal(request: GoalCreate, user_id: str = Query("default")):
    """Create a new goal."""
    now = datetime.now(timezone.utc)
    gid = str(uuid.uuid4())[:8]
    deadline = (now + timedelta(days=request.deadline_days)).isoformat()

    # Default milestones at 25%, 50%, 75%
    milestones = request.milestones
    if not milestones:
        milestones = [
            round(request.target_value * 0.25, 1),
            round(request.target_value * 0.50, 1),
            round(request.target_value * 0.75, 1),
        ]

    goal = {
        "id": gid,
        "name": request.name,
        "description": request.description,
        "goal_type": request.goal_type,
        "target_value": request.target_value,
        "target_unit": request.target_unit,
        "current_value": 0,
        "milestones": milestones,
        "status": "active",
        "created_at": now.isoformat(),
        "deadline": deadline,
    }
    user_goals.setdefault(user_id, []).append(goal)
    goal_streaks[gid] = {"current": 0, "best": 0, "last_date": ""}

    return GoalResponse(
        id=gid, name=goal["name"], description=goal["description"],
        goal_type=goal["goal_type"], target_value=goal["target_value"],
        target_unit=goal["target_unit"], current_value=0,
        progress_pct=0, status="active", milestones_achieved=[],
        streak_days=0, best_streak=0, created_at=goal["created_at"],
        deadline=goal["deadline"],
    )


@router.post("/{goal_id}/update", response_model=GoalResponse)
async def update_goal_progress(goal_id: str, update: GoalUpdate, user_id: str = Query("default")):
    """Update goal progress."""
    goal = None
    for g in user_goals.get(user_id, []):
        if g["id"] == goal_id:
            goal = g
            break

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    if update.current_value is not None:
        goal["current_value"] = update.current_value
    if update.name:
        goal["name"] = update.name

    # Log the update
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    goal_logs.setdefault(goal_id, []).append({"date": today, "value": goal["current_value"]})

    # Check if achieved
    if goal["current_value"] >= goal["target_value"]:
        goal["status"] = "achieved"

    _update_streak(goal_id)
    streak_info = goal_streaks.get(goal_id, {"current": 0, "best": 0})

    progress = (goal["current_value"] / goal["target_value"] * 100) if goal["target_value"] > 0 else 0
    achieved = [m for m in goal.get("milestones", []) if goal["current_value"] >= m]

    celebration = None
    if progress >= 100:
        celebration = CELEBRATIONS[100]
    elif progress >= 75:
        celebration = CELEBRATIONS[75]
    elif progress >= 50:
        celebration = CELEBRATIONS[50]
    elif progress >= 25:
        celebration = CELEBRATIONS[25]

    return GoalResponse(
        id=goal["id"], name=goal["name"], description=goal["description"],
        goal_type=goal["goal_type"], target_value=goal["target_value"],
        target_unit=goal["target_unit"], current_value=goal["current_value"],
        progress_pct=round(min(100, max(0, progress)), 1), status=goal["status"],
        milestones_achieved=achieved, streak_days=streak_info["current"],
        best_streak=streak_info["best"], created_at=goal["created_at"],
        deadline=goal["deadline"], celebration=celebration,
    )


@router.get("/{goal_id}/milestones", response_model=List[MilestoneResponse])
async def get_milestones(goal_id: str, user_id: str = Query("default")):
    """Get milestone details for a goal."""
    goal = None
    for g in user_goals.get(user_id, []):
        if g["id"] == goal_id:
            goal = g
            break

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    milestones = goal.get("milestones", [])
    current = goal["current_value"]

    return [
        MilestoneResponse(
            goal_id=goal_id,
            milestone_value=m,
            achieved_at=datetime.now(timezone.utc).isoformat() if current >= m else None,
            is_achieved=current >= m,
            celebration_message=CELEBRATIONS.get(int(m / goal["target_value"] * 100), f"Milestone {m} reached!"),
        )
        for m in sorted(milestones)
    ]


@router.delete("/{goal_id}")
async def delete_goal(goal_id: str, user_id: str = Query("default")):
    """Delete a goal."""
    goals = user_goals.get(user_id, [])
    for i, g in enumerate(goals):
        if g["id"] == goal_id:
            goals.pop(i)
            goal_logs.pop(goal_id, None)
            goal_streaks.pop(goal_id, None)
            return {"deleted": True}
    raise HTTPException(status_code=404, detail="Goal not found")


@router.get("/stats")
async def goal_stats(user_id: str = Query("default")):
    """Get goal statistics summary."""
    goals = user_goals.get(user_id, [])
    active = [g for g in goals if g["status"] == "active"]
    achieved = [g for g in goals if g["status"] == "achieved"]

    return {
        "total_goals": len(goals),
        "active": len(active),
        "achieved": len(achieved),
        "expired": len([g for g in goals if g["status"] == "expired"]),
        "best_streak": max((goal_streaks.get(g["id"], {}).get("best", 0) for g in goals), default=0),
    }

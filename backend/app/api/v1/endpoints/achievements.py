"""
Achievements, XP and levels, derived from what the user actually logged.

Nothing here can be granted by a request. Every badge is recomputed from
workout, recovery, sleep and mood records, so points and the leaderboard can
only move when the underlying activity does.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from app.core.per_user import current_user_id
from app.core.storage import storage
from app.services.gamification import calculate_user_level
from app.services.sleep_tracker import sleep_journal

router = APIRouter()

TIER_XP = {"bronze": 10, "silver": 50, "gold": 200, "platinum": 500}
ALL_TIME_DAYS = 3650

# (id, name, description, icon, tier, category, metric, target)
CATALOG = [
    ("first_workout", "First Steps", "Complete your first workout", "checkmark-circle", "bronze", "milestone", "workouts", 1),
    ("ten_workouts", "Getting Serious", "Complete 10 workouts", "barbell", "silver", "milestone", "workouts", 10),
    ("fifty_workouts", "Dedicated", "Complete 50 workouts", "medal", "gold", "milestone", "workouts", 50),
    ("hundred_workouts", "Century Club", "Complete 100 workouts", "trophy", "platinum", "milestone", "workouts", 100),
    ("streak_3", "Building Momentum", "Work out 3 days in a row", "flame", "bronze", "consistency", "best_streak", 3),
    ("streak_7", "Week Warrior", "Work out 7 days in a row", "flame", "silver", "consistency", "best_streak", 7),
    ("streak_30", "Monthly Master", "Work out 30 days in a row", "flame", "gold", "consistency", "best_streak", 30),
    ("streak_100", "Iron Will", "Work out 100 days in a row", "flame", "platinum", "consistency", "best_streak", 100),
    ("optimal_recovery", "Green Zone", "Reach an OPTIMAL recovery state", "heart", "bronze", "recovery", "optimal_days", 1),
    ("recovery_90", "Peak Performance", "Score 90+ on recovery", "star", "silver", "recovery", "recovery_90_days", 1),
    ("checkins_30", "Know Thyself", "Complete 30 daily check-ins", "clipboard", "gold", "recovery", "checkins", 30),
    ("sleep_7", "Sleep Tracker", "Log 7 nights of sleep", "moon", "bronze", "sleep", "nights", 7),
    ("sleep_efficient", "Sleep Champion", "Record a night at 90%+ sleep efficiency", "moon", "silver", "sleep", "efficient_nights", 1),
    ("mood_5", "Mindful Athlete", "Log your mood 5 times", "happy", "bronze", "mind", "moods", 5),
    ("feedback_10", "Coachable", "Leave feedback on 10 workouts", "chatbubble", "silver", "mind", "feedback", 10),
]


def _day_streaks(dates: list[str]) -> tuple[int, int]:
    """(current streak ending today or yesterday, best streak ever) in consecutive days."""
    days = sorted({datetime.strptime(d, "%Y-%m-%d").date() for d in dates if len(d) == 10})
    if not days:
        return 0, 0
    best = run = 1
    for prev, cur in zip(days, days[1:]):
        run = run + 1 if (cur - prev).days == 1 else 1
        best = max(best, run)
    today = datetime.now().date()
    current = run if (today - days[-1]).days <= 1 else 0
    return current, best


async def _metrics(user_id: str) -> dict:
    workouts = await storage.get_workout_logs(user_id, ALL_TIME_DAYS)
    recovery = await storage.get_recovery_logs(user_id, ALL_TIME_DAYS)
    memory = await storage.get_agent_memory(user_id)
    journal = sleep_journal.instance_for(user_id)
    nights = journal.nights(ALL_TIME_DAYS)
    dates = [(w.get("completed_at") or w.get("created_at") or "")[:10] for w in workouts]
    current, best = _day_streaks(dates)
    return {
        "workouts": len(workouts),
        "current_streak": current,
        "best_streak": best,
        "optimal_days": sum(1 for r in recovery if r.get("readiness_state") == "OPTIMAL"),
        "recovery_90_days": sum(1 for r in recovery if (r.get("recovery_score") or 0) >= 90),
        "checkins": len(recovery),
        "nights": len(nights),
        "efficient_nights": sum(1 for n in nights if (n.get("efficiency_pct") or 0) >= 90),
        "moods": len(memory.get("mood_logs", [])),
        "feedback": sum(1 for w in workouts if w.get("user_feedback_notes")),
    }


def _badges(metrics: dict) -> list[dict]:
    out = []
    for bid, name, desc, icon, tier, category, metric, target in CATALOG:
        value = metrics[metric]
        out.append({
            "id": bid, "name": name, "description": desc, "icon": icon, "tier": tier,
            "category": category, "xp": TIER_XP[tier], "progress": min(value, target),
            "target": target, "unlocked": value >= target,
        })
    return out


def _summary(metrics: dict, badges: list[dict]) -> dict:
    points = sum(b["xp"] for b in badges if b["unlocked"])
    level, progress = calculate_user_level(points)
    return {
        "points": points, "level": level, "level_progress": round(progress, 3),
        "points_to_next_level": 100 * (2 ** (level + 1) - 1) - points,
        "earned": sum(1 for b in badges if b["unlocked"]), "total": len(badges),
        "current_streak": metrics["current_streak"], "best_streak": metrics["best_streak"],
    }


@router.get("")
async def get_achievements():
    """Every badge with progress toward it."""
    return _badges(await _metrics(current_user_id()))


@router.get("/summary")
async def get_summary():
    """Points, level and streaks."""
    metrics = await _metrics(current_user_id())
    return _summary(metrics, _badges(metrics))


@router.get("/leaderboard")
async def get_leaderboard(limit: int = Query(20, ge=1, le=100)):
    """Points ranking. Other users appear only by rank; the caller sees their own place."""
    from app.core.auth import user_manager

    me = current_user_id()
    # ponytail: scores every account per request; cache or precompute past a few thousand users.
    accounts = await user_manager.list_users(limit=500)
    rows = []
    for account in accounts:
        uid = account.get("id")
        if not uid:
            continue
        metrics = await _metrics(uid)
        rows.append({"user_id": uid, "points": _summary(metrics, _badges(metrics))["points"]})
    rows.sort(key=lambda r: -r["points"])
    board: list[dict] = []
    mine: Optional[dict] = None
    for rank, row in enumerate(rows, start=1):
        entry = {"rank": rank, "points": row["points"], "is_you": row["user_id"] == me,
                 "name": "You" if row["user_id"] == me else f"Athlete {rank}"}
        if entry["is_you"]:
            mine = entry
        if rank <= limit:
            board.append(entry)
    return {"leaderboard": board, "you": mine, "participants": len(rows)}

"""Achievement badge endpoints — unlock status, badge wall, progress tracking."""

from __future__ import annotations
from fastapi import APIRouter, Query
from app.services.achievements_engine import check_achievements, get_all_badges, BADGE_DEFINITIONS
from app.core.storage import storage

router = APIRouter()


@router.get("/{user_id}")
async def get_user_achievements(user_id: str):
    """Get all achievements with unlock status for a user."""
    workouts = await storage.get_workouts(user_id, 730)
    recovery = await storage.get_recovery_logs(user_id, 730)

    # Compute user stats
    total_workouts = len(workouts)
    max_weight = 0
    total_volume = 0
    total_duration = 0
    longest_session = 0

    for w in workouts:
        dur = w.get("actual_duration_minutes", 0) or 0
        total_duration += dur
        if dur > longest_session:
            longest_session = dur
        for ex in w.get("exercises", []):
            weight = ex.get("actual_weight", 0) or 0
            reps = ex.get("actual_reps", 0) or 0
            sets = ex.get("sets", 0) or 0
            if weight > max_weight:
                max_weight = weight
            total_volume += weight * reps * sets

    user_stats = {
        "total_workouts": total_workouts,
        "current_streak": 0,  # Would come from streaks engine
        "best_streak": 0,
        "max_weight": max_weight,
        "total_volume": total_volume,
        "total_duration": total_duration,
        "longest_session": longest_session,
    }

    # Check all badges
    results = check_achievements(user_stats)
    unlocked = [r for r in results if r["unlocked"]]
    total_xp = sum(b["xp_reward"] for b in unlocked)

    return {
        "user_id": user_id,
        "total_xp": total_xp,
        "total_unlocked": len(unlocked),
        "total_badges": len(BADGE_DEFINITIONS),
        "completion_pct": round(len(unlocked) / max(1, len(BADGE_DEFINITIONS)) * 100, 1),
        "badges": results,
    }


@router.get("")
async def list_all_badges():
    """List all available achievement badges."""
    return {"badges": get_all_badges(), "total": len(BADGE_DEFINITIONS)}

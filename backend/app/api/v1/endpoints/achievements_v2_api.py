"""Achievement Badge System v2 — gamification badges with tiers, categories, and XP."""
from fastapi import APIRouter
from app.core.storage import storage

router = APIRouter()

BADGE_TIERS = ["bronze", "silver", "gold", "platinum"]

BADGE_CATALOG = [
    # Milestones
    {"id": "first_workout", "name": "First Steps", "description": "Complete your first workout", "tier": "bronze", "category": "milestone", "xp": 10},
    {"id": "ten_workouts", "name": "Getting Serious", "description": "Complete 10 workouts", "tier": "silver", "category": "milestone", "xp": 50},
    {"id": "fifty_workouts", "name": "Dedicated Athlete", "description": "Complete 50 workouts", "tier": "gold", "category": "milestone", "xp": 200},
    {"id": "hundred_workouts", "name": "Century Club", "description": "Complete 100 workouts", "tier": "platinum", "category": "milestone", "xp": 500},
    # Consistency
    {"id": "streak_3", "name": "Hat Trick", "description": "3-day workout streak", "tier": "bronze", "category": "consistency", "xp": 15},
    {"id": "streak_7", "name": "Week Warrior", "description": "7-day workout streak", "tier": "silver", "category": "consistency", "xp": 75},
    {"id": "streak_30", "name": "Monthly Master", "description": "30-day workout streak", "tier": "gold", "category": "consistency", "xp": 300},
    {"id": "streak_100", "name": "Iron Will", "description": "100-day workout streak", "tier": "platinum", "category": "consistency", "xp": 1000},
    # Strength
    {"id": "bench_1x", "name": "Bodyweight Bencher", "description": "Bench press bodyweight", "tier": "bronze", "category": "strength", "xp": 20},
    {"id": "bench_15x", "name": "Strong Pusher", "description": "Bench press 1.5x bodyweight", "tier": "silver", "category": "strength", "xp": 100},
    {"id": "squat_15x", "name": "Power Legs", "description": "Squat 1.5x bodyweight", "tier": "silver", "category": "strength", "xp": 100},
    {"id": "deadlift_2x", "name": "Deadlift Destroyer", "description": "Deadlift 2x bodyweight", "tier": "gold", "category": "strength", "xp": 250},
    {"id": "total_1000kg", "name": "Ton of Iron", "description": "Lift 1000kg in a single session", "tier": "platinum", "category": "strength", "xp": 500},
    # Recovery
    {"id": "optimal_recovery", "name": "Green Zone", "description": "Achieve OPTIMAL recovery state", "tier": "bronze", "category": "recovery", "xp": 10},
    {"id": "recovery_90", "name": "Peak Performance", "description": "Recovery score of 90+", "tier": "silver", "category": "recovery", "xp": 50},
    {"id": "sleep_perfect", "name": "Sleep Champion", "description": "Log 90%+ sleep efficiency", "tier": "bronze", "category": "recovery", "xp": 15},
    # Mental
    {"id": "mood_5", "name": "Mindful Athlete", "description": "Log mood 5 times", "tier": "bronze", "category": "mental", "xp": 10},
    {"id": "meditation_10", "name": "Inner Peace", "description": "Complete 10 meditation sessions", "tier": "silver", "category": "mental", "xp": 75},
    # Nutrition
    {"id": "protein_goal", "name": "Protein Pro", "description": "Hit protein target 7 days in a row", "tier": "silver", "category": "nutrition", "xp": 50},
    {"id": "calorie_streak", "name": "Calorie Commander", "description": "Stay within calorie target for 14 days", "tier": "gold", "category": "nutrition", "xp": 150},
    # Social
    {"id": "challenge_win", "name": "Champion", "description": "Win a fitness challenge", "tier": "gold", "category": "social", "xp": 200},
    {"id": "share_workout", "name": "Social Butterfly", "description": "Share 5 workouts with the community", "tier": "bronze", "category": "social", "xp": 10},
    # Special
    {"id": "early_bird", "name": "Early Bird", "description": "Complete 10 workouts before 7 AM", "tier": "silver", "category": "special", "xp": 50},
    {"id": "night_owl", "name": "Night Owl", "description": "Complete 10 workouts after 9 PM", "tier": "silver", "category": "special", "xp": 50},
]


@router.get("")
async def list_badges():
    """List all available achievement badges."""
    return {"badges": BADGE_CATALOG, "total": len(BADGE_CATALOG)}


@router.get("/{user_id}")
async def user_progress(user_id: str):
    """Get user achievement progress."""
    memory = await storage.get_agent_memory(user_id)
    workout_logs = await storage.get_workout_logs(user_id, 365)
    recovery_logs = await storage.get_recovery_logs(user_id, 365)

    total_xp = 0
    unlocked_count = 0
    results = []
    for badge in BADGE_CATALOG:
        unlocked = False
        if badge["category"] == "milestone":
            if "ten_workouts" in badge["id"]:
                unlocked = len(workout_logs) >= 10
            elif "fifty_workouts" in badge["id"]:
                unlocked = len(workout_logs) >= 50
            elif "hundred_workouts" in badge["id"]:
                unlocked = len(workout_logs) >= 100
            else:
                unlocked = len(workout_logs) >= 1
        elif badge["category"] == "recovery":
            if "90" in badge["id"]:
                unlocked = any(r.get("recovery_score", 0) >= 90 for r in recovery_logs)
            else:
                unlocked = any(r.get("readiness_state") == "OPTIMAL" for r in recovery_logs)
        elif badge["category"] == "mental":
            mood_count = len(memory.get("mood_logs", []))
            if "meditation" in badge["id"]:
                unlocked = memory.get("meditation_count", 0) >= 10
            else:
                unlocked = mood_count >= 5

        if unlocked:
            total_xp += badge["xp"]
            unlocked_count += 1

        results.append({
            "id": badge["id"],
            "name": badge["name"],
            "tier": badge["tier"],
            "category": badge["category"],
            "xp": badge["xp"],
            "unlocked": unlocked,
        })

    total_badges = len(BADGE_CATALOG)
    completion_pct = round(unlocked_count / total_badges * 100, 1) if total_badges else 0

    return {
        "badges": results,
        "total_xp": total_xp,
        "total_badges": total_badges,
        "unlocked_count": unlocked_count,
        "completion_pct": completion_pct,
    }

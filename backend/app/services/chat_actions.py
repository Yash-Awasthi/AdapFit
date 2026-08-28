"""
Chat action dispatch — lets the AI coach chat take real actions instead of only replying:
generate and save a workout, or generate and save a diet plan, using the user's own data.
Shared by chat.py and ws_chat.py so both the REST and WebSocket chat paths can act.
"""
import re
from datetime import date
from typing import Optional, Dict, Any

WORKOUT_ACTION_RE = re.compile(
    r"\b(create|generate|build|make|give me|plan out)\b.{0,20}\b(workout|routine|program|training session)\b",
    re.I,
)
DIET_ACTION_RE = re.compile(
    r"\b(create|generate|build|make|give me|plan out)\b.{0,20}\b(diet|meal plan|nutrition plan|eating plan)\b",
    re.I,
)

_GOAL_ALIASES = {
    "muscle_gain": "hypertrophy",
    "weight_loss": "fat_loss",
    "maintenance": "general_fitness",
}


def _normalize_goal(goal: str) -> str:
    return _GOAL_ALIASES.get(goal, goal)


async def _latest_weight_kg(user_id: str) -> float:
    try:
        from app.api.v1.endpoints.body_composition import measurements
        entries = measurements.get(user_id, [])
        for entry in reversed(entries):
            if entry.get("weight_kg"):
                return entry["weight_kg"]
    except Exception:
        pass
    return 75.0


async def _create_workout(user_id: str) -> Dict[str, Any]:
    from app.api.v1.endpoints.workouts import create_workout
    from app.models.schemas import WorkoutGenerateRequest

    req = WorkoutGenerateRequest(user_id=user_id, target_date=date.today().isoformat(), target_duration_minutes=45)
    resp = await create_workout(req)
    ex_names = ", ".join(e.get("name", "") if isinstance(e, dict) else getattr(e, "name", "") for e in resp.exercises[:4])
    reply = (
        f"Created your workout: {resp.title} ({resp.target_duration_minutes} min). "
        f"Exercises: {ex_names}. {resp.adaptation_rationale} Check the Workout tab."
    )
    return {"type": "workout_created", "reply": reply, "data": {"workout_id": resp.workout_id, "title": resp.title}}


async def _create_diet_plan(user_id: str) -> Dict[str, Any]:
    from app.services.meal_planner import meal_planner
    from app.core.storage import storage

    user = await storage.get_user(user_id)
    goal = _normalize_goal(user.get("primary_goal", "general_fitness")) if user else "general_fitness"
    weight_kg = await _latest_weight_kg(user_id)

    recovery_logs = await storage.get_recovery_logs(user_id, 1)
    recovery_score = recovery_logs[-1].get("recovery_score") if recovery_logs else None

    plan = meal_planner.generate_day_plan(weight_kg=weight_kg, goal=goal, recovery_score=recovery_score, training_day=True)
    await storage.save_diet_plan(user_id, plan)

    targets = plan["targets"]
    reply = (
        f"Created today's meal plan ({plan['plan_type']}): {targets['target_calories']} kcal, "
        f"{targets['protein_g']}g protein, {targets['carbs_g']}g carbs, {targets['fat_g']}g fat "
        f"across {len(plan['meals'])} meals. Check the Diet tab for the full breakdown."
    )
    return {"type": "diet_plan_created", "reply": reply, "data": plan}


async def maybe_execute_action(message: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Detect and run an actionable request (create workout / diet plan). Returns None if the message isn't one."""
    try:
        if WORKOUT_ACTION_RE.search(message):
            return await _create_workout(user_id)
        if DIET_ACTION_RE.search(message):
            return await _create_diet_plan(user_id)
    except Exception:
        return None
    return None

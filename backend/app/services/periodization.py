"""Periodization engine: generates 4-6 week mesocycle plans based on ACWR and recovery."""
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class WeekPlan(BaseModel):
    week: int
    phase: str  # "accumulation", "intensification", "deload", "peak"
    volume_pct: float  # % of peak volume
    intensity_pct: float  # % of peak intensity
    focus: str  # "hypertrophy", "strength", "power", "recovery"
    days_per_week: int
    target_acwr: float
    notes: str


class MesocyclePlan(BaseModel):
    plan_id: str
    name: str
    duration_weeks: int
    start_date: str
    end_date: str
    current_week: int
    weeks: List[WeekPlan]
    rationale: str
    acwr_target_range: List[float] = Field(default=[0.8, 1.3])


# Phase definitions for different mesocycle types
MESOCYCLES = {
    "strength": {
        "name": "Strength Block",
        "weeks": [
            {"phase": "accumulation", "volume_pct": 100, "intensity_pct": 70, "focus": "hypertrophy", "notes": "Build work capacity"},
            {"phase": "accumulation", "volume_pct": 90, "intensity_pct": 80, "focus": "strength", "notes": "Increase load"},
            {"phase": "intensification", "volume_pct": 75, "intensity_pct": 90, "focus": "strength", "notes": "Peak strength work"},
            {"phase": "peak", "volume_pct": 60, "intensity_pct": 100, "focus": "power", "notes": "Express peak strength"},
            {"phase": "deload", "volume_pct": 40, "intensity_pct": 60, "focus": "recovery", "notes": "Active recovery"},
        ],
    },
    "hypertrophy": {
        "name": "Hypertrophy Block",
        "weeks": [
            {"phase": "accumulation", "volume_pct": 80, "intensity_pct": 65, "focus": "hypertrophy", "notes": "Volume accumulation"},
            {"phase": "accumulation", "volume_pct": 100, "intensity_pct": 70, "focus": "hypertrophy", "notes": "Peak volume week"},
            {"phase": "intensification", "volume_pct": 90, "intensity_pct": 80, "focus": "strength", "notes": "Transition to heavier loads"},
            {"phase": "deload", "volume_pct": 50, "intensity_pct": 55, "focus": "recovery", "notes": "Deload before next cycle"},
        ],
    },
    "endurance": {
        "name": "Endurance Block",
        "weeks": [
            {"phase": "accumulation", "volume_pct": 85, "intensity_pct": 60, "focus": "hypertrophy", "notes": "Build aerobic base"},
            {"phase": "accumulation", "volume_pct": 100, "intensity_pct": 65, "focus": "hypertrophy", "notes": "Volume peak"},
            {"phase": "intensification", "volume_pct": 85, "intensity_pct": 80, "focus": "strength", "notes": "Tempo work"},
            {"phase": "intensification", "volume_pct": 70, "intensity_pct": 90, "focus": "power", "notes": "Interval training"},
            {"phase": "deload", "volume_pct": 45, "intensity_pct": 50, "focus": "recovery", "notes": "Recovery week"},
        ],
    },
}


def generate_mesocycle(
    goal: str = "strength",
    start_date: Optional[str] = None,
    current_acwr: float = 1.0,
    current_readiness: str = "MODERATE",
) -> MesocyclePlan:
    """Generate a periodized mesocycle plan based on goal and current state."""
    template = MESOCYCLES.get(goal, MESOCYCLES["strength"])
    weeks_data = template["weeks"]

    start = datetime.fromisoformat(start_date) if start_date else datetime.now(timezone.utc)
    end = start + timedelta(weeks=len(weeks_data))

    # Adjust week plan based on current readiness
    readiness_modifier = {
        "OPTIMAL": 1.0,
        "MODERATE": 0.95,
        "REDUCED": 0.85,
        "DEPLETED": 0.75,
    }.get(current_readiness, 1.0)

    week_plans = []
    for i, w in enumerate(weeks_data):
        adjusted_volume = w["volume_pct"] * readiness_modifier
        # ACWR target: keep in 0.8-1.3 sweet spot
        acwr_target = min(1.3, max(0.8, 0.9 + (w["intensity_pct"] - 65) * 0.008))

        week_plans.append(WeekPlan(
            week=i + 1,
            phase=w["phase"],
            volume_pct=round(adjusted_volume, 1),
            intensity_pct=w["intensity_pct"],
            focus=w["focus"],
            days_per_week=4 if w["phase"] != "deload" else 3,
            target_acwr=round(acwr_target, 2),
            notes=w["notes"],
        ))

    rationale = f"Generated {template['name']} ({len(weeks_data)} weeks) for {goal}. "
    if current_readiness != "OPTIMAL":
        rationale += f"Adjusted volume by {(readiness_modifier - 1) * 100:.0f}% due to {current_readiness.lower()} readiness. "
    rationale += f"ACWR target range: 0.80 - 1.30."

    return MesocyclePlan(
        plan_id=f"mp_{int(start.timestamp())}",
        name=template["name"],
        duration_weeks=len(weeks_data),
        start_date=start.strftime("%Y-%m-%d"),
        end_date=end.strftime("%Y-%m-%d"),
        current_week=1,
        weeks=week_plans,
        rationale=rationale,
    )

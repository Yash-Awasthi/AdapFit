"""Cycling Fueling Planner Service.

Extracted from intervals-icu-sync (inspiration).
Carbohydrate intake recommendations for cycling activities,
ride type classification, and fueling strategy generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RideType(Enum):
    VO2 = "vo2"
    THRESHOLD = "threshold"
    ENDURANCE = "endurance"
    RECOVERY = "recovery"
    RACE = "race"
    LONG_RIDE = "long_ride"
    SPRINT = "sprint"
    HILL = "hill"


class FuelingStrategy(Enum):
    NONE = "none"
    MINIMAL = "minimal"
    STANDARD = "standard"
    HIGH = "high"
    MAXIMUM = "maximum"


@dataclass
class FuelingTarget:
    ride_type: RideType
    min_grams_per_hour: float
    max_grams_per_hour: float
    hydration_ml_per_hour: float
    sodium_mg_per_hour: float
    caffeine_mg: float = 0


@dataclass
class FuelingPlan:
    ride_type: RideType
    duration_hours: float
    total_carbs_grams: float
    carbs_per_hour: float
    gel_count: int
    bottle_count: int
    water_ml: int
    sodium_mg: int
    pre_ride_meal: str
    strategy: FuelingStrategy
    timeline: list[dict[str, any]] = field(default_factory=list)


RIDE_TARGETS: dict[RideType, FuelingTarget] = {
    RideType.VO2: FuelingTarget(RideType.VO2, 40, 60, 500, 800, 100),
    RideType.THRESHOLD: FuelingTarget(RideType.THRESHOLD, 50, 70, 600, 900, 80),
    RideType.ENDURANCE: FuelingTarget(RideType.ENDURANCE, 60, 80, 700, 1000, 0),
    RideType.RECOVERY: FuelingTarget(RideType.RECOVERY, 0, 30, 400, 600, 0),
    RideType.RACE: FuelingTarget(RideType.RACE, 60, 90, 800, 1200, 150),
    RideType.LONG_RIDE: FuelingTarget(RideType.LONG_RIDE, 80, 90, 800, 1200, 100),
    RideType.SPRINT: FuelingTarget(RideType.SPRINT, 30, 50, 500, 700, 50),
    RideType.HILL: FuelingTarget(RideType.HILL, 40, 60, 600, 900, 50),
}

GEL_CARBS = 22
BOTTLE_CARBS_SPORTS = 40
BOTTLE_CARBS_CONC = 60
FATIGUE_BONUS = 10


def classify_ride_type(
    avg_power_watts: float | None = None,
    avg_heart_rate: int | None = None,
    max_heart_rate: int | None = None,
    duration_hours: float = 0,
    elevation_gain_m: float = 0,
    avg_speed_kmh: float = 0,
) -> RideType:
    """Classify ride type from activity metrics."""
    if duration_hours < 0.5:
        return RideType.RECOVERY
    if avg_heart_rate and max_heart_rate:
        hr_ratio = avg_heart_rate / max_heart_rate if max_heart_rate > 0 else 0
        if hr_ratio > 0.9:
            return RideType.VO2
        elif hr_ratio > 0.8:
            return RideType.THRESHOLD
    if duration_hours > 4:
        return RideType.LONG_RIDE
    if elevation_gain_m > 1000:
        return RideType.HILL
    if avg_speed_kmh > 35:
        return RideType.SPRINT
    return RideType.ENDURANCE


def calculate_fueling_target(
    ride_type: RideType,
    duration_hours: float,
    form_pct: float = 0,
    weight_kg: float = 70.0,
) -> FuelingTarget:
    """Calculate fueling target with adjustments."""
    base = RIDE_TARGETS[ride_type]
    min_g = base.min_grams_per_hour
    max_g = base.max_grams_per_hour
    if form_pct < -0.20:
        min_g += FATIGUE_BONUS
        max_g += FATIGUE_BONUS
    if duration_hours > 3:
        min_g = max(min_g, 60)
    if duration_hours < 1:
        min_g = min(min_g, 30)
        max_g = min(max_g, 40)
    return FuelingTarget(
        ride_type=ride_type,
        min_grams_per_hour=min_g,
        max_grams_per_hour=max_g,
        hydration_ml_per_hour=base.hydration_ml_per_hour,
        sodium_mg_per_hour=base.sodium_mg_per_hour,
        caffeine_mg=base.caffeine_mg,
    )


def generate_fueling_plan(
    ride_type: RideType,
    duration_hours: float,
    form_pct: float = 0,
    weight_kg: float = 70.0,
) -> FuelingPlan:
    """Generate complete fueling plan."""
    if duration_hours < 1:
        strategy = FuelingStrategy.NONE
    elif duration_hours < 1.5:
        strategy = FuelingStrategy.MINIMAL
    elif duration_hours < 3:
        strategy = FuelingStrategy.STANDARD
    elif duration_hours < 5:
        strategy = FuelingStrategy.HIGH
    else:
        strategy = FuelingStrategy.MAXIMUM
    target = calculate_fueling_target(ride_type, duration_hours, form_pct, weight_kg)
    avg_carbs = (target.min_grams_per_hour + target.max_grams_per_hour) / 2
    total_carbs = avg_carbs * duration_hours
    gel_count = int(total_carbs / GEL_CARBS) if strategy != FuelingStrategy.NONE else 0
    bottle_count = max(1, int(target.hydration_ml_per_hour * duration_hours / 500))
    water_ml = int(target.hydration_ml_per_hour * duration_hours)
    sodium_mg = int(target.sodium_mg_per_hour * duration_hours)
    pre_meal = _suggest_pre_ride_meal(ride_type, duration_hours)
    timeline = _build_timeline(ride_type, duration_hours, target)
    return FuelingPlan(
        ride_type=ride_type,
        duration_hours=duration_hours,
        total_carbs_grams=round(total_carbs),
        carbs_per_hour=round(avg_carbs),
        gel_count=gel_count,
        bottle_count=bottle_count,
        water_ml=water_ml,
        sodium_mg=sodium_mg,
        pre_ride_meal=pre_meal,
        strategy=strategy,
        timeline=timeline,
    )


def _suggest_pre_ride_meal(ride_type: RideType, duration_hours: float) -> str:
    if ride_type in (RideType.RECOVERY,):
        return "Light snack: banana + coffee, 30min before"
    if duration_hours > 3:
        return "Full meal 2-3h before: oats, banana, toast, eggs"
    if ride_type in (RideType.VO2, RideType.THRESHOLD):
        return "Moderate meal 1.5h before: banana, energy bar, coffee"
    return "Light meal 1-2h before: toast, banana, yogurt"


def _build_timeline(ride_type: RideType, duration_hours: float, target: FuelingTarget) -> list[dict]:
    timeline = []
    timeline.append({"time": "Pre-ride", "action": _suggest_pre_ride_meal(ride_type, duration_hours)})
    if target.max_grams_per_hour > 0:
        interval = max(20, min(45, int(60 / (target.max_grams_per_hour / GEL_CARBS))))
        t = interval
        while t < duration_hours * 60:
            timeline.append({"time": f"+{t}min", "action": f"Take gel ({GEL_CARBS}g carbs)"})
            t += interval
    bottle_interval = max(15, min(30, int(500 / target.hydration_ml_per_hour * 60)))
    t = bottle_interval
    while t < duration_hours * 60:
        timeline.append({"time": f"+{t}min", "action": "Drink 200ml water/electrolytes"})
        t += bottle_interval
    timeline.append({"time": "Post-ride", "action": "Recovery shake within 30min: protein + carbs"})
    return timeline


def calculate_weekly_fueling_load(plans: list[FuelingPlan]) -> dict:
    """Calculate weekly fueling totals."""
    total_carbs = sum(p.total_carbs_grams for p in plans)
    total_gels = sum(p.gel_count for p in plans)
    total_water = sum(p.water_ml for p in plans)
    avg_per_ride = total_carbs / len(plans) if plans else 0
    return {
        "total_carbs_grams": total_carbs,
        "total_gels": total_gels,
        "total_water_ml": total_water,
        "avg_carbs_per_ride": round(avg_per_ride),
        "ride_count": len(plans),
    }

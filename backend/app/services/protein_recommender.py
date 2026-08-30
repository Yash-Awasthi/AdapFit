"""Protein Recommendation Service.

Extracted from whoop-data (inspiration).
Calculates protein needs based on activity level, body weight,
and training goals with timing recommendations.

All pure functions — no DB, no async.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# --- Activity Levels ---

ACTIVITY_PROTEIN_FACTORS = {
    "sedentary": 0.8,
    "light": 1.0,
    "moderate": 1.2,
    "resistance/strength training": 1.6,
    "endurance training": 1.4,
    "mixed": 1.5,
    "athlete": 1.8,
    "bodybuilding": 2.2,
}

ACTIVITY_DESCRIPTIONS = {
    "sedentary": "Little to no exercise, desk job",
    "light": "Light exercise 1-3 days/week",
    "moderate": "Moderate exercise 3-5 days/week",
    "resistance/strength training": "Weight lifting, resistance exercises",
    "endurance training": "Running, cycling, swimming",
    "mixed": "Combination of strength and endurance",
    "athlete": "Professional or competitive athlete",
    "bodybuilding": "High-volume bodybuilding training",
}


@dataclass
class ProteinRecommendation:
    """Daily protein recommendation."""
    daily_grams: float
    per_kg_bodyweight: float
    activity_level: str
    body_weight_kg: Optional[float] = None
    timing: Optional[list[str]] = None
    notes: Optional[str] = None


@dataclass
class ProteinTiming:
    """Meal timing for protein distribution."""
    meal: str
    grams: float
    timing: str
    priority: str = "normal"  # "high", "normal", "optional"


# --- Core Calculations ---

def calculate_protein_needs(
    body_weight_kg: float,
    activity_level: str = "moderate",
) -> ProteinRecommendation:
    """Calculate daily protein needs.

    Args:
        body_weight_kg: Body weight in kilograms
        activity_level: Activity level string

    Returns:
        Protein recommendation
    """
    factor = ACTIVITY_PROTEIN_FACTORS.get(activity_level, 1.2)
    daily_grams = body_weight_kg * factor

    return ProteinRecommendation(
        daily_grams=round(daily_grams, 1),
        per_kg_bodyweight=round(factor, 2),
        activity_level=activity_level,
        body_weight_kg=body_weight_kg,
        timing=None,
        notes=_get_recommendation_notes(activity_level, daily_grams),
    )


def calculate_protein_from_lbs(
    body_weight_lbs: float,
    activity_level: str = "moderate",
) -> ProteinRecommendation:
    """Calculate protein needs from pounds.

    Args:
        body_weight_lbs: Body weight in pounds
        activity_level: Activity level string

    Returns:
        Protein recommendation
    """
    kg = body_weight_lbs * 0.453592
    return calculate_protein_needs(kg, activity_level)


# --- Timing ---

def distribute_protein_timing(
    daily_grams: float,
    num_meals: int = 4,
    activity_level: str = "moderate",
) -> list[ProteinTiming]:
    """Distribute protein across meals.

    Args:
        daily_grams: Total daily protein in grams
        num_meals: Number of meals per day
        activity_level: Activity level for timing advice

    Returns:
        List of protein timing recommendations
    """
    per_meal = daily_grams / num_meals
    timings = []

    meal_names = ["Breakfast", "Lunch", "Dinner", "Snack 1", "Snack 2", "Post-Workout"]
    meal_times = ["7:00 AM", "12:00 PM", "6:00 PM", "3:00 PM", "9:00 PM", "Immediately after"]

    for i in range(min(num_meals, len(meal_names))):
        priority = "high" if i in [1, 2] else "normal"  # Lunch and dinner are high priority
        if "training" in activity_level.lower() and i == num_meals - 1:
            priority = "high"
            meal_names[i] = "Post-Workout"
            meal_times[i] = "Within 30 min of training"

        timings.append(ProteinTiming(
            meal=meal_names[i],
            grams=round(per_meal, 1),
            timing=meal_times[i],
            priority=priority,
        ))

    return timings


# --- Goal-Based Adjustments ---

def adjust_for_goal(
    base_recommendation: ProteinRecommendation,
    goal: str,
) -> ProteinRecommendation:
    """Adjust protein recommendation for specific goals.

    Args:
        base_recommendation: Base protein recommendation
        goal: Target goal ("muscle_gain", "fat_loss", "maintenance", "endurance")

    Returns:
        Adjusted recommendation
    """
    adjustments = {
        "muscle_gain": 0.2,
        "fat_loss": 0.1,
        "maintenance": 0.0,
        "endurance": -0.1,
    }

    adjustment = adjustments.get(goal, 0.0)
    new_per_kg = base_recommendation.per_kg_bodyweight + adjustment
    new_per_kg = max(0.8, min(2.5, new_per_kg))

    if base_recommendation.body_weight_kg:
        daily_grams = base_recommendation.body_weight_kg * new_per_kg
    else:
        daily_grams = base_recommendation.daily_grams * (new_per_kg / base_recommendation.per_kg_bodyweight)

    notes = _get_goal_notes(goal, daily_grams)

    return ProteinRecommendation(
        daily_grams=round(daily_grams, 1),
        per_kg_bodyweight=round(new_per_kg, 2),
        activity_level=base_recommendation.activity_level,
        body_weight_kg=base_recommendation.body_weight_kg,
        timing=None,
        notes=notes,
    )


# --- Validation ---

def validate_activity_level(level: str) -> tuple[bool, str]:
    """Validate activity level string.

    Args:
        level: Activity level to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if level in ACTIVITY_PROTEIN_FACTORS:
        return True, ""

    # Try fuzzy match
    normalized = level.lower().strip()
    for key in ACTIVITY_PROTEIN_FACTORS:
        if key in normalized or normalized in key:
            return True, ""

    valid_levels = list(ACTIVITY_PROTEIN_FACTORS.keys())
    return False, f"Invalid activity level: '{level}'. Valid options: {valid_levels}"


def validate_body_weight(weight_kg: float) -> tuple[bool, str]:
    """Validate body weight.

    Args:
        weight_kg: Body weight in kg

    Returns:
        Tuple of (is_valid, error_message)
    """
    if weight_kg <= 0:
        return False, "Body weight must be positive"
    if weight_kg > 500:
        return False, "Body weight seems unreasonably high"
    return True, ""


# --- Helpers ---

def _get_recommendation_notes(activity_level: str, daily_grams: float) -> str:
    """Get contextual notes for recommendation."""
    notes = []

    if "resistance" in activity_level.lower() or "strength" in activity_level.lower():
        notes.append("For optimal muscle protein synthesis, spread intake across 4-5 meals.")
        notes.append("Consider 20-40g protein per meal for maximum MPS stimulation.")
    elif "endurance" in activity_level.lower():
        notes.append("Focus on recovery: consume protein within 30 minutes post-workout.")
        notes.append("Carbohydrate-protein combination improves glycogen replenishment.")
    elif "sedentary" in activity_level.lower():
        notes.append("Even with low activity, adequate protein supports muscle maintenance.")
    elif "bodybuilding" in activity_level.lower():
        notes.append("Higher protein intake supports recovery from high training volume.")
        notes.append("Consider casein protein before bed for sustained amino acid release.")

    if daily_grams > 200:
        notes.append("High protein intake — ensure adequate hydration (3+ liters water/day).")

    return " ".join(notes) if notes else "Moderate protein intake supports overall health."


def _get_goal_notes(goal: str, daily_grams: float) -> str:
    """Get notes for specific goal."""
    goal_notes = {
        "muscle_gain": "Protein increased for muscle synthesis. Combine with progressive overload.",
        "fat_loss": "Higher protein preserves muscle during caloric deficit. Aim for 1.2-1.6g/kg.",
        "maintenance": "Standard protein for muscle maintenance and general health.",
        "endurance": "Slightly lower protein to prioritize carbohydrate for fuel.",
    }
    base = goal_notes.get(goal, "Standard recommendation.")
    return f"{base} Total: {daily_grams:.0f}g/day."

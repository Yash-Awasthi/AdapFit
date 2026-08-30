"""Body composition metrics tracker — weight, BMI, body fat, muscle, water.

Extracted from inspiration/ZFIT/openscale.
Pattern: body metrics calculation from scale data (Bluetooth or manual entry).
Supports BMI, body fat percentage, lean body mass, fat mass, body water percentage.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ScaleReading:
    """Single scale measurement."""
    timestamp: datetime
    weight: float          # kg
    body_fat_pct: float | None = None   # %
    body_water_pct: float | None = None  # %
    muscle_mass: float | None = None     # kg
    bone_mass: float | None = None       # kg
    visceral_fat: int | None = None      # level 1-60
    basal_metabolic_rate: int | None = None  # kcal
    bmi: float | None = None


@dataclass(frozen=True)
class BodyComposition:
    """Computed body composition analysis."""
    bmi: float
    bmi_category: str
    body_fat_pct: float | None
    fat_mass: float | None
    lean_mass: float | None
    muscle_pct: float | None
    water_pct: float | None
    visceral_fat_level: int | None
    bmr: int | None
    ideal_weight_range: tuple[float, float]


def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """Calculate Body Mass Index."""
    if height_m <= 0:
        return 0.0
    return weight_kg / (height_m * height_m)


def bmi_category(bmi: float) -> str:
    """Classify BMI into WHO categories."""
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25.0:
        return "Normal weight"
    elif bmi < 30.0:
        return "Overweight"
    elif bmi < 35.0:
        return "Obesity class I"
    elif bmi < 40.0:
        return "Obesity class II"
    else:
        return "Obesity class III"


def ideal_weight(height_m: float) -> tuple[float, float]:
    """Calculate ideal weight range using BMI 18.5-24.9."""
    lower = 18.5 * height_m * height_m
    upper = 24.9 * height_m * height_m
    return (lower, upper)


def calculate_body_composition(reading: ScaleReading, height_m: float) -> BodyComposition:
    """Compute full body composition from a scale reading.

    If body_fat_pct is provided, compute fat_mass and lean_mass.
    If muscle_mass is provided, compute muscle_pct.
    """
    bmi = reading.bmi if reading.bmi is not None else calculate_bmi(reading.weight, height_m)
    category = bmi_category(bmi)

    fat_mass = None
    lean_mass = None
    if reading.body_fat_pct is not None:
        fat_mass = reading.weight * reading.body_fat_pct / 100
        lean_mass = reading.weight - fat_mass

    muscle_pct = None
    if reading.muscle_mass is not None and reading.weight > 0:
        muscle_pct = reading.muscle_mass / reading.weight * 100

    ideal = ideal_weight(height_m)

    bmr = reading.basal_metabolic_rate
    if bmr is None:
        # Mifflin-St Jeor equation (needs age and sex, use defaults)
        # BMR = 10*weight + 6.25*height(cm) - 5*age + 5 (male) / -161 (female)
        bmr = int(10 * reading.weight + 6.25 * height_m * 100 - 5 * 30 + 5)

    return BodyComposition(
        bmi=round(bmi, 1),
        bmi_category=category,
        body_fat_pct=reading.body_fat_pct,
        fat_mass=round(fat_mass, 1) if fat_mass else None,
        lean_mass=round(lean_mass, 1) if lean_mass else None,
        muscle_pct=round(muscle_pct, 1) if muscle_pct else None,
        water_pct=reading.body_water_pct,
        visceral_fat_level=reading.visceral_fat,
        bmr=bmr,
        ideal_weight_range=(round(ideal[0], 1), round(ideal[1], 1)),
    )


@dataclass
class Trend:
    metric: str
    direction: str  # "up", "down", "stable"
    delta: float
    pct_change: float


def analyze_trend(readings: list[ScaleReading], height_m: float) -> list[Trend]:
    """Analyze trends across multiple readings."""
    if len(readings) < 2:
        return []

    trends: list[Trend] = []
    first = readings[0]
    last = readings[-1]

    # Weight trend
    delta = last.weight - first.weight
    pct = delta / first.weight * 100 if first.weight > 0 else 0
    direction = "up" if delta > 0.1 else ("down" if delta < -0.1 else "stable")
    trends.append(Trend("weight", direction, round(delta, 1), round(pct, 1)))

    # BMI trend
    bmi_first = calculate_bmi(first.weight, height_m)
    bmi_last = calculate_bmi(last.weight, height_m)
    delta_bmi = bmi_last - bmi_first
    direction_bmi = "up" if delta_bmi > 0.1 else ("down" if delta_bmi < -0.1 else "stable")
    trends.append(Trend("bmi", direction_bmi, round(delta_bmi, 1),
                        round(delta_bmi / bmi_first * 100, 1) if bmi_first > 0 else 0))

    # Body fat trend
    if first.body_fat_pct is not None and last.body_fat_pct is not None:
        delta_bf = last.body_fat_pct - first.body_fat_pct
        direction_bf = "up" if delta_bf > 0.1 else ("down" if delta_bf < -0.1 else "stable")
        trends.append(Trend("body_fat", direction_bf, round(delta_bf, 1),
                            round(delta_bf / first.body_fat_pct * 100, 1) if first.body_fat_pct > 0 else 0))

    return trends

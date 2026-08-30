"""Cycling Analysis — Climb Categorization and Elevation Analysis.

Extracted from cycling-analysis-agent (inspiration).
UCI-style climb categorization, climb detection from elevation data,
elevation profile analysis, and cycling performance metrics.

All pure functions — no DB, no async, no matplotlib.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


# UCI-style climb categories
# Index = length_km * avg_grade_pct
CLIMB_CATEGORIES = [
    (80, "HC", 20),      # Hors Catégorie (beyond categorization)
    (40, "Cat 1", 10),   # Category 1
    (16, "Cat 2", 5),    # Category 2
    (6, "Cat 3", 2),     # Category 3
    (2, "Cat 4", 1),     # Category 4
    (0, "uncategorised", 0),
]


@dataclass
class ClimbSegment:
    """A detected climb segment."""
    start_km: float
    end_km: float
    length_km: float
    start_elevation_m: float
    end_elevation_m: float
    elevation_gain_m: float
    avg_grade_pct: float
    max_grade_pct: float
    category: str = "uncategorised"
    kom_points: int = 0
    index: float = 0.0


@dataclass
class ElevationProfile:
    """Complete elevation profile analysis."""
    total_distance_km: float = 0.0
    total_elevation_gain_m: float = 0.0
    total_elevation_loss_m: float = 0.0
    max_elevation_m: float = 0.0
    min_elevation_m: float = 0.0
    avg_grade_pct: float = 0.0
    max_grade_pct: float = 0.0
    climbing_m_per_km: float = 0.0
    difficulty_score: float = 0.0
    climbs: list = field(default_factory=list)


def categorise_climb(length_km: float, avg_grade_pct: float) -> tuple:
    """Categorize a climb using UCI-style index.

    Index = length_km * avg_grade_pct

    Args:
        length_km: Climb length in kilometers
        avg_grade_pct: Average gradient as percentage

    Returns:
        Tuple of (category_name, kom_points, index)
    """
    index = length_km * avg_grade_pct
    for threshold, name, points in CLIMB_CATEGORIES:
        if index >= threshold:
            return name, points, index
    return "uncategorised", 0, index


def detect_climbs(
    distances_km: list[float],
    elevations_m: list[float],
    min_gradient_pct: float = 3.0,
    min_length_m: float = 500.0,
    smoothing_window: int = 5,
) -> list[ClimbSegment]:
    """Detect climb segments from distance/elevation data.

    Args:
        distances_km: Cumulative distance in km
        elevations_m: Elevation in meters at each point
        min_gradient_pct: Minimum average gradient to consider as climb
        min_length_m: Minimum climb length in meters
        smoothing_window: Window size for elevation smoothing

    Returns:
        List of detected climb segments
    """
    if len(distances_km) < 10 or len(distances_km) != len(elevations_m):
        return []

    n = len(distances_km)

    # Smooth elevation
    elev = list(elevations_m)
    if smoothing_window > 1:
        smoothed = list(elev)
        for i in range(smoothing_window, n - smoothing_window):
            window = elev[i - smoothing_window:i + smoothing_window + 1]
            smoothed[i] = sum(window) / len(window)
        elev = smoothed

    # Calculate gradients between consecutive points
    gradients = []
    for i in range(1, n):
        d_m = (distances_km[i] - distances_km[i - 1]) * 1000.0
        if d_m <= 0:
            gradients.append(0.0)
            continue
        e_diff = elev[i] - elev[i - 1]
        grad = (e_diff / d_m) * 100.0
        gradients.append(grad)

    # Find climb segments (consecutive points with positive gradient)
    climbs = []
    in_climb = False
    climb_start = 0

    for i in range(1, n):
        if gradients[i - 1] >= min_gradient_pct / 3.0:  # ~1% threshold to start
            if not in_climb:
                in_climb = True
                climb_start = i - 1
        else:
            if in_climb:
                # End of climb
                start_m = distances_km[climb_start] * 1000.0
                end_m = distances_km[i - 1] * 1000.0
                length_m = end_m - start_m

                if length_m >= min_length_m:
                    elev_start = elev[climb_start]
                    elev_end = elev[i - 1]
                    elev_gain = max(0, elev_end - elev_start)
                    length_km = length_m / 1000.0

                    if length_km > 0:
                        avg_grade = (elev_gain / length_m) * 100.0
                    else:
                        avg_grade = 0.0

                    # Max gradient in the climb
                    climb_grads = gradients[climb_start:i - 1]
                    max_grad = max(climb_grads) if climb_grads else 0.0

                    cat, pts, idx = categorise_climb(length_km, avg_grade)

                    climbs.append(ClimbSegment(
                        start_km=distances_km[climb_start],
                        end_km=distances_km[i - 1],
                        length_km=round(length_km, 3),
                        start_elevation_m=round(elev_start, 1),
                        end_elevation_m=round(elev_end, 1),
                        elevation_gain_m=round(elev_gain, 1),
                        avg_grade_pct=round(avg_grade, 1),
                        max_grade_pct=round(max_grad, 1),
                        category=cat,
                        kom_points=pts,
                        index=round(idx, 1),
                    ))

                in_climb = False

    return climbs


def compute_elevation_profile(
    distances_km: list[float],
    elevations_m: list[float],
) -> ElevationProfile:
    """Compute complete elevation profile from distance/elevation data.

    Args:
        distances_km: Cumulative distance in km
        elevations_m: Elevation in meters

    Returns:
        ElevationProfile with all computed metrics
    """
    if len(distances_km) < 2 or len(distances_km) != len(elevations_m):
        return ElevationProfile()

    total_distance = distances_km[-1] - distances_km[0]
    total_gain = 0.0
    total_loss = 0.0
    max_elev = elevations_m[0]
    min_elev = elevations_m[0]
    max_grad = 0.0

    for i in range(1, len(elevations_m)):
        diff = elevations_m[i] - elevations_m[i - 1]
        if diff > 0:
            total_gain += diff
        else:
            total_loss += abs(diff)
        max_elev = max(max_elev, elevations_m[i])
        min_elev = min(min_elev, elevations_m[i])

        d_m = (distances_km[i] - distances_km[i - 1]) * 1000.0
        if d_m > 0:
            grad = abs(diff / d_m) * 100.0
            max_grad = max(max_grad, grad)

    avg_grade = (total_gain / (total_distance * 1000.0) * 100.0) if total_distance > 0 else 0.0
    climbing_per_km = total_gain / total_distance if total_distance > 0 else 0.0

    # Difficulty score: combines total climbing, max grade, and distance
    # Based on established cycling difficulty formulas
    difficulty = (
        total_gain * 0.01
        + max_grad * 2.0
        + total_distance * 0.5
    )

    climbs = detect_climbs(distances_km, elevations_m)

    return ElevationProfile(
        total_distance_km=round(total_distance, 2),
        total_elevation_gain_m=round(total_gain, 1),
        total_elevation_loss_m=round(total_loss, 1),
        max_elevation_m=round(max_elev, 1),
        min_elevation_m=round(min_elev, 1),
        avg_grade_pct=round(avg_grade, 2),
        max_grade_pct=round(max_grad, 1),
        climbing_m_per_km=round(climbing_per_km, 1),
        difficulty_score=round(difficulty, 1),
        climbs=climbs,
    )


def estimate_power_required(
    weight_kg: float,
    bike_weight_kg: float,
    gradient_pct: float,
    speed_kmh: float,
    cd_a: float = 0.3,
    crr: float = 0.005,
    air_density: float = 1.225,
) -> float:
    """Estimate power required to maintain speed on a gradient.

    Uses the standard cycling power model:
    P = (F_drag + F_rolling + F_gravity) * v

    Args:
        weight_kg: Rider weight in kg
        bike_weight_kg: Bike weight in kg
        gradient_pct: Gradient as percentage (positive = uphill)
        speed_kmh: Speed in km/h
        cd_a: Aerodynamic drag coefficient * frontal area (m²)
        crr: Coefficient of rolling resistance
        air_density: Air density in kg/m³

    Returns:
        Estimated power in watts
    """
    total_mass = weight_kg + bike_weight_kg
    speed_ms = speed_kmh / 3.6
    gradient = gradient_pct / 100.0

    if speed_ms <= 0:
        return 0.0

    # Gravity force
    f_gravity = total_mass * 9.81 * math.sin(math.atan(gradient))

    # Rolling resistance
    f_rolling = crr * total_mass * 9.81 * math.cos(math.atan(gradient))

    # Aerodynamic drag
    f_drag = 0.5 * air_density * cd_a * speed_ms ** 2

    # Total power
    power = (f_gravity + f_rolling + f_drag) * speed_ms

    return round(power, 1)


def estimate_vam(elevation_gain_m: float, time_hours: float) -> float:
    """Estimate VAM (Velocità Ascensionale Media) - average ascent speed.

    VAM = elevation_gain_m / time_hours

    Used to compare climbing performance regardless of distance.

    Args:
        elevation_gain_m: Total elevation gain in meters
        time_hours: Time in hours

    Returns:
        VAM in meters per hour
    """
    if time_hours <= 0:
        return 0.0
    return round(elevation_gain_m / time_hours, 0)


def classify_ride_type(
    total_distance_km: float,
    total_elevation_m: float,
    max_grade_pct: float,
) -> dict:
    """Classify the ride type based on characteristics.

    Args:
        total_distance_km: Total ride distance
        total_elevation_m: Total elevation gain
        max_grade_pct: Maximum gradient encountered

    Returns:
        Ride classification with type and description
    """
    # Climbing ratio (m per km)
    ratio = total_elevation_m / total_distance_km if total_distance_km > 0 else 0

    if ratio > 80 and max_grade_pct > 10:
        ride_type = "mountain"
        description = "Mountainous ride with significant climbing"
    elif ratio > 50:
        ride_type = "hilly"
        description = "Hilly terrain with notable elevation changes"
    elif ratio > 25:
        ride_type = "rolling"
        description = "Rolling terrain with moderate climbs"
    elif total_distance_km > 100:
        ride_type = "endurance"
        description = "Long endurance ride on mostly flat terrain"
    elif total_distance_km > 40:
        ride_type = "road"
        description = "Standard road ride"
    else:
        ride_type = "flat"
        description = "Flat terrain ride"

    return {
        "type": ride_type,
        "description": description,
        "climbing_ratio_m_per_km": round(ratio, 1),
        "total_distance_km": round(total_distance_km, 1),
        "total_elevation_m": round(total_elevation_m, 0),
    }


def estimate_calories_climbing(
    weight_kg: float,
    elevation_gain_m: float,
    distance_km: float,
    duration_hours: float,
) -> float:
    """Estimate calories burned during a climbing ride.

    Uses a simplified cycling energy expenditure model.

    Args:
        weight_kg: Total weight (rider + bike)
        elevation_gain_m: Total elevation gain in meters
        distance_km: Total distance in km
        duration_hours: Ride duration in hours

    Returns:
        Estimated calories burned
    """
    if duration_hours <= 0:
        return 0.0

    # Base metabolic cost: ~4 kcal/kg/hour for cycling
    base_cal = weight_kg * 4.0 * duration_hours

    # Climbing bonus: ~1 kcal per kg per 100m of elevation
    climb_cal = weight_kg * (elevation_gain_m / 100.0) * 1.0

    # Distance factor: longer rides are more efficient
    efficiency = min(1.0, 1.0 / (1.0 + distance_km * 0.001))

    total = (base_cal + climb_cal) * efficiency
    return round(total, 0)

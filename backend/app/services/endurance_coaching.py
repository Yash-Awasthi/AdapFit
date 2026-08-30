"""Endurance Coaching Analytics.

Extracted from coach (Coach Watts inspiration).
Implements performance metrics (CTL/ATL/TSB), power curve analysis,
training periodization, and nutrition timing for endurance athletes.

All pure functions — no database, no async.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional


class TrainingPhase(Enum):
    """Periodization training phases."""
    BASE = "base"
    BUILD = "build"
    PEAK = "peak"
    RACE = "race"
    RECOVERY = "recovery"
    TRANSITION = "transition"


class NutritionZone(Enum):
    """Training intensity nutrition zones."""
    RECOVERY = "recovery"  # <55% FTP
    STEADY = "steady"      # 55-75% FTP
    TEMPO = "tempo"        # 75-90% FTP
    THRESHOLD = "threshold"  # 90-105% FTP
    VO2MAX = "vo2max"      # >105% FTP


@dataclass
class DailyTrainingLoad:
    """Daily training load data point."""
    date: str  # YYYY-MM-DD
    tss: float  # Training Stress Score
    duration_min: float
    avg_hr: Optional[float] = None
    max_hr: Optional[float] = None
    avg_power: Optional[float] = None
    normalized_power: Optional[float] = None
    hr_max: float = 190.0  # estimated max HR
    ftp: float = 200.0  # Functional Threshold Power


@dataclass
class PerformanceMetrics:
    """Fitness/Fatigue/Form metrics."""
    date: str
    ctl: float  # Chronic Training Load (fitness)
    atl: float  # Acute Training Load (fatigue)
    tsb: float  # Training Stress Balance (form)
    tss_today: float = 0.0


@dataclass
class PowerCurvePoint:
    """Power curve data point."""
    duration_sec: float
    power: float  # watts
    date: str = ""


@dataclass
class NutritionPlan:
    """Daily nutrition plan based on training."""
    date: str
    training_zone: str
    carb_grams: float
    protein_grams: float
    fat_grams: float
    calories: float
    hydration_liters: float
    pre_workout_fuel: str
    during_workout_fuel: str
    post_workout_fuel: str


# --- CTL/ATL/TSB Calculations ---

def calculate_daily_tss(
    duration_min: float,
    intensity: float,
    hr_max: float = 190.0,
    avg_hr: Optional[float] = None,
) -> float:
    """Calculate Training Stress Score for a session.

    Simplified TSS calculation:
    TSS = duration_min * intensity * (hr_factor if HR provided)

    Args:
        duration_min: Session duration in minutes
        intensity: Normalized intensity 0-1 (fraction of FTP or threshold)
        hr_max: Maximum heart rate
        avg_hr: Average heart rate (optional, refines estimate)

    Returns:
        Training Stress Score (0-300+)
    """
    base_tss = duration_min * intensity * 2.0

    if avg_hr and hr_max > 0:
        hr_factor = avg_hr / hr_max
        base_tss *= (0.5 + hr_factor)

    return round(base_tss, 1)


def calculate_ctl_atl(
    daily_loads: list[DailyTrainingLoad],
    ctl_tau: int = 42,
    atl_tau: int = 7,
) -> list[PerformanceMetrics]:
    """Calculate CTL, ATL, and TSB over time.

    CTL (Chronic Training Load): 42-day exponentially weighted moving average
    ATL (Acute Training Load): 7-day exponentially weighted moving average
    TSB (Training Stress Balance): CTL - ATL

    Args:
        daily_loads: Chronologically sorted daily training loads
        ctl_tau: CTL time constant (default 42 days)
        atl_tau: ATL time constant (default 7 days)

    Returns:
        List of daily performance metrics
    """
    if not daily_loads:
        return []

    ctl_alpha = 1.0 - math.exp(-1.0 / ctl_tau)
    atl_alpha = 1.0 - math.exp(-1.0 / atl_tau)

    metrics = []
    prev_ctl = 0.0
    prev_atl = 0.0

    for load in daily_loads:
        ctl = prev_ctl * (1 - ctl_alpha) + load.tss * ctl_alpha
        atl = prev_atl * (1 - atl_alpha) + load.tss * atl_alpha
        tsb = ctl - atl

        metrics.append(PerformanceMetrics(
            date=load.date,
            ctl=round(ctl, 1),
            atl=round(atl, 1),
            tsb=round(tsb, 1),
            tss_today=load.tss,
        ))

        prev_ctl = ctl
        prev_atl = atl

    return metrics


def classify_tsb(tsb: float) -> dict:
    """Classify form based on TSB value.

    Args:
        tsb: Training Stress Balance

    Returns:
        Classification with phase, readiness, and recommendation
    """
    if tsb < -40:
        return {
            "zone": "very_fatigued",
            "phase": TrainingPhase.BUILD.value,
            "readiness": "very_low",
            "recommendation": "High training load — building fitness. Monitor for overtraining.",
        }
    elif tsb < -20:
        return {
            "zone": "fatigued",
            "phase": TrainingPhase.BUILD.value,
            "readiness": "low",
            "recommendation": "Moderate fatigue. Good time for hard training blocks.",
        }
    elif tsb < -10:
        return {
            "zone": "transitioning",
            "phase": TrainingPhase.PEAK.value,
            "readiness": "moderate",
            "recommendation": "Fitness building. Taper for race in 1-2 weeks.",
        }
    elif tsb < 10:
        return {
            "zone": "fresh",
            "phase": TrainingPhase.RACE.value,
            "readiness": "high",
            "recommendation": "Optimal race readiness. Good form for competition.",
        }
    elif tsb < 25:
        return {
            "zone": "very_fresh",
            "phase": TrainingPhase.RECOVERY.value,
            "readiness": "very_high",
            "recommendation": "Very fresh — may be detraining. Increase load if no race soon.",
        }
    else:
        return {
            "zone": "detrained",
            "phase": TrainingPhase.TRANSITION.value,
            "readiness": "very_high",
            "recommendation": "Significant detraining. Increase training stimulus.",
        }


# --- Power Curve Analysis ---

def build_power_curve(
    power_samples: list[tuple[float, float]],
) -> list[PowerCurvePoint]:
    """Build power-duration curve from sample data.

    Args:
        power_samples: List of (duration_sec, power_watts) tuples
                       Can contain multiple samples per duration

    Returns:
        Sorted power curve (longest duration first, highest power)
    """
    if not power_samples:
        return []

    # Group by duration buckets (1s, 5s, 15s, 30s, 1min, 5min, 10min, 20min, 30min, 60min)
    buckets = defaultdict(list)
    key_durations = [1, 5, 15, 30, 60, 180, 300, 600, 1200, 1800, 3600]

    for duration, power in power_samples:
        # Find closest bucket
        closest = min(key_durations, key=lambda d: abs(d - duration))
        if abs(closest - duration) / closest < 0.3:  # within 30% of bucket
            buckets[closest].append(power)

    curve = []
    for dur in sorted(buckets.keys()):
        max_power = max(buckets[dur])
        curve.append(PowerCurvePoint(
            duration_sec=dur,
            power=max_power,
        ))

    return sorted(curve, key=lambda p: p.duration_sec)


def estimate_ftp_from_curve(curve: list[PowerCurvePoint]) -> float:
    """Estimate FTP from power curve.

    FTP is approximately equal to 20-minute max power * 0.95.

    Args:
        curve: Power curve points

    Returns:
        Estimated FTP in watts
    """
    # Find closest to 20 min (1200s)
    target = 1200
    closest = min(curve, key=lambda p: abs(p.duration_sec - target))
    return closest.power * 0.95


def compute_power_zones(ftp: float) -> list[dict]:
    """Compute power training zones from FTP.

    Uses standard Coggan power zones.

    Args:
        ftp: Functional Threshold Power in watts

    Returns:
        List of zone definitions
    """
    return [
        {"zone": 1, "name": "Active Recovery", "min_pct": 0.0, "max_pct": 0.55,
         "min_watts": round(ftp * 0.0), "max_watts": round(ftp * 0.55)},
        {"zone": 2, "name": "Endurance", "min_pct": 0.56, "max_pct": 0.75,
         "min_watts": round(ftp * 0.56), "max_watts": round(ftp * 0.75)},
        {"zone": 3, "name": "Tempo", "min_pct": 0.76, "max_pct": 0.90,
         "min_watts": round(ftp * 0.76), "max_watts": round(ftp * 0.90)},
        {"zone": 4, "name": "Threshold", "min_pct": 0.91, "max_pct": 1.05,
         "min_watts": round(ftp * 0.91), "max_watts": round(ftp * 1.05)},
        {"zone": 5, "name": "VO2max", "min_pct": 1.06, "max_pct": 1.20,
         "min_watts": round(ftp * 1.06), "max_watts": round(ftp * 1.20)},
        {"zone": 6, "name": "Anaerobic", "min_pct": 1.21, "max_pct": 1.50,
         "min_watts": round(ftp * 1.21), "max_watts": round(ftp * 1.50)},
        {"zone": 7, "name": "Neuromuscular", "min_pct": 1.51, "max_pct": 99.99,
         "min_watts": round(ftp * 1.51), "max_watts": 9999},
    ]


# --- Nutrition Timing ---

def calculate_nutrition_for_session(
    duration_min: float,
    intensity: NutritionZone,
    body_weight_kg: float = 70.0,
) -> NutritionPlan:
    """Calculate nutrition plan for a training session.

    Based on endurance nutrition science:
    - Recovery zone: low carb, normal protein
    - Steady: moderate carb for fuel
    - Tempo/Threshold: high carb for sustained effort
    - VO2max: very high carb, minimal fat

    Args:
        duration_min: Session duration in minutes
        intensity: Training nutrition zone
        body_weight_kg: Athlete body weight

    Returns:
        NutritionPlan with macros and timing guidance
    """
    # Base calories per hour by intensity
    calories_per_hour = {
        NutritionZone.RECOVERY: 300,
        NutritionZone.STEADY: 500,
        NutritionZone.TEMPO: 700,
        NutritionZone.THRESHOLD: 900,
        NutritionZone.VO2MAX: 1100,
    }

    cal_per_hour = calories_per_hour.get(intensity, 500)
    total_calories = cal_per_hour * (duration_min / 60.0)

    # Macro split by intensity
    carb_pct = {
        NutritionZone.RECOVERY: 0.40,
        NutritionZone.STEADY: 0.55,
        NutritionZone.TEMPO: 0.65,
        NutritionZone.THRESHOLD: 0.70,
        NutritionZone.VO2MAX: 0.75,
    }

    protein_pct = {
        NutritionZone.RECOVERY: 0.30,
        NutritionZone.STEADY: 0.20,
        NutritionZone.TEMPO: 0.15,
        NutritionZone.THRESHOLD: 0.15,
        NutritionZone.VO2MAX: 0.15,
    }

    c_pct = carb_pct.get(intensity, 0.55)
    p_pct = protein_pct.get(intensity, 0.20)
    f_pct = 1.0 - c_pct - p_pct

    # 4 cal/g carbs, 4 cal/g protein, 9 cal/g fat
    carb_g = (total_calories * c_pct) / 4.0
    protein_g = (total_calories * p_pct) / 4.0
    fat_g = (total_calories * f_pct) / 9.0

    # Hydration: 500-1000ml per hour based on intensity
    hydration_map = {
        NutritionZone.RECOVERY: 0.5,
        NutritionZone.STEADY: 0.6,
        NutritionZone.TEMPO: 0.8,
        NutritionZone.THRESHOLD: 0.9,
        NutritionZone.VO2MAX: 1.0,
    }
    hydration = hydration_map.get(intensity, 0.6) * (duration_min / 60.0)

    # Fueling guidance
    pre_fuel = {
        NutritionZone.RECOVERY: "Light snack if needed (fruit, yogurt)",
        NutritionZone.STEADY: "Small meal 2h before (oatmeal, banana)",
        NutritionZone.TEMPO: "Moderate meal 2-3h before (rice, lean protein)",
        NutritionZone.THRESHOLD: "Full meal 3h before (pasta, chicken)",
        NutritionZone.VO2MAX: "High-carb meal 3-4h before (pasta, rice)",
    }

    during_fuel = {
        NutritionZone.RECOVERY: "Water only",
        NutritionZone.STEADY: "Water, optional sports drink",
        NutritionZone.TEMPO: "30-60g carbs/hour (gels, drink mix)",
        NutritionZone.THRESHOLD: "60-90g carbs/hour (gels, bars, drink)",
        NutritionZone.VO2MAX: "90+ g carbs/hour (gels, drink, chews)",
    }

    post_fuel = {
        NutritionZone.RECOVERY: "Normal balanced meal",
        NutritionZone.STEADY: "Recovery snack within 1h (protein + carbs)",
        NutritionZone.TEMPO: "Recovery shake within 30min, meal within 2h",
        NutritionZone.THRESHOLD: "Recovery shake within 20min, meal within 1.5h",
        NutritionZone.VO2MAX: "Recovery shake immediately, high-carb meal within 1h",
    }

    return NutritionPlan(
        date="",
        training_zone=intensity.value,
        carb_grams=round(carb_g, 1),
        protein_grams=round(protein_g, 1),
        fat_grams=round(fat_g, 1),
        calories=round(total_calories),
        hydration_liters=round(hydration, 2),
        pre_workout_fuel=pre_fuel.get(intensity, ""),
        during_workout_fuel=during_fuel.get(intensity, ""),
        post_workout_fuel=post_fuel.get(intensity, ""),
    )


# --- Periodization ---

def generate_periodization(
    weeks: int = 12,
    event_week: int = 10,
    current_fitness: float = 50.0,
    target_fitness: float = 75.0,
) -> list[dict]:
    """Generate a periodized training plan.

    Args:
        weeks: Total plan duration in weeks
        event_week: Week number of target event
        current_fitness: Starting CTL (0-100)
        target_fitness: Target CTL (0-100)

    Returns:
        List of weekly phase assignments with target TSS
    """
    plan = []
    fitness_ramp = (target_fitness - current_fitness) / weeks

    for week in range(1, weeks + 1):
        weeks_to_event = event_week - week

        if week <= weeks * 0.3:
            phase = TrainingPhase.BASE
            tss_multiplier = 1.0
        elif week <= weeks * 0.6:
            phase = TrainingPhase.BUILD
            tss_multiplier = 1.2
        elif week <= event_week - 2:
            phase = TrainingPhase.PEAK
            tss_multiplier = 1.3
        elif week <= event_week:
            phase = TrainingPhase.RACE
            tss_multiplier = 0.4  # taper
        else:
            phase = TrainingPhase.RECOVERY
            tss_multiplier = 0.5

        # Base TSS scales with fitness level
        base_tss = 300 + (current_fitness + fitness_ramp * week) * 3
        target_tss = base_tss * tss_multiplier

        # Every 4th week is recovery
        if week % 4 == 0 and phase not in (TrainingPhase.RACE, TrainingPhase.RECOVERY):
            tss_multiplier *= 0.7
            target_tss *= 0.7
            phase_note = "recovery week"
        else:
            phase_note = ""

        plan.append({
            "week": week,
            "phase": phase.value,
            "target_tss": round(target_tss),
            "tss_multiplier": round(tss_multiplier, 2),
            "note": phase_note,
            "fitness_target": round(current_fitness + fitness_ramp * week, 1),
        })

    return plan


# --- Daily Recommendations ---

def generate_daily_recommendation(
    tsb: float,
    sleep_quality: float = 0.8,
    hrv_status: str = "normal",
    recent_tss_avg: float = 200.0,
) -> dict:
    """Generate daily training recommendation based on current state.

    Combines form (TSB), recovery (sleep, HRV), and recent load.

    Args:
        tsb: Current Training Stress Balance
        sleep_quality: Sleep quality score 0-1
        hrv_status: 'low', 'normal', or 'high'
        recent_tss_avg: Average TSS over last 7 days

    Returns:
        Recommendation with intensity, type, and rationale
    """
    # Recovery adjustment
    recovery_score = sleep_quality
    if hrv_status == "high":
        recovery_score += 0.1
    elif hrv_status == "low":
        recovery_score -= 0.2
    recovery_score = max(0.0, min(1.0, recovery_score))

    # TSB-based recommendation
    form = classify_tsb(tsb)

    if tsb < -30 and recovery_score < 0.5:
        return {
            "intensity": "rest",
            "type": "Recovery Day",
            "duration_min": 0,
            "rationale": f"Heavy fatigue (TSB {tsb:.0f}) with poor recovery. Rest recommended.",
            "activities": ["Complete rest", "Light stretching", "Foam rolling"],
        }
    elif tsb < -20:
        return {
            "intensity": "moderate",
            "type": "Endurance Ride/Run",
            "duration_min": 60,
            "rationale": f"Building fitness (TSB {tsb:.0f}). Moderate endurance work.",
            "activities": ["Zone 2 endurance", "Steady pace", "Conversational effort"],
        }
    elif tsb < -5:
        return {
            "intensity": "hard",
            "type": "Interval Session",
            "duration_min": 75,
            "rationale": f"Good form (TSB {tsb:.0f}). Time for quality intervals.",
            "activities": ["VO2max intervals", "Threshold work", "Tempo efforts"],
        }
    elif tsb < 15:
        return {
            "intensity": "race_ready",
            "type": "Race Simulation",
            "duration_min": 90,
            "rationale": f"Peak form (TSB {tsb:.0f}). Practice race pace.",
            "activities": ["Race pace effort", "Strategy practice", "Mental rehearsal"],
        }
    else:
        return {
            "intensity": "recovery",
            "type": "Active Recovery",
            "duration_min": 30,
            "rationale": f"Very fresh (TSB {tsb:.0f}). Light activity to maintain feel.",
            "activities": ["Easy spin/walk", "Yoga", "Mobility work"],
        }


# --- Helper ---

from collections import defaultdict

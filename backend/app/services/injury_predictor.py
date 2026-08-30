"""
Injury prediction and prevention from injury-prediction-prevention-ml.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import math


@dataclass
class TrainingLoad:
    acwr: float = 1.0  # Acute:Chronic Workload Ratio
    acute_load: float = 0.0
    chronic_load: float = 0.0
    monotony: float = 0.0
    strain: float = 0.0


@dataclass
class InjuryRisk:
    risk_score: float  # 0-1
    risk_level: str  # low, moderate, high, critical
    contributing_factors: List[str]
    recommendations: List[str]


def compute_acwr(acute: float, chronic: float) -> float:
    if chronic <= 0:
        return 1.0
    return acute / chronic


def compute_training_monotony(daily_loads: List[float]) -> float:
    if not daily_loads:
        return 0.0
    mean_load = sum(daily_loads) / len(daily_loads)
    if mean_load <= 0:
        return 0.0
    std = math.sqrt(sum((l - mean_load) ** 2 for l in daily_loads) / len(daily_loads))
    return mean_load / max(std, 0.01)


def compute_strain(acute_load: float, monotony: float) -> float:
    return acute_load * monotony


def assess_injury_risk(
    training_load: TrainingLoad,
    sleep_hours: float = 7.0,
    stress_level: float = 0.0,
    previous_injury_days: int = 999,
    age: int = 25,
) -> InjuryRisk:
    score = 0.0
    factors = []
    recommendations = []

    acwr = training_load.acwr
    if acwr > 1.5:
        score += 0.4
        factors.append(f"ACWR {acwr:.2f} exceeds safe range (0.8-1.3)")
        recommendations.append("Reduce training load by 20-30% this week")
    elif acwr > 1.3:
        score += 0.2
        factors.append(f"ACWR {acwr:.2f} approaching upper limit")
        recommendations.append("Monitor load closely, avoid increases")
    elif acwr < 0.8:
        score += 0.1
        factors.append(f"ACWR {acwr:.2f} below optimal range")

    if training_load.monotony > 2.0:
        score += 0.15
        factors.append(f"Training monotony {training_load.monotony:.1f} is high")
        recommendations.append("Add training variety to reduce monotony")

    if sleep_hours < 6:
        score += 0.2
        factors.append(f"Sleep {sleep_hours:.1f}h is insufficient")
        recommendations.append("Aim for 7-9 hours of sleep")
    elif sleep_hours < 7:
        score += 0.1
        factors.append(f"Sleep {sleep_hours:.1f}h could be better")

    if stress_level > 0.7:
        score += 0.15
        factors.append("High stress levels detected")
        recommendations.append("Incorporate stress management techniques")

    if previous_injury_days < 28:
        score += 0.15
        factors.append(f"Injury occurred {previous_injury_days} days ago")
        recommendations.append("Continue gradual return-to-play protocol")

    if age > 35:
        score += 0.05
        factors.append("Age-related recovery considerations")

    if score >= 0.7:
        level = "critical"
    elif score >= 0.5:
        level = "high"
    elif score >= 0.3:
        level = "moderate"
    else:
        level = "low"

    if not recommendations:
        recommendations.append("Maintain current training approach")

    return InjuryRisk(
        risk_score=min(1.0, score),
        risk_level=level,
        contributing_factors=factors,
        recommendations=recommendations,
    )

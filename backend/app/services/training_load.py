"""
Training load calculation from trainingloadcalculator patterns.
"""
from dataclasses import dataclass
from typing import List
import math


@dataclass
class TrainingLoadResult:
    acwr: float = 1.0
    acute_load: float = 0.0
    chronic_load: float = 0.0
    monotony: float = 0.0
    strain: float = 0.0
    risk_level: str = "low"
    recommendation: str = ""


def compute_training_load(daily_loads: List[float]) -> TrainingLoadResult:
    if len(daily_loads) < 7:
        return TrainingLoadResult(risk_level="insufficient_data", recommendation="Need at least 7 days of data")
    acute = sum(daily_loads[-7:]) / 7
    chronic = sum(daily_loads[-28:]) / min(28, len(daily_loads)) if len(daily_loads) >= 28 else sum(daily_loads) / len(daily_loads)
    acwr = acute / chronic if chronic > 0 else 1.0
    monotony = acute / (math.sqrt(sum((l - acute) ** 2 for l in daily_loads[-7:]) / 7) or 1)
    strain = acute * monotony
    if acwr > 1.5:
        risk = "high"
        rec = "Reduce training load by 20-30% — high injury risk"
    elif acwr > 1.3:
        risk = "moderate"
        rec = "Monitor load closely — approaching upper limit"
    elif acwr < 0.8:
        risk = "low"
        rec = "Consider increasing training load"
    else:
        risk = "optimal"
        rec = "Maintain current training approach"
    return TrainingLoadResult(acwr=round(acwr, 2), acute_load=round(acute, 1), chronic_load=round(chronic, 1), monotony=round(monotony, 2), strain=round(strain, 1), risk_level=risk, recommendation=rec)

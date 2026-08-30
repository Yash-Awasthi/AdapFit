"""
Cardiovascular Analysis Service — Heart rate analysis, VO2 max estimation, risk assessment
Inspired by openhrv, athlete-injury-risk-detection
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class HeartRateZone:
    name: str
    min_bpm: float
    max_bpm: float
    zone_number: int
    description: str


@dataclass
class CardioAnalysis:
    resting_hr: float
    max_hr: float
    hr_reserve: float
    vo2_max_estimate: float
    zones: List[HeartRateZone]
    risk_level: RiskLevel
    fitness_score: float


class CardiovascularAnalyzer:
    """Pure function cardiovascular analysis."""

    @staticmethod
    def estimate_max_hr(age: int) -> float:
        return 220 - age

    @staticmethod
    def calculate_hr_reserve(resting_hr: float, max_hr: float) -> float:
        return max_hr - resting_hr

    @staticmethod
    def calculate_zones(resting_hr: float, max_hr: float) -> List[HeartRateZone]:
        reserve = max_hr - resting_hr
        return [
            HeartRateZone("Recovery", resting_hr + reserve * 0.5, resting_hr + reserve * 0.6, 1, "Light activity"),
            HeartRateZone("Aerobic", resting_hr + reserve * 0.6, resting_hr + reserve * 0.7, 2, "Cardio training"),
            HeartRateZone("Tempo", resting_hr + reserve * 0.7, resting_hr + reserve * 0.8, 3, "Threshold training"),
            HeartRateZone("Threshold", resting_hr + reserve * 0.8, resting_hr + reserve * 0.9, 4, "Hard effort"),
            HeartRateZone("Maximal", resting_hr + reserve * 0.9, max_hr, 5, "Sprint effort"),
        ]

    @staticmethod
    def estimate_vo2_max(resting_hr: float, age: int, sex: str = "male") -> float:
        if resting_hr <= 0:
            return 0.0
        vo2 = 15.3 * (max_hr / resting_hr)
        if sex == "female":
            vo2 *= 0.87
        age_factor = 1 - (age - 20) * 0.005
        vo2 *= max(0.5, age_factor)
        return round(vo2, 1)

    @staticmethod
    def assess_risk(resting_hr: float, age: int, vo2_max: float,
                    has_conditions: bool = False) -> RiskLevel:
        score = 0
        if resting_hr > 80:
            score += 2
        elif resting_hr > 70:
            score += 1
        if vo2_max < 30:
            score += 3
        elif vo2_max < 40:
            score += 2
        elif vo2_max < 50:
            score += 1
        if age > 60:
            score += 1
        if has_conditions:
            score += 2
        if score >= 5:
            return RiskLevel.VERY_HIGH
        elif score >= 3:
            return RiskLevel.HIGH
        elif score >= 1:
            return RiskLevel.MODERATE
        return RiskLevel.LOW

    @staticmethod
    def calculate_fitness_score(resting_hr: float, vo2_max: float, age: int) -> float:
        hr_score = max(0, min(40, (80 - resting_hr) * 0.8))
        vo2_score = max(0, min(40, (vo2_max - 20) * 0.5))
        age_score = max(0, min(20, (60 - age) * 0.3))
        return round(hr_score + vo2_score + age_score, 1)

    @staticmethod
    def analyze_heart_rate_series(hr_values: List[float]) -> Dict:
        if not hr_values:
            return {"error": "No data"}
        avg = sum(hr_values) / len(hr_values)
        min_hr = min(hr_values)
        max_hr = max(hr_values)
        variance = sum((h - avg) ** 2 for h in hr_values) / len(hr_values)
        std_dev = math.sqrt(variance)
        rmssd_values = [hr_values[i] - hr_values[i-1] for i in range(1, len(hr_values))]
        rmssd = math.sqrt(sum(d ** 2 for d in rmssd_values) / len(rmssd_values)) if rmssd_values else 0
        return {
            "average_hr": round(avg, 1),
            "min_hr": round(min_hr, 1),
            "max_hr": round(max_hr, 1),
            "std_dev": round(std_dev, 2),
            "rmssd": round(rmssd, 2),
            "sample_count": len(hr_values),
        }

    @classmethod
    def full_analysis(cls, resting_hr: float, age: int, sex: str = "male",
                     hr_values: Optional[List[float]] = None) -> CardioAnalysis:
        max_hr = cls.estimate_max_hr(age)
        hr_reserve = cls.calculate_hr_reserve(resting_hr, max_hr)
        vo2_max = cls.estimate_vo2_max(resting_hr, age, sex)
        zones = cls.calculate_zones(resting_hr, max_hr)
        risk = cls.assess_risk(resting_hr, age, vo2_max)
        fitness = cls.calculate_fitness_score(resting_hr, vo2_max, age)
        return CardioAnalysis(
            resting_hr=resting_hr,
            max_hr=max_hr,
            hr_reserve=hr_reserve,
            vo2_max_estimate=vo2_max,
            zones=zones,
            risk_level=risk,
            fitness_score=fitness,
        )

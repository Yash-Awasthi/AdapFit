"""
Stress Detection Service — HRV-based stress scoring and recovery detection
Inspired by bleakheart, heart-rate-camera
"""

import math
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class StressLevel(Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class StressReading:
    timestamp: float
    heart_rate: float
    hrv_rmssd: float
    hrv_sdnn: float
    blood_oxygen: float = 98.0
    skin_temp: float = 36.5


@dataclass
class StressResult:
    timestamp: float
    stress_score: float
    stress_level: StressLevel
    hrv_score: float
    hr_score: float
    recovery_status: str
    confidence: float


class StressDetector:
    """Pure function stress detection from physiological signals."""

    # Baseline ranges for healthy adults
    BASELINE = {
        "resting_hr": 65.0,
        "hrv_rmssd": 40.0,
        "hrv_sdnn": 50.0,
        "hr_range": (50, 100),
    }

    @staticmethod
    def calculate_hrv_score(rmssd: float, sdnn: float) -> float:
        rmssd_score = min(1.0, rmssd / 80.0)
        sdnn_score = min(1.0, sdnn / 100.0)
        return (rmssd_score * 0.6 + sdnn_score * 0.4)

    @staticmethod
    def calculate_hr_score(current_hr: float, resting_hr: float = 65.0) -> float:
        if current_hr <= resting_hr:
            return 1.0
        deviation = current_hr - resting_hr
        score = max(0.0, 1.0 - deviation / 50.0)
        return score

    @staticmethod
    def calculate_stress_score(hrv_score: float, hr_score: float) -> float:
        stress_score = (1.0 - hrv_score) * 0.6 + (1.0 - hr_score) * 0.4
        return round(max(0.0, min(1.0, stress_score)), 3)

    @staticmethod
    def classify_stress_level(score: float) -> StressLevel:
        if score < 0.2:
            return StressLevel.VERY_LOW
        elif score < 0.4:
            return StressLevel.LOW
        elif score < 0.6:
            return StressLevel.MODERATE
        elif score < 0.8:
            return StressLevel.HIGH
        else:
            return StressLevel.VERY_HIGH

    @staticmethod
    def detect_recovery(readings: List[StressReading]) -> str:
        if len(readings) < 5:
            return "insufficient_data"
        recent = readings[-5:]
        hrv_values = [r.hrv_rmssd for r in recent]
        avg_recent = sum(hrv_values) / len(hrv_values)
        overall = sum(r.hrv_rmssd for r in readings) / len(readings)
        if avg_recent > overall * 1.1:
            return "recovering"
        elif avg_recent < overall * 0.9:
            return "stressed"
        else:
            return "stable"

    @classmethod
    def analyze_reading(cls, reading: StressReading,
                        baseline: Optional[Dict] = None) -> StressResult:
        bl = baseline or cls.BASELINE
        hrv_score = cls.calculate_hrv_score(reading.hrv_rmssd, reading.hrv_sdnn)
        hr_score = cls.calculate_hr_score(reading.heart_rate, bl["resting_hr"])
        stress_score = cls.calculate_stress_score(hrv_score, hr_score)
        stress_level = cls.classify_stress_level(stress_score)
        hrv_range = (bl["hrv_rmssd"] * 0.5, bl["hrv_rmssd"] * 1.5)
        in_range = hrv_range[0] <= reading.hrv_rmssd <= hrv_range[1]
        confidence = 0.8 if in_range else 0.5
        if reading.blood_oxygen < 95:
            confidence *= 0.8
        return StressResult(
            timestamp=reading.timestamp,
            stress_score=stress_score,
            stress_level=stress_level,
            hrv_score=round(hrv_score, 3),
            hr_score=round(hr_score, 3),
            recovery_status="analyzing",
            confidence=round(confidence, 2),
        )

    @classmethod
    def analyze_session(cls, readings: List[StressReading]) -> Dict:
        if not readings:
            return {"error": "No readings"}
        results = [cls.analyze_reading(r) for r in readings]
        stress_scores = [r.stress_score for r in results]
        avg_stress = sum(stress_scores) / len(stress_scores)
        max_stress = max(stress_scores)
        min_stress = min(stress_scores)
        recovery = cls.detect_recovery(readings)
        for r in results:
            r.recovery_status = recovery
        return {
            "average_stress": round(avg_stress, 3),
            "max_stress": round(max_stress, 3),
            "min_stress": round(min_stress, 3),
            "stress_level": cls.classify_stress_level(avg_stress).value,
            "recovery_status": recovery,
            "readings_count": len(readings),
            "high_stress_episodes": sum(1 for s in stress_scores if s > 0.7),
            "low_stress_episodes": sum(1 for s in stress_scores if s < 0.3),
        }

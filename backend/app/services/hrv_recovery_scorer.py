"""
HRV-Based Recovery Scorer — calculates daily readiness from heart rate data.

Combines:
- HRV metrics (RMSSD, SDNN, LF/HF ratio)
- Resting heart rate trends
- Sleep quality data
- Training load history
- Subjective readiness (optional self-report)

Provides:
- Recovery score (0-100)
- Readiness classification (poor / fair / good / excellent)
- Training recommendation for the day
- Recovery trend analysis
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Tuple
import math


class ReadinessLevel(Enum):
    POOR = "poor"           # 0-30: rest day recommended
    FAIR = "fair"           # 30-50: light training only
    GOOD = "good"           # 50-75: moderate training
    EXCELLENT = "excellent" # 75-100: push hard


class TrainingRecommendation(Enum):
    REST_DAY = "rest_day"
    ACTIVE_RECOVERY = "active_recovery"  # yoga, walking, foam rolling
    LIGHT_SESSION = "light_session"       # 40-50% intensity
    MODERATE_SESSION = "moderate_session"  # 60-70% intensity
    HIGH_INTENSITY = "high_intensity"     # 80-90% intensity
    PEAK_SESSION = "peak_session"         # 90-100% intensity


@dataclass
class HRVMetrics:
    """Heart Rate Variability metrics from a single measurement."""
    timestamp: datetime
    duration_seconds: int
    rmssd: float            # Root mean square of successive differences (ms)
    sdnn: float             # Standard deviation of NN intervals (ms)
    lf_power: float         # Low frequency power (ms²)
    hf_power: float         # High frequency power (ms²)
    lf_hf_ratio: float      # LF/HF ratio
    resting_hr: float       # Resting heart rate (bpm)
    hrv_score: float        # Normalized 0-100


@dataclass
class SleepData:
    """Sleep quality data from wearable."""
    date: str  # YYYY-MM-DD
    total_minutes: int
    deep_minutes: int
    rem_minutes: int
    light_minutes: int
    awake_minutes: int
    sleep_score: float  # 0-100
    interruptions: int


@dataclass
class TrainingLoad:
    """Recent training load data."""
    date: str
    tss: float             # Training Stress Score
    duration_minutes: int
    intensity: float       # 0-1
    muscle_groups: List[str] = field(default_factory=list)


@dataclass
class RecoveryReport:
    """Complete recovery assessment."""
    date: str
    recovery_score: float           # 0-100
    readiness: ReadinessLevel
    recommendation: TrainingRecommendation
    factors: dict                   # breakdown of scoring factors
    trend: str                      # "improving", "stable", "declining"
    consecutive_rest_days: int
    suggested_max_intensity: float  # 0-1
    suggested_volume_multiplier: float  # 1.0 = normal, 0.5 = half
    notes: List[str] = field(default_factory=list)


class HRVRecoveryScorer:
    """
    Calculates daily recovery score from multiple physiological signals.
    """

    # Scoring weights
    WEIGHTS = {
        "hrv": 0.35,           # HRV trend vs baseline
        "resting_hr": 0.15,    # RHR trend vs baseline
        "sleep": 0.25,         # Sleep quality
        "training_load": 0.15, # Recent training load
        "trend": 0.10,         # Multi-day trend
    }

    def __init__(self):
        self.hrv_history: List[HRVMetrics] = []
        self.sleep_history: List[SleepData] = []
        self.training_history: List[TrainingLoad] = []

    def add_hrv(self, metrics: HRVMetrics):
        """Add an HRV measurement."""
        self.hrv_history.append(metrics)
        # Keep last 30 days
        cutoff = datetime.now() - timedelta(days=30)
        self.hrv_history = [h for h in self.hrv_history if h.timestamp > cutoff]

    def add_sleep(self, data: SleepData):
        """Add sleep data."""
        self.sleep_history.append(data)
        self.sleep_history = self.sleep_history[-30:]

    def add_training(self, load: TrainingLoad):
        """Add training load data."""
        self.training_history.append(load)
        self.training_history = self.training_history[-30:]

    def calculate_recovery(self, today: str) -> RecoveryReport:
        """Calculate today's recovery score and recommendation."""
        factors = {}

        # 1. HRV score (vs baseline)
        hrv_score = self._score_hrv()
        factors["hrv"] = {"score": hrv_score, "weight": self.WEIGHTS["hrv"]}

        # 2. Resting heart rate
        rhr_score = self._score_resting_hr()
        factors["resting_hr"] = {"score": rhr_score, "weight": self.WEIGHTS["resting_hr"]}

        # 3. Sleep quality
        sleep_score = self._score_sleep(today)
        factors["sleep"] = {"score": sleep_score, "weight": self.WEIGHTS["sleep"]}

        # 4. Training load
        load_score = self._score_training_load(today)
        factors["training_load"] = {"score": load_score, "weight": self.WEIGHTS["training_load"]}

        # 5. Multi-day trend
        trend_score, trend = self._score_trend()
        factors["trend"] = {"score": trend_score, "weight": self.WEIGHTS["trend"]}

        # Weighted average
        total_score = sum(
            factor["score"] * factor["weight"]
            for factor in factors.values()
        )
        total_score = max(0, min(100, total_score))

        # Determine readiness level
        if total_score >= 75:
            readiness = ReadinessLevel.EXCELLENT
        elif total_score >= 50:
            readiness = ReadinessLevel.GOOD
        elif total_score >= 30:
            readiness = ReadinessLevel.FAIR
        else:
            readiness = ReadinessLevel.POOR

        # Training recommendation
        recommendation = self._get_recommendation(total_score)
        max_intensity = self._get_max_intensity(total_score)
        volume_mult = self._get_volume_multiplier(total_score)

        # Count consecutive rest days
        consecutive_rest = self._count_consecutive_rest(today)

        # Notes
        notes = []
        if hrv_score < 40:
            notes.append("HRV is significantly below baseline — prioritize recovery")
        if sleep_score < 40:
            notes.append("Sleep quality was poor — consider sleep hygiene improvements")
        if load_score < 30:
            notes.append("Training load is high — consider reducing volume")

        return RecoveryReport(
            date=today,
            recovery_score=round(total_score, 1),
            readiness=readiness,
            recommendation=recommendation,
            factors=factors,
            trend=trend,
            consecutive_rest_days=consecutive_rest,
            suggested_max_intensity=max_intensity,
            suggested_volume_multiplier=volume_mult,
            notes=notes,
        )

    def _score_hrv(self) -> float:
        """Score HRV vs personal baseline."""
        if len(self.hrv_history) < 7:
            return 50.0  # insufficient data

        # Calculate baseline (7-day rolling average)
        recent = self.hrv_history[-7:]
        baseline_rmssd = sum(h.rmssd for h in recent) / len(recent)

        # Compare latest to baseline
        latest = self.hrv_history[-1]
        if baseline_rmssd == 0:
            return 50.0

        ratio = latest.rmssd / baseline_rmssd

        # Map to 0-100 score
        if ratio >= 1.2:
            return 90.0
        elif ratio >= 1.0:
            return 70.0 + (ratio - 1.0) * 100
        elif ratio >= 0.8:
            return 40.0 + (ratio - 0.8) * 150
        else:
            return max(0, ratio * 50)

    def _score_resting_hr(self) -> float:
        """Score resting heart rate vs baseline."""
        if len(self.hrv_history) < 7:
            return 50.0

        recent = self.hrv_history[-7:]
        baseline_rhr = sum(h.resting_hr for h in recent) / len(recent)
        latest = self.hrv_history[-1]

        # Lower RHR = better recovery
        diff = latest.resting_hr - baseline_rhr

        if diff <= -5:
            return 90.0
        elif diff <= 0:
            return 70.0
        elif diff <= 3:
            return 50.0
        elif diff <= 7:
            return 30.0
        else:
            return 10.0

    def _score_sleep(self, today: str) -> float:
        """Score sleep quality."""
        sleep = next((s for s in self.sleep_history if s.date == today), None)
        if not sleep:
            return 50.0

        score = 0.0

        # Total sleep (max 40 points)
        if sleep.total_minutes >= 480:
            score += 40
        elif sleep.total_minutes >= 420:
            score += 35
        elif sleep.total_minutes >= 360:
            score += 25
        elif sleep.total_minutes >= 300:
            score += 15
        else:
            score += 5

        # Deep sleep (max 25 points)
        deep_ratio = sleep.deep_minutes / max(sleep.total_minutes, 1)
        if deep_ratio >= 0.2:
            score += 25
        elif deep_ratio >= 0.15:
            score += 20
        elif deep_ratio >= 0.1:
            score += 15
        else:
            score += 5

        # REM sleep (max 20 points)
        rem_ratio = sleep.rem_minutes / max(sleep.total_minutes, 1)
        if rem_ratio >= 0.2:
            score += 20
        elif rem_ratio >= 0.15:
            score += 15
        else:
            score += 5

        # Interruptions (max 15 points)
        if sleep.interruptions == 0:
            score += 15
        elif sleep.interruptions <= 2:
            score += 10
        else:
            score += 5

        return min(100, score)

    def _score_training_load(self, today: str) -> float:
        """Score based on recent training load."""
        if not self.training_history:
            return 70.0

        # Calculate acute:chronic workload ratio
        recent_7d = [t for t in self.training_history if t.date >= today[:8]]  # simplified
        recent_tss = sum(t.tss for t in self.training_history[-7:])
        chronic_tss = sum(t.tss for t in self.training_history[-28:]) / 4 if len(self.training_history) >= 28 else recent_tss

        if chronic_tss == 0:
            return 70.0

        ratio = recent_tss / chronic_tss

        # Sweet spot is 0.8-1.3
        if 0.8 <= ratio <= 1.3:
            return 80.0
        elif ratio < 0.8:
            return 60.0  # undertraining
        elif ratio <= 1.5:
            return 50.0  # slightly over
        else:
            return 20.0  # significantly overtrained

    def _score_trend(self) -> Tuple[float, str]:
        """Score multi-day recovery trend."""
        if len(self.hrv_history) < 3:
            return 50.0, "stable"

        scores = []
        for h in self.hrv_history[-7:]:
            scores.append(h.hrv_score)

        if len(scores) < 3:
            return 50.0, "stable"

        # Simple linear regression slope
        n = len(scores)
        x_vals = list(range(n))
        x_mean = sum(x_vals) / n
        y_mean = sum(scores) / n

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, scores))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)

        if denominator == 0:
            return 50.0, "stable"

        slope = numerator / denominator

        if slope > 2:
            return 80.0, "improving"
        elif slope > 0.5:
            return 65.0, "improving"
        elif slope > -0.5:
            return 50.0, "stable"
        elif slope > -2:
            return 35.0, "declining"
        else:
            return 20.0, "declining"

    def _get_recommendation(self, score: float) -> TrainingRecommendation:
        if score >= 80:
            return TrainingRecommendation.PEAK_SESSION
        elif score >= 65:
            return TrainingRecommendation.HIGH_INTENSITY
        elif score >= 50:
            return TrainingRecommendation.MODERATE_SESSION
        elif score >= 35:
            return TrainingRecommendation.LIGHT_SESSION
        elif score >= 20:
            return TrainingRecommendation.ACTIVE_RECOVERY
        else:
            return TrainingRecommendation.REST_DAY

    def _get_max_intensity(self, score: float) -> float:
        return min(1.0, max(0.0, score / 100))

    def _get_volume_multiplier(self, score: float) -> float:
        if score >= 75:
            return 1.1
        elif score >= 50:
            return 1.0
        elif score >= 30:
            return 0.7
        else:
            return 0.0

    def _count_consecutive_rest(self, today: str) -> int:
        count = 0
        for t in reversed(self.training_history):
            if t.tss < 10:  # effectively a rest day
                count += 1
            else:
                break
        return count

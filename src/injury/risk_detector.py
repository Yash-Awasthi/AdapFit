"""
Injury Risk Detection — predicts muscle injury risk from training metrics.
Uses workload ratios, recovery signals, and RPE to compute risk scores.

Inspired by: athlete-injury-risk-detection (SHAP-explainable injury risk)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class RiskLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class MuscleGroup(Enum):
    QUADRICEPS = "quadriceps"
    HAMSTRINGS = "hamstrings"
    CALVES = "calves"
    GROIN = "groin"
    HIP_FLEXORS = "hip_flexors"
    LOWER_BACK = "lower_back"
    SHOULDERS = "shoulders"
    ROTATOR_CUFF = "rotator_cuff"
    WRISTS = "wrists"
    KNEES = "knees"
    ANKLES = "ankles"
    GENERAL = "general"


@dataclass
class TrainingDay:
    """Training data for a single day."""
    date: datetime
    duration_min: float
    intensity_rpe: float  # 1-10 RPE
    volume_load: float  # Sets × Reps × Weight
    distance_km: float = 0.0
    muscles_worked: list[MuscleGroup] = field(default_factory=list)
    is_high_intensity: bool = False


@dataclass
class RecoveryDay:
    """Recovery data for a single day."""
    date: datetime
    sleep_hours: float
    sleep_quality: float  # 0-1
    hrv_rmssd: float | None = None
    resting_hr: float | None = None
    soreness_score: float = 0.0  # 0-10
    stress_level: float = 0.0  # 0-10
    hydration_pct: float = 1.0  # 0-1


@dataclass
class RiskFactor:
    """A single contributing risk factor."""
    name: str
    value: float
    threshold: float
    weight: float  # How much this contributes to overall risk
    explanation: str


@dataclass
class InjuryRiskResult:
    """Complete injury risk assessment."""
    overall_risk: float  # 0-1
    risk_level: RiskLevel
    risk_factors: list[RiskFactor]
    muscle_specific_risks: dict[str, float]
    recommendations: list[str]
    acwr: float  # Acute:Chronic Workload Ratio
    summary: str


class InjuryRiskDetector:
    """Detects injury risk from training and recovery metrics.

    Based on the ACWR (Acute:Chronic Workload Ratio) model and
    multi-factor risk assessment.
    """

    def __init__(self, acute_window: int = 7, chronic_window: int = 28) -> None:
        self.acute_window = acute_window
        self.chronic_window = chronic_window

        # Risk thresholds
        self._acwr_optimal_low = 0.8
        self._acwr_optimal_high = 1.3
        self._acwr_danger_high = 1.5
        self._acwr_danger_low = 0.5
        self._max_rpe = 10.0
        self._min_sleep_hours = 7.0
        self._min_hrv_pct = 0.8  # 80% of baseline

    def compute_acwr(self, training_days: list[TrainingDay]) -> float:
        """Compute Acute:Chronic Workload Ratio."""
        if not training_days:
            return 1.0

        sorted_days = sorted(training_days, key=lambda d: d.date)
        now = sorted_days[-1].date

        # Acute load (last 7 days)
        acute_cutoff = now - timedelta(days=self.acute_window)
        acute_loads = [
            d.volume_load for d in sorted_days
            if d.date >= acute_cutoff
        ]
        acute_load = sum(acute_loads) / max(len(acute_loads), 1)

        # Chronic load (last 28 days, excluding acute)
        chronic_cutoff = now - timedelta(days=self.chronic_window)
        chronic_loads = [
            d.volume_load for d in sorted_days
            if chronic_cutoff <= d.date < acute_cutoff
        ]
        chronic_load = sum(chronic_loads) / max(len(chronic_loads), 1)

        if chronic_load == 0:
            return 1.0 if acute_load == 0 else 2.0

        return round(acute_load / chronic_load, 3)

    def compute_risk_factors(
        self,
        training_days: list[TrainingDay],
        recovery_days: list[RecoveryDay],
    ) -> list[RiskFactor]:
        """Compute individual risk factors."""
        factors: list[RiskFactor] = []

        # 1. ACWR
        acwr = self.compute_acwr(training_days)
        if acwr > self._acwr_danger_high:
            factors.append(RiskFactor(
                name="acute_chronic_ratio",
                value=acwr,
                threshold=self._acwr_optimal_high,
                weight=0.30,
                explanation=f"ACWR of {acwr:.2f} indicates sudden workload spike — injury risk elevated.",
            ))
        elif acwr < self._acwr_danger_low:
            factors.append(RiskFactor(
                name="acute_chronic_ratio",
                value=acwr,
                threshold=self._acwr_danger_low,
                weight=0.20,
                explanation=f"ACWR of {acwr:.2f} indicates undertraining — detrainning risk.",
            ))

        # 2. RPE spike
        if training_days:
            recent_rpe = [d.intensity_rpe for d in training_days[-3:]]
            avg_rpe = sum(recent_rpe) / len(recent_rpe)
            if avg_rpe >= 8.5:
                factors.append(RiskFactor(
                    name="high_rpe",
                    value=avg_rpe,
                    threshold=8.5,
                    weight=0.20,
                    explanation=f"Average RPE of {avg_rpe:.1f} indicates very high training intensity.",
                ))

        # 3. Sleep deficit
        if recovery_days:
            recent_sleep = [r.sleep_hours for r in recovery_days[-7:]]
            avg_sleep = sum(recent_sleep) / len(recent_sleep)
            if avg_sleep < self._min_sleep_hours:
                deficit = self._min_sleep_hours - avg_sleep
                factors.append(RiskFactor(
                    name="sleep_deficit",
                    value=avg_sleep,
                    threshold=self._min_sleep_hours,
                    weight=0.20,
                    explanation=f"Average sleep of {avg_sleep:.1f}h is below the 7h minimum for recovery.",
                ))

        # 4. High soreness
        if recovery_days:
            recent_soreness = [r.soreness_score for r in recovery_days[-3:]]
            avg_soreness = sum(recent_soreness) / len(recent_soreness)
            if avg_soreness >= 7:
                factors.append(RiskFactor(
                    name="high_soreness",
                    value=avg_soreness,
                    threshold=7.0,
                    weight=0.15,
                    explanation=f"Average soreness of {avg_soreness:.1f}/10 suggests incomplete recovery.",
                ))

        # 5. HRV suppression
        if recovery_days:
            hrv_values = [r.hrv_rmssd for r in recovery_days[-7:] if r.hrv_rmssd is not None]
            if len(hrv_values) >= 3:
                baseline_hrv = sum(hrv_values) / len(hrv_values)
                recent_hrv = sum(hrv_values[-3:]) / max(len(hrv_values[-3:]), 1)
                if baseline_hrv > 0 and recent_hrv / baseline_hrv < self._min_hrv_pct:
                    factors.append(RiskFactor(
                        name="hrv_suppression",
                        value=recent_hrv,
                        threshold=baseline_hrv * self._min_hrv_pct,
                        weight=0.15,
                        explanation="HRV is suppressed, indicating autonomic stress or incomplete recovery.",
                    ))

        # 6. Hydration
        if recovery_days:
            recent_hydration = [r.hydration_pct for r in recovery_days[-3:]]
            avg_hydration = sum(recent_hydration) / len(recent_hydration)
            if avg_hydration < 0.8:
                factors.append(RiskFactor(
                    name="dehydration",
                    value=avg_hydration,
                    threshold=0.8,
                    weight=0.10,
                    explanation="Dehydration increases muscle injury risk and reduces performance.",
                ))

        return factors

    def _compute_muscle_risks(
        self,
        training_days: list[TrainingDay],
        recovery_days: list[RecoveryDay],
    ) -> dict[str, float]:
        """Compute per-muscle-group risk scores."""
        muscle_loads: dict[MuscleGroup, list[float]] = {}
        for day in training_days[-14:]:
            for muscle in day.muscles_worked:
                muscle_loads.setdefault(muscle, []).append(day.volume_load)

        risks: dict[str, float] = {}
        for muscle, loads in muscle_loads.items():
            if len(loads) < 2:
                continue
            # Simple overload detection
            recent = loads[-3:] if len(loads) >= 3 else loads
            chronic_avg = sum(loads) / len(loads)
            acute_avg = sum(recent) / len(recent)

            if chronic_avg > 0:
                ratio = acute_avg / chronic_avg
                risk = max(0, min(1, (ratio - 1.0) * 2))
            else:
                risk = 0

            risks[muscle.value] = round(risk, 3)

        return risks

    def _generate_recommendations(
        self, factors: list[RiskFactor], acwr: float
    ) -> list[str]:
        """Generate actionable recommendations based on risk factors."""
        recs = []
        factor_names = {f.name for f in factors}

        if "acute_chronic_ratio" in factor_names:
            if acwr > 1.5:
                recs.append("Reduce training volume by 20-30% this week to bring ACWR back to safe range (0.8-1.3).")
            elif acwr < 0.5:
                recs.append("Gradually increase training load by 5-10% per week to rebuild chronic base.")

        if "high_rpe" in factor_names:
            recs.append("Lower training intensity. Aim for RPE 6-7 for most sessions.")

        if "sleep_deficit" in factor_names:
            recs.append("Prioritize 7-9 hours of sleep. Set a consistent bedtime and wake time.")

        if "high_soreness" in factor_names:
            recs.append("Add an active recovery day with light movement and stretching.")

        if "hrv_suppression" in factor_names:
            recs.append("HRV is low — consider a rest day or very light training today.")

        if "dehydration" in factor_names:
            recs.append("Increase water intake to at least 35ml per kg bodyweight daily.")

        if not recs:
            recs.append("Risk factors are within normal range. Maintain current training approach.")

        return recs

    def assess(
        self,
        training_days: list[TrainingDay],
        recovery_days: list[RecoveryDay],
    ) -> InjuryRiskResult:
        """Perform complete injury risk assessment."""
        factors = self.compute_risk_factors(training_days, recovery_days)
        acwr = self.compute_acwr(training_days)
        muscle_risks = self._compute_muscle_risks(training_days, recovery_days)

        # Weighted overall risk
        overall_risk = sum(f.weight * min(f.value / max(f.threshold, 0.01), 2.0) / 2.0 for f in factors)
        overall_risk = min(1.0, max(0.0, overall_risk))

        if overall_risk >= 0.75:
            risk_level = RiskLevel.CRITICAL
        elif overall_risk >= 0.5:
            risk_level = RiskLevel.HIGH
        elif overall_risk >= 0.25:
            risk_level = RiskLevel.MODERATE
        else:
            risk_level = RiskLevel.LOW

        recommendations = self._generate_recommendations(factors, acwr)

        summary = (
            f"Injury risk: {risk_level.value.upper()} ({overall_risk:.0%}). "
            f"ACWR: {acwr:.2f}. "
            f"{len(factors)} active risk factors. "
            f"{recommendations[0] if recommendations else ''}"
        )

        return InjuryRiskResult(
            overall_risk=round(overall_risk, 3),
            risk_level=risk_level,
            risk_factors=factors,
            muscle_specific_risks=muscle_risks,
            recommendations=recommendations,
            acwr=acwr,
            summary=summary,
        )

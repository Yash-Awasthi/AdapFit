"""
Sleep Stage Classifier — classifies sleep stages from wearable sensor data.
Computes sleep architecture metrics, efficiency, and quality scores.

Inspired by: asleep (wearable sleep classification)
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, IntEnum
from typing import Any


class SleepStage(IntEnum):
    """PSG-standard sleep stages."""
    WAKE = 0
    NREM1 = 1  # Light sleep
    NREM2 = 2  # Core sleep
    NREM3 = 3  # Deep sleep
    REM = 4    # Rapid Eye Movement


class SleepQuality(Enum):
    """Overall sleep quality rating."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    VERY_POOR = "very_poor"


from enum import Enum


@dataclass
class Epoch:
    """A single 30-second epoch of sleep data."""
    timestamp: datetime
    stage: SleepStage
    acceleration_magnitude: float = 0.0  # g
    heart_rate: float | None = None
    spo2: float | None = None


@dataclass
class SleepArchitecture:
    """Detailed breakdown of sleep stages."""
    total_time_in_bed_min: float
    total_sleep_time_min: float
    sleep_onset_latency_min: float  # Time to fall asleep
    wake_after_sleep_onset_min: float  # WASO
    sleep_efficiency: float  # TST / TIB
    num_awakenings: int
    num_stage_transitions: int

    # Stage durations (minutes)
    wake_min: float
    nrem1_min: float
    nrem2_min: float
    nrem3_min: float
    rem_min: float

    # Stage percentages (of TST)
    wake_pct: float
    nrem1_pct: float
    nrem2_pct: float
    nrem3_pct: float
    rem_pct: float

    # REM metrics
    rem_latency_min: float  # Time from sleep onset to first REM
    num_rem_periods: int


@dataclass
class SleepAnalysisResult:
    """Complete sleep analysis result."""
    sleep_date: str
    quality: SleepQuality
    quality_score: float  # 0-100
    architecture: SleepArchitecture
    quality_metrics: dict[str, float]
    recommendations: list[str]
    summary: str


class SleepStageClassifier:
    """Classifies sleep stages from accelerometer data using rule-based heuristics.

    Uses movement intensity, heart rate, and temporal patterns to
    classify epochs into sleep stages.
    """

    EPOCH_DURATION_SEC = 30

    def __init__(
        self,
        movement_threshold_low: float = 0.05,  # g
        movement_threshold_high: float = 0.25,  # g
        hr_deep_threshold: float = 60.0,
        hr_rem_threshold: float = 65.0,
    ) -> None:
        self.movement_threshold_low = movement_threshold_low
        self.movement_threshold_high = movement_threshold_high
        self.hr_deep_threshold = hr_deep_threshold
        self.hr_rem_threshold = hr_rem_threshold

    def classify_epoch(self, accel_magnitude: float, hr: float | None = None) -> SleepStage:
        """Classify a single epoch based on movement and heart rate."""
        if accel_magnitude > self.movement_threshold_high:
            return SleepStage.WAKE
        elif accel_magnitude > self.movement_threshold_low:
            return SleepStage.NREM1
        elif hr is not None and hr < self.hr_deep_threshold:
            return SleepStage.NREM3
        elif hr is not None and hr > self.hr_rem_threshold:
            return SleepStage.REM
        else:
            return SleepStage.NREM2

    def classify_session(self, epochs: list[Epoch]) -> list[Epoch]:
        """Classify all epochs and apply temporal smoothing."""
        classified = []
        for ep in epochs:
            stage = self.classify_epoch(ep.acceleration_magnitude, ep.heart_rate)
            classified.append(Epoch(
                timestamp=ep.timestamp,
                stage=stage,
                acceleration_magnitude=ep.acceleration_magnitude,
                heart_rate=ep.heart_rate,
            ))

        # Apply 3-epoch median smoothing to reduce noise
        if len(classified) >= 3:
            smoothed = []
            for i in range(len(classified)):
                if i == 0 or i == len(classified) - 1:
                    smoothed.append(classified[i])
                else:
                    window = [classified[i-1].stage, classified[i].stage, classified[i+1].stage]
                    median_stage = sorted(window)[1]
                    smoothed.append(Epoch(
                        timestamp=classified[i].timestamp,
                        stage=median_stage,
                        acceleration_magnitude=classified[i].acceleration_magnitude,
                        heart_rate=classified[i].heart_rate,
                    ))
            classified = smoothed

        return classified

    def _compute_architecture(self, epochs: list[Epoch], time_in_bed_min: float) -> SleepArchitecture:
        """Compute detailed sleep architecture from classified epochs."""
        n = len(epochs)
        total_epochs = n
        epoch_min = self.EPOCH_DURATION_SEC / 60.0

        # Count stages
        stage_counts = Counter(ep.stage for ep in epochs)

        wake_min = stage_counts.get(SleepStage.WAKE, 0) * epoch_min
        nrem1_min = stage_counts.get(SleepStage.NREM1, 0) * epoch_min
        nrem2_min = stage_counts.get(SleepStage.NREM2, 0) * epoch_min
        nrem3_min = stage_counts.get(SleepStage.NREM3, 0) * epoch_min
        rem_min = stage_counts.get(SleepStage.REM, 0) * epoch_min

        total_sleep = nrem1_min + nrem2_min + nrem3_min + rem_min
        sleep_onset = self._find_sleep_onset(epochs) * epoch_min
        waso = self._find_waso(epochs) * epoch_min
        efficiency = total_sleep / max(time_in_bed_min, 1)

        # Count awakenings (wake episodes > 1 epoch after sleep onset)
        awakenings = self._count_awakenings(epochs)
        transitions = self._count_transitions(epochs)

        # REM metrics
        rem_latency = self._find_rem_latency(epochs) * epoch_min
        num_rem_periods = self._count_rem_periods(epochs)

        # Percentages
        tst = max(total_sleep, 1)
        return SleepArchitecture(
            total_time_in_bed_min=round(time_in_bed_min, 1),
            total_sleep_time_min=round(total_sleep, 1),
            sleep_onset_latency_min=round(sleep_onset, 1),
            wake_after_sleep_onset_min=round(waso, 1),
            sleep_efficiency=round(efficiency, 3),
            num_awakenings=awakenings,
            num_stage_transitions=transitions,
            wake_min=round(wake_min, 1),
            nrem1_min=round(nrem1_min, 1),
            nrem2_min=round(nrem2_min, 1),
            nrem3_min=round(nrem3_min, 1),
            rem_min=round(rem_min, 1),
            wake_pct=round(wake_min / max(time_in_bed_min, 1) * 100, 1),
            nrem1_pct=round(nrem1_min / tst * 100, 1),
            nrem2_pct=round(nrem2_min / tst * 100, 1),
            nrem3_pct=round(nrem3_min / tst * 100, 1),
            rem_pct=round(rem_min / tst * 100, 1),
            rem_latency_min=round(rem_latency, 1),
            num_rem_periods=num_rem_periods,
        )

    def _find_sleep_onset(self, epochs: list[Epoch]) -> int:
        """Find the epoch index where sleep onset occurs (3+ consecutive non-wake)."""
        threshold = 3
        k = 0
        for i, ep in enumerate(epochs):
            if ep.stage != SleepStage.WAKE:
                k += 1
                if k >= threshold:
                    return i - threshold + 1
            else:
                k = 0
        return 0

    def _find_waso(self, epochs: list[Epoch]) -> int:
        """Find total wake-after-sleep-onset epochs."""
        onset = self._find_sleep_onset(epochs)
        return sum(1 for ep in epochs[onset:] if ep.stage == SleepStage.WAKE)

    def _count_awakenings(self, epochs: list[Epoch]) -> int:
        """Count awakening episodes (2+ consecutive wake epochs during sleep)."""
        onset = self._find_sleep_onset(epochs)
        count = 0
        in_wake = False
        for ep in epochs[onset:]:
            if ep.stage == SleepStage.WAKE:
                if not in_wake:
                    count += 1
                    in_wake = True
            else:
                in_wake = False
        return count

    def _count_transitions(self, epochs: list[Epoch]) -> int:
        """Count stage transitions."""
        transitions = 0
        for i in range(1, len(epochs)):
            if epochs[i].stage != epochs[i-1].stage:
                transitions += 1
        return transitions

    def _find_rem_latency(self, epochs: list[Epoch]) -> int:
        """Find epoch of first REM period after sleep onset."""
        onset = self._find_sleep_onset(epochs)
        for i, ep in enumerate(epochs[onset:], start=onset):
            if ep.stage == SleepStage.REM:
                return i - onset
        return len(epochs) - onset

    def _count_rem_periods(self, epochs: list[Epoch]) -> int:
        """Count distinct REM periods."""
        onset = self._find_sleep_onset(epochs)
        count = 0
        in_rem = False
        for ep in epochs[onset:]:
            if ep.stage == SleepStage.REM:
                if not in_rem:
                    count += 1
                    in_rem = True
            elif ep.stage != SleepStage.WAKE:
                in_rem = False
        return count

    def _score_quality(self, arch: SleepArchitecture) -> tuple[SleepQuality, float]:
        """Score overall sleep quality (0-100)."""
        score = 100.0

        # Efficiency penalty
        if arch.sleep_efficiency < 0.85:
            score -= (0.85 - arch.sleep_efficiency) * 200
        elif arch.sleep_efficiency > 0.95:
            score += 5

        # Duration penalty (ideal: 7-9 hours)
        hours = arch.total_sleep_time_min / 60
        if hours < 6:
            score -= (6 - hours) * 10
        elif hours > 10:
            score -= (hours - 10) * 5

        # Deep sleep bonus (13-23% ideal)
        if arch.nrem3_pct >= 13:
            score += 5
        elif arch.nrem3_pct < 10:
            score -= (10 - arch.nrem3_pct) * 3

        # REM bonus (20-25% ideal)
        if 20 <= arch.rem_pct <= 25:
            score += 5
        elif arch.rem_pct < 15:
            score -= (15 - arch.rem_pct) * 2

        # Awakening penalty
        if arch.num_awakenings > 5:
            score -= (arch.num_awakenings - 5) * 3

        # Sleep onset penalty
        if arch.sleep_onset_latency_min > 30:
            score -= (arch.sleep_onset_latency_min - 30) * 0.5

        score = max(0, min(100, score))

        if score >= 85:
            quality = SleepQuality.EXCELLENT
        elif score >= 70:
            quality = SleepQuality.GOOD
        elif score >= 55:
            quality = SleepQuality.FAIR
        elif score >= 40:
            quality = SleepQuality.POOR
        else:
            quality = SleepQuality.VERY_POOR

        return quality, round(score, 1)

    def _generate_recommendations(self, arch: SleepArchitecture, quality: SleepQuality) -> list[str]:
        """Generate personalized sleep improvement recommendations."""
        recs = []

        if arch.sleep_efficiency < 0.85:
            recs.append("Your sleep efficiency is below 85%. Try reducing time in bed to match actual sleep time.")
        if arch.sleep_onset_latency_min > 20:
            recs.append("It takes you over 20 minutes to fall asleep. Consider a pre-sleep wind-down routine.")
        if arch.nrem3_pct < 13:
            recs.append("Deep sleep is below optimal. Avoid alcohol and caffeine before bed.")
        if arch.rem_pct < 18:
            recs.append("REM sleep is low. Maintain consistent sleep/wake times and avoid late-night screens.")
        if arch.num_awakenings > 5:
            recs.append("Frequent awakenings detected. Check room temperature (ideal: 65-68°F).")
        if arch.wake_after_sleep_onset_min > 30:
            recs.append("Significant wake time after sleep onset. Consider relaxation techniques before bed.")
        if arch.total_sleep_time_min < 420:
            recs.append("Total sleep is under 7 hours. Aim for 7-9 hours for optimal recovery.")

        if not recs:
            recs.append("Great sleep! Maintain your current habits.")

        return recs

    def analyze(
        self,
        epochs: list[Epoch],
        time_in_bed_min: float | None = None,
    ) -> SleepAnalysisResult:
        """Perform full sleep analysis on a set of epochs."""
        classified = self.classify_session(epochs)

        if time_in_bed_min is None:
            time_in_bed_min = len(classified) * self.EPOCH_DURATION_SEC / 60.0

        arch = self._compute_architecture(classified, time_in_bed_min)
        quality, score = self._score_quality(arch)
        recommendations = self._generate_recommendations(arch, quality)

        quality_metrics = {
            "efficiency": arch.sleep_efficiency,
            "deep_sleep_pct": arch.nrem3_pct,
            "rem_pct": arch.rem_pct,
            "sleep_onset_min": arch.sleep_onset_latency_min,
            "waso_min": arch.wake_after_sleep_onset_min,
            "awakenings": arch.num_awakenings,
        }

        sleep_date = classified[0].timestamp.strftime("%Y-%m-%d") if classified else "unknown"

        return SleepAnalysisResult(
            sleep_date=sleep_date,
            quality=quality,
            quality_score=score,
            architecture=arch,
            quality_metrics=quality_metrics,
            recommendations=recommendations,
            summary=(
                f"Slept {arch.total_sleep_time_min / 60:.1f}h with {arch.sleep_efficiency * 100:.0f}% efficiency. "
                f"Deep: {arch.nrem3_pct:.0f}%, REM: {arch.rem_pct:.0f}%, "
                f"Quality: {quality.value} ({score}/100)."
            ),
        )

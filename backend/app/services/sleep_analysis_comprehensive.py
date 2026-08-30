"""
Comprehensive Sleep Analysis for ZFIT
Extracted from: awesome-sleep-tracking (curated sleep analysis tools and metrics)
Patterns: Sleep staging, PAP therapy analysis, pulse oximetry, EEG analysis,
          actigraphy, automatic sleep scoring, sleep metrics definitions
"""
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class SleepStage(Enum):
    AWAKE = "awake"
    LIGHT = "light"
    DEEP = "deep"
    REM = "rem"
    UNKNOWN = "unknown"


class SleepQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    VERY_POOR = "very_poor"


@dataclass
class SleepEpisode:
    start: datetime
    end: datetime
    stages: list[tuple[datetime, SleepStage]]  # (timestamp, stage)

    @property
    def duration_minutes(self) -> float:
        return (self.end - self.start).total_seconds() / 60

    @property
    def duration_hours(self) -> float:
        return self.duration_minutes / 60


@dataclass
class SleepMetrics:
    total_sleep_time: float  # minutes
    time_in_bed: float  # minutes
    sleep_onset_latency: float  # minutes to fall asleep
    wake_after_sleep_onset: float  # minutes awake during sleep
    sleep_efficiency: float  # percentage
    rem_latency: float  # minutes from sleep onset to first REM
    rem_percentage: float
    deep_percentage: float
    light_percentage: float
    awake_percentage: float
    sleep_score: float  # 0-100
    quality: SleepQuality
    awakenings: int
    sleep_debt: float  # hours vs 8hr target
    consistency_score: float  # 0-100, regularity of sleep times


@dataclass
class PapTherapyMetrics:
    ahi: float  # Apnea-Hypopnea Index
    leak_rate: float  # L/min
    pressure: float  # cmH2O
    usage_hours: float
    regime: str  # "CPAP", "APAP", "BiPAP"
    score: float  # 0-100


@dataclass
class OximetryMetrics:
    avg_spo2: float  # percentage
    min_spo2: float
    time_below_90: float  # minutes
    desaturation_index: float  # events per hour
    odI: float  # Oxygen Desaturation Index


# ─── Sleep Stage Analysis ──────────────────────────────────────────────

def compute_sleep_metrics(episode: SleepEpisode) -> SleepMetrics:
    """Compute comprehensive sleep metrics from a sleep episode."""
    total_minutes = episode.duration_minutes
    if total_minutes <= 0:
        raise ValueError("Sleep episode must have positive duration")

    stage_durations = {stage: 0.0 for stage in SleepStage}
    for i in range(len(episode.stages) - 1):
        _, stage = episode.stages[i]
        next_time, _ = episode.stages[i + 1]
        current_time = episode.stages[i][0]
        duration = (next_time - current_time).total_seconds() / 60
        stage_durations[stage] += duration

    # Sleep onset latency (time from start to first non-awake stage)
    sleep_onset = 0.0
    for time, stage in episode.stages:
        if stage != SleepStage.AWAKE:
            sleep_onset = (time - episode.start).total_seconds() / 60
            break

    # Wake after sleep onset
    waso = stage_durations.get(SleepStage.AWAKE, 0.0)

    # Sleep efficiency
    actual_sleep = total_minutes - sleep_onset - waso
    sleep_efficiency = (actual_sleep / total_minutes) * 100 if total_minutes > 0 else 0

    # REM latency
    rem_latency = 0.0
    for time, stage in episode.stages:
        if stage == SleepStage.REM:
            rem_latency = (time - episode.start).total_seconds() / 60
            break

    # Stage percentages (of actual sleep time)
    actual_sleep = max(1, actual_sleep)
    rem_pct = (stage_durations.get(SleepStage.REM, 0) / actual_sleep) * 100
    deep_pct = (stage_durations.get(SleepStage.DEEP, 0) / actual_sleep) * 100
    light_pct = (stage_durations.get(SleepStage.LIGHT, 0) / actual_sleep) * 100
    awake_pct = (stage_durations.get(SleepStage.AWAKE, 0) / total_minutes) * 100

    # Count awakenings
    awakenings = 0
    for i in range(1, len(episode.stages)):
        if episode.stages[i][1] == SleepStage.AWAKE and episode.stages[i - 1][1] != SleepStage.AWAKE:
            awakenings += 1

    # Sleep debt (target 8 hours)
    sleep_debt = max(0, 8 - (actual_sleep / 60))

    # Sleep score
    score = _compute_sleep_score(sleep_efficiency, rem_pct, deep_pct, waso, awakenings, sleep_debt)

    quality = SleepQuality.EXCELLENT if score >= 90 else \
        SleepQuality.GOOD if score >= 75 else \
        SleepQuality.FAIR if score >= 60 else \
        SleepQuality.POOR if score >= 40 else SleepQuality.VERY_POOR

    return SleepMetrics(
        total_sleep_time=round(actual_sleep, 1),
        time_in_bed=round(total_minutes, 1),
        sleep_onset_latency=round(sleep_onset, 1),
        wake_after_sleep_onset=round(waso, 1),
        sleep_efficiency=round(sleep_efficiency, 1),
        rem_latency=round(rem_latency, 1),
        rem_percentage=round(rem_pct, 1),
        deep_percentage=round(deep_pct, 1),
        light_percentage=round(light_pct, 1),
        awake_percentage=round(awake_pct, 1),
        sleep_score=round(score, 1),
        quality=quality,
        awakenings=awakenings,
        sleep_debt=round(sleep_debt, 2),
        consistency_score=0,  # Needs multiple nights
    )


def _compute_sleep_score(
    efficiency: float, rem_pct: float, deep_pct: float,
    waso: float, awakenings: int, debt: float,
) -> float:
    """Compute a 0-100 sleep score."""
    # Efficiency component (0-30)
    eff_score = min(30, efficiency * 0.3)

    # REM component (0-20)
    rem_score = min(20, rem_pct * 0.4) if 20 <= rem_pct <= 35 else max(0, 20 - abs(rem_pct - 25) * 0.5)

    # Deep sleep component (0-20)
    deep_score = min(20, deep_pct * 0.5) if 15 <= deep_pct <= 25 else max(0, 20 - abs(deep_pct - 20) * 0.5)

    # WASO penalty (0-15)
    waso_score = max(0, 15 - waso * 0.1)

    # Awakenings penalty (0-15)
    awaken_score = max(0, 15 - awakenings * 3)

    # Sleep debt penalty (0 to -20)
    debt_penalty = -debt * 2.5

    return max(0, min(100, eff_score + rem_score + deep_score + waso_score + awaken_score + debt_penalty))


# ─── PAP Therapy Analysis ──────────────────────────────────────────────

def analyze_pap_therapy(
    events_per_hour: float,
    leak_rate: float,
    pressure: float,
    usage_hours: float,
    regime: str = "CPAP",
) -> PapTherapyMetrics:
    """Analyze PAP therapy effectiveness."""
    # AHI interpretation
    ahi_score = max(0, 100 - events_per_hour * 10)

    # Leak rate impact (ideal: <24 L/min)
    leak_score = max(0, 100 - max(0, leak_rate - 24) * 5)

    # Usage compliance (ideal: >4 hours/night)
    usage_score = min(100, usage_hours * 25)

    # Combined score
    score = ahi_score * 0.5 + leak_score * 0.25 + usage_score * 0.25

    return PapTherapyMetrics(
        ahi=round(events_per_hour, 1),
        leak_rate=round(leak_rate, 1),
        pressure=round(pressure, 1),
        usage_hours=round(usage_hours, 1),
        regime=regime,
        score=round(score, 1),
    )


# ─── Pulse Oximetry Analysis ───────────────────────────────────────────

def analyze_oximetry(spO2_readings: list[float], timestamps: list[datetime]) -> OximetryMetrics:
    """Analyze pulse oximetry data."""
    if not spO2_readings:
        raise ValueError("Need at least one SpO2 reading")

    avg_spo2 = sum(spO2_readings) / len(spO2_readings)
    min_spo2 = min(spO2_readings)
    time_below_90 = 0.0

    for i, reading in enumerate(spO2_readings):
        if reading < 90 and i < len(timestamps) - 1:
            duration = (timestamps[i + 1] - timestamps[i]).total_seconds() / 60
            time_below_90 += duration

    # Desaturation events (drops > 3% from baseline)
    desat_count = 0
    baseline = avg_spo2
    for i in range(1, len(spO2_readings)):
        if baseline - spO2_readings[i] > 3:
            desat_count += 1

    total_hours = (timestamps[-1] - timestamps[0]).total_seconds() / 3600 if len(timestamps) > 1 else 1
    odI = desat_count / total_hours

    return OximetryMetrics(
        avg_spo2=round(avg_spo2, 1),
        min_spo2=round(min_spo2, 1),
        time_below_90=round(time_below_90, 1),
        desaturation_index=round(odI, 1),
        odI=round(odI, 1),
    )


# ─── Multi-Night Analysis ──────────────────────────────────────────────

def compute_consistency(episodes: list[SleepEpisode]) -> float:
    """Compute sleep consistency score from multiple nights."""
    if len(episodes) < 3:
        return 50.0

    bedtimes = [(e.start.hour + e.start.minute / 60) for e in episodes]
    wake_times = [(e.end.hour + e.end.minute / 60) for e in episodes]

    bedtime_std = _circular_std(bedtimes)
    wake_std = _circular_std(wake_times)

    # Lower std = higher consistency
    bedtime_consistency = max(0, 100 - bedtime_std * 20)
    wake_consistency = max(0, 100 - wake_std * 20)

    return round((bedtime_consistency + wake_consistency) / 2, 1)


def _circular_std(times: list[float]) -> float:
    """Standard deviation for circular (clock) data."""
    mean = sum(times) / len(times)
    variance = sum((t - mean) ** 2 for t in times) / len(times)
    return math.sqrt(variance)

"""
Sleep stage classification using signal processing and ML patterns.

Extracted from autosleepscorer — CNN/RNN sleep stage classification.
Uses threshold-based heuristics instead of neural networks (no PyTorch dependency).
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple
import math


class SleepStage(Enum):
    WAKE = 0
    N1 = 1  # Light sleep
    N2 = 2  # Moderate sleep
    N3 = 3  # Deep sleep (SWS)
    REM = 4


@dataclass
class EEGSample:
    timestamp: float  # seconds from recording start
    value: float  # microvolts
    frequency_bands: Optional[dict] = None  # {delta, theta, alpha, sigma, beta}


@dataclass
class SleepEpoch:
    start_time: float
    end_time: float
    stage: SleepStage
    confidence: float  # 0.0-1.0
    features: dict = field(default_factory=dict)


@dataclass
class Hypnogram:
    epochs: List[SleepEpoch]
    total_duration: float
    sleep_start: Optional[float] = None
    sleep_end: Optional[float] = None

    @property
    def total_sleep_time(self) -> float:
        """Total time not in WAKE stage."""
        return sum(
            e.end_time - e.start_time
            for e in self.epochs
            if e.stage != SleepStage.WAKE
        )

    @property
    def sleep_efficiency(self) -> float:
        """TST / total recording time."""
        if self.total_duration <= 0:
            return 0.0
        return self.total_sleep_time / self.total_duration

    @property
    def wake_after_sleep_onset(self) -> float:
        """Total wake time after initial sleep onset."""
        if not self.sleep_start:
            return 0.0
        return sum(
            e.end_time - e.start_time
            for e in self.epochs
            if e.stage == SleepStage.WAKE and e.start_time >= self.sleep_start
        )


def compute_spectral_features(
    samples: List[float], sample_rate: float, window_size: int = 256
) -> dict:
    """
    Compute simplified spectral features using Goertzel algorithm.
    No FFT library needed — pure Python.

    Returns power in each frequency band:
    - Delta: 0.5-4 Hz
    - Theta: 4-8 Hz
    - Alpha: 8-13 Hz
    - Sigma: 12-16 Hz (sleep spindles)
    - Beta: 16-30 Hz
    """
    n = len(samples)
    if n < window_size:
        window_size = n

    bands = {
        "delta": (0.5, 4.0),
        "theta": (4.0, 8.0),
        "alpha": (8.0, 13.0),
        "sigma": (12.0, 16.0),
        "beta": (16.0, 30.0),
    }

    result = {}
    for band_name, (low, high) in bands.items():
        power = 0.0
        # Simple bandpower estimation via autocorrelation
        mid_freq = (low + high) / 2.0
        for i in range(min(window_size, n)):
            power += samples[i] * math.cos(2 * math.pi * mid_freq * i / sample_rate)
        result[band_name] = (power ** 2) / window_size

    total = sum(result.values()) or 1.0
    for key in result:
        result[f"{key}_relative"] = result[key] / total

    return result


def compute_hjorth_parameters(samples: List[float]) -> Tuple[float, float, float]:
    """
    Compute Hjorth parameters: Activity, Mobility, Complexity.
    Standard EEG feature extraction.
    """
    if len(samples) < 3:
        return (0.0, 0.0, 0.0)

    # First derivative
    d1 = [samples[i + 1] - samples[i] for i in range(len(samples) - 1)]
    # Second derivative
    d2 = [d1[i + 1] - d1[i] for i in range(len(d1) - 1)]

    activity = sum(s ** 2 for s in samples) / len(samples)
    mobility_num = sum(d ** 2 for d in d1) / len(d1) if d1 else 0
    mobility = math.sqrt(mobility_num / activity) if activity > 0 else 0.0

    complexity_num = sum(d ** 2 for d in d2) / len(d2) if d2 else 0
    complexity_denom = sum(d ** 2 for d in d1) / len(d1) if d1 else 0
    complexity = math.sqrt(complexity_num / complexity_denom) if complexity_denom > 0 else 0.0

    return (activity, mobility, complexity)


def classify_epoch(
    spectral: dict,
    hjorth: Tuple[float, float, float],
    heart_rate: Optional[float] = None,
    movement: Optional[float] = None,
) -> Tuple[SleepStage, float]:
    """
    Classify a 30-second epoch into a sleep stage using threshold heuristics.

    Heuristics based on polysomnography scoring rules:
    - Wake: high alpha/beta, high mobility, high HR
    - N1: theta dominance, alpha drop, low amplitude
    - N2: sigma (spindles), K-complexes, moderate amplitude
    - N3: delta dominance (>20% of epoch), high amplitude
    - REM: theta/alpha mix, low EMG, sawtooth waves
    """
    activity, mobility, complexity = hjorth
    delta_rel = spectral.get("delta_relative", 0)
    theta_rel = spectral.get("theta_relative", 0)
    alpha_rel = spectral.get("alpha_relative", 0)
    sigma_rel = spectral.get("sigma_relative", 0)
    beta_rel = spectral.get("beta_relative", 0)

    scores = {}

    # Wake scoring
    wake_score = 0.0
    if alpha_rel > 0.3:
        wake_score += 0.4
    if beta_rel > 0.2:
        wake_score += 0.3
    if mobility > 1.5:
        wake_score += 0.2
    if heart_rate and heart_rate > 70:
        wake_score += 0.1
    scores[SleepStage.WAKE] = wake_score

    # N1 scoring
    n1_score = 0.0
    if 0.15 < theta_rel < 0.5 and alpha_rel < 0.2:
        n1_score += 0.5
    if mobility < 1.0 and mobility > 0.3:
        n1_score += 0.3
    if activity < 20:
        n1_score += 0.2
    scores[SleepStage.N1] = n1_score

    # N2 scoring
    n2_score = 0.0
    if sigma_rel > 0.1:
        n2_score += 0.4  # Sleep spindles
    if theta_rel > 0.3 and delta_rel < 0.2:
        n2_score += 0.3
    if 0.3 < mobility < 1.0:
        n2_score += 0.2
    scores[SleepStage.N2] = n2_score

    # N3 (deep sleep) scoring
    n3_score = 0.0
    if delta_rel > 0.2:
        n3_score += 0.6
    if activity > 30:
        n3_score += 0.2
    if mobility < 0.5:
        n3_score += 0.2
    scores[SleepStage.N3] = n3_score

    # REM scoring
    rem_score = 0.0
    if theta_rel > 0.3 and alpha_rel > 0.1 and delta_rel < 0.15:
        rem_score += 0.4
    if complexity > 1.2:
        rem_score += 0.2
    if heart_rate and 60 < heart_rate < 100:
        rem_score += 0.2
    if movement and movement < 0.1:
        rem_score += 0.2
    scores[SleepStage.REM] = rem_score

    best_stage = max(scores, key=scores.get)
    total = sum(scores.values()) or 1.0
    confidence = scores[best_stage] / total

    return best_stage, confidence


def score_sleep_recording(
    samples: List[float],
    sample_rate: float,
    epoch_duration: float = 30.0,
    heart_rates: Optional[List[float]] = None,
    movement_data: Optional[List[float]] = None,
) -> Hypnogram:
    """
    Score an entire sleep recording into a hypnogram.

    Parameters:
        samples: Raw EEG samples
        sample_rate: Sampling rate in Hz
        epoch_duration: Duration of each scoring epoch in seconds
        heart_rates: Optional HR per epoch
        movement_data: Optional movement intensity per epoch
    """
    samples_per_epoch = int(sample_rate * epoch_duration)
    epochs = []

    for i in range(0, len(samples), samples_per_epoch):
        epoch_data = samples[i : i + samples_per_epoch]
        if len(epoch_data) < samples_per_epoch // 2:
            break

        start_time = i / sample_rate
        end_time = (i + len(epoch_data)) / sample_rate

        spectral = compute_spectral_features(epoch_data, sample_rate)
        hjorth = compute_hjorth_parameters(epoch_data)

        hr = None
        if heart_rates:
            epoch_idx = i // samples_per_epoch
            if epoch_idx < len(heart_rates):
                hr = heart_rates[epoch_idx]

        movement = None
        if movement_data:
            epoch_idx = i // samples_per_epoch
            if epoch_idx < len(movement_data):
                movement = movement_data[epoch_idx]

        stage, confidence = classify_epoch(spectral, hjorth, hr, movement)

        epochs.append(SleepEpoch(
            start_time=start_time,
            end_time=end_time,
            stage=stage,
            confidence=confidence,
            features={
                "spectral": spectral,
                "hjorth_activity": hjorth[0],
                "hjorth_mobility": hjorth[1],
                "hjorth_complexity": hjorth[2],
            },
        ))

    total_duration = epochs[-1].end_time if epochs else 0.0

    # Find sleep onset (first non-WAKE epoch)
    sleep_start = None
    sleep_end = None
    for e in epochs:
        if e.stage != SleepStage.WAKE and sleep_start is None:
            sleep_start = e.start_time
        if e.stage != SleepStage.WAKE:
            sleep_end = e.end_time

    return Hypnogram(
        epochs=epochs,
        total_duration=total_duration,
        sleep_start=sleep_start,
        sleep_end=sleep_end,
    )


def compute_sleep_metrics(hypnogram: Hypnogram) -> dict:
    """
    Compute standard sleep architecture metrics from a hypnogram.
    """
    stage_times = {stage: 0.0 for stage in SleepStage}
    for epoch in hypnogram.epochs:
        stage_times[epoch.stage] += epoch.end_time - epoch.start_time

    total_sleep = hypnogram.total_sleep_time
    if total_sleep <= 0:
        total_sleep = 1.0  # avoid division by zero

    return {
        "total_sleep_time": hypnogram.total_sleep_time,
        "sleep_efficiency": hypnogram.sleep_efficiency,
        "sleep_onset_latency": (hypnogram.sleep_start or 0) - 0,
        "wake_after_sleep_onset": hypnogram.wake_after_sleep_onset,
        "time_in_wake": stage_times[SleepStage.WAKE],
        "time_in_n1": stage_times[SleepStage.N1],
        "time_in_n2": stage_times[SleepStage.N2],
        "time_in_n3": stage_times[SleepStage.N3],
        "time_in_rem": stage_times[SleepStage.REM],
        "pct_n1": stage_times[SleepStage.N1] / total_sleep,
        "pct_n2": stage_times[SleepStage.N2] / total_sleep,
        "pct_n3": stage_times[SleepStage.N3] / total_sleep,
        "pct_rem": stage_times[SleepStage.REM] / total_sleep,
        "rem_latency": _compute_rem_latency(hypnogram),
        "num_stage_transitions": _count_transitions(hypnogram),
        "sleep_stage_index": _compute_sleep_stage_index(hypnogram),
    }


def _compute_rem_latency(hypnogram: Hypnogram) -> float:
    """Time from sleep onset to first REM epoch."""
    if not hypnogram.sleep_start:
        return 0.0
    for epoch in hypnogram.epochs:
        if epoch.stage == SleepStage.REM:
            return epoch.start_time - hypnogram.sleep_start
    return hypnogram.total_duration - hypnogram.sleep_start


def _count_transitions(hypnogram: Hypnogram) -> int:
    """Count number of sleep stage transitions."""
    if len(hypnogram.epochs) < 2:
        return 0
    count = 0
    for i in range(1, len(hypnogram.epochs)):
        if hypnogram.epochs[i].stage != hypnogram.epochs[i - 1].stage:
            count += 1
    return count


def _compute_sleep_stage_index(hypnogram: Hypnogram) -> float:
    """
    Composite sleep quality index (0-100).
    Higher = better sleep quality.
    """
    metrics = compute_sleep_metrics(hypnogram) if not hasattr(hypnogram, "epochs") else {}

    score = 0.0
    # Sleep efficiency (0-30 points)
    score += min(30, hypnogram.sleep_efficiency * 30)

    # Deep sleep percentage (0-25 points, ideal ~15-20%)
    deep_pct = sum(
        e.end_time - e.start_time
        for e in hypnogram.epochs
        if e.stage == SleepStage.N3
    ) / max(hypnogram.total_sleep_time, 1)
    score += min(25, deep_pct * 125)

    # REM percentage (0-25 points, ideal ~20-25%)
    rem_pct = sum(
        e.end_time - e.start_time
        for e in hypnogram.epochs
        if e.stage == SleepStage.REM
    ) / max(hypnogram.total_sleep_time, 1)
    score += min(25, rem_pct * 100)

    # Wake duration penalty (0-20 points, less wake = better)
    wake_pct = sum(
        e.end_time - e.start_time
        for e in hypnogram.epochs
        if e.stage == SleepStage.WAKE
    ) / max(hypnogram.total_duration, 1)
    score += max(0, 20 - wake_pct * 200)

    return min(100.0, max(0.0, score))

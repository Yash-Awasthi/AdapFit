"""
OpenHRV biofeedback patterns — breathing pacer and HRV coherence.
"""
from dataclasses import dataclass
from typing import List, Optional
import math


@dataclass
class BreathingSession:
    inhale_seconds: float = 4.0
    hold_seconds: float = 0.0
    exhale_seconds: float = 6.0
    cycles: int = 10
    coherence_score: float = 0.0


@dataclass
class CoherenceResult:
    score: float  # 0-1
    level: str  # low, medium, high
    peak_frequency: float
    lf_hf_ratio: float
    duration_seconds: float


def compute_coherence_score(rr_intervals: List[float], sample_rate: float = 4.0) -> CoherenceResult:
    if len(rr_intervals) < 30:
        return CoherenceResult(score=0, level="low", peak_frequency=0, lf_hf_ratio=0, duration_seconds=0)

    mean_rr = sum(rr_intervals) / len(rr_intervals)
    centered = [r - mean_rr for r in rr_intervals]
    n = len(centered)

    peak_freq = 0.0
    peak_mag = 0.0
    lf_power = 0.0
    hf_power = 0.0

    for k in range(n // 2):
        freq = k * sample_rate / n
        real = sum(centered[i] * math.cos(2 * math.pi * k * i / n) for i in range(n))
        imag = sum(centered[i] * math.sin(2 * math.pi * k * i / n) for i in range(n))
        mag = math.sqrt(real ** 2 + imag ** 2) / n

        if freq < 4.0:
            if mag > peak_mag:
                peak_mag = mag
                peak_freq = freq
        if 0.04 <= freq < 0.15:
            lf_power += mag ** 2
        elif 0.15 <= freq < 0.4:
            hf_power += mag ** 2

    total_power = lf_power + hf_power
    coherence = peak_mag / max(total_power, 1e-10) if total_power > 0 else 0
    coherence = min(1.0, coherence * 3)

    if coherence >= 0.7:
        level = "high"
    elif coherence >= 0.4:
        level = "medium"
    else:
        level = "low"

    lf_hf = lf_power / hf_power if hf_power > 0 else 0
    duration = len(rr_intervals) / sample_rate

    return CoherenceResult(score=round(coherence, 3), level=level, peak_frequency=round(peak_freq, 3), lf_hf_ratio=round(lf_hf, 3), duration_seconds=duration)


def generate_breathing_pacer(target_coherence: float = 0.7) -> BreathingSession:
    if target_coherence >= 0.7:
        return BreathingSession(inhale_seconds=5.0, hold_seconds=0.0, exhale_seconds=5.0, cycles=10)
    elif target_coherence >= 0.4:
        return BreathingSession(inhale_seconds=4.0, hold_seconds=2.0, exhale_seconds=6.0, cycles=10)
    else:
        return BreathingSession(inhale_seconds=3.0, hold_seconds=0.0, exhale_seconds=4.0, cycles=10)


def compute_breathing_rate(rr_intervals: List[float], sample_rate: float = 4.0) -> float:
    if len(rr_intervals) < 20:
        return 0.0
    diffs = [rr_intervals[i + 1] - rr_intervals[i] for i in range(len(rr_intervals) - 1)]
    zero_crossings = sum(1 for i in range(1, len(diffs)) if diffs[i] * diffs[i - 1] < 0)
    return zero_crossings * sample_rate / (2 * len(rr_intervals))

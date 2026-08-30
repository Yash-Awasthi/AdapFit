"""
Remote photoplethysmography from rppg — camera-based vital signs.
"""
from dataclasses import dataclass
from typing import List
import math


@dataclass
class RPPGResult:
    heart_rate: float = 0.0
    heart_rate_variability: float = 0.0
    respiratory_rate: float = 0.0
    blood_oxygen_estimate: float = 0.0
    signal_quality: float = 0.0
    timestamps: List[float] = None
    signal: List[float] = None

    def __post_init__(self):
        if self.timestamps is None: self.timestamps = []
        if self.signal is None: self.signal = []


def pos_algorithm(signal: List[float], fps: float = 30.0) -> List[float]:
    n = len(signal)
    if n < 6:
        return signal
    alpha = 1.5
    result = list(signal)
    for i in range(6, n):
        result[i] = signal[i] + alpha * (signal[i] - signal[i - 6])
    return result


def compute_rppg_hr(filtered_signal: List[float], fps: float) -> float:
    if len(filtered_signal) < fps * 2:
        return 0.0
    mean = sum(filtered_signal) / len(filtered_signal)
    centered = [s - mean for s in filtered_signal]
    diffs = [centered[i] - centered[i - 1] for i in range(1, len(centered))]
    zero_crossings = sum(1 for i in range(1, len(diffs)) if diffs[i] * diffs[i - 1] < 0)
    return zero_crossings * fps / (2 * len(filtered_signal)) * 60


def analyze_rppg(green_channel: List[float], fps: float = 30.0) -> RPPGResult:
    if not green_channel:
        return RPPGResult()
    filtered = pos_algorithm(green_channel, fps)
    hr = compute_rppg_hr(filtered, fps)
    mean_val = sum(filtered) / len(filtered)
    variance = sum((s - mean_val) ** 2 for s in filtered) / len(filtered)
    quality = min(1.0, variance / 100.0) if variance > 0 else 0.0
    return RPPGResult(heart_rate=round(hr, 1), signal_quality=quality, signal=filtered)

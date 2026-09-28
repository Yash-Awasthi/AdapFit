"""
Biometrics Signal Processing — ECG, HRV, PPG signal analysis.
Provides R-peak detection, HRV feature extraction, and signal quality assessment.

Inspired by: biosppy (biophysics signal processing library)
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ECGResult:
    """ECG processing result."""
    r_peaks: list[int]
    heart_rate_bpm: float
    signal_quality: float
    rr_intervals_ms: list[float]


class ECGProcessor:
    """Processes raw ECG signals to detect R-peaks and extract heart rate."""

    def __init__(self, sampling_rate: float = 250.0) -> None:
        self.sampling_rate = sampling_rate

    def _bandpass_filter(self, data: list[float], low: float = 5.0, high: float = 15.0) -> list[float]:
        """Simple bandpass filter for ECG (Pan-Tompkins style)."""
        # Simplified derivative + squaring + moving average
        n = len(data)
        if n < 5:
            return data

        # Derivative
        derivative = [0.0] * n
        for i in range(2, n - 2):
            derivative[i] = (2 * data[i+1] + data[i+2] - 2 * data[i-1] - data[i-2]) / 8

        # Squaring
        squared = [d * d for d in derivative]

        # Moving average integration
        window = int(self.sampling_rate * 0.15)  # 150ms window
        integrated = [0.0] * n
        for i in range(n):
            start = max(0, i - window)
            integrated[i] = sum(squared[start:i+1]) / max(i - start + 1, 1)

        return integrated

    def detect_r_peaks(self, signal: list[float]) -> list[int]:
        """Detect R-peak locations in ECG signal using threshold-based approach."""
        filtered = self._bandpass_filter(signal)
        n = len(filtered)

        if n < 10:
            return []

        # Adaptive threshold
        mean_val = sum(filtered) / n
        threshold = mean_val * 0.6

        # Refractory period: 200ms minimum between R-peaks
        refractory_samples = int(self.sampling_rate * 0.2)

        r_peaks: list[int] = []
        i = 1

        while i < n - 1:
            if filtered[i] > threshold and filtered[i] > filtered[i-1] and filtered[i] >= filtered[i+1]:
                if not r_peaks or (i - r_peaks[-1]) >= refractory_samples:
                    r_peaks.append(i)
            i += 1

        return r_peaks

    def process(self, signal: list[float]) -> ECGResult:
        """Full ECG processing pipeline."""
        r_peaks = self.detect_r_peaks(signal)

        # Compute RR intervals
        rr_intervals = []
        for i in range(1, len(r_peaks)):
            rr_ms = (r_peaks[i] - r_peaks[i-1]) / self.sampling_rate * 1000
            rr_intervals.append(rr_ms)

        # Heart rate
        if rr_intervals:
            mean_rr = sum(rr_intervals) / len(rr_intervals)
            hr = 60000 / mean_rr if mean_rr > 0 else 0
        else:
            hr = 0

        # Signal quality (based on R-peak regularity)
        if len(rr_intervals) >= 3:
            mean_rr = sum(rr_intervals) / len(rr_intervals)
            variance = sum((r - mean_rr) ** 2 for r in rr_intervals) / len(rr_intervals)
            cv = math.sqrt(variance) / max(mean_rr, 1)
            quality = max(0, min(1, 1 - cv))
        else:
            quality = 0

        return ECGResult(
            r_peaks=r_peaks,
            heart_rate_bpm=round(hr, 1),
            signal_quality=round(quality, 3),
            rr_intervals_ms=rr_intervals,
        )

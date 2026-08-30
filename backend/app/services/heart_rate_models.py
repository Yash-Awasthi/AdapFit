"""
ML heart rate models from ml-heart-rate-models — signal processing for HR estimation.
"""
from dataclasses import dataclass
from typing import List, Optional
import math


@dataclass
class HRPrediction:
    bpm: float
    confidence: float
    method: str
    signal_quality: float


def sliding_window_average(signal: List[float], window: int) -> List[float]:
    result = []
    for i in range(len(signal)):
        start = max(0, i - window // 2)
        end = min(len(signal), i + window // 2 + 1)
        result.append(sum(signal[start:end]) / (end - start))
    return result


def detect_peaks(signal: List[float], min_height: float = 0.0, min_distance: int = 5) -> List[int]:
    peaks = []
    for i in range(1, len(signal) - 1):
        if signal[i] > signal[i - 1] and signal[i] > signal[i + 1] and signal[i] >= min_height:
            if not peaks or (i - peaks[-1]) >= min_distance:
                peaks.append(i)
    return peaks


def estimate_hr_from_peaks(peaks: List[int], sample_rate: float) -> float:
    if len(peaks) < 2:
        return 0.0
    intervals = [peaks[i + 1] - peaks[i] for i in range(len(peaks) - 1)]
    avg_interval = sum(intervals) / len(intervals)
    return 60 * sample_rate / avg_interval if avg_interval > 0 else 0.0


def bandpass_filter(signal: List[float], low: float, high: float, fs: float) -> List[float]:
    n = len(signal)
    result = list(signal)
    for _ in range(2):
        smoothed = list(result)
        for i in range(2, n - 2):
            smoothed[i] = (result[i - 2] + result[i - 1] + result[i] + result[i + 1] + result[i + 2]) / 5
        result = smoothed
    return result


def compute_snr(signal: List[float]) -> float:
    if len(signal) < 10:
        return 0.0
    mean = sum(signal) / len(signal)
    signal_power = sum((s - mean) ** 2 for s in signal) / len(signal)
    noise_estimate = sum(abs(signal[i] - signal[i - 1]) for i in range(1, len(signal))) / (len(signal) - 1)
    return signal_power / max(noise_estimate ** 2, 1e-10)


def multi_method_hr_estimation(signal: List[float], sample_rate: float) -> HRPrediction:
    filtered = bandpass_filter(signal, 0.7, 4.0, sample_rate)
    snr = compute_snr(filtered)
    quality = min(1.0, snr / 10.0)

    peaks = detect_peaks(filtered, min_height=max(filtered) * 0.3 if filtered else 0, min_distance=int(sample_rate * 0.3))
    hr_peaks = estimate_hr_from_peaks(peaks, sample_rate)

    diffs = [filtered[i] - filtered[i - 1] for i in range(1, len(filtered))]
    zero_crossings = sum(1 for i in range(1, len(diffs)) if diffs[i] * diffs[i - 1] < 0)
    hr_autocorr = zero_crossings * 30 / max(len(filtered), 1) * sample_rate

    candidates = [hr for hr in [hr_peaks, hr_autocorr] if 40 < hr < 220]
    final_hr = sum(candidates) / len(candidates) if candidates else 0.0
    confidence = min(1.0, len(candidates) / 2 * quality)

    return HRPrediction(bpm=round(final_hr, 1), confidence=confidence, method="multi", signal_quality=quality)

"""BVP Signal Processing Service.

Extracted from pyvhr (inspiration).
Blood Volume Pulse signal processing: CHROM, LGI, POS methods,
BPM estimation, and signal filtering for rPPG.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BVPSignal:
    signal: list[float]
    sample_rate: float
    method: str = ""
    bpm: float = 0.0
    snr: float = 0.0


@dataclass
class BPMResult:
    bpm: float
    confidence: float
    method: str
    signal_quality: str  # "good", "fair", "poor"


def cpu_chrom(r: list[float], g: list[float], b: list[float]) -> list[float]:
    """CHROM method for BVP extraction from RGB signals."""
    n = len(r)
    xcomp = [3 * r[i] - 2 * g[i] for i in range(n)]
    ycomp = [1.5 * r[i] + g[i] - 1.5 * b[i] for i in range(n)]
    s_x = statistics.stdev(xcomp) if len(xcomp) > 1 else 1.0
    s_y = statistics.stdev(ycomp) if len(ycomp) > 1 else 1.0
    alpha = s_x / s_y if s_y > 0 else 1.0
    bvp = [xcomp[i] - alpha * ycomp[i] for i in range(n)]
    return bvp


def cpu_lgi(r: list[float], g: list[float], b: list[float]) -> list[float]:
    """LGI method for BVP extraction."""
    n = len(r)
    signals = [r, g, b]
    means = [statistics.mean(s) for s in signals]
    normalized = [[(s[i] - means[j]) for i in range(n)] for j, s in enumerate(signals)]
    eigs = []
    for sig in normalized:
        variance = statistics.variance(sig) if len(sig) > 1 else 1.0
        eigs.append(variance)
    total = sum(eigs) if sum(eigs) > 0 else 1.0
    weights = [e / total for e in eigs]
    bvp = [sum(weights[j] * normalized[j][i] for j in range(3)) for i in range(n)]
    return bvp


def cpu_pos(r: list[float], g: list[float], b: list[float], fps: float = 30.0) -> list[float]:
    """POS (Plane-Orthogonal-to-Skin) method for BVP extraction."""
    n = len(r)
    h = [r[i] - g[i] for i in range(n)]
    s = [-0.5 * r[i] - g[i] + 1.5 * b[i] for i in range(n)]
    alpha = [h[i] / (s[i] + 1e-6) for i in range(n)]
    mean_alpha = statistics.mean(alpha) if alpha else 0
    x = [h[i] - mean_alpha * s[i] for i in range(n)]
    return x


def bandpass_filter(signal: list[float], low_freq: float = 0.75, high_freq: float = 3.0, sample_rate: float = 30.0) -> list[float]:
    """Simple bandpass filter using moving average approximation."""
    if not signal:
        return []
    low_period = int(sample_rate / high_freq) if high_freq > 0 else 1
    high_period = int(sample_rate / low_freq) if low_freq > 0 else len(signal)
    low_period = max(1, low_period)
    high_period = max(low_period + 1, high_period)
    low_passed = _moving_average(signal, low_period)
    high_passed = _moving_average(low_passed, high_period)
    result = [low_passed[i] - high_passed[i] for i in range(min(len(low_passed), len(high_passed)))]
    return result


def _moving_average(data: list[float], window: int) -> list[float]:
    """Compute moving average."""
    if window <= 0 or not data:
        return data
    result = []
    for i in range(len(data)):
        start = max(0, i - window // 2)
        end = min(len(data), i + window // 2 + 1)
        result.append(statistics.mean(data[start:end]))
    return result


def estimate_bpm(bvp: list[float], sample_rate: float = 30.0) -> float:
    """Estimate BPM from BVP signal using peak detection."""
    if len(bvp) < sample_rate:
        return 0.0
    peaks = _detect_peaks(bvp)
    if len(peaks) < 2:
        return 0.0
    intervals = [peaks[i + 1] - peaks[i] for i in range(len(peaks) - 1)]
    avg_interval = statistics.mean(intervals) if intervals else 1.0
    if avg_interval <= 0:
        return 0.0
    bpm = 60.0 * sample_rate / avg_interval
    return round(bpm, 1)


def _detect_peaks(signal: list[float], threshold: float = 0.0) -> list[int]:
    """Simple peak detection."""
    if len(signal) < 3:
        return []
    peaks = []
    mean_val = statistics.mean(signal)
    thresh = max(threshold, mean_val)
    for i in range(1, len(signal) - 1):
        if signal[i] > signal[i - 1] and signal[i] > signal[i + 1] and signal[i] > thresh:
            peaks.append(i)
    return peaks


def calculate_snr(signal: list[float], bpm: float, sample_rate: float = 30.0) -> float:
    """Calculate Signal-to-Noise Ratio for BVP signal."""
    if not signal or bpm <= 0:
        return 0.0
    peak_freq = bpm / 60.0
    n = len(signal)
    signal_power = 0.0
    noise_power = 0.0
    for i in range(n):
        freq = i * sample_rate / n
        power = signal[i] ** 2
        if abs(freq - peak_freq) < 0.1 or abs(freq + peak_freq) < 0.1:
            signal_power += power
        else:
            noise_power += power
    if noise_power <= 0:
        return 10.0
    return 10 * math.log10(signal_power / noise_power)


def classify_signal_quality(snr: float) -> str:
    """Classify signal quality from SNR."""
    if snr > 10:
        return "good"
    elif snr > 5:
        return "fair"
    else:
        return "poor"


def process_rppg_signal(
    r: list[float], g: list[float], b: list[float],
    sample_rate: float = 30.0,
    method: str = "chrom",
) -> BPMResult:
    """Process rPPG signal and extract BPM."""
    if method == "chrom":
        bvp = cpu_chrom(r, g, b)
    elif method == "lgi":
        bvp = cpu_lgi(r, g, b)
    elif method == "pos":
        bvp = cpu_pos(r, g, b, sample_rate)
    else:
        bvp = cpu_chrom(r, g, b)
    filtered = bandpass_filter(bvp, 0.75, 3.0, sample_rate)
    bpm = estimate_bpm(filtered, sample_rate)
    snr = calculate_snr(filtered, bpm, sample_rate)
    quality = classify_signal_quality(snr)
    confidence = min(1.0, max(0.0, (snr + 5) / 20))
    return BPMResult(bpm=bpm, confidence=round(confidence, 2), method=method, signal_quality=quality)

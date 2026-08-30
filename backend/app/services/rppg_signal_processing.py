"""Remote Photoplethysmography (rPPG) Signal Processing.

Extracted from advanced-rppg (inspiration).
Heart rate estimation from video using chrominance-based methods,
bandpass filtering, and signal quality assessment.

All pure functions — no OpenCV dependency, just math on signal arrays.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class rPPGResult:
    """Result of rPPG heart rate estimation."""
    heart_rate_bpm: float = 0.0
    confidence: float = 0.0
    signal_quality: float = 0.0
    method: str = ""
    samples_used: int = 0


def extract_rgb_means(
    r_channel: list[float],
    g_channel: list[float],
    b_channel: list[float],
) -> tuple[list[float], list[float], list[float]]:
    """Normalize RGB signals by removing DC component.

    Args:
        r_channel: Raw red channel values
        g_channel: Raw green channel values
        b_channel: Raw blue channel values

    Returns:
        Normalized (R, G, B) signals with zero mean
    """
    n = len(r_channel)
    if n == 0:
        return [], [], []

    mean_r = sum(r_channel) / n
    mean_g = sum(g_channel) / n
    mean_b = sum(b_channel) / n

    std_r = math.sqrt(sum((x - mean_r) ** 2 for x in r_channel) / n) or 1.0
    std_g = math.sqrt(sum((x - mean_g) ** 2 for x in g_channel) / n) or 1.0
    std_b = math.sqrt(sum((x - mean_b) ** 2 for x in b_channel) / n) or 1.0

    return (
        [(x - mean_r) / std_r for x in r_channel],
        [(x - mean_g) / std_g for x in g_channel],
        [(x - mean_b) / std_b for x in b_channel],
    )


def chrominance_method(
    r_signal: list[float],
    g_signal: list[float],
    b_signal: list[float],
    fps: float = 30.0,
    min_hr: float = 40.0,
    max_hr: float = 200.0,
) -> rPPGResult:
    """Chrominance-based rPPG heart rate estimation.

    Uses the CHROM method (De Haan & Jeanne, 2013):
    Xs = 3R - 2G
    Ys = 1.5R + G - 1.5B
    alpha = std(Xs) / std(Ys)
    P = Xs - alpha * Ys

    Then estimates HR from the dominant frequency of P.

    Args:
        r_signal: Red channel time series
        g_signal: Green channel time series
        b_signal: Blue channel time series
        fps: Frame rate in Hz
        min_hr: Minimum heart rate (bpm)
        max_hr: Maximum heart rate (bpm)

    Returns:
        rPPGResult with estimated heart rate and quality
    """
    n = len(g_signal)
    if n < 30:
        return rPPGResult(method="chrominance", samples_used=n)

    # Normalize
    r_norm, g_norm, b_norm = extract_rgb_means(r_signal, g_signal, b_signal)

    if not r_norm:
        return rPPGResult(method="chrominance", samples_used=0)

    # Chrominance signals
    xs = [3 * r_norm[i] - 2 * g_norm[i] for i in range(n)]
    ys = [1.5 * r_norm[i] + g_norm[i] - 1.5 * b_norm[i] for i in range(n)]

    # Alpha scaling
    std_xs = math.sqrt(sum(x ** 2 for x in xs) / n)
    std_ys = math.sqrt(sum(y ** 2 for y in ys) / n)
    alpha = std_xs / std_ys if std_ys > 0 else 1.0

    # Combined signal
    pulse = [xs[i] - alpha * ys[i] for i in range(n)]

    # Bandpass filter (0.7-4.0 Hz for HR 42-240 bpm)
    filtered = bandpass_filter(pulse, fps, 0.7, 4.0)

    # Estimate heart rate from dominant frequency
    hr, confidence = estimate_dominant_frequency(filtered, fps, min_hr, max_hr)

    # Signal quality
    quality = compute_signal_quality(filtered)

    return rPPGResult(
        heart_rate_bpm=round(hr, 1),
        confidence=round(confidence, 3),
        signal_quality=round(quality, 3),
        method="chrominance",
        samples_used=n,
    )


def pos_method(
    r_signal: list[float],
    g_signal: list[float],
    b_signal: list[float],
    fps: float = 30.0,
    min_hr: float = 40.0,
    max_hr: float = 200.0,
) -> rPPGResult:
    """Plane-Orthogonal-to-Skin (POS) rPPG method.

    Uses orthogonal projection to extract pulse signal.

    Args:
        r_signal: Red channel time series
        g_signal: Green channel time series
        b_signal: Blue channel time series
        fps: Frame rate in Hz
        min_hr: Minimum heart rate (bpm)
        max_hr: Maximum heart rate (bpm)

    Returns:
        rPPGResult with estimated heart rate
    """
    n = len(g_signal)
    if n < 30:
        return rPPGResult(method="POS", samples_used=n)

    r_norm, g_norm, b_norm = extract_rgb_means(r_signal, g_signal, b_signal)

    if not r_norm:
        return rPPGResult(method="POS", samples_used=0)

    # POS projection matrix
    pulse = []
    for i in range(n):
        # Project onto plane orthogonal to [1,1,1] then rotate
        h = 2 * g_norm[i] - r_norm[i] - b_norm[i]
        pulse.append(h)

    filtered = bandpass_filter(pulse, fps, 0.7, 4.0)
    hr, confidence = estimate_dominant_frequency(filtered, fps, min_hr, max_hr)
    quality = compute_signal_quality(filtered)

    return rPPGResult(
        heart_rate_bpm=round(hr, 1),
        confidence=round(confidence, 3),
        signal_quality=round(quality, 3),
        method="POS",
        samples_used=n,
    )


def green_channel_method(
    g_signal: list[float],
    fps: float = 30.0,
    min_hr: float = 40.0,
    max_hr: float = 200.0,
) -> rPPGResult:
    """Simple green channel rPPG method.

    Uses only the green channel, which has highest blood absorption.

    Args:
        g_signal: Green channel time series
        fps: Frame rate in Hz
        min_hr: Minimum heart rate (bpm)
        max_hr: Maximum heart rate (bpm)

    Returns:
        rPPGResult with estimated heart rate
    """
    n = len(g_signal)
    if n < 30:
        return rPPGResult(method="green_channel", samples_used=n)

    # Normalize
    mean_g = sum(g_signal) / n
    std_g = math.sqrt(sum((x - mean_g) ** 2 for x in g_signal) / n) or 1.0
    g_norm = [(x - mean_g) / std_g for x in g_signal]

    filtered = bandpass_filter(g_norm, fps, 0.7, 4.0)
    hr, confidence = estimate_dominant_frequency(filtered, fps, min_hr, max_hr)
    quality = compute_signal_quality(filtered)

    return rPPGResult(
        heart_rate_bpm=round(hr, 1),
        confidence=round(confidence, 3),
        signal_quality=round(quality, 3),
        method="green_channel",
        samples_used=n,
    )


def bandpass_filter(
    signal_data: list[float],
    fps: float,
    low_hz: float = 0.7,
    high_hz: float = 4.0,
    order: int = 2,
) -> list[float]:
    """Simple Butterworth-style bandpass filter.

    Uses cascaded first-order sections for stability.

    Args:
        signal_data: Input signal
        fps: Sampling rate in Hz
        low_hz: Low cutoff frequency
        high_hz: High cutoff frequency
        order: Filter order

    Returns:
        Filtered signal
    """
    n = len(signal_data)
    if n < 4:
        return list(signal_data)

    # Bilinear transform approximation
    nyq = fps / 2.0
    low = low_hz / nyq
    high = high_hz / nyq

    # Clamp to valid range
    low = max(0.01, min(low, 0.99))
    high = max(low + 0.01, min(high, 0.99))

    # Simple IIR filter coefficients (approximate Butterworth)
    # High-pass component
    hp_b = [1.0, -2.0, 1.0]
    hp_a = [1.0, -2.0 * math.cos(2 * math.pi * low), 1.0 - 4.0 * low]

    # Low-pass component
    lp_b = [(1.0 - high) / 2.0, (1.0 - high), (1.0 - high) / 2.0]
    lp_a = [1.0, -2.0 * math.cos(2 * math.pi * high) * (1.0 - 0.1 * high), (1.0 - 0.1 * high) ** 2]

    # Apply high-pass then low-pass
    filtered = signal_data[:]

    # High-pass
    for _ in range(order):
        temp = [0.0] * n
        for i in range(2, n):
            temp[i] = (
                hp_b[0] * filtered[i]
                + hp_b[1] * filtered[i - 1]
                + hp_b[2] * filtered[i - 2]
                - hp_a[1] * temp[i - 1]
                - hp_a[2] * temp[i - 2]
            )
        filtered = temp

    # Low-pass
    for _ in range(order):
        temp = [0.0] * n
        for i in range(2, n):
            temp[i] = (
                lp_b[0] * filtered[i]
                + lp_b[1] * filtered[i - 1]
                + lp_b[2] * filtered[i - 2]
                - lp_a[1] * temp[i - 1]
                - lp_a[2] * temp[i - 2]
            )
        filtered = temp

    return filtered


def estimate_dominant_frequency(
    signal_data: list[float],
    fps: float,
    min_hr: float = 40.0,
    max_hr: float = 200.0,
) -> tuple[float, float]:
    """Estimate heart rate from dominant frequency using DFT.

    Args:
        signal_data: Filtered pulse signal
        fps: Sampling rate in Hz
        min_hr: Minimum heart rate (bpm)
        max_hr: Maximum heart rate (bpm)

    Returns:
        Tuple of (heart_rate_bpm, confidence)
    """
    n = len(signal_data)
    if n < 10:
        return 0.0, 0.0

    # Compute DFT magnitude (simplified)
    min_freq = min_hr / 60.0
    max_freq = max_hr / 60.0

    best_power = 0.0
    best_freq = 0.0
    total_power = 0.0

    for k in range(1, n // 2):
        freq = k * fps / n
        if freq < min_freq or freq > max_freq:
            continue

        # DFT magnitude
        real_sum = sum(signal_data[j] * math.cos(2 * math.pi * k * j / n) for j in range(n))
        imag_sum = sum(signal_data[j] * math.sin(2 * math.pi * k * j / n) for j in range(n))
        power = (real_sum ** 2 + imag_sum ** 2) / n

        total_power += power
        if power > best_power:
            best_power = power
            best_freq = freq

    if best_freq == 0 or total_power == 0:
        return 0.0, 0.0

    hr = best_freq * 60.0
    confidence = best_power / total_power if total_power > 0 else 0.0

    return hr, min(confidence, 1.0)


def compute_signal_quality(signal_data: list[float]) -> float:
    """Compute signal quality metric (0-1).

    Based on SNR estimate and signal stability.

    Args:
        signal_data: Filtered pulse signal

    Returns:
        Quality score (0=poor, 1=excellent)
    """
    n = len(signal_data)
    if n < 10:
        return 0.0

    mean_val = sum(signal_data) / n
    variance = sum((x - mean_val) ** 2 for x in signal_data) / n

    if variance == 0:
        return 0.0

    # Signal-to-noise estimate
    diffs = [signal_data[i + 1] - signal_data[i] for i in range(n - 1)]
    noise_var = sum(d ** 2 for d in diffs) / len(diffs)

    snr = variance / noise_var if noise_var > 0 else 0.0

    # Normalize to 0-1
    quality = min(1.0, snr / 5.0)

    return quality


def compute_rr_from_hr_timeseries(
    heart_rates: list[float],
    timestamps: list[float],
) -> list[float]:
    """Compute RR intervals from heart rate time series.

    Args:
        heart_rates: Sequence of HR measurements (bpm)
        timestamps: Corresponding timestamps (seconds)

    Returns:
        RR intervals in seconds
    """
    if len(heart_rates) < 2:
        return []

    rr_intervals = []
    for i in range(1, len(heart_rates)):
        if heart_rates[i] > 0:
            rr = 60.0 / heart_rates[i]
            rr_intervals.append(rr)

    return rr_intervals


def merge_rppg_results(
    results: list[rPPGResult],
) -> rPPGResult:
    """Merge multiple rPPG estimates using weighted average.

    Weights by confidence and signal quality.

    Args:
        results: List of rPPG results from different methods

    Returns:
        Merged result with weighted average HR
    """
    valid = [r for r in results if r.heart_rate_bpm > 0 and r.confidence > 0]

    if not valid:
        return rPPGResult()

    weights = [r.confidence * r.signal_quality for r in valid]
    total_weight = sum(weights)

    if total_weight == 0:
        return valid[0]

    weighted_hr = sum(
        r.heart_rate_bpm * w for r, w in zip(valid, weights)
    ) / total_weight

    avg_confidence = sum(r.confidence for r in valid) / len(valid)
    avg_quality = sum(r.signal_quality for r in valid) / len(valid)

    return rPPGResult(
        heart_rate_bpm=round(weighted_hr, 1),
        confidence=round(avg_confidence, 3),
        signal_quality=round(avg_quality, 3),
        method="merged",
        samples_used=sum(r.samples_used for r in valid),
    )

"""Remote photoplethysmography (rPPG) — heart rate from video frames.

Extracted from inspiration/ZFIT/heartbeat-js.
Pattern: signal processing pipeline that detects pulse from subtle skin color changes.
Steps: face ROI extraction → average color per frame → detrend → bandpass filter → FFT → peak detection.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class RGBPixel:
    r: float
    g: float
    b: float


@dataclass(frozen=True)
class HeartRateResult:
    bpm: float
    confidence: float  # 0.0-1.0
    peak_frequency: float  # Hz
    spectrum: list[float]


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: list[float], mean: float) -> float:
    if len(values) < 2:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)


def _detrend(signal: list[float]) -> list[float]:
    """Remove linear trend from signal using least-squares approximation."""
    n = len(signal)
    if n < 2:
        return signal[:]
    mean = _mean(signal)
    # Simple linear regression: y = a + b*x
    x_mean = (n - 1) / 2
    y_mean = mean
    num = sum((i - x_mean) * (signal[i] - y_mean) for i in range(n))
    den = sum((i - x_mean) ** 2 for i in range(n))
    slope = num / den if den != 0 else 0
    intercept = y_mean - slope * x_mean
    return [signal[i] - (intercept + slope * i) for i in range(n)]


def _moving_average(signal: list[float], window: int = 5) -> list[float]:
    """Simple moving average filter."""
    n = len(signal)
    result = []
    for i in range(n):
        start = max(0, i - window // 2)
        end = min(n, i + window // 2 + 1)
        result.append(_mean(signal[start:end]))
    return result


def _bandpass_filter(signal: list[float], fps: float, low_hz: float = 0.75, high_hz: float = 4.0) -> list[float]:
    """Simple Butterworth-like bandpass (0.75-4.0 Hz = 45-240 BPM).

    Uses moving average subtraction as a crude high-pass and
    a simple threshold as a low-pass.
    """
    # High-pass: subtract moving average
    window_size = max(3, int(fps / high_hz))
    baseline = _moving_average(signal, window_size)
    filtered = [signal[i] - baseline[i] for i in range(len(signal))]

    # Low-pass: moving average smoothing
    window_size = max(3, int(fps / low_hz / 2))
    filtered = _moving_average(filtered, window_size)

    return filtered


def _fft_magnitude(signal: list[float], fps: float) -> tuple[list[float], list[float]]:
    """Compute FFT magnitude spectrum. Returns (frequencies, magnitudes).

    Uses a simple DFT (O(n²)) since we keep signal lengths small (<256 samples).
    """
    n = len(signal)
    if n < 4:
        return [], []

    # Apply Hann window
    windowed = [signal[i] * (0.5 - 0.5 * math.cos(2 * math.pi * i / (n - 1))) for i in range(n)]

    # DFT
    half = n // 2
    freqs = [i * fps / n for i in range(half)]
    magnitudes = []
    for k in range(half):
        real = 0.0
        imag = 0.0
        for j in range(n):
            angle = -2 * math.pi * k * j / n
            real += windowed[j] * math.cos(angle)
            imag += windowed[j] * math.sin(angle)
        magnitudes.append(math.sqrt(real * real + imag * imag) / n)

    return freqs, magnitudes


def _chrom_method(frames: list[RGBPixel]) -> list[float]:
    """CHROM (Chrominance-based) rPPG signal extraction.

    Combines R, G, B channels to suppress illumination changes:
    X = 3*R - 2*G
    Y = 1.5*R + G - 1.5*B
    """
    signals = []
    for px in frames:
        x = 3 * px.r - 2 * px.g
        y = 1.5 * px.r + px.g - 1.5 * px.b
        signals.append(x - y)  # simplified alpha-stable combination
    return signals


def _green_method(frames: list[RGBPixel]) -> list[float]:
    """Simple green-channel method — green has strongest PPG signal."""
    return [px.g for px in frames]


def estimate_heart_rate(
    frames: list[RGBPixel],
    fps: float = 30.0,
    method: str = "chrom",
) -> HeartRateResult:
    """Estimate heart rate from a sequence of skin color frames.

    Args:
        frames: list of averaged skin ROI RGB values, one per video frame
        fps: frames per second of the video
        method: "chrom" for CHROM method, "green" for green channel only

    Returns:
        HeartRateResult with BPM, confidence, peak frequency, spectrum
    """
    if len(frames) < 30:
        return HeartRateResult(bpm=0, confidence=0, peak_frequency=0, spectrum=[])

    # Step 1: Extract raw PPG signal
    if method == "chrom":
        raw_signal = _chrom_method(frames)
    else:
        raw_signal = _green_method(frames)

    # Step 2: Detrend
    detrended = _detrend(raw_signal)

    # Step 3: Bandpass filter (0.75-4.0 Hz = 45-240 BPM)
    filtered = _bandpass_filter(detrended, fps)

    # Step 4: Normalize
    mean = _mean(filtered)
    std = _std(filtered, mean)
    if std > 0:
        normalized = [(v - mean) / std for v in filtered]
    else:
        normalized = filtered

    # Step 5: FFT
    freqs, magnitudes = _fft_magnitude(normalized, fps)

    if not freqs:
        return HeartRateResult(bpm=0, confidence=0, peak_frequency=0, spectrum=[])

    # Step 6: Find peak in 0.75-4.0 Hz range (45-240 BPM)
    best_freq = 0
    best_mag = 0
    total_mag = sum(magnitudes)
    for i, freq in enumerate(freqs):
        if 0.75 <= freq <= 4.0 and magnitudes[i] > best_mag:
            best_mag = magnitudes[i]
            best_freq = freq

    bpm = best_freq * 60 if best_freq > 0 else 0

    # Confidence: ratio of peak energy to total energy
    confidence = best_mag / total_mag if total_mag > 0 else 0
    confidence = min(confidence * 10, 1.0)  # scale up

    return HeartRateResult(
        bpm=bpm,
        confidence=confidence,
        peak_frequency=best_freq,
        spectrum=magnitudes,
    )


def extract_roi_average(
    frame_data: list[list[list[RGBPixel]]],
    fps: float = 30.0,
) -> HeartRateResult:
    """Extract averaged skin color from frame regions and estimate HR.

    Args:
        frame_data: list of frames, each frame is a list of rows, each row is a list of RGBPixels
                    (the face ROI region)
        fps: video frame rate
    """
    frames: list[RGBPixel] = []
    for frame in frame_data:
        r_sum = g_sum = b_sum = 0
        count = 0
        for row in frame:
            for px in row:
                r_sum += px.r
                g_sum += px.g
                b_sum += px.b
                count += 1
        if count > 0:
            frames.append(RGBPixel(r_sum / count, g_sum / count, b_sum / count))

    return estimate_heart_rate(frames, fps)

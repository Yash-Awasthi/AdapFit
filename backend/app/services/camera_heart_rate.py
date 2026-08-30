"""
Camera-based heart rate estimation using remote photoplethysmography.

Extracted from heart-rate-camera — rPPG signal processing patterns.
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple
import math


@dataclass
class HeartRateResult:
    bpm: float
    confidence: float
    signal_quality: float
    timestamps: List[float]
    signal: List[float]


def bandpass_filter(
    signal: List[float],
    low_freq: float,
    high_freq: float,
    sample_rate: float,
) -> List[float]:
    """Simple Butterworth-like bandpass filter using moving averages."""
    period = 1.0 / sample_rate
    low_period = 1.0 / high_freq if high_freq > 0 else len(signal) * period
    high_period = 1.0 / low_freq if low_freq > 0 else len(signal) * period

    low_window = max(1, int(low_period / period))
    high_window = max(1, int(high_period / period))

    # Simple moving average for smoothing
    result = list(signal)
    for _ in range(3):
        smoothed = list(result)
        for i in range(high_window, len(result) - high_window):
            smoothed[i] = sum(result[i - high_window:i + high_window + 1]) / (2 * high_window + 1)
        result = smoothed

    return result


def compute_fft(signal: List[float], sample_rate: float) -> Tuple[List[float], List[float]]:
    """Compute frequency spectrum using DFT (no numpy)."""
    n = len(signal)
    if n == 0:
        return [], []

    freqs = []
    magnitudes = []

    for k in range(n // 2):
        freq = k * sample_rate / n
        if freq < 0.5 or freq > 4.0:  # Heart rate range: 30-240 BPM
            continue

        real = sum(signal[i] * math.cos(2 * math.pi * k * i / n) for i in range(n))
        imag = sum(signal[i] * math.sin(2 * math.pi * k * i / n) for i in range(n))
        mag = math.sqrt(real ** 2 + imag ** 2) / n

        freqs.append(freq)
        magnitudes.append(mag)

    return freqs, magnitudes


def estimate_bpm(
    signal: List[float],
    sample_rate: float,
) -> Tuple[float, float]:
    """Estimate BPM from a PPG signal using FFT peak detection."""
    if len(signal) < sample_rate * 2:
        return 0.0, 0.0

    # Remove DC component
    mean_val = sum(signal) / len(signal)
    centered = [s - mean_val for s in signal]

    freqs, magnitudes = compute_fft(centered, sample_rate)

    if not freqs or not magnitudes:
        return 0.0, 0.0

    # Find peak frequency
    peak_idx = 0
    peak_mag = 0
    for i, mag in enumerate(magnitudes):
        if mag > peak_mag:
            peak_mag = mag
            peak_idx = i

    if peak_idx >= len(freqs):
        return 0.0, 0.0

    peak_freq = freqs[peak_idx]
    bpm = peak_freq * 60

    # Confidence based on peak prominence
    avg_mag = sum(magnitudes) / len(magnitudes) if magnitudes else 0
    confidence = min(1.0, peak_mag / (avg_mag * 3)) if avg_mag > 0 else 0.0

    return bpm, confidence


def extract_roi_from_frame(
    frame_width: int,
    frame_height: int,
    forehead_ratio: float = 0.3,
) -> Tuple[int, int, int, int]:
    """Extract forehead ROI coordinates (simplified — real version uses face detection)."""
    x1 = int(frame_width * 0.35)
    y1 = int(frame_height * 0.15)
    x2 = int(frame_width * 0.65)
    y2 = int(frame_height * 0.35)
    return x1, y1, x2, y2


def compute_signal_quality(signal: List[float], sample_rate: float) -> float:
    """Compute signal quality metric (0-1)."""
    if len(signal) < sample_rate:
        return 0.0

    mean_val = sum(signal) / len(signal)
    variance = sum((s - mean_val) ** 2 for s in signal) / len(signal)
    std_dev = math.sqrt(variance) if variance > 0 else 0.0

    # SNR approximation
    if std_dev == 0:
        return 0.0

    noise_window = max(1, int(sample_rate * 0.1))
    noise_variances = []
    for i in range(0, len(signal) - noise_window, noise_window):
        chunk = signal[i:i + noise_window]
        chunk_mean = sum(chunk) / len(chunk)
        chunk_var = sum((c - chunk_mean) ** 2 for c in chunk) / len(chunk)
        noise_variances.append(chunk_var)

    avg_noise = sum(noise_variances) / len(noise_variances) if noise_variances else 1.0
    snr = variance / max(avg_noise, 1e-10)

    return min(1.0, snr / 10.0)


class CameraHeartRateMonitor:
    """Camera-based heart rate monitor using rPPG."""

    def __init__(self, sample_rate: float = 30.0, buffer_duration: float = 10.0):
        self.sample_rate = sample_rate
        self.buffer_size = int(sample_rate * buffer_duration)
        self.signal_buffer: List[float] = []
        self.timestamp_buffer: List[float] = []

    def process_frame(self, mean_color: Tuple[float, float, float], timestamp: float) -> Optional[HeartRateResult]:
        """Process a frame's mean color value (Green channel for rPPG)."""
        green_value = mean_color[1]  # Green channel most sensitive to blood pulse

        self.signal_buffer.append(green_value)
        self.timestamp_buffer.append(timestamp)

        if len(self.signal_buffer) > self.buffer_size:
            self.signal_buffer = self.signal_buffer[-self.buffer_size:]
            self.timestamp_buffer = self.timestamp_buffer[-self.buffer_size:]

        if len(self.signal_buffer) < self.buffer_size // 2:
            return None

        # Filter signal
        filtered = bandpass_filter(self.signal_buffer, 0.7, 4.0, self.sample_rate)

        # Estimate BPM
        bpm, confidence = estimate_bpm(filtered, self.sample_rate)

        # Quality
        quality = compute_signal_quality(filtered, self.sample_rate)

        return HeartRateResult(
            bpm=round(bpm, 1),
            confidence=confidence,
            signal_quality=quality,
            timestamps=list(self.timestamp_buffer),
            signal=list(filtered),
        )

    def reset(self):
        self.signal_buffer = []
        self.timestamp_buffer = []

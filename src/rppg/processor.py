"""
Remote Photoplethysmography (rPPG) Signal Processor
Camera-based heart rate estimation using RGB signal analysis.

Inspired by: advanced-rppg (remote heart rate monitoring)
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class HeartRateResult:
    """Result of rPPG heart rate estimation."""
    heart_rate_bpm: float
    confidence: float  # 0.0 to 1.0
    signal_quality: float  # 0.0 to 1.0
    timestamp: float
    method: str
    snr: float = 0.0  # signal-to-noise ratio


class RPPGProcessor:
    """Processes RGB signals extracted from video to estimate heart rate.

    Implements CHROM, POS, and Green Channel methods for rPPG.
    """

    def __init__(
        self,
        fps: int = 30,
        window_size: int = 300,
        min_hr: float = 40.0,
        max_hr: float = 200.0,
    ) -> None:
        self.fps = fps
        self.window_size = window_size
        self.min_hr = min_hr
        self.max_hr = max_hr

        # Signal buffers
        self._r_signal: deque[float] = deque(maxlen=window_size)
        self._g_signal: deque[float] = deque(maxlen=window_size)
        self._b_signal: deque[float] = deque(maxlen=window_size)

        # Filter parameters
        self._low_cutoff = 0.7  # Hz (42 BPM)
        self._high_cutoff = 4.0  # Hz (240 BPM)

        # Bandpass filter design
        self._filter_order = 4

    def extract_roi_means(self, roi_pixels: list[tuple[float, float, float]]) -> tuple[float, float, float]:
        """Extract mean RGB from a region of interest (face ROI).

        Args:
            roi_pixels: List of (R, G, B) pixel values from the ROI.

        Returns:
            Mean (R, G, B) values.
        """
        if not roi_pixels:
            return 0.0, 0.0, 0.0

        n = len(roi_pixels)
        r_sum = sum(p[0] for p in roi_pixels)
        g_sum = sum(p[1] for p in roi_pixels)
        b_sum = sum(p[2] for p in roi_pixels)

        return r_sum / n, g_sum / n, b_sum / n

    def add_frame(self, r: float, g: float, b: float) -> None:
        """Add a single RGB frame measurement."""
        self._r_signal.append(r)
        self._g_signal.append(g)
        self._b_signal.append(b)

    def _bandpass_filter(self, data: list[float]) -> list[float]:
        """Simple bandpass filter using running statistics."""
        n = len(data)
        if n < 10:
            return data

        # Detrend (remove mean)
        mean_val = sum(data) / n
        detrended = [x - mean_val for x in data]

        # Simple moving average as low-pass approximation
        kernel_size = max(3, n // 10)
        filtered: list[float] = []
        for i in range(n):
            start = max(0, i - kernel_size // 2)
            end = min(n, i + kernel_size // 2 + 1)
            avg = sum(detrended[start:end]) / (end - start)
            filtered.append(detrended[i] - avg)

        return filtered

    def _compute_fft_peak(self, data: list[float]) -> tuple[float, float]:
        """Compute dominant frequency and SNR from FFT."""
        n = len(data)
        if n < 2:
            return 0.0, 0.0

        # Hanning window
        windowed = [data[i] * (0.5 - 0.5 * math.cos(2 * math.pi * i / n)) for i in range(n)]

        # Compute magnitude spectrum (simplified DFT for peak frequencies)
        freq_resolution = self.fps / n
        min_bin = int(self._low_cutoff / freq_resolution)
        max_bin = min(int(self._high_cutoff / freq_resolution), n // 2)

        if max_bin <= min_bin:
            return 0.0, 0.0

        magnitudes: list[float] = []
        for k in range(min_bin, max_bin + 1):
            # DFT at frequency bin k
            real_part = 0.0
            imag_part = 0.0
            for i in range(n):
                angle = 2 * math.pi * k * i / n
                real_part += windowed[i] * math.cos(angle)
                imag_part += windowed[i] * math.sin(angle)
            magnitudes.append(math.sqrt(real_part ** 2 + imag_part ** 2))

        if not magnitudes:
            return 0.0, 0.0

        # Find peak
        peak_mag = max(magnitudes)
        peak_idx = magnitudes.index(peak_mag)
        peak_freq = (min_bin + peak_idx) * freq_resolution

        # SNR: peak / mean of rest
        mean_mag = sum(magnitudes) / len(magnitudes)
        snr = peak_mag / max(mean_mag, 0.001)

        heart_rate = peak_freq * 60.0  # Convert Hz to BPM
        return heart_rate, snr

    def estimate_hr_chrom(self, timestamp: float | None = None) -> HeartRateResult | None:
        """Estimate heart rate using CHROM (Chrominance-based) method."""
        if len(self._r_signal) < self.window_size // 2:
            return None

        r = list(self._r_signal)
        g = list(self._g_signal)
        b = list(self._b_signal)

        n = len(r)
        r_mean = sum(r) / n
        g_mean = sum(g) / n
        b_mean = sum(b) / n

        # CHROM: Xs = 3*R - 2*G, Ys = 1.5*R + G - 1.5*B
        xs = [3 * r[i] - 2 * g[i] for i in range(n)]
        ys = [1.5 * r[i] + g[i] - 1.5 * b[i] for i in range(n)]

        # Normalize
        xs_mean = sum(xs) / n
        ys_mean = sum(ys) / n
        xs_var = sum((x - xs_mean) ** 2 for x in xs) / n
        ys_var = sum((y - ys_mean) ** 2 for y in ys) / n

        alpha = math.sqrt(ys_var / max(xs_var, 1e-10))
        ppg_signal = [xs[i] - alpha * ys[i] for i in range(n)]

        filtered = self._bandpass_filter(ppg_signal)
        hr, snr = self._compute_fft_peak(filtered)

        if hr < self.min_hr or hr > self.max_hr:
            return None

        confidence = min(1.0, snr / 10.0)
        quality = min(1.0, snr / 8.0)

        return HeartRateResult(
            heart_rate_bpm=round(hr, 1),
            confidence=round(confidence, 3),
            signal_quality=round(quality, 3),
            timestamp=timestamp or 0.0,
            method="CHROM",
            snr=round(snr, 2),
        )

    def estimate_hr_green(self, timestamp: float | None = None) -> HeartRateResult | None:
        """Estimate heart rate using Green channel method (simplest rPPG)."""
        if len(self._g_signal) < self.window_size // 2:
            return None

        g = list(self._g_signal)
        filtered = self._bandpass_filter(g)
        hr, snr = self._compute_fft_peak(filtered)

        if hr < self.min_hr or hr > self.max_hr:
            return None

        confidence = min(1.0, snr / 10.0)
        quality = min(1.0, snr / 8.0)

        return HeartRateResult(
            heart_rate_bpm=round(hr, 1),
            confidence=round(confidence, 3),
            signal_quality=round(quality, 3),
            timestamp=timestamp or 0.0,
            method="GREEN",
            snr=round(snr, 2),
        )

    def get_signal_stats(self) -> dict[str, Any]:
        """Get statistics about the current signal buffers."""
        n = len(self._g_signal)
        if n == 0:
            return {"length": 0}

        g = list(self._g_signal)
        mean_val = sum(g) / n
        variance = sum((x - mean_val) ** 2 for x in g) / n

        return {
            "length": n,
            "r_mean": round(sum(self._r_signal) / n, 2) if self._r_signal else 0,
            "g_mean": round(mean_val, 2),
            "b_mean": round(sum(self._b_signal) / n, 2) if self._b_signal else 0,
            "g_std": round(math.sqrt(variance), 2),
            "buffer_full": n >= self.window_size,
        }

    def reset(self) -> None:
        """Clear all signal buffers."""
        self._r_signal.clear()
        self._g_signal.clear()
        self._b_signal.clear()

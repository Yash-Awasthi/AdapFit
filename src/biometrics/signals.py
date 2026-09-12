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


@dataclass
class HRVFeatures:
    """Comprehensive HRV feature set."""
    # Time domain
    mean_rr_ms: float
    sdnn_ms: float  # Standard deviation of NN intervals
    rmssd_ms: float  # Root mean square of successive differences
    sdsd_ms: float  # Standard deviation of successive differences
    nn50_count: int  # Number of successive differences > 50ms
    pnn50_pct: float  # Percentage of NN50
    nn20_count: int
    pnn20_pct: float
    range_rr_ms: float
    median_rr_ms: float

    # Frequency domain
    vlf_power: float  # Very Low Frequency (0.003-0.04 Hz)
    lf_power: float  # Low Frequency (0.04-0.15 Hz)
    hf_power: float  # High Frequency (0.15-0.4 Hz)
    lf_hf_ratio: float
    total_power: float
    lf_nu: float  # Normalized units
    hf_nu: float

    # Non-linear
    sample_entropy: float
    poincare_sd1: float
    poincare_sd2: float


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


class HRVAnalyzer:
    """Extracts comprehensive HRV features from RR interval data."""

    def __init__(self, sampling_rate: float = 250.0) -> None:
        self.sampling_rate = sampling_rate

    def analyze(self, rr_intervals_ms: list[float]) -> HRVFeatures:
        """Compute full HRV feature set from RR intervals."""
        if len(rr_intervals_ms) < 2:
            return self._empty_features()

        rr = [r for r in rr_intervals_ms if 300 <= r <= 1500]  # Filter outliers
        if len(rr) < 2:
            return self._empty_features()

        # Time domain
        n = len(rr)
        mean_rr = sum(rr) / n
        variance = sum((r - mean_rr) ** 2 for r in rr) / (n - 1)
        sdnn = math.sqrt(variance)

        # Successive differences
        diffs = [rr[i+1] - rr[i] for i in range(n - 1)]
        diffs_sq = [d * d for d in diffs]
        rmssd = math.sqrt(sum(diffs_sq) / len(diffs_sq))

        abs_diffs = [abs(d) for d in diffs]
        sdsd = math.sqrt(sum((d - sum(abs_diffs)/len(abs_diffs))**2 for d in abs_diffs) / max(len(abs_diffs)-1, 1))

        nn50 = sum(1 for d in abs_diffs if d > 50)
        pnn50 = nn50 / max(len(abs_diffs), 1) * 100
        nn20 = sum(1 for d in abs_diffs if d > 20)
        pnn20 = nn20 / max(len(abs_diffs), 1) * 100

        sorted_rr = sorted(rr)
        range_rr = sorted_rr[-1] - sorted_rr[0]
        median_rr = sorted_rr[n // 2]

        # Frequency domain (simplified using autocorrelation-based approximation)
        vlf, lf, hf = self._estimate_frequency_powers(rr, mean_rr)

        total_power = vlf + lf + hf
        lf_hf = lf / max(hf, 0.001)
        lf_nu = lf / max(lf + hf, 0.001) * 100
        hf_nu = hf / max(lf + hf, 0.001) * 100

        # Non-linear: Poincaré
        sd1, sd2 = self._poincare(rr)

        # Sample entropy (simplified)
        samp_en = self._sample_entropy(rr, m=2, r=0.2 * sdnn)

        return HRVFeatures(
            mean_rr_ms=round(mean_rr, 2),
            sdnn_ms=round(sdnn, 2),
            rmssd_ms=round(rmssd, 2),
            sdsd_ms=round(sdsd, 2),
            nn50_count=nn50,
            pnn50_pct=round(pnn50, 2),
            nn20_count=nn20,
            pnn20_pct=round(pnn20, 2),
            range_rr_ms=round(range_rr, 2),
            median_rr_ms=round(median_rr, 2),
            vlf_power=round(vlf, 2),
            lf_power=round(lf, 2),
            hf_power=round(hf, 2),
            lf_hf_ratio=round(lf_hf, 3),
            total_power=round(total_power, 2),
            lf_nu=round(lf_nu, 2),
            hf_nu=round(hf_nu, 2),
            sample_entropy=round(samp_en, 4),
            poincare_sd1=round(sd1, 2),
            poincare_sd2=round(sd2, 2),
        )

    def _estimate_frequency_powers(
        self, rr: list[float], mean_rr: float
    ) -> tuple[float, float, float]:
        """Estimate VLF, LF, HF power using periodogram approach."""
        # Detrend
        detrended = [r - mean_rr for r in rr]
        n = len(detrended)

        # Hanning window
        windowed = [detrended[i] * (0.5 - 0.5 * math.cos(2 * math.pi * i / n)) for i in range(n)]

        # Compute power spectrum at target frequencies
        dt = mean_rr / 1000  # Convert ms to seconds
        freqs = [k / (n * dt) for k in range(n // 2)]

        powers = []
        for k in range(n // 2):
            real_part = sum(windowed[i] * math.cos(2 * math.pi * k * i / n) for i in range(n))
            imag_part = sum(windowed[i] * math.sin(2 * math.pi * k * i / n) for i in range(n))
            powers.append((real_part**2 + imag_part**2) / n)

        # Integrate over frequency bands
        def band_power(low: float, high: float) -> float:
            total = 0
            for j, f in enumerate(freqs):
                if low <= f <= high and j < len(powers):
                    total += powers[j] * (freqs[1] - freqs[0] if len(freqs) > 1 else 1)
            return total

        vlf = band_power(0.003, 0.04)
        lf = band_power(0.04, 0.15)
        hf = band_power(0.15, 0.4)

        return vlf, lf, hf

    def _poincare(self, rr: list[float]) -> tuple[float, float]:
        """Compute Poincaré plot features SD1 and SD2."""
        n = len(rr)
        if n < 2:
            return 0.0, 0.0

        diffs = [rr[i+1] - rr[i] for i in range(n - 1)]
        diff_sq = [d * d for d in diffs]

        sd1 = math.sqrt(sum(diff_sq) / (2 * len(diffs))) if diffs else 0

        # SD2: longitudinal variability
        mean_rr = sum(rr) / n
        sd2 = math.sqrt(sum((r - mean_rr)**2 for r in rr) / n) * math.sqrt(2)

        return sd1, sd2

    def _sample_entropy(self, data: list[float], m: int = 2, r: float = 0.2) -> float:
        """Simplified sample entropy computation."""
        n = len(data)
        if n < m + 2 or r <= 0:
            return 0.0

        # Count template matches
        def count_matches(length: int) -> int:
            count = 0
            templates = []
            for i in range(n - length):
                templates.append(tuple(data[i:i+length]))
            for i in range(len(templates)):
                for j in range(i + 1, len(templates)):
                    if all(abs(templates[i][k] - templates[j][k]) <= r for k in range(length)):
                        count += 1
            return count

        a = count_matches(m)
        b = count_matches(m + 1)

        if a == 0 or b == 0:
            return 0.0

        return -math.log(b / a)

    def _empty_features(self) -> HRVFeatures:
        """Return empty HRV features."""
        return HRVFeatures(
            mean_rr_ms=0, sdnn_ms=0, rmssd_ms=0, sdsd_ms=0,
            nn50_count=0, pnn50_pct=0, nn20_count=0, pnn20_pct=0,
            range_rr_ms=0, median_rr_ms=0,
            vlf_power=0, lf_power=0, hf_power=0, lf_hf_ratio=0,
            total_power=0, lf_nu=0, hf_nu=0,
            sample_entropy=0, poincare_sd1=0, poincare_sd2=0,
        )

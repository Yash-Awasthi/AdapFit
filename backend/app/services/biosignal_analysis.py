"""Biosignal Analysis — ECG, EDA, and Signal Processing.

Extracted from biobss (inspiration).
ECG R-peak detection, morphological feature extraction,
EDA decomposition (phasic/tonic), signal entropy, Hjorth parameters.

All pure functions — no DB, no async, just math.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional


# --- ECG Peak Detection (Pan-Tompkins inspired) ---

def detect_r_peaks_simple(
    signal: list[float],
    sampling_rate: float = 250.0,
) -> list[int]:
    """Detect R-peak locations using a simplified Pan-Tompkins algorithm.

    Steps: bandpass filter (derivative + squaring + moving average) → threshold.

    Args:
        signal: ECG signal samples
        sampling_rate: Sampling rate in Hz

    Returns:
        List of R-peak sample indices
    """
    if len(signal) < 10 or sampling_rate <= 0:
        return []

    n = len(signal)

    # Step 1: Derivative (5-point)
    derivative = [0.0] * n
    for i in range(2, n - 2):
        derivative[i] = (2 * signal[i + 1] + signal[i + 2] - signal[i - 2] - 2 * signal[i - 1]) / 8.0

    # Step 2: Squaring
    squared = [d * d for d in derivative]

    # Step 3: Moving window integration
    window_size = int(0.15 * sampling_rate)  # 150ms window
    if window_size < 1:
        window_size = 1
    integrated = [0.0] * n
    running_sum = 0.0
    for i in range(n):
        running_sum += squared[i]
        if i >= window_size:
            running_sum -= squared[i - window_size]
        integrated[i] = running_sum / window_size

    # Step 4: Adaptive thresholding
    signal_peaks = []
    noise_peaks = []
    threshold_i = max(integrated) * 0.25 if max(integrated) > 0 else 1.0
    spki = threshold_i  # signal peak estimate
    npki = threshold_i * 0.1  # noise peak estimate

    min_rr = int(0.2 * sampling_rate)  # 200ms minimum RR interval
    last_peak = -min_rr

    for i in range(window_size, n - window_size):
        # A QRS complex wider than one sample integrates to a flat plateau, so
        # the right-hand comparison must accept equality or no peak is ever
        # found. Taking >= on the right selects the plateau's last sample.
        if integrated[i] > integrated[i - 1] and integrated[i] >= integrated[i + 1]:
            if integrated[i] > threshold_i and (i - last_peak) >= min_rr:
                # Find the actual R-peak in the original signal near this location
                search_start = max(0, i - window_size)
                search_end = min(n, i + window_size)
                local_max_idx = max(range(search_start, search_end), key=lambda j: signal[j])

                if not signal_peaks or (local_max_idx - signal_peaks[-1]) >= min_rr:
                    signal_peaks.append(local_max_idx)
                    spki = 0.125 * integrated[i] + 0.875 * spki
                    last_peak = local_max_idx
                else:
                    noise_peaks.append(i)
                    npki = 0.125 * integrated[i] + 0.875 * npki
            else:
                noise_peaks.append(i)
                npki = 0.125 * integrated[i] + 0.875 * npki

            threshold_i = npki + 0.25 * (spki - npki)

    return signal_peaks


def compute_rr_intervals(
    r_peaks: list[int],
    sampling_rate: float = 250.0,
) -> list[float]:
    """Compute RR intervals from R-peak locations.

    Args:
        r_peaks: R-peak sample indices
        sampling_rate: Sampling rate in Hz

    Returns:
        RR intervals in milliseconds
    """
    if len(r_peaks) < 2:
        return []
    return [
        (r_peaks[i + 1] - r_peaks[i]) / sampling_rate * 1000.0
        for i in range(len(r_peaks) - 1)
    ]


def compute_ecg_morphology(
    signal: list[float],
    r_peaks: list[int],
    sampling_rate: float = 250.0,
) -> dict:
    """Compute ECG morphological features.

    Extracts RR intervals, heart rate, HRV metrics, and wave timing estimates.

    Args:
        signal: ECG signal samples
        r_peaks: R-peak locations
        sampling_rate: Sampling rate in Hz

    Returns:
        Dictionary of morphological features
    """
    if len(r_peaks) < 2:
        return {"error": "Need at least 2 R-peaks"}

    rr = compute_rr_intervals(r_peaks, sampling_rate)
    if not rr:
        return {"error": "No RR intervals"}

    mean_rr = sum(rr) / len(rr)
    hr = 60000.0 / mean_rr if mean_rr > 0 else 0.0

    # HRV metrics
    n = len(rr)
    rr_var = sum((r - mean_rr) ** 2 for r in rr) / max(n - 1, 1)
    sdnn = math.sqrt(rr_var)

    sq_diffs = [(rr[i + 1] - rr[i]) ** 2 for i in range(n - 1)]
    rmssd = math.sqrt(sum(sq_diffs) / max(n - 1, 1))

    nn50 = sum(1 for i in range(n - 1) if abs(rr[i + 1] - rr[i]) > 50.0)
    pnn50 = (nn50 / max(n - 1, 1)) * 100.0

    # Simple QRS width estimate (half of RR interval range)
    qrs_width_ms = (max(rr) - min(rr)) * 0.1 if len(rr) > 1 else 0.0

    # R-peak amplitude statistics
    r_amplitudes = [signal[peak] for peak in r_peaks if 0 <= peak < len(signal)]

    return {
        "rr_intervals_ms": rr,
        "mean_rr_ms": round(mean_rr, 2),
        "heart_rate_bpm": round(hr, 1),
        "sdnn_ms": round(sdnn, 2),
        "rmssd_ms": round(rmssd, 2),
        "nn50": nn50,
        "pnn50_pct": round(pnn50, 2),
        "qrs_width_est_ms": round(qrs_width_ms, 2),
        "r_peak_count": len(r_peaks),
        "r_amplitude_mean": round(sum(r_amplitudes) / len(r_amplitudes), 4) if r_amplitudes else 0.0,
        "r_amplitude_std": round(
            math.sqrt(sum((a - sum(r_amplitudes) / len(r_amplitudes)) ** 2 for a in r_amplitudes) / len(r_amplitudes)),
            4,
        ) if len(r_amplitudes) > 1 else 0.0,
    }


# --- EDA Analysis ---

def eda_decompose(
    signal: list[float],
    sampling_rate: float = 20.0,
) -> dict:
    """Decompose EDA signal into phasic and tonic components.

    Uses a simple low-pass filter for tonic and subtraction for phasic.

    Args:
        signal: Raw EDA signal (skin conductance)
        sampling_rate: Sampling rate in Hz

    Returns:
        Dictionary with tonic and phasic components
    """
    if not signal:
        return {"tonic": [], "phasic": []}

    n = len(signal)

    # Tonic: low-pass filtered (exponential moving average, 0.5s window)
    alpha = 1.0 - math.exp(-1.0 / (0.5 * sampling_rate))
    tonic = [0.0] * n
    tonic[0] = signal[0]
    for i in range(1, n):
        tonic[i] = tonic[i - 1] + alpha * (signal[i] - tonic[i - 1])

    # Phasic: raw minus tonic
    phasic = [signal[i] - tonic[i] for i in range(n)]

    return {
        "tonic": tonic,
        "phasic": phasic,
        "tonic_mean": round(sum(tonic) / n, 4),
        "phasic_rms": round(math.sqrt(sum(p ** 2 for p in phasic) / n), 4),
    }


def eda_features(
    signal: list[float],
    sampling_rate: float = 20.0,
) -> dict:
    """Extract EDA features from a raw signal.

    Decomposes into phasic/tonic, then extracts features from both.

    Args:
        signal: Raw EDA signal
        sampling_rate: Sampling rate in Hz

    Returns:
        Dictionary of EDA features
    """
    if not signal:
        return {"error": "Empty signal"}

    decomp = eda_decompose(signal, sampling_rate)
    tonic = decomp["tonic"]
    phasic = decomp["phasic"]
    n = len(signal)

    # Tonic features (SCL - Skin Conductance Level)
    tonic_mean = decomp["tonic_mean"]
    tonic_range = max(tonic) - min(tonic) if tonic else 0.0

    # Phasic features (SCR - Skin Conductance Response)
    # Count SCR peaks (local maxima in phasic signal)
    threshold = max(phasic) * 0.1 if max(phasic) > 0 else 0.01
    scr_count = 0
    for i in range(1, n - 1):
        if phasic[i] > phasic[i - 1] and phasic[i] > phasic[i + 1] and phasic[i] > threshold:
            scr_count += 1

    phasic_rms = decomp["phasic_rms"]

    return {
        "tonic_mean_scl": tonic_mean,
        "tonic_range": round(tonic_range, 4),
        "phasic_rms": phasic_rms,
        "scr_count": scr_count,
        "scr_frequency_per_min": round(scr_count / (n / sampling_rate / 60.0), 2) if n > 0 else 0.0,
        "signal_length_sec": round(n / sampling_rate, 2),
    }


# --- Signal Processing Utilities ---

def calculate_shannon_entropy(
    signal: list[float],
    bins: int = 20,
) -> float:
    """Calculate Shannon entropy of a signal.

    S(X) = -sum(p(xi) * log2(p(xi)))

    Args:
        signal: Input signal
        bins: Number of histogram bins for discretization

    Returns:
        Shannon entropy in bits
    """
    if not signal:
        return 0.0

    # Discretize signal into bins
    min_val = min(signal)
    max_val = max(signal)
    if min_val == max_val:
        return 0.0

    range_val = max_val - min_val
    counts = [0] * bins
    for val in signal:
        idx = min(int((val - min_val) / range_val * bins), bins - 1)
        counts[idx] += 1

    total = len(signal)
    entropy = 0.0
    for count in counts:
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)

    return round(entropy, 4)


def calculate_sample_entropy(
    signal: list[float],
    m: int = 2,
    r: float = 0.2,
) -> float:
    """Calculate sample entropy of a signal.

    Measures signal complexity/regularity. Higher values indicate more
    complexity/randomness.

    Args:
        signal: Input signal
        m: Embedding dimension (default 2)
        r: Tolerance (fraction of std, default 0.2)

    Returns:
        Sample entropy value
    """
    n = len(signal)
    if n < m + 2:
        return 0.0

    std = math.sqrt(sum((x - sum(signal) / n) ** 2 for x in signal) / n)
    if std == 0:
        return 0.0

    tolerance = r * std

    def count_matches(dim: int) -> int:
        count = 0
        for i in range(n - dim):
            for j in range(i + 1, n - dim):
                match = all(
                    abs(signal[i + k] - signal[j + k]) < tolerance
                    for k in range(dim)
                )
                if match:
                    count += 1
        return count

    a = count_matches(m)
    b = count_matches(m + 1)

    if a == 0 or b == 0:
        return 0.0

    return -math.log(b / a)


def hjorth_parameters(
    signal: list[float],
) -> dict:
    """Calculate Hjorth parameters (activity, mobility, complexity).

    Activity: signal variance
    Mobility: mean frequency
    Complexity: signal bandwidth change

    Args:
        signal: Input signal

    Returns:
        Dictionary with activity, mobility, complexity
    """
    n = len(signal)
    if n < 3:
        return {"activity": 0.0, "mobility": 0.0, "complexity": 0.0}

    mean_val = sum(signal) / n
    activity = sum((x - mean_val) ** 2 for x in signal) / n

    if activity == 0:
        return {"activity": 0.0, "mobility": 0.0, "complexity": 0.0}

    # First derivative
    d1 = [signal[i + 1] - signal[i] for i in range(n - 1)]
    # Second derivative
    d2 = [d1[i + 1] - d1[i] for i in range(len(d1) - 1)]

    mob_num = sum(x ** 2 for x in d1) / len(d1)
    mobility = math.sqrt(mob_num / activity) if activity > 0 else 0.0

    if mob_num > 0:
        comp_num = sum(x ** 2 for x in d2) / len(d2)
        complexity = math.sqrt(comp_num / mob_num)
    else:
        complexity = 0.0

    return {
        "activity": round(activity, 6),
        "mobility": round(mobility, 6),
        "complexity": round(complexity, 6),
    }


def bandpower(
    signal: list[float],
    sampling_rate: float = 250.0,
    low_freq: float = 0.5,
    high_freq: float = 40.0,
) -> float:
    """Estimate bandpower using the trapezoidal rule on a periodogram.

    Args:
        signal: Input signal
        sampling_rate: Sampling rate in Hz
        low_freq: Lower frequency bound (Hz)
        high_freq: Upper frequency bound (Hz)

    Returns:
        Bandpower in signal units squared
    """
    n = len(signal)
    if n < 4:
        return 0.0

    # Simple DFT magnitude squared (periodogram)
    freqs = []
    powers = []
    for k in range(1, n // 2):
        freq = k * sampling_rate / n
        if freq < low_freq or freq > high_freq:
            continue

        real_part = sum(signal[j] * math.cos(2 * math.pi * k * j / n) for j in range(n))
        imag_part = sum(signal[j] * math.sin(2 * math.pi * k * j / n) for j in range(n))
        power = (real_part ** 2 + imag_part ** 2) / (n * sampling_rate)

        freqs.append(freq)
        powers.append(power)

    if len(freqs) < 2:
        return 0.0

    # Trapezoidal integration
    total = 0.0
    for i in range(1, len(freqs)):
        total += (freqs[i] - freqs[i - 1]) * (powers[i] + powers[i - 1]) / 2.0

    return round(total, 6)


def signal_quality_index(
    signal: list[float],
    sampling_rate: float = 250.0,
) -> dict:
    """Estimate signal quality using statistical measures.

    Args:
        signal: Input signal
        sampling_rate: Sampling rate in Hz

    Returns:
        Quality assessment with SNR estimate and clipping detection
    """
    if not signal:
        return {"quality": "unknown", "snr_db": 0.0, "clipping": False}

    n = len(signal)
    mean_val = sum(signal) / n
    variance = sum((x - mean_val) ** 2 for x in signal) / n

    # Check for clipping (values at min or max)
    min_val = min(signal)
    max_val = max(signal)
    clip_count = sum(1 for x in signal if x == min_val or x == max_val)
    clipping = clip_count / n > 0.05  # more than 5% at limits

    # Simple SNR estimate: signal variance / noise variance (assumes noise is high-freq)
    # Use differences as noise estimate
    diffs = [signal[i + 1] - signal[i] for i in range(n - 1)]
    noise_var = sum(d ** 2 for d in diffs) / len(diffs)
    signal_var = variance

    snr = 10 * math.log10(signal_var / noise_var) if noise_var > 0 else 0.0

    # Quality classification
    if clipping:
        quality = "poor"
    elif snr < 10:
        quality = "fair"
    elif snr < 20:
        quality = "good"
    else:
        quality = "excellent"

    return {
        "quality": quality,
        "snr_db": round(snr, 2),
        "clipping": clipping,
        "variance": round(variance, 6),
        "dynamic_range": round(max_val - min_val, 6),
    }

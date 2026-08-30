"""
Sleep Staging Service — Extracted from YASA (Yet Another Spindle Algorithm) patterns.

Provides automatic sleep staging from physiological signals, sleep spindle
detection, slow oscillation analysis, and sleep quality metrics.
Inspired by YASA's multi-band spectral analysis approach.

All functions are pure — no DB, no async, just signal processing math.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Enums and data structures
# ---------------------------------------------------------------------------

class SleepStage(str, Enum):
    """Standard sleep stages (AASM classification)."""
    WAKE = "W"
    N1 = "N1"
    N2 = "N2"
    N3 = "N3"  # Deep sleep / SWS
    REM = "REM"


@dataclass
class EEGSample:
    """Single EEG data point."""
    timestamp: float  # seconds from recording start
    value: float  # microvolts
    channel: str = "C3"  # default EEG channel


@dataclass
class SleepEpoch:
    """30-second epoch with sleep stage and confidence."""
    epoch_number: int
    start_time: float  # seconds
    end_time: float  # seconds
    stage: SleepStage
    confidence: float  # 0.0-1.0
    features: Dict[str, float] = field(default_factory=dict)


@dataclass
class SleepSpindle:
    """Detected sleep spindle event."""
    onset: float  # seconds
    offset: float  # seconds
    duration: float  # seconds
    frequency: float  # Hz (typically 11-16 Hz)
    amplitude: float  # microvolts
    density: float  # spindles per minute
    channel: str = "C3"


@dataclass
class SlowOscillation:
    """Detected slow oscillation event."""
    onset: float  # seconds
    offset: float  # seconds
    duration: float  # seconds (typically 0.5-1.0 Hz)
    amplitude: float  # microvolts
    up_phase_peak: float  # peak of up-phase
    down_phase_trough: float  # trough of down-phase


@dataclass
class SleepArchitecture:
    """Complete sleep architecture analysis."""
    total_record_time: float  # minutes
    total_sleep_time: float  # minutes
    sleep_onset_latency: float  # minutes
    wake_after_sleep_onset: float  # minutes
    sleep_efficiency: float  # percentage
    # Stage percentages (of TST)
    pct_wake: float
    pct_n1: float
    pct_n2: float
    pct_n3: float
    pct_rem: float
    # Cycling
    rem_latency: float  # minutes from sleep onset to first REM
    cycle_count: int
    avg_cycle_length: float  # minutes
    # Quality scores
    deep_sleep_score: float  # 0-100
    rem_score: float  # 0-100
    overall_quality: float  # 0-100


# ---------------------------------------------------------------------------
# Signal processing utilities
# ---------------------------------------------------------------------------

def _bandpass_filter(
    signal: List[float],
    low_freq: float,
    high_freq: float,
    sampling_rate: float,
) -> List[float]:
    """
    Simple bandpass filter using moving average approximation.
    
    For production use, scipy.signal.butter + sosfilt would be preferred.
    This is a lightweight approximation for the sleep staging pipeline.
    """
    if len(signal) < 3:
        return signal[:]
    
    # Simple moving average as low-pass approximation
    window_low = max(1, int(sampling_rate / high_freq))
    window_high = max(1, int(sampling_rate / low_freq))
    
    # High-pass: subtract long MA from signal
    long_ma = _moving_average(signal, window_high)
    high_passed = [signal[i] - long_ma[i] for i in range(len(signal))]
    
    # Low-pass: apply short MA
    result = _moving_average(high_passed, window_low)
    
    return result


def _moving_average(data: List[float], window: int) -> List[float]:
    """Compute centered moving average."""
    if window <= 0 or not data:
        return data[:]
    
    window = min(window, len(data))
    result = []
    half = window // 2
    
    for i in range(len(data)):
        start = max(0, i - half)
        end = min(len(data), i + half + 1)
        result.append(sum(data[start:end]) / (end - start))
    
    return result


def _compute_power_spectral_density(
    signal: List[float],
    sampling_rate: float,
    freq_bins: Optional[List[float]] = None,
) -> Dict[str, float]:
    """
    Compute PSD using periodogram (simplified DFT).
    
    Returns power in standard EEG frequency bands:
    - Delta: 0.5-4 Hz
    - Theta: 4-8 Hz
    - Alpha: 8-13 Hz
    - Sigma: 11-16 Hz (spindle band)
    - Beta: 16-30 Hz
    """
    n = len(signal)
    if n < 4:
        return {"delta": 0, "theta": 0, "alpha": 0, "sigma": 0, "beta": 0}
    
    # Simplified: compute band power via autocorrelation
    # For full DFT, use numpy.fft
    
    bands = {
        "delta": (0.5, 4.0),
        "theta": (4.0, 8.0),
        "alpha": (8.0, 13.0),
        "sigma": (11.0, 16.0),
        "beta": (16.0, 30.0),
    }
    
    result = {}
    for band_name, (low, high) in bands.items():
        # Estimate band power using zero-crossing rate and amplitude
        band_signal = _bandpass_filter(signal, low, high, sampling_rate)
        power = sum(x ** 2 for x in band_signal) / n
        result[band_name] = power
    
    return result


def _compute_hjorth_parameters(signal: List[float]) -> Dict[str, float]:
    """
    Compute Hjorth parameters: Activity, Mobility, Complexity.
    
    These are classic EEG descriptors used in sleep staging.
    """
    if len(signal) < 3:
        return {"activity": 0, "mobility": 0, "complexity": 0}
    
    # Activity: variance of the signal
    mean = sum(signal) / len(signal)
    activity = sum((x - mean) ** 2 for x in signal) / len(signal)
    
    # First derivative
    d1 = [signal[i + 1] - signal[i] for i in range(len(signal) - 1)]
    # Second derivative
    d2 = [d1[i + 1] - d1[i] for i in range(len(d1) - 1)]
    
    # Mobility: sqrt(var(d1) / var(signal))
    d1_var = sum(x ** 2 for x in d1) / len(d1) - (sum(d1) / len(d1)) ** 2
    mobility = math.sqrt(abs(d1_var / activity)) if activity > 0 else 0
    
    # Complexity: mobility(d1) / mobility(signal)
    d2_var = sum(x ** 2 for x in d2) / len(d2) - (sum(d2) / len(d2)) ** 2
    d1_var_for_complexity = d1_var
    mobility_d1 = math.sqrt(abs(d2_var / d1_var_for_complexity)) if d1_var_for_complexity > 0 else 0
    complexity = _safe_div(mobility_d1, mobility)
    
    return {"activity": activity, "mobility": mobility, "complexity": complexity}


def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    """Safe division."""
    return a / b if b != 0 else default


# ---------------------------------------------------------------------------
# Sleep stage classification
# ---------------------------------------------------------------------------

def classify_epoch(
    eeg_samples: List[EEGSample],
    eog_samples: Optional[List[float]] = None,
    emg_samples: Optional[List[float]] = None,
    sampling_rate: float = 256.0,
) -> Tuple[SleepStage, float, Dict[str, float]]:
    """
    Classify a 30-second epoch into a sleep stage.
    
    Uses rule-based classification inspired by YASA's approach:
    1. Compute spectral features (band powers)
    2. Compute Hjorth parameters
    3. Apply decision tree rules
    
    Args:
        eeg_samples: 30 seconds of EEG data
        eog_samples: Optional EOG data for REM detection
        emg_samples: Optional EMG data for muscle tone
        sampling_rate: Sampling rate in Hz
    
    Returns:
        (stage, confidence, features_dict)
    """
    if not eeg_samples:
        return SleepStage.WAKE, 0.0, {}
    
    values = [s.value for s in eeg_samples]
    
    # Compute features
    psd = _compute_power_spectral_density(values, sampling_rate)
    hjorth = _compute_hjorth_parameters(values)
    
    # Band ratios
    delta_power = psd.get("delta", 0)
    theta_power = psd.get("theta", 0)
    alpha_power = psd.get("alpha", 0)
    sigma_power = psd.get("sigma", 0)
    beta_power = psd.get("beta", 0)
    
    total_power = delta_power + theta_power + alpha_power + sigma_power + beta_power
    
    if total_power > 0:
        delta_ratio = delta_power / total_power
        theta_ratio = theta_power / total_power
        alpha_ratio = alpha_power / total_power
        sigma_ratio = sigma_power / total_power
        beta_ratio = beta_power / total_power
    else:
        delta_ratio = theta_ratio = alpha_ratio = sigma_ratio = beta_ratio = 0
    
    # EMG tone (simplified)
    emg_power = 0.0
    if emg_samples and emg_samples:
        emg_power = sum(x ** 2 for x in emg_samples) / len(emg_samples)
    
    features = {
        "delta_ratio": delta_ratio,
        "theta_ratio": theta_ratio,
        "alpha_ratio": alpha_ratio,
        "sigma_ratio": sigma_ratio,
        "beta_ratio": beta_ratio,
        "emg_power": emg_power,
        "hjorth_activity": hjorth["activity"],
        "hjorth_mobility": hjorth["mobility"],
        "hjorth_complexity": hjorth["complexity"],
    }
    
    # Decision rules (simplified YASA-like logic)
    confidence = 0.5
    
    # Wake: high alpha, low delta, high EMG
    if alpha_ratio > 0.3 and delta_ratio < 0.3:
        confidence = min(0.9, 0.5 + alpha_ratio)
        return SleepStage.WAKE, confidence, features
    
    # N3 (deep sleep): high delta
    if delta_ratio > 0.4:
        confidence = min(0.85, 0.5 + delta_ratio * 0.5)
        return SleepStage.N3, confidence, features
    
    # REM: low EMG, theta dominant, sawtooth waves (simplified)
    if emg_power < 50 and theta_ratio > 0.3 and delta_ratio < 0.3:
        confidence = min(0.8, 0.5 + theta_ratio * 0.5)
        return SleepStage.REM, confidence, features
    
    # N2: sigma spindles present
    if sigma_ratio > 0.15:
        confidence = min(0.75, 0.5 + sigma_ratio)
        return SleepStage.N2, confidence, features
    
    # N1: theta dominant, transition stage
    if theta_ratio > 0.25:
        confidence = 0.55
        return SleepStage.N1, confidence, features
    
    # Default to N2 if ambiguous
    return SleepStage.N2, 0.4, features


def stage_full_night(
    eeg_epochs: List[List[EEGSample]],
    sampling_rate: float = 256.0,
) -> List[SleepEpoch]:
    """
    Stage an entire night of sleep from 30-second epochs.
    
    Args:
        eeg_epochs: List of 30-second EEG epoch data
        sampling_rate: Sampling rate in Hz
    
    Returns:
        List of SleepEpoch with classified stages
    """
    epochs = []
    for i, epoch_data in enumerate(eeg_epochs):
        stage, confidence, features = classify_epoch(
            epoch_data, sampling_rate=sampling_rate
        )
        epochs.append(SleepEpoch(
            epoch_number=i,
            start_time=i * 30.0,
            end_time=(i + 1) * 30.0,
            stage=stage,
            confidence=confidence,
            features=features,
        ))
    
    return epochs


# ---------------------------------------------------------------------------
# Sleep spindle detection
# ---------------------------------------------------------------------------

def detect_spindles(
    eeg_samples: List[EEGSample],
    sampling_rate: float = 256.0,
    min_duration: float = 0.5,
    max_duration: float = 2.0,
    min_amplitude: float = 5.0,
    freq_range: Tuple[float, float] = (11.0, 16.0),
) -> List[SleepSpindle]:
    """
    Detect sleep spindles using bandpass filtering + amplitude thresholding.
    
    Sleep spindles are bursts of 11-16 Hz activity lasting 0.5-2.0 seconds,
    characteristic of N2 sleep.
    
    Inspired by YASA's multi-channel spindle detection algorithm.
    """
    if not eeg_samples:
        return []
    
    values = [s.value for s in eeg_samples]
    timestamps = [s.timestamp for s in eeg_samples]
    
    # Bandpass filter to sigma band
    sigma_signal = _bandpass_filter(values, freq_range[0], freq_range[1], sampling_rate)
    
    # Compute envelope (absolute value)
    envelope = [abs(x) for x in sigma_signal]
    
    # Smooth envelope
    smooth_window = int(sampling_rate * 0.1)  # 100ms smoothing
    smoothed = _moving_average(envelope, smooth_window)
    
    # Threshold detection
    threshold = min_amplitude
    in_spindle = False
    spindle_start = 0
    spindles = []
    
    for i in range(len(smoothed)):
        if smoothed[i] > threshold and not in_spindle:
            in_spindle = True
            spindle_start = i
        elif smoothed[i] <= threshold and in_spindle:
            in_spindle = False
            duration = (timestamps[i] - timestamps[spindle_start])
            
            if min_duration <= duration <= max_duration:
                # Find peak frequency in spindle
                spindle_data = values[spindle_start:i + 1]
                peak_freq = _estimate_dominant_frequency(
                    spindle_data, sampling_rate, freq_range
                )
                peak_amp = max(spindle_data) - min(spindle_data)
                
                spindles.append(SleepSpindle(
                    onset=timestamps[spindle_start],
                    offset=timestamps[i],
                    duration=duration,
                    frequency=peak_freq,
                    amplitude=peak_amp / 2,
                    density=0,  # Computed later
                ))
    
    # Compute density (spindles per minute)
    if spindles:
        total_duration_min = (timestamps[-1] - timestamps[0]) / 60.0
        density = len(spindles) / max(1, total_duration_min)
        for s in spindles:
            s.density = density
    
    return spindles


def _estimate_dominant_frequency(
    signal: List[float],
    sampling_rate: float,
    freq_range: Tuple[float, float],
) -> float:
    """Estimate dominant frequency in a signal segment."""
    if len(signal) < 4:
        return (freq_range[0] + freq_range[1]) / 2
    
    # Zero-crossing rate approximation
    zero_crossings = sum(
        1 for i in range(1, len(signal))
        if (signal[i] >= 0) != (signal[i - 1] >= 0)
    )
    
    duration = len(signal) / sampling_rate
    freq = zero_crossings / (2 * duration) if duration > 0 else 0
    
    # Clamp to expected range
    return max(freq_range[0], min(freq_range[1], freq))


# ---------------------------------------------------------------------------
# Slow oscillation detection
# ---------------------------------------------------------------------------

def detect_slow_oscillations(
    eeg_samples: List[EEGSample],
    sampling_rate: float = 256.0,
    min_duration: float = 0.5,
    max_duration: float = 2.0,
    min_amplitude: float = 75.0,
) -> List[SlowOscillation]:
    """
    Detect slow oscillations (0.5-1 Hz) in EEG.
    
    Slow oscillations are the hallmark of N3 (deep) sleep.
    They consist of an up-phase (depolarization) followed by
    a down-phase (hyperpolarization).
    """
    if not eeg_samples:
        return []
    
    values = [s.value for s in eeg_samples]
    timestamps = [s.timestamp for s in eeg_samples]
    
    # Low-pass filter to isolate slow oscillations
    so_signal = _bandpass_filter(values, 0.3, 1.5, sampling_rate)
    
    # Find peaks and troughs
    peaks = []
    troughs = []
    
    for i in range(1, len(so_signal) - 1):
        if so_signal[i] > so_signal[i - 1] and so_signal[i] > so_signal[i + 1]:
            peaks.append((i, so_signal[i]))
        elif so_signal[i] < so_signal[i - 1] and so_signal[i] < so_signal[i + 1]:
            troughs.append((i, so_signal[i]))
    
    # Match peaks and troughs into slow oscillation events
    oscillations = []
    
    for peak_idx, peak_val in peaks:
        # Find nearest trough after peak
        for trough_idx, trough_val in troughs:
            if trough_idx > peak_idx:
                duration = timestamps[trough_idx] - timestamps[peak_idx]
                amplitude = peak_val - trough_val
                
                if (min_duration <= duration <= max_duration and
                        amplitude >= min_amplitude):
                    oscillations.append(SlowOscillation(
                        onset=timestamps[peak_idx],
                        offset=timestamps[trough_idx],
                        duration=duration,
                        amplitude=amplitude / 2,
                        up_phase_peak=peak_val,
                        down_phase_trough=trough_val,
                    ))
                break
    
    return oscillations


# ---------------------------------------------------------------------------
# Sleep architecture analysis
# ---------------------------------------------------------------------------

def analyze_architecture(
    epochs: List[SleepEpoch],
    total_record_time_minutes: float,
) -> SleepArchitecture:
    """
    Analyze complete sleep architecture from staged epochs.
    
    Computes standard sleep metrics:
    - Sleep efficiency, latency, WASO
    - Stage percentages
    - REM latency
    - Cycle analysis
    - Quality scores
    """
    if not epochs:
        return SleepArchitecture(
            total_record_time=total_record_time_minutes,
            total_sleep_time=0, sleep_onset_latency=0,
            wake_after_sleep_onset=0, sleep_efficiency=0,
            pct_wake=100, pct_n1=0, pct_n2=0, pct_n3=0, pct_rem=0,
            rem_latency=0, cycle_count=0, avg_cycle_length=0,
            deep_sleep_score=0, rem_score=0, overall_quality=0,
        )
    
    # Stage counts
    stage_counts = {stage: 0 for stage in SleepStage}
    for epoch in epochs:
        stage_counts[epoch.stage] += 1
    
    total_epochs = len(epochs)
    epoch_minutes = 30.0 / 60.0  # 0.5 minutes per epoch
    
    # Sleep onset: first non-Wake epoch
    sleep_onset_epoch = total_epochs  # default: no sleep
    for i, epoch in enumerate(epochs):
        if epoch.stage != SleepStage.WAKE:
            sleep_onset_epoch = i
            break
    
    # WASO: wake epochs after sleep onset
    wake_after_onset = sum(
        1 for epoch in epochs[sleep_onset_epoch:]
        if epoch.stage == SleepStage.WAKE
    )
    
    # Total sleep time (TST)
    total_sleep_epochs = total_epochs - stage_counts[SleepStage.WAKE]
    tst_minutes = total_sleep_epochs * epoch_minutes
    
    # Sleep efficiency
    sol_minutes = sleep_onset_epoch * epoch_minutes
    efficiency = _safe_div(tst_minutes, total_record_time_minutes - sol_minutes) * 100
    
    # Stage percentages (of TST)
    pct_wake = _safe_div(stage_counts[SleepStage.WAKE], total_epochs) * 100
    pct_n1 = _safe_div(stage_counts[SleepStage.N1], total_sleep_epochs) * 100
    pct_n2 = _safe_div(stage_counts[SleepStage.N2], total_sleep_epochs) * 100
    pct_n3 = _safe_div(stage_counts[SleepStage.N3], total_sleep_epochs) * 100
    pct_rem = _safe_div(stage_counts[SleepStage.REM], total_sleep_epochs) * 100
    
    # REM latency
    rem_latency = 0
    for i, epoch in enumerate(epochs[sleep_onset_epoch:], start=sleep_onset_epoch):
        if epoch.stage == SleepStage.REM:
            rem_latency = (i - sleep_onset_epoch) * epoch_minutes
            break
    
    # Cycle analysis (NREM-REM cycles)
    cycles = 0
    current_cycle_start = sleep_onset_epoch
    in_rem = False
    
    for i, epoch in enumerate(epochs[sleep_onset_epoch:], start=sleep_onset_epoch):
        if epoch.stage == SleepStage.REM and not in_rem:
            in_rem = True
        elif epoch.stage != SleepStage.REM and in_rem:
            cycles += 1
            in_rem = False
    
    avg_cycle_length = _safe_div(tst_minutes, max(1, cycles))
    
    # Quality scores
    # Deep sleep: 15-20% is optimal
    deep_score = max(0, 100 - abs(pct_n3 - 17.5) * 5)
    # REM: 20-25% is optimal
    rem_score = max(0, 100 - abs(pct_rem - 22.5) * 4)
    # Overall: weighted combination
    overall = (
        deep_score * 0.3 +
        rem_score * 0.3 +
        min(100, efficiency) * 0.2 +
        max(0, 100 - sol_minutes * 2) * 0.1 +
        max(0, 100 - _safe_div(wake_after_onset * epoch_minutes, 30) * 100) * 0.1
    )
    
    return SleepArchitecture(
        total_record_time=total_record_time_minutes,
        total_sleep_time=tst_minutes,
        sleep_onset_latency=sol_minutes,
        wake_after_sleep_onset=wake_after_onset * epoch_minutes,
        sleep_efficiency=efficiency,
        pct_wake=pct_wake,
        pct_n1=pct_n1,
        pct_n2=pct_n2,
        pct_n3=pct_n3,
        pct_rem=pct_rem,
        rem_latency=rem_latency,
        cycle_count=cycles,
        avg_cycle_length=avg_cycle_length,
        deep_sleep_score=deep_score,
        rem_score=rem_score,
        overall_quality=overall,
    )


def calculate_sleep_debt(
    actual_sleep_hours: float,
    recommended_hours: float = 8.0,
    tracking_days: int = 7,
    daily_sleeps: Optional[List[float]] = None,
) -> Dict[str, float]:
    """
    Calculate sleep debt over a tracking period.
    
    Sleep debt accumulates when consistently sleeping less than needed.
    Research suggests it takes 2-4 nights of recovery sleep to repay
    1 hour of sleep debt.
    
    Returns:
        Dict with sleep_debt_hours, recovery_nights_needed, etc.
    """
    if daily_sleeps:
        total_sleep = sum(daily_sleeps)
        total_needed = recommended_hours * len(daily_sleeps)
    else:
        total_sleep = actual_sleep_hours * tracking_days
        total_needed = recommended_hours * tracking_days
    
    debt_hours = max(0, total_needed - total_sleep)
    
    # Recovery: ~2-4 nights per hour of debt (conservative: 3)
    recovery_nights = math.ceil(debt_hours / 3) if debt_hours > 0 else 0
    
    # Sleep efficiency score (0-100)
    actual_avg = _safe_div(total_sleep, len(daily_sleeps) if daily_sleeps else tracking_days)
    efficiency_score = min(100, _safe_div(actual_avg, recommended_hours) * 100)
    
    return {
        "sleep_debt_hours": round(debt_hours, 1),
        "total_sleep_hours": round(total_sleep, 1),
        "total_needed_hours": round(total_needed, 1),
        "recovery_nights_needed": recovery_nights,
        "average_sleep_hours": round(actual_avg, 1),
        "efficiency_score": round(efficiency_score, 1),
        "tracking_days": len(daily_sleeps) if daily_sleeps else tracking_days,
    }

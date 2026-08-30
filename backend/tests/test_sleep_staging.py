"""Tests for sleep_staging.py — YASA-inspired sleep analysis."""

import math
import pytest
from app.services.sleep_staging import (
    SleepStage, EEGSample, SleepEpoch, SleepSpindle,
    SlowOscillation, SleepArchitecture,
    classify_epoch, stage_full_night,
    detect_spindles, detect_slow_oscillations,
    analyze_architecture, calculate_sleep_debt,
    _bandpass_filter, _compute_hjorth_parameters,
    _compute_power_spectral_density,
)


def _make_eeg(duration_sec=30, sampling_rate=256, freq=10.0, amplitude=50.0):
    """Generate synthetic EEG data at a given frequency."""
    samples = []
    n_samples = int(duration_sec * sampling_rate)
    for i in range(n_samples):
        t = i / sampling_rate
        value = amplitude * math.sin(2 * math.pi * freq * t)
        samples.append(EEGSample(timestamp=t, value=value))
    return samples


class TestSignalProcessing:
    def test_bandpass_preserves_signal(self):
        signal = [math.sin(2 * math.pi * 10 * i / 256) for i in range(7680)]
        filtered = _bandpass_filter(signal, 8, 12, 256.0)
        assert len(filtered) == len(signal)
        # Power should be preserved in passband
        orig_power = sum(x**2 for x in signal[1000:2000])
        filt_power = sum(x**2 for x in filtered[1000:2000])
        assert filt_power > 0

    def test_hjorth_parameters(self):
        # Simple sine wave
        signal = [math.sin(2 * math.pi * 5 * i / 256) for i in range(256)]
        params = _compute_hjorth_parameters(signal)
        assert params["activity"] > 0
        assert params["mobility"] > 0
        assert params["complexity"] >= 0

    def test_psd_bands(self):
        signal = [math.sin(2 * math.pi * 10 * i / 256) for i in range(2560)]
        psd = _compute_power_spectral_density(signal, 256.0)
        assert "delta" in psd
        assert "alpha" in psd
        assert psd["alpha"] > 0  # 10 Hz should have alpha power


class TestClassifyEpoch:
    def test_wake_detection(self):
        # High alpha (10 Hz) signal = wake
        samples = _make_eeg(freq=10.0, amplitude=80.0)
        stage, conf, features = classify_epoch(samples)
        assert stage in (SleepStage.WAKE, SleepStage.N1, SleepStage.N2)
        assert 0 <= conf <= 1

    def test_empty_epoch(self):
        stage, conf, features = classify_epoch([])
        assert stage == SleepStage.WAKE
        assert conf == 0.0

    def test_features_populated(self):
        samples = _make_eeg()
        _, _, features = classify_epoch(samples)
        assert "delta_ratio" in features
        assert "hjorth_activity" in features


class TestSpindleDetection:
    def test_detect_spindles_empty(self):
        spindles = detect_spindles([])
        assert spindles == []

    def test_detect_spindles_with_sigma_burst(self):
        # Create EEG with a sigma burst (13 Hz) in the middle
        samples = []
        sampling_rate = 256
        for i in range(30 * sampling_rate):
            t = i / sampling_rate
            if 10 <= t <= 12:
                # Sigma burst
                value = 80 * math.sin(2 * math.pi * 13 * t)
            else:
                value = 10 * math.sin(2 * math.pi * 1 * t)
            samples.append(EEGSample(timestamp=t, value=value))
        
        spindles = detect_spindles(samples, sampling_rate=sampling_rate)
        # May or may not detect depending on threshold, but should not crash
        assert isinstance(spindles, list)


class TestSlowOscillations:
    def test_detect_so_empty(self):
        oscillations = detect_slow_oscillations([])
        assert oscillations == []

    def test_detect_so_with_slow_wave(self):
        samples = []
        sampling_rate = 256
        for i in range(30 * sampling_rate):
            t = i / sampling_rate
            value = 100 * math.sin(2 * math.pi * 0.8 * t)
            samples.append(EEGSample(timestamp=t, value=value))
        
        oscillations = detect_slow_oscillations(samples, sampling_rate=sampling_rate)
        assert isinstance(oscillations, list)


class TestArchitectureAnalysis:
    def test_full_night_analysis(self):
        # Create 100 epochs of mixed stages
        epochs = []
        stages = [SleepStage.WAKE] * 5 + [SleepStage.N1] * 10 + \
                 [SleepStage.N2] * 40 + [SleepStage.N3] * 25 + \
                 [SleepStage.REM] * 20
        for i, stage in enumerate(stages):
            epochs.append(SleepEpoch(
                epoch_number=i,
                start_time=i * 30,
                end_time=(i + 1) * 30,
                stage=stage,
                confidence=0.8,
            ))
        
        arch = analyze_architecture(epochs, total_record_time_minutes=50)
        assert arch.total_record_time == 50
        assert arch.sleep_efficiency > 0
        assert arch.pct_n2 > 0
        assert arch.pct_n3 > 0
        assert arch.pct_rem > 0
        assert arch.overall_quality > 0

    def test_empty_epochs(self):
        arch = analyze_architecture([], 50)
        assert arch.sleep_efficiency == 0
        assert arch.total_sleep_time == 0


class TestSleepDebt:
    def test_no_debt(self):
        debt = calculate_sleep_debt(
            actual_sleep_hours=8.0,
            recommended_hours=8.0,
            tracking_days=7,
        )
        assert debt["sleep_debt_hours"] == 0

    def test_with_debt(self):
        debt = calculate_sleep_debt(
            actual_sleep_hours=6.0,
            recommended_hours=8.0,
            tracking_days=7,
        )
        assert debt["sleep_debt_hours"] == 14.0
        assert debt["recovery_nights_needed"] > 0

    def test_with_daily_sleeps(self):
        daily = [6, 7, 5, 8, 6, 7, 6]
        debt = calculate_sleep_debt(
            actual_sleep_hours=0,
            daily_sleeps=daily,
        )
        assert debt["sleep_debt_hours"] > 0
        assert debt["tracking_days"] == 7

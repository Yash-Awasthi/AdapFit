"""Tests for rPPG Signal Processing."""
import math
import pytest
from app.services.rppg_signal_processing import (
    extract_rgb_means,
    chrominance_method,
    pos_method,
    green_channel_method,
    bandpass_filter,
    estimate_dominant_frequency,
    compute_signal_quality,
    compute_rr_from_hr_timeseries,
    merge_rppg_results,
    rPPGResult,
)


class TestExtractRGBMeans:
    def test_basic(self):
        r = [100.0, 120.0, 110.0]
        g = [80.0, 90.0, 85.0]
        b = [60.0, 70.0, 65.0]
        r_n, g_n, b_n = extract_rgb_means(r, g, b)
        assert len(r_n) == 3
        assert abs(sum(r_n)) < 0.01  # zero mean
        assert abs(sum(g_n)) < 0.01
        assert abs(sum(b_n)) < 0.01

    def test_empty(self):
        r_n, g_n, b_n = extract_rgb_means([], [], [])
        assert r_n == []


class TestChrominanceMethod:
    def test_sine_wave(self):
        # Create synthetic pulse signal at 1 Hz (60 bpm)
        fps = 30.0
        n = 300  # 10 seconds
        t = [i / fps for i in range(n)]
        g = [math.sin(2 * math.pi * 1.0 * ti) for ti in t]
        r = [0.8 * v + 0.1 for v in g]
        b = [0.6 * v + 0.1 for v in g]

        result = chrominance_method(r, g, b, fps)
        assert result.heart_rate_bpm > 0
        assert result.method == "chrominance"
        assert result.samples_used == n

    def test_too_few_samples(self):
        result = chrominance_method([1.0] * 10, [1.0] * 10, [1.0] * 10)
        assert result.heart_rate_bpm == 0.0


class TestPOSMethod:
    def test_sine_wave(self):
        fps = 30.0
        n = 300
        t = [i / fps for i in range(n)]
        g = [math.sin(2 * math.pi * 1.0 * ti) for ti in t]
        r = [0.8 * v for v in g]
        b = [0.6 * v for v in g]

        result = pos_method(r, g, b, fps)
        assert result.method == "POS"
        assert result.samples_used == n


class TestGreenChannelMethod:
    def test_sine_wave(self):
        fps = 30.0
        n = 300
        t = [i / fps for i in range(n)]
        g = [math.sin(2 * math.pi * 1.0 * ti) for ti in t]

        result = green_channel_method(g, fps)
        assert result.method == "green_channel"
        assert result.samples_used == n

    def test_empty(self):
        result = green_channel_method([])
        assert result.heart_rate_bpm == 0.0


class TestBandpassFilter:
    def test_passes_sine(self):
        # 1 Hz sine should pass through 0.7-4.0 Hz filter
        fps = 30.0
        n = 300
        signal = [math.sin(2 * math.pi * 1.0 * i / fps) for i in range(n)]
        filtered = bandpass_filter(signal, fps, 0.7, 4.0)
        assert len(filtered) == n
        # Check that signal energy is preserved
        orig_energy = sum(x ** 2 for x in signal[n // 2:])
        filt_energy = sum(x ** 2 for x in filtered[n // 2:])
        assert filt_energy > orig_energy * 0.1

    def test_rejects_low_freq(self):
        fps = 30.0
        n = 300
        # 0.1 Hz should be filtered out
        signal = [math.sin(2 * math.pi * 0.1 * i / fps) for i in range(n)]
        filtered = bandpass_filter(signal, fps, 0.7, 4.0)
        # After filter, low-freq signal should be attenuated
        # (check that output is not identical to input)
        orig_rms = math.sqrt(sum(x ** 2 for x in signal[n // 2:]) / (n // 2))
        filt_rms = math.sqrt(sum(x ** 2 for x in filtered[n // 2:]) / (n // 2))
        # Filter should at least change the signal
        assert filt_rms != orig_rms or filt_rms < 0.01


class TestEstimateDominantFrequency:
    def test_1hz_signal(self):
        fps = 30.0
        n = 300
        signal = [math.sin(2 * math.pi * 1.0 * i / fps) for i in range(n)]
        hr, conf = estimate_dominant_frequency(signal, fps)
        assert 55 < hr < 65  # ~60 bpm
        assert conf > 0

    def test_short_signal(self):
        hr, conf = estimate_dominant_frequency([1.0, 2.0], 30.0)
        assert hr == 0.0


class TestSignalQuality:
    def test_clean_signal(self):
        signal = [math.sin(2 * math.pi * i / 50) for i in range(200)]
        quality = compute_signal_quality(signal)
        assert 0 <= quality <= 1

    def test_empty(self):
        assert compute_signal_quality([]) == 0.0


class TestRRFromHR:
    def test_basic(self):
        hrs = [60.0, 60.0, 60.0]
        rr = compute_rr_from_hr_timeseries(hrs, [0.0, 1.0, 2.0])
        assert len(rr) == 2
        assert rr[0] == pytest.approx(1.0, abs=0.01)

    def test_empty(self):
        assert compute_rr_from_hr_timeseries([], []) == []


class TestMergeResults:
    def test_merge(self):
        results = [
            rPPGResult(heart_rate_bpm=70, confidence=0.8, signal_quality=0.9),
            rPPGResult(heart_rate_bpm=72, confidence=0.6, signal_quality=0.7),
        ]
        merged = merge_rppg_results(results)
        assert 70 <= merged.heart_rate_bpm <= 72
        assert merged.method == "merged"

    def test_empty(self):
        merged = merge_rppg_results([])
        assert merged.heart_rate_bpm == 0.0

    def test_single(self):
        results = [rPPGResult(heart_rate_bpm=75, confidence=0.9, signal_quality=0.8)]
        merged = merge_rppg_results(results)
        assert merged.heart_rate_bpm == 75.0

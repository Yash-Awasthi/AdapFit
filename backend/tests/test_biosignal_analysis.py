"""Tests for Biosignal Analysis."""
import math
import pytest
from app.services.biosignal_analysis import (
    detect_r_peaks_simple,
    compute_rr_intervals,
    compute_ecg_morphology,
    eda_decompose,
    eda_features,
    calculate_shannon_entropy,
    calculate_sample_entropy,
    hjorth_parameters,
    bandpower,
    signal_quality_index,
)


class TestRPeakDetection:
    def test_simple_ecg(self):
        # Create a synthetic ECG-like signal with R-peaks
        import math as m
        sr = 250.0
        duration = 2.0  # 2 seconds
        n = int(sr * duration)
        t = [i / sr for i in range(n)]

        # Two R-peaks at t=0.5 and t=1.3
        signal = []
        for ti in t:
            val = 0.0
            # R-peak 1
            val += 1.0 * m.exp(-((ti - 0.5) ** 2) / (2 * 0.001))
            # R-peak 2
            val += 1.2 * m.exp(-((ti - 1.3) ** 2) / (2 * 0.001))
            # Noise
            val += 0.01 * m.sin(2 * m.pi * 60 * ti)
            signal.append(val)

        peaks = detect_r_peaks_simple(signal, sr)
        assert len(peaks) >= 1  # Should detect at least one peak

    def test_empty_signal(self):
        assert detect_r_peaks_simple([]) == []

    def test_constant_signal(self):
        signal = [1.0] * 100
        peaks = detect_r_peaks_simple(signal)
        assert len(peaks) == 0


class TestRRIntervals:
    def test_basic(self):
        peaks = [100, 350, 600]
        rr = compute_rr_intervals(peaks, 250.0)
        assert len(rr) == 2
        assert rr[0] == pytest.approx(1000.0, rel=0.01)
        assert rr[1] == pytest.approx(1000.0, rel=0.01)

    def test_single_peak(self):
        assert compute_rr_intervals([100]) == []

    def test_empty(self):
        assert compute_rr_intervals([]) == []


class TestECGMorphology:
    def test_basic(self):
        signal = [0.0] * 1000
        peaks = [100, 350, 600, 850]
        result = compute_ecg_morphology(signal, peaks, 250.0)
        assert "heart_rate_bpm" in result
        assert "sdnn_ms" in result
        assert "rmssd_ms" in result
        assert result["r_peak_count"] == 4

    def test_too_few_peaks(self):
        result = compute_ecg_morphology([0.0] * 100, [50], 250.0)
        assert "error" in result


class TestEDADecompose:
    def test_basic(self):
        # Synthetic EDA: tonic rise + phasic peaks
        n = 200
        signal = [0.5 + 0.001 * i + 0.1 * (1 if 50 <= i <= 55 else 0) for i in range(n)]
        result = eda_decompose(signal, 20.0)
        assert len(result["tonic"]) == n
        assert len(result["phasic"]) == n
        assert result["tonic_mean"] > 0

    def test_empty(self):
        result = eda_decompose([])
        assert result["tonic"] == []


class TestEDAFeatures:
    def test_basic(self):
        n = 200
        signal = [0.5 + 0.001 * i + 0.1 * (1 if 50 <= i <= 55 else 0) for i in range(n)]
        features = eda_features(signal, 20.0)
        assert "tonic_mean_scl" in features
        assert "scr_count" in features
        assert features["signal_length_sec"] == 10.0

    def test_empty(self):
        features = eda_features([])
        assert "error" in features


class TestShannonEntropy:
    def test_uniform(self):
        # Uniform distribution has max entropy
        signal = [float(i % 10) for i in range(100)]
        entropy = calculate_shannon_entropy(signal)
        assert entropy > 0

    def test_constant(self):
        signal = [5.0] * 100
        entropy = calculate_shannon_entropy(signal)
        assert entropy == 0.0

    def test_empty(self):
        assert calculate_shannon_entropy([]) == 0.0


class TestSampleEntropy:
    def test_periodic_signal(self):
        # Periodic signal has low entropy
        signal = [math.sin(2 * math.pi * i / 50) for i in range(200)]
        se = calculate_sample_entropy(signal)
        assert se >= 0

    def test_short_signal(self):
        assert calculate_sample_entropy([1.0, 2.0]) == 0.0


class TestHjorthParameters:
    def test_basic(self):
        signal = [math.sin(2 * math.pi * i / 50) for i in range(200)]
        params = hjorth_parameters(signal)
        assert params["activity"] > 0
        assert params["mobility"] > 0
        assert params["complexity"] > 0

    def test_constant(self):
        signal = [5.0] * 100
        params = hjorth_parameters(signal)
        assert params["activity"] == 0.0

    def test_short(self):
        params = hjorth_parameters([1.0])
        assert params["activity"] == 0.0


class TestBandpower:
    def test_sine_wave(self):
        # 10 Hz sine should have power concentrated at 10 Hz
        sr = 250.0
        n = 500
        signal = [math.sin(2 * math.pi * 10 * i / sr) for i in range(n)]
        bp = bandpower(signal, sr, 8.0, 12.0)
        assert bp > 0

    def test_out_of_band(self):
        sr = 250.0
        n = 500
        signal = [math.sin(2 * math.pi * 10 * i / sr) for i in range(n)]
        bp = bandpower(signal, sr, 40.0, 100.0)
        assert bp < 0.001  # Should be near zero


class TestSignalQuality:
    def test_clean_signal(self):
        signal = [math.sin(2 * math.pi * i / 50) for i in range(200)]
        sq = signal_quality_index(signal)
        assert sq["quality"] in ("good", "excellent")
        assert not sq["clipping"]

    def test_clipping(self):
        signal = [1.0] * 100 + [-1.0] * 100
        sq = signal_quality_index(signal)
        assert sq["clipping"] is True
        assert sq["quality"] == "poor"

    def test_empty(self):
        sq = signal_quality_index([])
        assert sq["quality"] == "unknown"

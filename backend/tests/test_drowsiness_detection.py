"""Tests for drowsiness_detection.py — drowsiness/fatigue detection service."""

import math
import pytest
from app.services.drowsiness_detection import (
    DrowsinessDetector, BioSignal, CalibrationBaseline,
    AlertnessLevel, StressLevel,
)


@pytest.fixture
def alert_signal():
    return BioSignal(
        timestamp=1.0, heart_rate=65, rr_intervals_ms=[800, 820, 790, 810, 800],
        eda_signal=3.0, blink_rate=15, head_pitch=0, eye_aspect_ratio=0.3,
    )


@pytest.fixture
def drowsy_signal():
    return BioSignal(
        timestamp=1.0, heart_rate=55, rr_intervals_ms=[1000, 1050, 980, 1020, 1000],
        eda_signal=1.0, blink_rate=25, head_pitch=15, eye_aspect_ratio=0.15,
    )


class TestHRV:
    def test_rr_intervals_from_peaks(self):
        peaks = [0.0, 0.8, 1.6, 2.4]
        rr = DrowsinessDetector.rr_intervals_from_peaks(peaks)
        assert len(rr) == 3
        assert all(abs(r - 800.0) < 1 for r in rr)

    def test_rr_intervals_short(self):
        rr = DrowsinessDetector.rr_intervals_from_peaks([0.0])
        assert rr == []

    def test_filter_plausible_rr(self):
        rr = [800, 820, 790, 2000, 810]  # 2000 is implausible
        valid = DrowsinessDetector.filter_plausible_rr(rr)
        assert valid[3] == False  # 2000ms flagged

    def test_rmssd(self):
        rr = [800, 820, 790, 810, 800]
        rmssd = DrowsinessDetector.calculate_rmssd(rr)
        assert rmssd > 0
        assert not math.isnan(rmssd)

    def test_rmssd_short(self):
        rmssd = DrowsinessDetector.calculate_rmssd([800])
        assert math.isnan(rmssd)

    def test_sdnn(self):
        rr = [800, 820, 790, 810, 800]
        sdnn = DrowsinessDetector.calculate_sdnn(rr)
        assert sdnn > 0

    def test_pnn50(self):
        rr = [800, 860, 800, 860]  # diffs > 50
        pnn = DrowsinessDetector.calculate_pnn50(rr)
        assert pnn > 0

    def test_mean_hr(self):
        rr = [800, 800, 800]
        hr = DrowsinessDetector.mean_hr(rr)
        assert hr == pytest.approx(75.0, rel=0.01)


class TestStressStaging:
    def test_high_rmssd_low_stress(self):
        stage = DrowsinessDetector.stage_from_rmssd(60.0)
        assert stage == "none"

    def test_low_rmssd_high_stress(self):
        stage = DrowsinessDetector.stage_from_rmssd(10.0)
        assert stage == "high"

    def test_nan_returns_empty(self):
        stage = DrowsinessDetector.stage_from_rmssd(float('nan'))
        assert stage == ""

    def test_stress_score(self):
        score = DrowsinessDetector.rmssd_to_stress_score(20.0, 40.0)
        assert score > 50  # Lower RMSSD = higher stress


class TestEDA:
    def test_arousal_low(self):
        arousal = DrowsinessDetector.eda_relative_arousal(2.0, 2.0, 1.0)
        assert arousal == 0.0

    def test_arousal_high(self):
        arousal = DrowsinessDetector.eda_relative_arousal(3.0, 2.0, 1.0)
        assert arousal == 1.0

    def test_eda_stress_score(self):
        score = DrowsinessDetector.eda_to_stress_score(0.5)
        assert score == 50.0


class TestBlink:
    def test_normal_blink(self):
        score = DrowsinessDetector.blink_rate_score(15.0, 15.0)
        assert score == 0.0

    def test_high_blink_rate(self):
        score = DrowsinessDetector.blink_rate_score(25.0, 15.0)
        assert score > 0


class TestEAR:
    def test_normal_ear(self):
        score = DrowsinessDetector.ear_drowsiness_score(0.3, 0.3)
        assert score == 0.0

    def test_low_ear(self):
        score = DrowsinessDetector.ear_drowsiness_score(0.1, 0.3)
        assert score > 50


class TestHeadPose:
    def test_upright(self):
        score = DrowsinessDetector.head_pose_drowsiness_score(0)
        assert score == 0.0

    def test_nodding(self):
        score = DrowsinessDetector.head_pose_drowsiness_score(25)
        assert score > 50


class TestCalibration:
    def test_calibrate_empty(self):
        baseline = DrowsinessDetector.calibrate([])
        assert baseline.resting_rmssd == 40.0

    def test_calibrate_with_signals(self):
        signals = [
            BioSignal(timestamp=i, heart_rate=65, rr_intervals_ms=[800, 820, 790, 810, 800],
                     eda_signal=2.0, blink_rate=15, eye_aspect_ratio=0.3)
            for i in range(5)
        ]
        baseline = DrowsinessDetector.calibrate(signals)
        assert baseline.samples_collected == 5
        assert baseline.resting_rmssd > 0


class TestAnalyze:
    def test_alert_analysis(self, alert_signal):
        result = DrowsinessDetector.analyze(alert_signal)
        assert result.alertness_score > 60
        assert result.alertness_level in (AlertnessLevel.ALERT, AlertnessLevel.SLIGHTLY_DROWSY)

    def test_drowsy_analysis(self, drowsy_signal):
        result = DrowsinessDetector.analyze(drowsy_signal)
        assert result.alertness_score < 60

    def test_series_analysis(self, alert_signal):
        results = DrowsinessDetector.analyze_series([alert_signal, alert_signal])
        assert len(results) == 2

    def test_alertness_info(self):
        info = DrowsinessDetector.get_alertness_info()
        assert "levels" in info
        assert "alert" in info["levels"]

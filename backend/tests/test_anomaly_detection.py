"""Tests for Anomaly Detection."""
import pytest
from app.services.anomaly_detection import (
    threshold_detect,
    persistence_detect,
    level_shift_detect,
    seasonal_detect,
    aggregate_detect,
    analyze_anomalies,
)


class TestThresholdDetect:
    def test_high_threshold(self):
        values = [10, 12, 11, 50, 13, 12, 60, 11]
        result = threshold_detect(values, high=40)
        assert result == [False, False, False, True, False, False, True, False]

    def test_low_threshold(self):
        values = [10, 12, 5, 13, 12, 3, 11]
        result = threshold_detect(values, low=8)
        assert result == [False, False, True, False, False, True, False]

    def test_both_thresholds(self):
        values = [5, 15, 25, 35, 45]
        result = threshold_detect(values, low=10, high=40)
        assert result == [True, False, False, False, True]


class TestPersistenceDetect:
    def test_filter_short(self):
        anomalies = [True, False, True, True, True, False]
        result = persistence_detect(anomalies, min_duration=3)
        assert result == [False, False, True, True, True, False]

    def test_keep_long(self):
        anomalies = [True, True, True, True, True]
        result = persistence_detect(anomalies, min_duration=3)
        assert all(result)

    def test_empty(self):
        result = persistence_detect([], min_duration=3)
        assert result == []


class TestLevelShiftDetect:
    def test_detect_shift(self):
        # Create data with clear level shift
        values = [10] * 50 + [50] * 50
        result = level_shift_detect(values, window=20, threshold=2.0)
        assert any(result[45:55])  # Should detect around index 50

    def test_no_shift(self):
        values = [10 + (i % 5) * 0.1 for i in range(100)]
        result = level_shift_detect(values, window=20)
        assert not any(result)


class TestSeasonalDetect:
    def test_detect_spike(self):
        # 24-hour pattern with spike
        values = [10 + (i % 24) * 0.1 for i in range(48)]
        values[30] = 100  # Spike
        result = seasonal_detect(values, period=24, threshold=2.0)
        assert result[30] is True

    def test_no_spike(self):
        values = [10 + (i % 24) * 0.1 for i in range(48)]
        result = seasonal_detect(values, period=24)
        assert not any(result)


class TestAggregateDetect:
    def test_any(self):
        d1 = [False, True, False, True]
        d2 = [True, False, False, False]
        result = aggregate_detect([d1, d2], method="any")
        assert result == [True, True, False, True]

    def test_all(self):
        d1 = [True, True, False]
        d2 = [True, False, False]
        result = aggregate_detect([d1, d2], method="all")
        assert result == [True, False, False]

    def test_majority(self):
        d1 = [True, True, False]
        d2 = [True, False, False]
        d3 = [False, True, False]
        result = aggregate_detect([d1, d2, d3], method="majority", threshold=2)
        assert result == [True, True, False]


class TestAnalyzeAnomalies:
    def test_basic(self):
        values = [10] * 50 + [50] * 5 + [10] * 50
        result = analyze_anomalies(values, high_threshold=30)
        assert result.total_anomalies >= 1

    def test_empty(self):
        result = analyze_anomalies([])
        assert result.total_anomalies == 0

    def test_no_anomalies(self):
        values = [10, 11, 12, 11, 10, 11, 12]
        result = analyze_anomalies(values, high_threshold=100)
        assert result.total_anomalies == 0

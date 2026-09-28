"""Tests for realtime_pipeline.py."""

import time
import math
import pytest
from app.services.realtime_pipeline import (
    DataPoint, StreamType, CircularBuffer, aggregate_window,
    detect_anomaly, detect_trend, downsample, auto_downsample,
    AlertManager, HealthDataPipeline, PipelineConfig, AlertSeverity,
)


class TestCircularBuffer:
    def test_add_and_retrieve(self):
        buf = CircularBuffer(10)
        for i in range(5):
            buf.add(i)
        assert buf.size == 5
        assert buf.get_recent(3) == [2, 3, 4]

    def test_capacity_overflow(self):
        buf = CircularBuffer(3)
        for i in range(10):
            buf.add(i)
        assert buf.size == 3
        assert buf.get_all() == [7, 8, 9]
        assert buf.total_added == 10

    def test_get_since(self):
        buf = CircularBuffer(100)
        now = time.time()
        for i in range(5):
            buf.add(DataPoint(StreamType.HEART_RATE, 70 + i, now + i))
        result = buf.get_since(now + 2)
        assert len(result) == 3


class TestWindowAggregate:
    def test_basic_aggregation(self):
        now = time.time()
        points = [
            DataPoint(StreamType.HEART_RATE, 70, now - 60),
            DataPoint(StreamType.HEART_RATE, 80, now - 30),
            DataPoint(StreamType.HEART_RATE, 75, now),
        ]
        agg = aggregate_window(points, 120, now)
        assert agg is not None
        assert agg.count == 3
        assert agg.mean == pytest.approx(75, abs=0.1)
        assert agg.min == 70
        assert agg.max == 80

    def test_empty_window(self):
        agg = aggregate_window([], 60, time.time())
        assert agg is None


class TestAnomalyDetection:
    def test_normal_point(self):
        now = time.time()
        recent = [DataPoint(StreamType.HEART_RATE, 70 + i * 0.5, now - i) for i in range(20)]
        point = DataPoint(StreamType.HEART_RATE, 71, now)
        assert detect_anomaly(point, recent) is False

    def test_anomalous_point(self):
        now = time.time()
        recent = [DataPoint(StreamType.HEART_RATE, 70 + (i % 3), now - i) for i in range(20)]
        point = DataPoint(StreamType.HEART_RATE, 200, now)
        assert detect_anomaly(point, recent) is True

    def test_insufficient_data(self):
        now = time.time()
        recent = [DataPoint(StreamType.HEART_RATE, 70, now - i) for i in range(5)]
        point = DataPoint(StreamType.HEART_RATE, 200, now)
        assert detect_anomaly(point, recent) is False


class TestDownsampling:
    def test_downsample_reduces_points(self):
        now = time.time()
        points = [DataPoint(StreamType.HEART_RATE, 70 + i % 5, now - 3600 + i) for i in range(3600)]
        result = downsample(points, 60)
        assert len(result) < len(points)
        assert len(result) <= 61  # ~3600 / 60, off-by-one OK

    def test_auto_downsample(self):
        now = time.time()
        recent = [DataPoint(StreamType.HEART_RATE, 70, now - i) for i in range(100)]
        old = [DataPoint(StreamType.HEART_RATE, 70, now - 100000 - i) for i in range(1000)]
        result = auto_downsample(recent + old, now)
        assert len(result) < len(recent + old)


class TestAlertManager:
    def test_warning_alert(self):
        mgr = AlertManager(cooldown_seconds=0)
        now = time.time()
        alert = mgr.check_threshold(StreamType.HEART_RATE, 110, 100, 120, now)
        assert alert is not None
        assert alert.severity == AlertSeverity.WARNING

    def test_critical_alert(self):
        mgr = AlertManager(cooldown_seconds=0)
        now = time.time()
        alert = mgr.check_threshold(StreamType.HEART_RATE, 150, 100, 120, now)
        assert alert is not None
        assert alert.severity == AlertSeverity.CRITICAL

    def test_no_alert(self):
        mgr = AlertManager(cooldown_seconds=0)
        alert = mgr.check_threshold(StreamType.HEART_RATE, 70, 100, 120, time.time())
        assert alert is None


class TestHealthPipeline:
    def test_ingest_and_status(self):
        pipeline = HealthDataPipeline()
        now = time.time()
        pipeline.ingest(DataPoint(StreamType.HEART_RATE, 72, now))
        status = pipeline.get_status(StreamType.HEART_RATE)
        assert status.is_active is True
        assert status.points_received == 1

    def test_aggregates(self):
        pipeline = HealthDataPipeline(PipelineConfig(window_sizes=[5]))
        now = time.time()
        for i in range(10):
            pipeline.ingest(DataPoint(StreamType.HEART_RATE, 70 + i, now + i))
        aggs = pipeline.get_aggregates(StreamType.HEART_RATE, now + 10)
        assert len(aggs) > 0

    def test_alert_rule(self):
        pipeline = HealthDataPipeline()
        pipeline.set_alert_rule(StreamType.HEART_RATE, 100, 120)
        alert = pipeline.ingest(DataPoint(StreamType.HEART_RATE, 110, time.time()))
        assert alert is not None
        assert alert.severity == AlertSeverity.WARNING

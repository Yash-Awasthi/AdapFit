"""Tests for wearable decoder service."""

import pytest
from app.services.wearable_decoder import (
    decode_frame,
    calculate_rr_metrics,
    aggregate_heart_rate,
    classify_hr_zone,
    get_category_info,
    CATEGORIES,
)


class TestFrameDecoding:
    def test_decode_hr_frame(self):
        data = bytes([0x03, 72])  # category=3 (hr), hr=72
        frame = decode_frame(data)
        assert frame.category == "hr"
        assert frame.heart_rate == 72

    def test_decode_battery_frame(self):
        data = bytes([0x08, 85])  # category=8 (battery), level=85
        frame = decode_frame(data)
        assert frame.category == "battery"
        assert frame.battery_level == 85

    def test_decode_empty(self):
        frame = decode_frame(b"")
        assert frame.category == "unknown"

    def test_decode_rr_intervals(self):
        data = bytes([0x04]) + b"\x03\xe8\x03\xe8"  # category=4 (rr), two 1000ms intervals
        frame = decode_frame(data)
        assert frame.category == "rr"
        assert len(frame.rr_intervals) == 2


class TestRRMetrics:
    def test_calculate_rmssd(self):
        intervals = [800, 810, 790, 805, 795]
        result = calculate_rr_metrics(intervals)
        assert result.rmssd > 0
        assert result.mean_rr == pytest.approx(800, abs=1)

    def test_empty_intervals(self):
        result = calculate_rr_metrics([])
        assert len(result.intervals_ms) == 0


class TestHeartRate:
    def test_aggregate(self):
        from app.services.wearable_decoder import DecodedFrame
        frames = [
            DecodedFrame(category="hr", heart_rate=70, timestamp=1.0),
            DecodedFrame(category="hr", heart_rate=75, timestamp=2.0),
        ]
        result = aggregate_heart_rate(frames)
        assert result.bpm == 72 or result.bpm == 73
        assert result.confidence > 0

    def test_classify_zone(self):
        assert classify_hr_zone(100, 200) == "Zone 1 - Warm Up"
        assert classify_hr_zone(60, 200) == "Rest"
        assert classify_hr_zone(170, 200) == "Zone 4 - Anaerobic"
        assert classify_hr_zone(195, 200) == "Zone 5 - Maximum"


class TestCategoryInfo:
    def test_get_info(self):
        info = get_category_info("hr")
        assert info["name"] == "hr"
        assert info["is_valid"]

    def test_invalid_category(self):
        info = get_category_info("invalid")
        assert not info["is_valid"]

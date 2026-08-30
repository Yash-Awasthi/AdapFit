"""Tests for BLE Data Processor."""
import pytest
from app.services.ble_data_processor import (
    BLEHRParser,
    HeartRateFrame,
    BatteryReading,
    ContactStatus,
    compute_instant_hr,
    normalize_timestamps_to_epoch,
    detect_skin_contact_events,
    compute_rr_statistics,
    normalize_battery_level,
    filter_noisy_rr_intervals,
    estimate_hrv_from_frames,
    compute_energy_expenditure,
    compute_average_hr,
    classify_hr_zone,
)


class TestBLEHRParser:
    def test_parse_simple_frame(self):
        raw = bytes([0x00, 72])  # 16-bit flag off, HR=72
        frame = BLEHRParser.parse_frame(raw, 1000000)
        assert frame.avg_hr == 72.0

    def test_parse_16bit_hr(self):
        raw = bytes([0x01, 0x48, 0x00])  # 16-bit flag on, HR=72
        frame = BLEHRParser.parse_frame(raw, 1000000)
        assert frame.avg_hr == 72.0

    def test_parse_with_rr_intervals(self):
        # flags=0x10 (RR interval), HR=72, RR=1024 units = 1000.0ms, RR=1024 units
        raw = bytes([0x10, 72, 0x00, 0x04, 0x00, 0x04])
        frame = BLEHRParser.parse_frame(raw, 1000000)
        assert len(frame.rr_intervals_ms) == 2
        assert frame.rr_intervals_ms[0] == pytest.approx(1000.0, rel=0.01)

    def test_parse_with_energy(self):
        # flags=0x08 (energy), HR=80, energy=5000 (5kJ)
        raw = bytes([0x08, 80, 0x88, 0x13])
        frame = BLEHRParser.parse_frame(raw, 1000000)
        assert frame.energy_kj == pytest.approx(5.0, rel=0.01)

    def test_parse_empty_frame(self):
        frame = BLEHRParser.parse_frame(bytes([]), 0)
        assert frame.avg_hr == 0.0

    def test_parse_short_frame(self):
        frame = BLEHRParser.parse_frame(bytes([0x00]), 0)
        assert frame.avg_hr == 0.0


class TestComputeInstantHR:
    def test_normal_rr(self):
        assert compute_instant_hr(1000.0) == 60.0

    def test_fast_rr(self):
        assert compute_instant_hr(500.0) == 120.0

    def test_zero_rr(self):
        assert compute_instant_hr(0.0) == 0.0

    def test_negative_rr(self):
        assert compute_instant_hr(-100.0) == 0.0


class TestNormalizeTimestamps:
    def test_basic_normalization(self):
        frames = [
            HeartRateFrame(timestamp_ns=100, avg_hr=70),
            HeartRateFrame(timestamp_ns=200, avg_hr=75),
        ]
        result = normalize_timestamps_to_epoch(frames, 1000000)
        assert result[0].timestamp_ns == 1000000
        assert result[1].timestamp_ns == 1000100

    def test_empty_frames(self):
        assert normalize_timestamps_to_epoch([], 0) == []


class TestSkinContact:
    def test_detect_transitions(self):
        frames = [
            HeartRateFrame(timestamp_ns=1, avg_hr=70, contact=ContactStatus.UNKNOWN),
            HeartRateFrame(timestamp_ns=2, avg_hr=71, contact=ContactStatus.GOOD),
            HeartRateFrame(timestamp_ns=3, avg_hr=72, contact=ContactStatus.GOOD),
            HeartRateFrame(timestamp_ns=4, avg_hr=73, contact=ContactStatus.LOST),
        ]
        events = detect_skin_contact_events(frames)
        assert len(events) == 2
        assert events[0]["type"] == "established"
        assert events[1]["type"] == "lost"

    def test_no_transitions(self):
        frames = [
            HeartRateFrame(timestamp_ns=1, avg_hr=70, contact=ContactStatus.GOOD),
            HeartRateFrame(timestamp_ns=2, avg_hr=71, contact=ContactStatus.GOOD),
        ]
        events = detect_skin_contact_events(frames)
        assert len(events) == 0


class TestRRStatistics:
    def test_normal_rr(self):
        rr = [1000.0, 1050.0, 950.0, 1020.0, 980.0]
        stats = compute_rr_statistics(rr)
        assert stats["count"] == 5
        assert stats["mean_rr"] == pytest.approx(1000.0)
        assert stats["min_rr"] == 950.0
        assert stats["max_rr"] == 1050.0

    def test_empty_rr(self):
        stats = compute_rr_statistics([])
        assert stats["count"] == 0

    def test_single_rr(self):
        stats = compute_rr_statistics([1000.0])
        assert stats["count"] == 1
        assert stats["sdnn"] == 0.0


class TestFilterRR:
    def test_filter_outliers(self):
        rr = [1000.0, 1050.0, 100.0, 3000.0, 980.0]
        filtered = filter_noisy_rr_intervals(rr)
        assert len(filtered) == 3
        assert 100.0 not in filtered
        assert 3000.0 not in filtered

    def test_all_valid(self):
        rr = [800.0, 900.0, 1000.0]
        filtered = filter_noisy_rr_intervals(rr)
        assert len(filtered) == 3


class TestHRVFromFrames:
    def test_from_frames(self):
        frames = [
            HeartRateFrame(timestamp_ns=1, avg_hr=70, rr_intervals_ms=[1000.0, 1050.0, 950.0]),
            HeartRateFrame(timestamp_ns=2, avg_hr=71, rr_intervals_ms=[1020.0, 980.0]),
        ]
        hrv = estimate_hrv_from_frames(frames)
        assert hrv["count"] == 5
        assert hrv["sdnn"] > 0


class TestBatteryLevel:
    def test_normal_level(self):
        assert normalize_battery_level(85) == 85

    def test_over_100(self):
        assert normalize_battery_level(120) == 100

    def test_negative(self):
        assert normalize_battery_level(-5) == 0

    def test_zero(self):
        assert normalize_battery_level(0) == 0


class TestEnergyExpenditure:
    def test_sum_energy(self):
        frames = [
            HeartRateFrame(timestamp_ns=1, avg_hr=70, energy_kj=5.0),
            HeartRateFrame(timestamp_ns=2, avg_hr=71, energy_kj=3.0),
            HeartRateFrame(timestamp_ns=3, avg_hr=72, energy_kj=None),
        ]
        total = compute_energy_expenditure(frames)
        assert total == 8.0

    def test_no_energy(self):
        frames = [HeartRateFrame(timestamp_ns=1, avg_hr=70)]
        assert compute_energy_expenditure(frames) == 0.0


class TestAverageHR:
    def test_weighted_average(self):
        frames = [
            HeartRateFrame(timestamp_ns=0, avg_hr=60),
            HeartRateFrame(timestamp_ns=1_000_000_000, avg_hr=120),  # 1 second later
        ]
        avg = compute_average_hr(frames)
        # Weighted: frame[0] hr=60 weighted by dt=1s = 60*1.0, then frame[1]=120
        # Actually: we weight frame[i-1] by dt, so only frame[0] gets weight 1s
        # avg = (60*1.0) / 1.0 = 60.0 (last frame not weighted)
        assert avg == pytest.approx(60.0)

    def test_empty(self):
        assert compute_average_hr([]) == 0.0


class TestHRZone:
    def test_zone1(self):
        zone = classify_hr_zone(95, 190)
        assert zone["zone"] == 1

    def test_zone3(self):
        zone = classify_hr_zone(140, 190)
        assert zone["zone"] == 3

    def test_zone5(self):
        zone = classify_hr_zone(185, 190)
        assert zone["zone"] == 5

    def test_zero_max(self):
        zone = classify_hr_zone(70, 0)
        assert zone["zone"] == 0

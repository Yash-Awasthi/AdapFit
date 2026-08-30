"""Tests for Smart Ring Parser."""
import pytest
from datetime import datetime, timezone
from app.services.smart_ring_parser import (
    calculate_checksum,
    make_packet,
    validate_packet,
    parse_packet_header,
    parse_heart_rate_log,
    aggregate_heart_rates,
    parse_sport_detail,
    aggregate_sport_details,
    parse_spo2_packet,
    detect_sleep_periods,
    create_daily_summary,
    HeartRateLog,
    SportDetail,
)


class TestPacketProtocol:
    def test_checksum(self):
        packet = bytearray(16)
        packet[0] = 21
        packet[-1] = 0
        cs = calculate_checksum(packet)
        assert 0 <= cs <= 255

    def test_make_packet(self):
        packet = make_packet(21)
        assert len(packet) == 16
        assert packet[0] == 21
        assert packet[-1] == calculate_checksum(packet[:-1]) + packet[-1] - packet[-1]

    def test_make_packet_with_data(self):
        data = bytearray([1, 2, 3])
        packet = make_packet(21, data)
        assert packet[1] == 1
        assert packet[2] == 2
        assert packet[3] == 3

    def test_validate_packet(self):
        packet = make_packet(21)
        assert validate_packet(packet)

    def test_invalid_checksum(self):
        packet = make_packet(21)
        packet[-1] = (packet[-1] + 1) % 256
        assert not validate_packet(packet)

    def test_wrong_length(self):
        assert not validate_packet(bytearray(10))

    def test_parse_header(self):
        packet = make_packet(21)
        cmd, sub = parse_packet_header(packet)
        assert cmd == 21
        assert sub == 0


class TestHeartRate:
    def test_aggregate(self):
        logs = [
            HeartRateLog(heart_rates=[60, 70, 80]),
            HeartRateLog(heart_rates=[65, 75, 85]),
        ]
        result = aggregate_heart_rates(logs)
        assert result["avg"] == 72.5
        assert result["min"] == 60
        assert result["max"] == 85
        assert result["count"] == 6

    def test_empty(self):
        result = aggregate_heart_rates([])
        assert result["count"] == 0

    def test_with_zeros(self):
        logs = [HeartRateLog(heart_rates=[0, 70, 0, 80])]
        result = aggregate_heart_rates(logs)
        assert result["count"] == 2


class TestSportDetail:
    def test_timestamp(self):
        detail = SportDetail(year=2024, month=1, day=15, time_index=16)
        assert detail.timestamp.hour == 4
        assert detail.timestamp.minute == 0

    def test_aggregate(self):
        details = [
            SportDetail(steps=100, calories=50, distance_m=200),
            SportDetail(steps=200, calories=100, distance_m=400),
        ]
        result = aggregate_sport_details(details)
        assert result["total_steps"] == 300
        assert result["total_calories"] == 150
        assert result["total_distance_m"] == 600
        assert result["active_minutes"] == 30


class TestSpO2:
    def test_parse(self):
        packet = bytearray(16)
        packet[0] = 22
        packet[1] = 0
        packet[2] = 98  # SpO2
        packet[3] = 95  # confidence
        result = parse_spo2_packet(packet)
        assert result["spo2"] == 98
        assert result["confidence"] == 95

    def test_no_data(self):
        packet = bytearray(16)
        packet[0] = 22
        packet[1] = 255
        assert parse_spo2_packet(packet) is None

    def test_invalid_spo2(self):
        packet = bytearray(16)
        packet[0] = 22
        packet[2] = 0
        assert parse_sport_detail(packet, datetime.now(timezone.utc)) is None


class TestSleepDetection:
    def test_detect_periods(self):
        # Need >= 7 consecutive low-HR readings at 5-min intervals to meet 0.5h threshold
        hr_log = HeartRateLog(
            heart_rates=[70, 55, 50, 48, 52, 55, 50, 48, 52, 55, 50, 48, 70],
            timestamp=datetime(2024, 1, 15, 0, 0, tzinfo=timezone.utc),
        )
        periods = detect_sleep_periods(hr_log, low_hr_threshold=60, min_duration_hours=0.5)
        assert len(periods) >= 1

    def test_no_sleep(self):
        hr_log = HeartRateLog(
            heart_rates=[80, 85, 90, 95, 80, 85, 90, 95],
            timestamp=datetime(2024, 1, 15, 0, 0, tzinfo=timezone.utc),
        )
        periods = detect_sleep_periods(hr_log, low_hr_threshold=60)
        assert len(periods) == 0


class TestDailySummary:
    def test_create(self):
        hr_logs = [HeartRateLog(heart_rates=[60, 70, 80, 90])]
        details = [SportDetail(steps=5000, calories=200, distance_m=3000)]
        summary = create_daily_summary(hr_logs, details, "2024-01-15")
        assert summary.date == "2024-01-15"
        assert summary.total_steps == 5000
        assert summary.avg_heart_rate == 75.0

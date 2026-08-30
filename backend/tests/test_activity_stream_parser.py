"""Tests for Activity Stream Parser Service."""
import pytest
from datetime import datetime, timedelta
from app.services.activity_stream_parser import (
    GPSPoint, ActivityType, ACTIVITY_NAME_MAP,
    haversine_distance, calculate_total_distance, calculate_elevation_stats,
    calculate_speed_from_gps, classify_activity_type, calculate_calories,
    calculate_vo2max, calculate_pace, format_pace, calculate_splits,
    build_activity_from_points, create_stream_from_points,
)


class TestHaversine:
    def test_same_point(self):
        assert haversine_distance(40.0, -74.0, 40.0, -74.0) == 0.0

    def test_known_distance(self):
        d = haversine_distance(40.7128, -74.0060, 40.7580, -73.9855)
        assert 2000 < d < 6000

    def test_symmetry(self):
        d1 = haversine_distance(40.0, -74.0, 41.0, -73.0)
        d2 = haversine_distance(41.0, -73.0, 40.0, -74.0)
        assert abs(d1 - d2) < 0.01


class TestTotalDistance:
    def test_empty(self):
        assert calculate_total_distance([]) == 0.0

    def test_single_point(self):
        assert calculate_total_distance([GPSPoint(40.0, -74.0)]) == 0.0

    def test_two_points(self):
        points = [GPSPoint(40.0, -74.0), GPSPoint(40.001, -74.0)]
        d = calculate_total_distance(points)
        assert d > 0


class TestElevation:
    def test_gain_only(self):
        points = [GPSPoint(0, 0, 100), GPSPoint(0, 0, 200), GPSPoint(0, 0, 300)]
        gain, loss = calculate_elevation_stats(points)
        assert gain == 200
        assert loss == 0

    def test_loss_only(self):
        points = [GPSPoint(0, 0, 300), GPSPoint(0, 0, 200), GPSPoint(0, 0, 100)]
        gain, loss = calculate_elevation_stats(points)
        assert gain == 0
        assert loss == 200

    def test_mixed(self):
        points = [GPSPoint(0, 0, 100), GPSPoint(0, 0, 200), GPSPoint(0, 0, 150)]
        gain, loss = calculate_elevation_stats(points)
        assert gain == 100
        assert loss == 50


class TestSpeedFromGPS:
    def test_empty(self):
        assert calculate_speed_from_gps([]) == []

    def test_stationary(self):
        points = [GPSPoint(40.0, -74.0, timestamp=datetime(2025, 1, 1, 0, 0, i)) for i in range(3)]
        speeds = calculate_speed_from_gps(points)
        assert all(s == 0.0 for s in speeds)


class TestClassify:
    def test_run(self):
        assert classify_activity_type(1800, 10000) == ActivityType.RUN

    def test_ride(self):
        assert classify_activity_type(1800, 25000) == ActivityType.RIDE

    def test_walk(self):
        assert classify_activity_type(1800, 2000) == ActivityType.WALK

    def test_zero_duration(self):
        assert classify_activity_type(0, 0) == ActivityType.WORKOUT


class TestCalories:
    def test_run_30min(self):
        cal = calculate_calories(ActivityType.RUN, 1800, 70.0)
        assert 200 < cal < 500

    def test_with_hr(self):
        cal_low = calculate_calories(ActivityType.RUN, 1800, 70.0, 100)
        cal_high = calculate_calories(ActivityType.RUN, 1800, 70.0, 160)
        assert cal_high > cal_low


class TestVO2max:
    def test_basic(self):
        vo2 = calculate_vo2max(10000, 2400)
        assert vo2 > 0

    def test_zero(self):
        assert calculate_vo2max(0, 0) == 0.0


class TestPace:
    def test_basic(self):
        pace = calculate_pace(1000, 300)
        assert pace == 300.0

    def test_format(self):
        assert format_pace(300) == "5:00"
        assert format_pace(330) == "5:30"

    def test_zero_distance(self):
        assert calculate_pace(0, 300) == 0.0


class TestSplits:
    def test_no_points(self):
        assert calculate_splits([]) == []

    def test_one_split(self):
        points = []
        for i in range(100):
            points.append(GPSPoint(40.0 + i * 0.0001, -74.0, timestamp=datetime(2025, 1, 1, 0, i // 60, i % 60)))
        splits = calculate_splits(points, split_distance_meters=100)
        assert len(splits) > 0


class TestBuildActivity:
    def test_empty_points(self):
        from app.services.activity_stream_parser import Activity
        activity = build_activity_from_points([], ActivityType.RUN)
        assert activity.distance == 0.0

    def test_with_points(self):
        points = [GPSPoint(40.0 + i * 0.0001, -74.0, 100, datetime(2025, 1, 1, 0, i // 60, i * 10), heart_rate=140) for i in range(5)]
        activity = build_activity_from_points(points, ActivityType.RUN)
        assert activity.activity_type == ActivityType.RUN
        assert activity.avg_heart_rate == 140


class TestStream:
    def test_build_stream(self):
        points = [GPSPoint(40.0 + i * 0.001, -74.0, 100 + i, heart_rate=140 + i) for i in range(5)]
        stream = create_stream_from_points(points)
        assert len(stream.time) == 5
        assert len(stream.latitude) == 5
        assert len(stream.heart_rate) == 5

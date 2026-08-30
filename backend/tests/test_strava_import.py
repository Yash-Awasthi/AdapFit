"""Tests for Strava data import service."""
import pytest
from app.services.strava_import import (
    parse_activity, parse_route, import_activities, aggregate_weekly,
    calculate_tss, decode_polyline, STRAVA_TYPE_MAP,
)


class TestParseActivity:
    def test_run_activity(self):
        raw = {
            "id": 12345,
            "name": "Morning Run",
            "type": "Run",
            "start_date": "2026-01-15T07:30:00Z",
            "distance": 10000,
            "moving_time": 3000,
            "elapsed_time": 3200,
            "total_elevation_gain": 120,
            "average_speed": 3.33,
            "max_speed": 4.5,
            "average_heartrate": 155,
            "max_heartrate": 178,
            "calories": 650,
        }
        a = parse_activity(raw)
        assert a is not None
        assert a.activity_type == "Run"
        assert a.zfit_type == "run"
        assert a.distance_meters == 10000
        assert a.avg_heart_rate == 155
        assert a.calories == 650

    def test_ride_activity(self):
        raw = {
            "id": 12346,
            "name": "Afternoon Ride",
            "type": "Ride",
            "start_date": "2026-01-15T14:00:00Z",
            "distance": 50000,
            "moving_time": 5400,
            "average_watts": 180,
            "max_watts": 450,
            "kilojoules": 972,
        }
        a = parse_activity(raw)
        assert a is not None
        assert a.zfit_type == "cycle"
        assert a.avg_power == 180

    def test_swim_activity(self):
        raw = {"id": 12347, "type": "Swim", "start_date": "2026-01-15T06:00:00Z", "distance": 2000, "moving_time": 2400}
        a = parse_activity(raw)
        assert a is not None
        assert a.zfit_type == "swim"

    def test_trainer_flag(self):
        raw = {"id": 12348, "type": "VirtualRide", "start_date": "2026-01-15T08:00:00Z", "trainer": True}
        a = parse_activity(raw)
        assert a is not None
        assert a.trainer is True

    def test_empty_returns_none(self):
        assert parse_activity({}) is None

    def test_type_mapping_completeness(self):
        # All mapped types should have zfit equivalents
        for strava_type, zfit_type in STRAVA_TYPE_MAP.items():
            assert isinstance(zfit_type, str)
            assert len(zfit_type) > 0


class TestCalculateTSS:
    def test_duration_only(self):
        tss = calculate_tss(duration_minutes=60)
        assert 50 <= tss <= 70

    def test_power_based(self):
        tss = calculate_tss(duration_minutes=60, avg_power=200, ftp=200)
        assert tss > 0

    def test_hr_based(self):
        tss = calculate_tss(duration_minutes=60, avg_hr=155, max_hr=190)
        assert tss > 0

    def test_capped_at_500(self):
        tss = calculate_tss(duration_minutes=600, avg_power=400, ftp=200)
        assert tss <= 500


class TestImportActivities:
    def test_basic_import(self):
        records = [
            {
                "id": str(i),
                "type": "Run",
                "start_date": f"2026-01-{i:02d}T07:00:00Z",
                "distance": 10000,
                "moving_time": 3000,
            }
            for i in range(1, 8)
        ]
        r = import_activities(records)
        assert r["imported"] == 7
        assert "run" in r["type_summary"]

    def test_deduplication(self):
        records = [
            {"id": "123", "type": "Run", "start_date": "2026-01-01T07:00:00Z"},
            {"id": "123", "type": "Run", "start_date": "2026-01-01T07:00:00Z"},
        ]
        r = import_activities(records)
        assert r["imported"] == 1
        assert r["skipped_duplicates"] == 1

    def test_weekly_aggregation(self):
        records = [
            {"id": str(i), "type": "Run", "start_date": f"2026-01-{i:02d}T07:00:00Z", "distance": 10000, "moving_time": 3000}
            for i in range(1, 15)  # 2 weeks
        ]
        r = import_activities(records)
        assert len(r["weekly_volume"]) >= 1
        assert r["weekly_volume"][0]["activity_count"] > 0

    def test_type_summary(self):
        records = [
            {"id": "1", "type": "Run", "start_date": "2026-01-01T07:00:00Z", "distance": 10000, "moving_time": 3000, "calories": 650},
            {"id": "2", "type": "Ride", "start_date": "2026-01-01T14:00:00Z", "distance": 50000, "moving_time": 5400, "calories": 1200},
        ]
        r = import_activities(records)
        assert "run" in r["type_summary"]
        assert "cycle" in r["type_summary"]
        assert r["type_summary"]["run"]["count"] == 1
        assert r["type_summary"]["cycle"]["count"] == 1


class TestDecodePolyline:
    def test_simple_polyline(self):
        # This is a known polyline for a few points
        coords = decode_polyline("_p~iF~ps|U_ulLnnqC_mqNvxq`@")
        assert len(coords) > 0
        assert all(isinstance(c, tuple) and len(c) == 2 for c in coords)

    def test_empty_polyline(self):
        assert decode_polyline("") == []

    def test_two_points(self):
        coords = decode_polyline("_p~iF~ps|U_ulLnnqC_mqNvxq`@")
        assert len(coords) >= 2


class TestAggregateWeekly:
    def test_empty_list(self):
        assert aggregate_weekly([]) == []

    def test_same_week(self):
        from app.services.strava_import import StravaActivity
        activities = [
            StravaActivity(id="1", name="Run 1", activity_type="Run", zfit_type="run",
                          start_date="2026-01-12T07:00:00Z", distance_meters=10000, moving_time_seconds=3000),
            StravaActivity(id="2", name="Run 2", activity_type="Run", zfit_type="run",
                          start_date="2026-01-14T07:00:00Z", distance_meters=12000, moving_time_seconds=3600),
        ]
        result = aggregate_weekly(activities)
        assert len(result) == 1
        assert result[0]["activity_count"] == 2

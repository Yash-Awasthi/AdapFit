"""Tests for Apple Health Parser."""
import pytest
from app.services.apple_health_parser import (
    parse_health_record,
    parse_workout_record,
    analyze_structure,
    get_records_by_type,
    compute_statistics,
    compute_daily_statistics,
    compute_weekly_trends,
    detect_anomalies,
    classify_sleep_stage,
    compute_sleep_summary,
    search_records,
    HealthRecord,
    WorkoutRecord,
    RecordType,
)


SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<HealthData locale="en_US">
    <Record type="HKQuantityTypeIdentifierHeartRate" sourceName="iPhone"
            startDate="2024-01-15 08:00:00 +0000" endDate="2024-01-15 08:00:01 +0000"
            value="72" unit="count/min"/>
    <Record type="HKQuantityTypeIdentifierHeartRate" sourceName="Watch"
            startDate="2024-01-15 08:05:00 +0000" endDate="2024-01-15 08:05:01 +0000"
            value="85" unit="count/min"/>
    <Record type="HKQuantityTypeIdentifierStepCount" sourceName="iPhone"
            startDate="2024-01-15 09:00:00 +0000" endDate="2024-01-15 09:10:00 +0000"
            value="500" unit="count"/>
    <Record type="HKQuantityTypeIdentifierStepCount" sourceName="iPhone"
            startDate="2024-01-16 09:00:00 +0000" endDate="2024-01-16 09:10:00 +0000"
            value="800" unit="count"/>
    <Workout workoutActivityType="HKWorkoutActivityTypeRunning"
            startDate="2024-01-15 07:00:00 +0000" endDate="2024-01-15 08:00:00 +0000"
            duration="60" durationUnit="min"
            totalDistance="8" totalDistanceUnit="km"
            totalEnergyBurned="600" totalEnergyBurnedUnit="kcal"
            sourceName="Apple Watch"/>
</HealthData>
"""


class TestParseRecord:
    def test_parse_basic(self):
        elem = {
            "type": "HKQuantityTypeIdentifierHeartRate",
            "value": "72",
            "unit": "count/min",
            "startDate": "2024-01-15 08:00:00 +0000",
            "endDate": "2024-01-15 08:00:01 +0000",
            "sourceName": "iPhone",
        }
        record = parse_health_record(elem)
        assert record.record_type == "HKQuantityTypeIdentifierHeartRate"
        assert record.value == 72.0
        assert record.unit == "count/min"
        assert record.source_name == "iPhone"

    def test_parse_missing_fields(self):
        record = parse_health_record({})
        assert record.record_type == ""
        assert record.value == 0.0


class TestParseWorkout:
    def test_parse_workout(self):
        elem = {
            "workoutActivityType": "HKWorkoutActivityTypeRunning",
            "duration": "60",
            "durationUnit": "min",
            "startDate": "2024-01-15 07:00:00 +0000",
            "endDate": "2024-01-15 08:00:00 +0000",
            "totalDistance": "8",
            "totalDistanceUnit": "km",
            "totalEnergyBurned": "600",
            "totalEnergyBurnedUnit": "kcal",
            "sourceName": "Apple Watch",
        }
        workout = parse_workout_record(elem)
        assert workout.workout_type == "HKWorkoutActivityTypeRunning"
        assert workout.duration == 60.0
        assert workout.total_distance == 8.0
        assert workout.total_calories == 600.0


class TestAnalyzeStructure:
    def test_basic_analysis(self):
        summary = analyze_structure(SAMPLE_XML)
        assert summary.total_records == 4
        assert summary.total_workouts == 1
        assert len(summary.record_types) == 2
        assert len(summary.workout_types) == 1
        assert len(summary.sources) == 2

    def test_empty_xml(self):
        summary = analyze_structure("<HealthData></HealthData>")
        assert summary.total_records == 0
        assert summary.total_workouts == 0


class TestGetRecordsByType:
    def test_get_hr_records(self):
        records = get_records_by_type(SAMPLE_XML, "HKQuantityTypeIdentifierHeartRate")
        assert len(records) == 2
        assert all(r.record_type == "HKQuantityTypeIdentifierHeartRate" for r in records)

    def test_get_step_records(self):
        records = get_records_by_type(SAMPLE_XML, "HKQuantityTypeIdentifierStepCount")
        assert len(records) == 2

    def test_limit(self):
        records = get_records_by_type(SAMPLE_XML, "HKQuantityTypeIdentifierHeartRate", limit=1)
        assert len(records) == 1


class TestStatistics:
    def test_basic_stats(self):
        records = [
            HealthRecord("HR", 70.0, "bpm", "", ""),
            HealthRecord("HR", 80.0, "bpm", "", ""),
            HealthRecord("HR", 90.0, "bpm", "", ""),
        ]
        stats = compute_statistics(records)
        assert stats["count"] == 3
        assert stats["mean"] == 80.0
        assert stats["min"] == 70.0
        assert stats["max"] == 90.0

    def test_empty_stats(self):
        stats = compute_statistics([])
        assert stats["count"] == 0


class TestDailyStatistics:
    def test_by_day(self):
        records = [
            HealthRecord("HR", 70.0, "bpm", "2024-01-15T08:00:00", ""),
            HealthRecord("HR", 80.0, "bpm", "2024-01-15T09:00:00", ""),
            HealthRecord("HR", 90.0, "bpm", "2024-01-16T08:00:00", ""),
        ]
        daily = compute_daily_statistics(records)
        assert len(daily) == 2
        assert daily["2024-01-15"]["count"] == 2
        assert daily["2024-01-16"]["count"] == 1


class TestWeeklyTrends:
    def test_trends(self):
        records = [
            HealthRecord("HR", 70.0, "bpm", "2024-01-15T08:00:00", ""),
            HealthRecord("HR", 80.0, "bpm", "2024-01-22T08:00:00", ""),
        ]
        trends = compute_weekly_trends(records, weeks=4)
        assert len(trends) <= 4
        assert all("week" in t for t in trends)


class TestAnomalies:
    def test_detect_outlier(self):
        records = [
            HealthRecord("HR", 70.0, "bpm", "", ""),
            HealthRecord("HR", 72.0, "bpm", "", ""),
            HealthRecord("HR", 71.0, "bpm", "", ""),
            HealthRecord("HR", 200.0, "bpm", "", ""),  # anomaly
        ]
        anomalies = detect_anomalies(records, z_threshold=1.0)
        assert len(anomalies) >= 1
        assert any(a.value == 200.0 for a in anomalies)

    def test_no_anomalies(self):
        records = [
            HealthRecord("HR", 70.0, "bpm", "", ""),
            HealthRecord("HR", 71.0, "bpm", "", ""),
            HealthRecord("HR", 72.0, "bpm", "", ""),
        ]
        anomalies = detect_anomalies(records)
        assert len(anomalies) == 0


class TestSleepClassification:
    def test_stages(self):
        assert classify_sleep_stage(0) == "inBed"
        assert classify_sleep_stage(3) == "core"
        assert classify_sleep_stage(4) == "deep"
        assert classify_sleep_stage(5) == "rem"
        assert classify_sleep_stage(99) == "unknown"


class TestSleepSummary:
    def test_basic_summary(self):
        records = [
            HealthRecord("Sleep", 4.0, "", "2024-01-15T22:00:00+00:00", "2024-01-15T23:00:00+00:00"),
            HealthRecord("Sleep", 3.0, "", "2024-01-15T23:00:00+00:00", "2024-01-16T06:00:00+00:00"),
        ]
        summary = compute_sleep_summary(records)
        assert summary["total_minutes"] > 0

    def test_empty_sleep(self):
        summary = compute_sleep_summary([])
        assert summary["total_minutes"] == 0


class TestSearch:
    def test_search(self):
        results = search_records(SAMPLE_XML, "HeartRate")
        assert len(results) >= 2

    def test_search_no_match(self):
        results = search_records(SAMPLE_XML, "nonexistent")
        assert len(results) == 0

    def test_search_limit(self):
        results = search_records(SAMPLE_XML, "Heart", max_results=1)
        assert len(results) == 1

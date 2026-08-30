"""Tests for daily health brief service."""

import pytest
from app.services.daily_health_brief import (
    DailySteps,
    DailySleep,
    DailyHeartRate,
    DailyWorkout,
    parse_steps_data,
    parse_sleep_data,
    parse_heart_rate_data,
    parse_workout_data,
    calculate_wellness_score,
    generate_recommendations,
    generate_daily_brief,
)


class TestParsing:
    def test_parse_steps(self):
        data = [{"date": "2024-01-01", "steps": "8500", "distance_km": "5.2", "floors_climbed": "3"}]
        result = parse_steps_data(data)
        assert len(result) == 1
        assert result[0].steps == 8500

    def test_parse_sleep(self):
        data = [{"date": "2024-01-01", "total_minutes": "420", "deep_minutes": "90", "rem_minutes": "100", "core_minutes": "200", "awake_minutes": "30"}]
        result = parse_sleep_data(data)
        assert len(result) == 1
        assert result[0].total_minutes == 420

    def test_parse_heart_rate(self):
        data = [{"date": "2024-01-01", "resting_hr": "62", "max_hr": "155", "min_hr": "55", "avg_hr": "78", "hrv_rmssd": "45.2"}]
        result = parse_heart_rate_data(data)
        assert len(result) == 1
        assert result[0].resting_hr == 62

    def test_parse_workouts(self):
        data = [{"date": "2024-01-01", "workout_type": "Run", "duration_minutes": "45", "calories_burned": "400", "avg_heart_rate": "140", "max_heart_rate": "165"}]
        result = parse_workout_data(data)
        assert len(result) == 1
        assert result[0].workout_type == "Run"


class TestWellnessScore:
    def test_full_data(self):
        steps = DailySteps(date="2024-01-01", steps=10000)
        sleep = DailySleep(date="2024-01-01", total_minutes=480, deep_minutes=100)
        hr = DailyHeartRate(date="2024-01-01", resting_hr=60)
        workouts = [DailyWorkout(date="2024-01-01", duration_minutes=60)]
        score = calculate_wellness_score(steps, sleep, hr, workouts)
        assert 80 <= score <= 100

    def test_no_data(self):
        score = calculate_wellness_score(None, None, None, [])
        assert score == 0.0


class TestRecommendations:
    def test_low_steps(self):
        steps = DailySteps(date="2024-01-01", steps=2000)
        recs = generate_recommendations(steps, None, None, [])
        assert any("sedentary" in r.lower() for r in recs)

    def test_no_workout(self):
        recs = generate_recommendations(None, None, None, [])
        assert any("No workout" in r for r in recs)

    def test_high_hr(self):
        hr = DailyHeartRate(date="2024-01-01", resting_hr=85)
        recs = generate_recommendations(None, None, hr, [])
        assert any("elevated" in r.lower() for r in recs)


class TestDailyBrief:
    def test_generate(self):
        steps = [DailySteps(date="2024-01-01", steps=8000)]
        sleep = [DailySleep(date="2024-01-01", total_minutes=420, deep_minutes=80)]
        hr = [DailyHeartRate(date="2024-01-01", resting_hr=65)]
        workouts = [DailyWorkout(date="2024-01-01", workout_type="Run", duration_minutes=30, calories_burned=300)]
        brief = generate_daily_brief("2024-01-01", steps, sleep, hr, workouts)
        assert brief.date == "2024-01-01"
        assert brief.wellness_score > 0
        assert brief.summary_text != ""

    def test_generate_low_data(self):
        steps = [DailySteps(date="2024-01-01", steps=2000)]
        sleep = [DailySleep(date="2024-01-01", total_minutes=300, deep_minutes=40)]
        hr = [DailyHeartRate(date="2024-01-01", resting_hr=85)]
        brief = generate_daily_brief("2024-01-01", steps, sleep, hr, [])
        assert len(brief.recommendations) > 0

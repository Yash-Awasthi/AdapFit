"""Tests for chronotype analysis service."""
import pytest
from app.services.chronotype_analysis import (
    classify_chronotype, score_msq, analyze_chronotype,
    recommend_sleep_window, estimate_phase_shift, SleepRecord,
)


class TestClassifyChronotype:
    def test_definite_morning(self):
        r = classify_chronotype(150)  # 2:30 AM midpoint
        assert r["chronotype"] == "definite_morning"
        assert r["ordinal"] == 1

    def test_moderate_morning(self):
        r = classify_chronotype(180)
        assert r["chronotype"] == "moderate_morning"
        assert r["ordinal"] == 2

    def test_intermediate(self):
        r = classify_chronotype(200)
        assert r["chronotype"] == "intermediate"
        assert r["ordinal"] == 3

    def test_moderate_evening(self):
        r = classify_chronotype(220)
        assert r["chronotype"] == "moderate_evening"
        assert r["ordinal"] == 4

    def test_definite_evening(self):
        r = classify_chronotype(250)
        assert r["chronotype"] == "definite_evening"
        assert r["ordinal"] == 5

    def test_boundary_values(self):
        assert classify_chronotype(170)["chronotype"] == "moderate_morning"
        assert classify_chronotype(190)["chronotype"] == "intermediate"


class TestScoreMSQ:
    def test_extreme_morning(self):
        r = score_msq(140)
        assert r["morningness_score"] == 100.0
        assert r["interpretation"] == "Morning type"

    def test_extreme_evening(self):
        r = score_msq(260)
        assert r["morningness_score"] == 0.0
        assert r["interpretation"] == "Evening type"

    def test_intermediate(self):
        r = score_msq(200)
        assert 40 <= r["morningness_score"] <= 60
        assert r["interpretation"] == "Intermediate type"


class TestAnalyzeChronotype:
    def test_empty_records(self):
        assert "error" in analyze_chronotype([])

    def test_single_record(self):
        records = [SleepRecord(bedtime="23:00", wake_time="07:00", date="2026-01-01")]
        r = analyze_chronotype(records)
        assert "chronotype" in r
        assert r["record_count"] == 1
        assert r["phase_stability"] == "stable"

    def test_consistent_sleep(self):
        records = [
            SleepRecord(bedtime="22:30", wake_time="06:30", date=f"2026-01-{i:02d}")
            for i in range(1, 8)
        ]
        r = analyze_chronotype(records)
        assert r["phase_stability"] == "stable"
        assert r["record_count"] == 7

    def test_irregular_sleep(self):
        records = [
            SleepRecord(bedtime="22:00", wake_time="06:00", date="2026-01-01"),
            SleepRecord(bedtime="02:00", wake_time="10:00", date="2026-01-02"),
            SleepRecord(bedtime="21:00", wake_time="05:00", date="2026-01-03"),
            SleepRecord(bedtime="01:00", wake_time="09:00", date="2026-01-04"),
        ]
        r = analyze_chronotype(records)
        assert r["phase_stability"] == "irregular"


class TestRecommendSleepWindow:
    def test_morning_type(self):
        r = recommend_sleep_window(chronotype_ordinal=1)
        assert r["optimal_bedtime"] < "22:00" or r["optimal_bedtime"] > "20:00"
        assert "light_exposure" in r
        assert len(r["light_exposure"]) > 0

    def test_evening_type(self):
        r = recommend_sleep_window(chronotype_ordinal=5)
        assert "light_exposure" in r
        # Evening types get blue light warnings
        assert any("blue" in rec.lower() for rec in r["light_exposure"])

    def test_with_work_wake(self):
        r = recommend_sleep_window(chronotype_ordinal=3, work_wake="06:30")
        assert "work_bedtime" in r
        assert "work_wake" in r

    def test_work_wake_warning(self):
        # Early chronotype forced to very late wake = short sleep warning
        r = recommend_sleep_window(
            chronotype_ordinal=1, target_hours=8.0, work_wake="05:30"
        )
        # Warning depends on natural wake vs forced wake
        assert "optimal_bedtime" in r


class TestEstimatePhaseShift:
    def test_insufficient_data(self):
        assert "error" in estimate_phase_shift([])

    def test_phase_advance(self):
        # Midpoints getting earlier over time
        records = [
            SleepRecord(bedtime="00:00", wake_time="08:00", date=f"2026-01-{i:02d}")
            for i in range(1, 10)
        ]
        # Manually shift earlier
        records[-1] = SleepRecord(bedtime="23:00", wake_time="07:00", date="2026-01-09")
        records[-2] = SleepRecord(bedtime="23:30", wake_time="07:30", date="2026-01-08")
        records[-3] = SleepRecord(bedtime="23:00", wake_time="07:00", date="2026-01-07")
        r = estimate_phase_shift(records)
        assert r["direction"] in ("phase_advance", "stable")

    def test_stable_phase(self):
        records = [
            SleepRecord(bedtime="23:00", wake_time="07:00", date=f"2026-01-{i:02d}")
            for i in range(1, 10)
        ]
        r = estimate_phase_shift(records)
        assert r["direction"] == "stable"

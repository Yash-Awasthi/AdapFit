"""The merged sleep API scores only what was measured."""
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.services.sleep_analyzer import analyze_oximetry
from app.services.sleep_tracker import SleepJournal, minutes_between

client = TestClient(app)


def test_duration_wraps_midnight():
    assert minutes_between("23:30", "07:00") == 450
    assert minutes_between("01:00", "08:00") == 420


def test_a_manual_night_invents_no_stages():
    journal = SleepJournal()
    journal.log("23:00", "07:00", quality_rating=4)
    result = journal.analysis()
    assert result["stage_breakdown"] == []
    assert "deep_sleep" not in result["measured"] and "rem_sleep" not in result["measured"]
    assert result["avg_duration_hours"] == 8.0


def test_wearable_stages_are_scored():
    journal = SleepJournal()
    journal.log("23:00", "07:00", source="wearable", deep_minutes=90, rem_minutes=110,
                light_minutes=240, awake_minutes=40)
    result = journal.analysis()
    assert {"deep_sleep", "rem_sleep"} <= set(result["measured"])
    assert len(result["stage_breakdown"]) == 4


def test_debt_counts_only_logged_shortfall():
    journal = SleepJournal()
    journal.log("01:00", "07:00")
    journal.log("23:00", "07:00")
    debt = journal.debt()
    assert debt["debt_hours"] == 1.0 and debt["short_nights"] == 1


def test_bedtime_plan_needs_a_target_and_ends_on_full_cycles():
    journal = SleepJournal()
    assert journal.bedtime_plan() is None
    journal.set_profile(target_wake="06:30")
    plan = journal.bedtime_plan()
    assert plan["options"][0] == {"bedtime": "21:15", "cycles": 6, "sleep_hours": 9.0, "within_recommended": True}


def test_one_long_dip_counts_once():
    start = datetime(2026, 1, 1, 0, 0)
    readings = [96] * 20 + [90] * 10 + [96] * 20
    stamps = [start + timedelta(seconds=30 * i) for i in range(len(readings))]
    result = analyze_oximetry(readings, stamps)
    assert result["dips"] == 1


def test_sleep_endpoints_round_trip():
    r = client.post("/api/v1/sleep/logs", json={"bedtime": "23:15", "wake_time": "06:45", "quality_rating": 3})
    assert r.status_code == 201 and r.json()["total_minutes"] == 450
    assert client.put("/api/v1/sleep/profile", json={"target_wake": "06:45"}).status_code == 200
    analysis = client.get("/api/v1/sleep/analysis").json()
    assert analysis["nights_analyzed"] >= 1 and analysis["bedtime_plan"]["target_wake"] == "06:45"


def test_bad_clock_time_is_rejected():
    assert client.post("/api/v1/sleep/logs", json={"bedtime": "25:00", "wake_time": "07:00"}).status_code == 422


def test_smart_alarm_wakes_in_light_sleep():
    target = datetime(2026, 1, 1, 7, 0)
    samples = [{"timestamp": (target - timedelta(minutes=m)).isoformat(), "movement": 0.02, "heart_rate": 52}
               for m in range(40, 10, -1)]
    samples.append({"timestamp": (target - timedelta(minutes=8)).isoformat(), "movement": 0.3, "heart_rate": 64})
    r = client.post("/api/v1/sleep/smart-alarm", json={"target_time": target.isoformat(), "samples": samples})
    assert r.status_code == 200
    assert r.json()["should_wake"] is True

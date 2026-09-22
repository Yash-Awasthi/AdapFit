"""
Cardiac rehab: the target zone needs a real age, and a blank reading is not a
reassuring one.

Age defaulted to 65, so a 45-year-old was given a 65-year-old's training
ceiling. Blood pressure defaulted to "120/80" and oxygen saturation to 97,
which silenced the alerts this service exists to raise for exactly the patient
who recorded nothing.
"""
import pytest

from app.services.cardiac_rehab import CardiacRehabService


@pytest.fixture
def service():
    return CardiacRehabService()


def test_a_program_needs_an_age(service):
    result = service.setup_program("u", {})
    assert result["status"] == "insufficient_data"
    assert "heart_rate_zones" not in result


def test_an_implausible_age_is_refused(service):
    assert service.setup_program("u", {"age": 4})["status"] == "insufficient_data"
    assert service.setup_program("u", {"age": "fifty"})["status"] == "insufficient_data"


def test_the_target_zone_follows_the_age_given(service):
    younger = service.setup_program("a", {"age": 45})["heart_rate_zones"]
    older = service.setup_program("b", {"age": 70})["heart_rate_zones"]
    assert younger["maximum"] == 175
    assert older["maximum"] == 150
    assert younger["target_max"] > older["target_max"]


def test_unrecorded_vitals_are_stored_as_absent(service):
    service.setup_program("u", {"age": 60})
    entry = service.log_daily("u", {"exercise_min": 20})
    logged = service.daily_logs["u"][-1]
    assert logged["blood_pressure"] is None
    assert logged["spo2"] is None
    assert entry["alerts"] == [], "an alert was raised from a reading nobody took"


def test_real_readings_still_raise_their_alerts(service):
    service.setup_program("u", {"age": 60})
    entry = service.log_daily("u", {"bp": "155/95", "spo2": 90})
    assert "Blood pressure elevated" in entry["alerts"]
    assert "Oxygen saturation low" in entry["alerts"]


def test_a_low_blood_pressure_is_flagged(service):
    service.setup_program("u", {"age": 60})
    assert "Blood pressure low" in service.log_daily("u", {"bp": "85/55"})["alerts"]


def test_an_unparseable_blood_pressure_does_not_crash(service):
    service.setup_program("u", {"age": 60})
    assert service.log_daily("u", {"bp": "not a reading"})["alerts"] == []


def test_average_rpe_ignores_days_that_recorded_none(service):
    service.setup_program("u", {"age": 60})
    service.log_daily("u", {"rpe": 8, "exercise_min": 30})
    service.log_daily("u", {"exercise_min": 30})  # no RPE
    summary = service.get_progress_summary("u")
    assert summary["average_rpe"] == 8.0, "a blank RPE was averaged in as a middling 5"


def test_no_rpe_at_all_reports_none_rather_than_a_number(service):
    service.setup_program("u", {"age": 60})
    service.log_daily("u", {"exercise_min": 15})
    assert service.get_progress_summary("u")["average_rpe"] is None

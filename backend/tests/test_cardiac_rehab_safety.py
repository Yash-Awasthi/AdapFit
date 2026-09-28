"""
Cardiac rehab: the zone is prescribed or resting + 20, never 220 minus age, and
a blank reading is not a reassuring one.

Age-predicted zones do not hold for heart patients, most of all on beta
blockers. Blood pressure defaulted to "120/80" and oxygen saturation to 97,
which silenced the alerts this service exists to raise.
"""
import pytest

from app.services.cardiac_rehab import CardiacRehabService


@pytest.fixture
def service():
    return CardiacRehabService()


def test_no_heart_rate_given_means_effort_only(service):
    zones = service.setup_program("u", {})["heart_rate_zones"]
    assert zones["target_max"] is None and zones["source"] == "effort_only" and "RPE" in zones["effort"]


def test_age_does_not_set_a_zone(service):
    zones = service.setup_program("u", {"age": 45})["heart_rate_zones"]
    assert zones["target_max"] is None


def test_prescribed_zone_wins(service):
    zones = service.setup_program("u", {"resting_hr": 60, "prescribed_hr_min": 95, "prescribed_hr_max": 115})["heart_rate_zones"]
    assert (zones["target_min"], zones["target_max"], zones["source"]) == (95, 115, "prescribed")


def test_resting_plus_twenty_cap(service):
    zones = service.setup_program("u", {"resting_hr": 64})["heart_rate_zones"]
    assert zones["target_max"] == 84 and zones["source"] == "resting_plus_20"


def test_no_invented_fluid_limit(service):
    service.setup_program("u", {})
    assert "Fluid intake over daily limit" not in service.log_daily("u", {"fluid_ml": 3000})["alerts"]


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

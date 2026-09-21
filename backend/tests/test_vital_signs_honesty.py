"""
Vital signs are measured or absent, never invented.

The ECG endpoints used to answer with a random heart rate and made-up PR, QRS
and QT intervals labelled "Normal Sinus Rhythm", and an SpO2 estimate carried
a random pulse rate. A fabricated clinical reading is indistinguishable from a
real one once it reaches the screen, so these tests pin the absence.
"""
import pytest

from app.services.vital_signs import VitalSignsService


@pytest.fixture
def service():
    return VitalSignsService()


def test_starting_an_ecg_says_the_hardware_is_missing(service):
    result = service.start_ecg_measurement("u1")
    assert result["supported"] is False
    assert result["reason"] == "no_ecg_hardware"


def test_an_ecg_frame_never_produces_a_reading(service):
    for _ in range(50):
        result = service.process_ecg_frame("u1")
        assert result["supported"] is False
    assert service.get_ecg_history("u1") == []


def test_a_recorded_ecg_keeps_unreported_intervals_absent(service):
    service.record_ecg(heart_rate=62, rhythm="normal")
    reading = service.get_ecg_history("u1")[-1]
    assert reading["heart_rate"] == 62
    assert reading["pr_interval"] is None
    assert reading["qrs_duration"] is None
    assert reading["qt_interval"] is None


def test_a_recorded_ecg_keeps_the_intervals_a_device_did_report(service):
    service.record_ecg(heart_rate=58, rhythm="bradycardia", pr_interval_ms=168.0, qrs_duration_ms=92.0)
    reading = service.get_ecg_history("u1")[-1]
    assert reading["pr_interval"] == 168.0
    assert reading["qrs_duration"] == 92.0
    assert reading["qt_interval"] is None
    assert reading["classification"] == "Bradycardia"


def test_spo2_carries_no_pulse_unless_one_was_supplied(service):
    result = service.estimate_spo2(red_avg=0.6, infrared_avg=0.7)
    assert result["pulse_rate"] is None
    assert 70 <= result["spo2_percent"] <= 100


def test_spo2_keeps_a_supplied_pulse(service):
    assert service.estimate_spo2(red_avg=0.6, infrared_avg=0.7, pulse_rate=64)["pulse_rate"] == 64


def test_spo2_requires_both_channels():
    with pytest.raises(TypeError):
        VitalSignsService().estimate_spo2()  # type: ignore[call-arg]


def test_a_dead_infrared_channel_is_an_error_not_a_reading(service):
    assert "error" in service.estimate_spo2(red_avg=0.6, infrared_avg=0)


def test_the_summary_reports_nothing_rather_than_a_placeholder(service):
    summary = service.get_vitals_summary()
    assert summary["heart_rate"]["value"] is None
    assert summary["spo2"]["value"] is None
    assert summary["temperature"]["value"] is None
    assert summary["total_readings"] == 0

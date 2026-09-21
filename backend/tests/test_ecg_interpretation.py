"""
ECG interpretation comes from the intervals, or it does not come at all.

This service used to choose a rhythm with random.choice and report it with a
confidence between 0.85 and 0.99, so roughly one call in five announced atrial
fibrillation and told the user to see a cardiologist within 24 hours. These
tests pin the two properties that replaced it: the same recording always reads
the same way, and a recording that says nothing produces no classification.
"""
import random

import pytest

from app.services.ecg_interpreter import IRREGULAR_CV, MIN_INTERVALS, ECGInterpreterService


@pytest.fixture
def service():
    return ECGInterpreterService()


def _steady(count=40, mean_ms=820.0, jitter=12.0, seed=1):
    rng = random.Random(seed)
    return [mean_ms + rng.uniform(-jitter, jitter) for _ in range(count)]


def test_no_intervals_gives_no_classification(service):
    result = service.interpret_ecg("u", {})
    assert result["status"] == "inconclusive"
    assert result["reason"] == "insufficient_data"
    assert "classification" not in result


def test_too_few_intervals_is_inconclusive(service):
    result = service.interpret_ecg("u", {"rr_intervals_ms": _steady(count=MIN_INTERVALS - 1)})
    assert result["status"] == "inconclusive"


def test_inconclusive_readings_are_not_stored(service):
    service.interpret_ecg("u", {})
    service.interpret_ecg("u", {"rr_intervals_ms": [800, 810]})
    assert service.get_ecg_history("u") == []


def test_the_same_recording_always_reads_the_same_way(service):
    rr = _steady()
    first = service.interpret_ecg("u", {"rr_intervals_ms": rr})
    second = service.interpret_ecg("u", {"rr_intervals_ms": rr})
    assert first["classification"] == second["classification"]
    assert first["heart_rate_bpm"] == second["heart_rate_bpm"]


def test_heart_rate_follows_the_intervals(service):
    slow = service.interpret_ecg("u", {"rr_intervals_ms": _steady(mean_ms=1200)})
    fast = service.interpret_ecg("u", {"rr_intervals_ms": _steady(mean_ms=500)})
    assert slow["heart_rate_bpm"] == pytest.approx(50, abs=2)
    assert fast["heart_rate_bpm"] == pytest.approx(120, abs=3)
    assert "slow rate" in slow["classification"]
    assert "fast rate" in fast["classification"]


def test_steady_intervals_read_as_regular(service):
    result = service.interpret_ecg("u", {"rr_intervals_ms": _steady()})
    assert result["rhythm"] == "regular"
    assert result["rr_variation_pct"] < IRREGULAR_CV * 100


def test_erratic_intervals_read_as_irregular(service):
    rng = random.Random(7)
    erratic = [rng.uniform(500, 1200) for _ in range(40)]
    result = service.interpret_ecg("u", {"rr_intervals_ms": erratic})
    assert result["rhythm"] == "irregular"


def test_no_reading_ever_names_an_arrhythmia(service):
    """Naming a condition is a clinical diagnosis, not something R-R intervals give."""
    rng = random.Random(3)
    banned = ("fibrillation", "afib", "a-fib", "flutter", "tachycardia", "bradycardia")
    for seed in range(20):
        rr = [rng.uniform(400, 1400) for _ in range(40)]
        result = service.interpret_ecg("u", {"rr_intervals_ms": rr})
        text = f"{result.get('classification', '')} {result.get('description', '')}".lower()
        assert not any(word in text for word in banned), text


def test_every_analysed_reading_carries_a_disclaimer(service):
    assert "not a diagnosis" in service.interpret_ecg("u", {"rr_intervals_ms": _steady()})["disclaimer"]


def test_hrv_needs_real_readings_first(service):
    assert service.get_heart_rate_variability("u")["status"] == "insufficient_data"


def test_hrv_is_computed_from_the_stored_readings(service):
    for seed in range(6):
        service.interpret_ecg("u", {"rr_intervals_ms": _steady(seed=seed)})
    result = service.get_heart_rate_variability("u")
    assert result["status"] == "ok"
    assert result["hrv_ms"] > 0
    assert result["readings_used"] == 6


def test_the_irregularity_summary_counts_rather_than_scores(service):
    assert service.get_irregularity_summary("u")["status"] == "no_data"
    service.interpret_ecg("u", {"rr_intervals_ms": _steady()})
    summary = service.get_irregularity_summary("u")
    assert summary["irregular_readings"] == 0
    assert summary["total_readings"] == 1
    assert "not a diagnosis" in summary["disclaimer"]

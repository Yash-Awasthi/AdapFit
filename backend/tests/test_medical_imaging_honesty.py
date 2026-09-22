"""
A skin lesion is scored from measurements, or it is not scored.

The ABCDE features defaulted to random values, so a request carrying no
measurements could come back "URGENT: High suspicion for melanoma" — or miss a
real one — by chance, and the differential attached invented percentages to
the word melanoma. These tests pin the measured behaviour.
"""
import pytest

from app.services.medical_imaging import MedicalImagingService

FULL = {
    "asymmetry_score": 0.2,
    "border_irregularity": 0.2,
    "color_variation": 0.2,
    "diameter_mm": 3.0,
}


@pytest.fixture
def service():
    return MedicalImagingService()


def test_no_features_gives_no_score(service):
    result = service.analyze_skin_lesion({})
    assert result["status"] == "insufficient_data"
    assert "risk_level" not in result
    assert set(result["missing_features"]) == set(service.REQUIRED_FEATURES)


def test_a_partial_measurement_is_refused(service):
    result = service.analyze_skin_lesion({"asymmetry_score": 0.9})
    assert result["status"] == "insufficient_data"
    assert "asymmetry_score" not in result["missing_features"]


def test_a_boolean_is_not_a_measurement(service):
    result = service.analyze_skin_lesion({**FULL, "diameter_mm": True})
    assert result["status"] == "insufficient_data"


def test_the_same_lesion_always_scores_the_same(service):
    first = service.analyze_skin_lesion(FULL)
    second = service.analyze_skin_lesion(FULL)
    assert first["abcde_score"] == second["abcde_score"]
    assert first["risk_level"] == second["risk_level"]


def test_a_benign_looking_lesion_scores_low(service):
    result = service.analyze_skin_lesion(FULL)
    assert result["abcde_score"] == 0
    assert result["risk_level"] == "low"


def test_a_lesion_meeting_every_criterion_scores_critical(service):
    result = service.analyze_skin_lesion({
        "asymmetry_score": 0.9,
        "border_irregularity": 0.9,
        "color_variation": 0.9,
        "diameter_mm": 12.0,
        "evolution_detected": True,
    })
    assert result["abcde_score"] == 5
    assert result["risk_level"] == "critical"
    assert result["criteria_assessed"] == 5


def test_no_condition_is_named(service):
    result = service.analyze_skin_lesion({**FULL, "asymmetry_score": 0.9, "border_irregularity": 0.9})
    assert "differential_diagnosis" not in result
    assert "melanoma" not in result["recommendation"].lower()


def test_no_confidence_figure_is_invented(service):
    assert "confidence" not in service.analyze_skin_lesion(FULL)


def test_every_score_says_what_it_is_not(service):
    assert "does not diagnose" in service.analyze_skin_lesion(FULL)["disclaimer"]

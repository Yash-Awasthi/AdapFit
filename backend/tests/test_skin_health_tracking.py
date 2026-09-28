"""
A mole is tracked by measurement, not by a fixed reassuring analysis.

`analyze_mole_photo` returned symmetry 85, border 80, colour 75 and
"overall risk: low" for every mole regardless of what it looked like — a fixed
reassuring result, about skin cancer, for a photo nothing examined. What a
phone can genuinely do is notice change, which is the "E" in ABCDE and the
sign that most warrants a clinician.
"""
import pytest

from app.services.skin_health import SkinHealthService


@pytest.fixture
def service():
    return SkinHealthService()


@pytest.fixture
def mole_id(service):
    service.add_mole("upper back", "back", 4.0, "brown")
    return next(iter(service._moles))


def test_the_fabricated_photo_analysis_is_gone(service):
    assert not hasattr(service, "analyze_mole_photo")


def test_a_measurement_needs_a_real_size(service, mole_id):
    assert "error" in service.record_measurement(mole_id, 0)
    assert "error" in service.record_measurement(mole_id, -3)


def test_an_unknown_mole_is_not_measured(service):
    assert "error" in service.record_measurement("no-such-mole", 5.0)


def test_a_stable_mole_reports_no_change(service, mole_id):
    result = service.record_measurement(mole_id, 4.1)
    assert result["changes"] == []
    assert "No change" in result["recommendation"]


def test_growth_is_reported_and_sends_the_user_to_a_clinician(service, mole_id):
    result = service.record_measurement(mole_id, 7.0)
    assert result["growth_mm"] == pytest.approx(3.0)
    assert any("Grew" in change for change in result["changes"])
    assert "clinician" in result["recommendation"]


def test_a_colour_change_is_reported(service, mole_id):
    result = service.record_measurement(mole_id, 4.0, "black")
    assert any("Colour changed" in change for change in result["changes"])


def test_the_abcde_score_follows_the_new_measurement(service, mole_id):
    before = service._moles[mole_id]["abcde_score"]["total"]
    service.record_measurement(mole_id, 12.0, "multi")
    after = service._moles[mole_id]["abcde_score"]["total"]
    assert after > before


def test_no_risk_verdict_is_invented(service, mole_id):
    result = service.record_measurement(mole_id, 4.0)
    assert "overall_risk" not in result
    assert "symmetry_score" not in result
    assert "does not diagnose" in result["disclaimer"]


def test_every_measurement_is_kept(service, mole_id):
    service.record_measurement(mole_id, 4.5)
    service.record_measurement(mole_id, 5.0)
    history = service.get_mole_history(mole_id)
    assert [round(entry["size_mm"], 1) for entry in history] == [4.5, 5.0]


def test_abcde_without_a_photo_assesses_only_diameter(service):
    mole = service.add_mole("arm", "arm", 8.0, "black")["mole"]
    score = mole["abcde_score"]
    assert score["asymmetry"] is None and score["border"] is None and score["assessed"] == 1


def test_photo_features_that_worsen_count_as_change(service, mole_id):
    service.record_measurement(mole_id, None, features={"asymmetry_score": 0.1, "border_irregularity": 0.2, "color_variation": 0.1})
    result = service.record_measurement(mole_id, None, features={"asymmetry_score": 0.6, "border_irregularity": 0.2, "color_variation": 0.1})
    assert "Shape became less even" in result["changes"]
    assert service.get_mole(mole_id)["abcde_score"]["evolution"] == 1


def test_fitzpatrick_type_feeds_the_check_plan(service):
    service.assess_skin_type({"skin_color": 1, "sun_reaction": 1, "tanning_ability": 1})
    assert service.get_skin_cancer_risk()["skin_type_risk"] == "very_high"

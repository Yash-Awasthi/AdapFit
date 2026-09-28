"""Check-ups follow age and sex and turn off once done."""
from datetime import date

from app.services.preventive_screening import PreventiveScreeningService


def test_needs_a_profile():
    assert PreventiveScreeningService().schedule()["status"] == "needs_profile"


def test_a_35_year_old_woman_gets_ncd_screening():
    s = PreventiveScreeningService()
    s.set_profile(35, "female")
    ids = {c["id"] for c in s.schedule()["checks"]}
    assert {"blood_sugar", "cervical_cancer", "breast_exam"} <= ids and "eyes" not in ids


def test_logging_a_check_clears_it():
    s = PreventiveScreeningService()
    s.set_profile(45, "male")
    s.log("blood_sugar", date.today().isoformat())
    sugar = next(c for c in s.schedule()["checks"] if c["id"] == "blood_sugar")
    assert sugar["due"] is False

"""Prohibited fixed dose combinations match on ingredients and, where the notification names one, the form."""
from app.services.banned_fdc import check


def test_listed_form_is_flagged_with_its_notification():
    r = check(["nimesulide", "paracetamol"], "Nise P DT Tablet")
    assert r["status"] == "prohibited" and "02.06.2023" in r["notification"]
    assert "ask your doctor or pharmacist" in r["message"]


def test_the_same_ingredients_in_an_unlisted_form_are_not_flagged():
    assert check(["nimesulide", "paracetamol"], "Nise P Tablet") is None
    assert check(["aceclofenac", "paracetamol"], "Zerodol-P Tablet") is None
    assert check(["aceclofenac", "paracetamol"], "Hifenac SR-P Tablet")["status"] == "prohibited"


def test_salt_names_and_spelling_do_not_hide_a_match():
    assert check(["amoxycillin", "bromhexine hydrochloride"])["status"] == "prohibited"


def test_a_notification_quashed_in_court_is_reported_as_such():
    assert check(["etodolac", "paracetamol"])["status"] == "quashed"


def test_2026_notification_is_included():
    assert "20.06.2026" in check(["cefuroxime", "serratiopeptidase"])["notification"]

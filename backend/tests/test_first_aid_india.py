"""First aid speaks to India: local numbers, metric units, snakebite and poisoning."""
import json

from app.services.first_aid import first_aid_service as fa


def test_no_us_numbers_or_units():
    text = json.dumps([fa.emergency_protocols, fa.cpr_training], ensure_ascii=False)
    for banned in ("911", "°F", "inches", "feet"):
        assert banned not in text


def test_snakebite_and_poisoning_are_life_threatening():
    out = fa.assess_emergency(["snake bite"])
    assert out["call_emergency"] and out["relevant_protocols"][0]["name"] == "Snakebite"
    assert fa.assess_emergency(["pesticide"])["call_emergency"]

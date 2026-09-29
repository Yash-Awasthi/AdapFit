"""Generated replies never keep a diagnosis or a medication change."""
from app.services.safety_policy import screen_reply


def test_medication_change_is_removed():
    out = screen_reply("Good sleep last night. You should reduce your metformin dose this week. Keep walking.")
    assert "metformin" not in out and "Keep walking." in out and "ask your doctor" in out


def test_diagnosis_is_removed():
    out = screen_reply("Your HRV dropped 20%. You probably have atrial fibrillation.")
    assert "fibrillation" not in out and out.startswith("Your HRV dropped 20%.")


def test_ordinary_advice_is_untouched():
    text = "Your recovery is 72, above your usual. Train as planned and stop for water every 20 minutes."
    assert screen_reply(text) == text

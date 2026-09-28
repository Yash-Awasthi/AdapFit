"""Triage uses the reported severity and red flags; it never names a cause."""
from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)


def check(**body):
    return c.post("/api/v1/symptoms/check", json=body).json()


def test_a_ten_out_of_ten_headache_is_an_emergency():
    assert check(symptom="headache", severity=10)["level"] == "emergency"


def test_a_red_flag_escalates_a_mild_symptom():
    assert check(symptom="headache", severity=3, red_flags=["Fever with a stiff neck"])["level"] == "emergency"


def test_a_long_cough_needs_a_doctor_and_mentions_tb():
    r = check(symptom="cough", severity=2, days=20)
    assert r["level"] == "doctor" and "TB" in r["action"]


def test_no_causes_are_named():
    r = check(symptom="stomach pain", severity=5)
    assert "possible_causes" not in r and "appendicitis" not in str(r).lower()


def test_free_text_red_flag_is_caught():
    r = check(symptom="dizziness", severity=3, note="my face is drooping")
    assert r["level"] == "emergency"

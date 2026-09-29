"""App crash reports are accepted without sign-in and bounded in size."""
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

c = TestClient(app)


def test_crash_report_without_token(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_DISABLED", False)
    r = c.post("/api/v1/client-errors", json={"message": "TypeError: x is undefined", "stack": "at Home",
                                              "fatal": True, "platform": "android", "version": "2.0.0"})
    assert r.status_code == 204


def test_oversized_report_is_refused():
    assert c.post("/api/v1/client-errors", json={"message": "x" * 501}).status_code == 422


def test_signup_can_read_consent_purposes_without_a_token(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_DISABLED", False)
    r = c.get("/api/v1/privacy/consent/purposes")
    assert r.status_code == 200 and "health_data" in r.json()["purposes"]


def test_dev_bypass_still_checks_a_token_that_is_sent():
    # AUTH_DISABLED is on in tests; an expired or forged token must still get 401 so the app refreshes.
    assert c.get("/api/v1/privacy/consent", headers={"Authorization": "Bearer not-a-token"}).status_code == 401
    assert c.get("/api/v1/privacy/consent").status_code == 200

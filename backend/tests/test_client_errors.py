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

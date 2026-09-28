"""Glucose summary uses real episodes and consensus targets, and never advises dosing."""
import time

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from tests.conftest import register_user

c = TestClient(app)


@pytest.fixture(autouse=True)
def _auth(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_DISABLED", False)


def test_a_run_of_lows_is_one_episode_and_targets_are_reported():
    h = {"Authorization": f"Bearer {register_user('cgm@example.com', 'cgm-user')['tokens']['access_token']}"}
    now = time.time() - 6 * 3600
    values = [110] * 10 + [62, 60, 58, 61] + [120] * 10 + [65]
    readings = [{"timestamp": now + i * 300, "value_mgdl": v} for i, v in enumerate(values)]
    assert c.post("/api/v1/diabetes/glucose/import", headers=h, json={"readings": readings}).json()["imported"] == len(values)
    s = c.get("/api/v1/diabetes/glucose/summary", headers=h).json()
    assert s["episodes"]["hypo_count"] == 2
    assert s["targets_met"]["below_70_under_4pct"] is False
    text = (s["next_step"] + str(c.get("/api/v1/diabetes/glucose/patterns", headers=h).json())).lower()
    assert "insulin" not in text and "medication adjustment" not in text

"""Family sharing: invite by email, share only what was granted."""
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from tests.conftest import register_user

c = TestClient(app)


@pytest.fixture(autouse=True)
def _auth(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_DISABLED", False)


def _h(email, name):
    return {"Authorization": f"Bearer {register_user(email, name)['tokens']['access_token']}"}


def test_invite_accept_and_see_only_shared_categories():
    parent, child = _h("parent@example.com", "parent1"), _h("child@example.com", "child1")
    c.post("/api/v1/emergency/medical-info", headers=parent, json={"blood_type": "O+", "allergies": ["sulfa"]})
    c.post("/api/v1/sleep/logs", headers=parent, json={"bedtime": "22:30", "wake_time": "06:00"})
    assert c.post("/api/v1/family-network/invite", headers=child, json={"invitee": "parent@example.com", "relationship": "parent"}).json()["sent"]
    invite = c.get("/api/v1/family-network/invites", headers=parent).json()["invites"][0]
    c.post("/api/v1/family-network/invite/accept", headers=parent, json={"invite_id": invite["invite_id"]})
    conn = c.get("/api/v1/family-network/connections", headers=parent).json()["connections"][0]["connection_id"]
    c.post("/api/v1/family-network/permissions", headers=parent, json={"connection_id": conn, "permissions": {"view_emergency": True}})
    seen = c.get(f"/api/v1/family-network/member/{conn}", headers=child).json()
    assert "sulfa" in str(seen["emergency"]) and "sleep" not in seen


def test_unknown_email_gets_the_same_reply():
    h = _h("lonely@example.com", "lonely1")
    r = c.post("/api/v1/family-network/invite", headers=h, json={"invitee": "nobody@example.com"}).json()
    assert r["sent"] is True

"""Consent gates, guardian consent, account erasure and export under the DPDP Act."""
import asyncio
import re
import time

import pytest
from fastapi.testclient import TestClient

from app.core import durable, privacy
from app.core.auth import user_manager
from app.core.config import settings
from app.main import app
from tests.conftest import register_user

c = TestClient(app)
PASSWORD = "Str0ngPassw0rd!"


@pytest.fixture(autouse=True)
def _auth(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_DISABLED", False)


def _h(reg):
    return {"Authorization": f"Bearer {reg['tokens']['access_token']}"}


def _signup(email, username, **extra):
    body = {"email": email, "username": username, "password": PASSWORD, **extra}
    return c.post("/api/v1/auth/register", json=body)


def test_signup_needs_a_birth_date_and_the_required_consent():
    assert _signup("nodob@example.com", "nodob").status_code == 400
    r = _signup("noconsent@example.com", "noconsent", birth_date="1990-05-01", consent={"ai": True})
    assert r.status_code == 400 and "health data" in r.json()["detail"]
    r = _signup("ok@example.com", "okuser", birth_date="1990-05-01", consent={"health_data": True, "ai": False})
    assert r.status_code == 200
    purposes = r.json()["privacy"]["purposes"]
    assert purposes["health_data"]["granted"] and not purposes["ai"]["granted"]
    assert purposes["health_data"]["version"] == privacy.POLICY_VERSION


def test_an_account_without_current_consent_is_held_at_the_consent_screen():
    reg = register_user("legacy@example.com", "legacyuser")
    uid, h = reg["user"]["id"], _h(reg)
    dict.pop(privacy._records, uid)
    r = c.get("/api/v1/goals", headers=h)
    assert r.status_code == 403 and r.json()["detail"] == "consent_required"
    assert c.get("/api/v1/privacy/consent", headers=h).json()["needs_consent"]
    assert c.put("/api/v1/privacy/consent", headers=h, json={"choices": {"health_data": True}}).status_code == 200
    assert c.get("/api/v1/goals", headers=h).status_code == 200


def test_withdrawing_ai_and_sharing_takes_effect():
    reg = register_user("withdraw@example.com", "withdrawuser")
    uid, h = reg["user"]["id"], _h(reg)
    assert privacy.allowed("ai", uid)
    c.put("/api/v1/privacy/consent", headers=h, json={"choices": {"ai": False, "sharing": False}})
    assert not privacy.allowed("ai", uid)
    r = c.post("/api/v1/community/share", headers=h, json={"title": "Hello"})
    assert r.status_code == 403 and r.json()["detail"] == "sharing_consent_required"
    assert c.post("/api/v1/diet/photo-log", headers=h, json={"image_base64": "x", "meal_type": "lunch"}).status_code == 403
    events = c.get("/api/v1/privacy/consent/history", headers=h).json()["events"]
    assert [e["granted"] for e in events if e["purpose"] == "ai"] == [True, False]


def test_a_child_needs_a_guardian_who_can_agree(monkeypatch):
    sent = []

    async def fake_send(to, subject, body):
        sent.append((to, body))
        return True

    monkeypatch.setattr("app.core.mailer.send_mail", fake_send)
    child_dob = f"{time.gmtime().tm_year - 14}-01-01"
    assert _signup("kid@example.com", "kiduser", birth_date=child_dob).status_code == 400  # no guardian email
    r = _signup("kid@example.com", "kiduser", birth_date=child_dob, guardian_email="parent@example.com",
                consent={"health_data": True, "ai": True, "analytics": True})
    assert r.status_code == 200 and r.json()["privacy"]["guardian_pending"]
    h = {"Authorization": f"Bearer {r.json()['tokens']['access_token']}"}
    assert c.get("/api/v1/goals", headers=h).json()["detail"] == "guardian_pending"
    assert c.put("/api/v1/privacy/consent", headers=h, json={"choices": {"ai": True}}).status_code == 403

    to, body = sent[-1]
    token = re.search(r"/privacy/guardian/(\S+)", body).group(1)
    assert to == "parent@example.com"
    page = c.get(f"/api/v1/privacy/guardian/{token}")
    assert page.status_code == 200 and "name=analytics" not in page.text
    refused = c.post(f"/api/v1/privacy/guardian/{token}", data={"decision": "agree", "name": "A Parent",
                                                                 "relationship": "Mother", "health_data": "1"})
    assert "Not saved" in refused.text  # adulthood not declared
    ok = c.post(f"/api/v1/privacy/guardian/{token}", data={"decision": "agree", "name": "A Parent",
                                                            "relationship": "Mother", "declared_adult": "1",
                                                            "health_data": "1", "ai": "1"})
    assert "Consent recorded" in ok.text
    state = c.get("/api/v1/privacy/consent", headers=h).json()
    assert state["guardian"]["relationship"] == "Mother"
    assert state["purposes"]["ai"]["granted"] and not state["purposes"]["analytics"]["granted"]
    assert c.get("/api/v1/goals", headers=h).status_code == 200
    assert "expired" in c.get(f"/api/v1/privacy/guardian/{token}").text


def test_a_guardian_who_declines_deletes_the_account(monkeypatch):
    sent = []

    async def fake_send(to, subject, body):
        sent.append(body)
        return True

    monkeypatch.setattr("app.core.mailer.send_mail", fake_send)
    r = _signup("kid2@example.com", "kiduser2", birth_date=f"{time.gmtime().tm_year - 10}-06-01",
                guardian_email="parent2@example.com")
    uid = r.json()["user"]["id"]
    token = re.search(r"/privacy/guardian/(\S+)", sent[-1]).group(1)
    assert "deleted" in c.post(f"/api/v1/privacy/guardian/{token}", data={"decision": "decline"}).text
    assert uid not in user_manager._users


def test_deletion_waits_out_the_grace_period_then_erases_shared_records():
    other = register_user("neighbour@example.com", "neighbour")
    post = c.post("/api/v1/community/share", headers=_h(other), json={"title": "Morning run"}).json()

    reg = register_user("leaving@example.com", "leavinguser")
    uid, h = reg["user"]["id"], _h(reg)
    c.post("/api/v1/fertility/log", headers=h, json={"user_id": uid, "date": "2026-09-01", "data": {"bbt": 36.5}})
    goal = c.post("/api/v1/goals", headers=h, json={"name": "Squat", "goal_type": "strength", "target_value": 100}).json()
    c.post(f"/api/v1/goals/{goal['id']}/update", headers=h, json={"current_value": 60})
    c.post(f"/api/v1/community/{post['id']}/comments", headers=h, json={"text": "Nice"})
    c.post(f"/api/v1/community/{post['id']}/like", headers=h)

    exported = c.get("/api/v1/export/all", headers=h).json()["data"]
    assert "2026-09-01" in str(exported["shared_feature_data"])
    assert exported["privacy"]["purposes"]["health_data"]["granted"]

    assert c.post("/api/v1/auth/delete-account", headers=h, json={"password": "wrong"}).status_code == 403
    assert c.post("/api/v1/auth/delete-account", headers=h, json={"password": PASSWORD}).json()["grace_minutes"] == 30
    assert c.get("/api/v1/goals", headers=h).json()["detail"] == "deletion_pending"
    assert c.get("/api/v1/export/all", headers=h).status_code == 200
    assert c.post("/api/v1/auth/delete-account/cancel", headers=h).json()["cancelled"]
    assert c.get("/api/v1/goals", headers=h).status_code == 200

    c.post("/api/v1/auth/delete-account", headers=h, json={"password": PASSWORD})
    assert asyncio.run(privacy.run_due_deletions(time.time() + 60)) == 0
    assert asyncio.run(privacy.run_due_deletions(time.time() + privacy.DELETION_GRACE_SECONDS + 1)) == 1

    assert uid not in user_manager._users
    held = str(durable.export_shared(uid)) + str({k: v for k, v in dict.items(privacy._records) if k == uid})
    assert uid not in held and "2026-09-01" not in held
    from app.api.v1.endpoints.goals import goal_logs
    from app.api.v1.endpoints.community import community_comments, community_likes, shared_workouts
    assert goal["id"] not in goal_logs
    assert post["id"] in shared_workouts and not community_comments.get(post["id"])
    assert uid not in community_likes.get(post["id"], set())
    rows = asyncio.run(durable._store().load_all())
    assert not [r for r in rows if uid.encode() in r[2] or r[1] == uid]


def test_retention_erases_unconfirmed_children_and_warns_the_long_inactive(monkeypatch):
    mails = []

    async def fake_send(to, subject, body):
        mails.append((to, subject))
        return True

    monkeypatch.setattr("app.core.mailer.send_mail", fake_send)
    kid = _signup("kid3@example.com", "kiduser3", birth_date=f"{time.gmtime().tm_year - 12}-01-01",
                  guardian_email="parent3@example.com").json()["user"]["id"]
    idle = register_user("idle@example.com", "idleuser")["user"]["id"]
    user_manager._users[idle].created_at = time.time() - (privacy.INACTIVE_DAYS + 1) * 86400

    later = time.time() + privacy.GUARDIAN_WAIT_DAYS * 86400 + 60
    asyncio.run(privacy.run_due_deletions(later))
    assert kid not in user_manager._users
    assert idle in user_manager._users and ("idle@example.com", "Your AdapFit account will be deleted") in mails

    asyncio.run(user_manager.login("idle@example.com", PASSWORD))
    asyncio.run(privacy.run_due_deletions(later + privacy.INACTIVE_NOTICE_HOURS * 3600))
    assert idle in user_manager._users

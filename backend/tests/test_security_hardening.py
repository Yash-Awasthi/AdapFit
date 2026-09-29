"""Sessions, password reset, the durable audit log, encryption at rest, the vault and public surfaces."""
import asyncio
import re
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import audit, crypto, durable
from app.core.auth import create_access_token, user_manager
from app.core.config import settings
from app.main import app
from tests.conftest import register_user

c = TestClient(app)
PASSWORD = "Str0ngPassw0rd!"


@pytest.fixture(autouse=True)
def _auth(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_DISABLED", False)


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


def _login(email, password=PASSWORD):
    return c.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_a_refresh_token_is_not_an_api_credential():
    """It used to pass AuthMiddleware and skip identity binding, so any user_id was readable."""
    me = register_user("rt-caller@example.com", "rtcaller")
    victim = register_user("rt-victim@example.com", "rtvictim")["user"]["id"]
    refresh = me["tokens"]["refresh_token"]
    assert c.get(f"/api/v1/users/{victim}", headers=_bearer(refresh)).status_code == 401
    assert c.get(f"/api/v1/export/all?user_id={victim}", headers=_bearer(refresh)).status_code == 401


def test_password_change_ends_other_sessions_and_keeps_this_one():
    reg = register_user("chpw@example.com", "chpwuser")
    old_access, old_refresh = reg["tokens"]["access_token"], reg["tokens"]["refresh_token"]
    time.sleep(0.01)
    r = c.post("/api/v1/auth/change-password", headers=_bearer(old_access),
               json={"old_password": PASSWORD, "new_password": "N3wPassword!"})
    assert r.status_code == 200
    fresh = r.json()["tokens"]
    assert c.get("/api/v1/auth/me", headers=_bearer(old_access)).status_code == 401
    assert c.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh}).status_code == 401
    assert c.get("/api/v1/auth/me", headers=_bearer(fresh["access_token"])).status_code == 200


def test_reusing_a_rotated_refresh_token_ends_every_session():
    reg = register_user("reuse@example.com", "reuseuser")
    first = reg["tokens"]["refresh_token"]
    rotated = c.post("/api/v1/auth/refresh", json={"refresh_token": first}).json()["tokens"]
    # The thief replays the old token: both the thief and the owner lose the session.
    assert c.post("/api/v1/auth/refresh", json={"refresh_token": first}).status_code == 401
    assert c.post("/api/v1/auth/refresh", json={"refresh_token": rotated["refresh_token"]}).status_code == 401
    events = [e["event"] for e in asyncio.run(audit.entries(reg["user"]["id"]))]
    assert "refresh_token_reuse" in events and "sessions_revoked" in events


def test_sign_out_ends_the_session_without_an_access_token():
    reg = register_user("logout@example.com", "logoutuser")
    refresh = reg["tokens"]["refresh_token"]
    assert c.post("/api/v1/auth/logout", json={"refresh_token": refresh}).status_code == 200
    assert c.post("/api/v1/auth/refresh", json={"refresh_token": refresh}).status_code == 401


def test_a_suspended_account_loses_access_at_once():
    reg = register_user("suspend@example.com", "suspenduser")
    h = _bearer(reg["tokens"]["access_token"])
    assert c.get("/api/v1/auth/me", headers=h).status_code == 200
    asyncio.run(user_manager.suspend_user(reg["user"]["id"]))
    assert c.get("/api/v1/goals", headers=h).status_code == 401


def test_password_reset_by_email_link(monkeypatch):
    sent = []

    async def fake_send(to, subject, body):
        sent.append((to, body))
        return True

    monkeypatch.setattr("app.core.mailer.send_mail", fake_send)
    reg = register_user("reset@example.com", "resetuser")
    same = {"message": "If the email has an account, a reset link has been sent"}
    assert c.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"}).json() == same
    assert c.post("/api/v1/auth/forgot-password", json={"email": "reset@example.com"}).json() == same
    assert len(sent) == 1 and sent[0][0] == "reset@example.com"
    token = re.search(r"/auth/reset-password/(\S+)", sent[0][1]).group(1)

    assert "New password" in c.get(f"/api/v1/auth/reset-password/{token}").text
    r = c.post(f"/api/v1/auth/reset-password/{token}", data={"password": "weak", "confirm": "weak"})
    assert "Not saved" in r.text
    r = c.post(f"/api/v1/auth/reset-password/{token}", data={"password": "Rese7Password", "confirm": "Rese7Password"})
    assert "Password changed" in r.text
    assert "expired" in c.get(f"/api/v1/auth/reset-password/{token}").text
    assert c.post("/api/v1/auth/refresh", json={"refresh_token": reg["tokens"]["refresh_token"]}).status_code == 401
    assert _login("reset@example.com").status_code == 401
    assert _login("reset@example.com", "Rese7Password").status_code == 200


def test_security_events_are_durable_and_visible_to_the_owner():
    reg = register_user("auditme@example.com", "auditme")
    assert _login("auditme@example.com", "WrongPassw0rd").status_code == 401
    _login("nosuch@example.com", "WrongPassw0rd")
    rows = c.get("/api/v1/auth/activity", headers=_bearer(reg["tokens"]["access_token"])).json()["entries"]
    events = [e["event"] for e in rows]
    assert "login_failed_bad_password" in events and "register" in events
    assert all(e["user_id"] == reg["user"]["id"] or e["actor_id"] == reg["user"]["id"] for e in rows)
    # An email with no account is kept only as a keyed hash, never in clear.
    unknown = [e for e in asyncio.run(audit.entries(None, 1000)) if e["event"] == "login_failed_unknown_email"]
    assert unknown and all("nosuch" not in str(e) for e in unknown)
    assert unknown[0]["details"]["email_hash"] == audit.email_hash("nosuch@example.com")


def test_audit_entries_older_than_a_year_are_purged():
    asyncio.run(audit.record("old_event", user_id="purge-user"))
    assert asyncio.run(audit.purge_expired(now=time.time() + audit.RETENTION_SECONDS + 10)) >= 1
    assert not asyncio.run(audit.entries("purge-user"))


def test_admin_access_to_another_users_records_is_logged():
    victim = register_user("watched@example.com", "watcheduser")
    admin_id = register_user("support@example.com", "supportuser")["user"]["id"]
    h = _bearer(create_access_token(admin_id, role="admin"))
    c.get(f"/api/v1/decision/today?user_id={victim['user']['id']}", headers=h)
    rows = c.get("/api/v1/auth/activity", headers=_bearer(victim["tokens"]["access_token"])).json()["entries"]
    assert any(e["event"] == "admin_access" and e["actor_id"] == admin_id for e in rows)


def test_feature_state_is_encrypted_at_rest_and_bound_to_its_row():
    store = durable.durable_dict("tests.security.secret_store")
    store["u-secret"] = {"note": "PLAINTEXT-MARKER"}
    asyncio.run(durable.flush())
    raw = dict((k, v) for n, k, v in asyncio.run(durable._store().load_all()) if n == "tests.security.secret_store")
    blob = raw["u-secret"]
    assert crypto.is_sealed(blob) and b"PLAINTEXT-MARKER" not in blob
    # A blob moved to another row does not decrypt: the row is authenticated with the data.
    with pytest.raises(Exception):
        crypto.open_sealed(blob, durable._aad("tests.security.secret_store", "someone-else"))


def test_key_rotation_reencrypts_stored_rows(monkeypatch):
    store = durable.durable_dict("tests.security.rotate_store")
    store["k"] = {"v": 1}
    asyncio.run(durable.flush())
    import base64
    dev_id, dev_key = crypto.keyring()[0]
    dev = f"{dev_id}:{base64.b64encode(dev_key).decode()}"
    k2 = f"k2:{crypto.new_key()}"
    monkeypatch.setenv("DATA_ENCRYPTION_KEYS", f"{k2},{dev}")
    crypto.keyring.cache_clear()
    try:
        assert asyncio.run(durable.reseal_all()) >= 1
        rows = asyncio.run(durable._store().load_all())
        assert {crypto.key_id_of(b) for _, _, b in rows} == {"k2"}
    finally:
        # Back to the development key for the rest of the run.
        monkeypatch.setenv("DATA_ENCRYPTION_KEYS", f"{dev},{k2}")
        crypto.keyring.cache_clear()
        asyncio.run(durable.reseal_all())
        monkeypatch.delenv("DATA_ENCRYPTION_KEYS")
        crypto.keyring.cache_clear()


def test_vault_passphrase_and_time_limited_share():
    owner = register_user("vault-owner@example.com", "vaultowner")
    friend = register_user("vault-friend@example.com", "vaultfriend")
    stranger = register_user("vault-stranger@example.com", "vaultstranger")
    ho, hf, hs = (_bearer(r["tokens"]["access_token"]) for r in (owner, friend, stranger))

    rec = c.post("/api/v1/encryption/encrypt", headers=ho,
                 json={"data": {"hba1c": 6.1}, "label": "lab", "passphrase": "correct horse"}).json()
    assert rec["protected"]
    stored = dict.get(__import__("app.core.encryption", fromlist=["_records"])._records, rec["id"])
    assert "6.1" not in stored["payload"]
    assert c.post("/api/v1/encryption/decrypt", headers=ho, json={"encrypted_id": rec["id"]}).status_code == 403
    assert c.post("/api/v1/encryption/decrypt", headers=ho,
                  json={"encrypted_id": rec["id"], "passphrase": "wrong one!"}).status_code == 403
    ok = c.post("/api/v1/encryption/decrypt", headers=ho, json={"encrypted_id": rec["id"], "passphrase": "correct horse"})
    assert ok.json()["data"] == {"hba1c": 6.1}

    share = c.post("/api/v1/encryption/share", headers=ho, json={
        "encrypted_id": rec["id"], "recipient_id": friend["user"]["id"], "max_accesses": 1}).json()
    body = {"encrypted_id": rec["id"], "passphrase": "correct horse", "share_id": share["id"]}
    assert c.post("/api/v1/encryption/decrypt", headers=hs, json=body).status_code == 404
    assert c.post("/api/v1/encryption/decrypt", headers=hf, json=body).json()["data"] == {"hba1c": 6.1}
    assert c.post("/api/v1/encryption/decrypt", headers=hf, json=body).status_code == 404  # reads used up
    events = c.get("/api/v1/auth/activity", headers=ho).json()["entries"]
    assert any(e["event"] == "vault_share_read" and e["actor_id"] == friend["user"]["id"] for e in events)


def test_profile_creation_needs_an_account_and_uses_its_id():
    assert c.post("/api/v1/users", json={"email": "anon@example.com"}).status_code == 401
    reg = register_user("profile@example.com", "profileuser")
    r = c.post("/api/v1/users", headers=_bearer(reg["tokens"]["access_token"]), json={"email": "other@example.com"})
    assert r.status_code == 201 and r.json()["id"] == reg["user"]["id"] and r.json()["email"] == "profile@example.com"


def test_profile_name_defaults_to_the_display_name_given_at_sign_up():
    reg = register_user("named@example.com", "nameduser", display_name="Asha Rao")
    r = c.post("/api/v1/users", headers=_bearer(reg["tokens"]["access_token"]), json={})
    assert r.status_code == 201 and r.json()["name"] == "Asha Rao"


def test_compliance_reports_measured_controls_not_blanket_claims():
    reg = register_user("compliance@example.com", "complianceuser")
    r = c.get("/api/v1/security/compliance/dpdp", headers=_bearer(reg["tokens"]["access_token"])).json()
    statuses = {x["control"]: x["status"] for x in r["results"]}
    assert statuses["breach_notification"] == "not_verified"
    assert statuses["audit_logging"] == "implemented"
    assert r["implemented"] < r["total"]


def test_metrics_need_the_scraper_token(monkeypatch):
    monkeypatch.setattr(settings, "METRICS_TOKEN", "scrape-secret")
    assert c.get("/metrics").status_code == 401
    assert c.get("/metrics", headers=_bearer("scrape-secret")).status_code == 200


def test_rate_limit_answers_429_with_retry_after(monkeypatch):
    from app.core import rate_limiter

    monkeypatch.setattr(rate_limiter, "RULES", ((("/api/v1/auth/login",), 2, 0.01, "auth"),))
    tiny = FastAPI()

    @tiny.post("/api/v1/auth/login")
    async def login():
        return {}

    tiny.add_middleware(rate_limiter.RateLimitMiddleware)
    t = TestClient(tiny)
    assert [t.post("/api/v1/auth/login").status_code for _ in range(3)] == [200, 200, 429]
    assert int(t.post("/api/v1/auth/login").headers["Retry-After"]) >= 1

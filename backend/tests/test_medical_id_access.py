"""Access control on the medical ID routes.

The emergency view carries blood type, allergies, current medications and
emergency contacts. It is reached by putting a user id in the URL path, so
without an owner check any account can read any other account's record by
changing one path segment. These tests pin the check in place.
"""
import pytest
from fastapi.testclient import TestClient

from app.core.auth import create_access_token, user_manager
from app.core.config import settings
from app.main import app

c = TestClient(app)


@pytest.fixture(autouse=True)
def _auth_enforced(monkeypatch):
    """Turn the local development bypass off so the owner check is exercised."""
    monkeypatch.setattr(settings, "AUTH_DISABLED", False)


@pytest.fixture(scope="module")
def owner():
    return user_manager.register("mid-owner@example.com", "mid-owner", "Str0ngPassw0rd!")["user"]["id"]


@pytest.fixture(scope="module")
def stranger():
    return user_manager.register("mid-stranger@example.com", "mid-stranger", "Str0ngPassw0rd!")["user"]["id"]


def _headers(user_id):
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


MEDICAL_ROUTES = [
    ("get", "/api/v1/medical-id/emergency/{uid}"),
    ("get", "/api/v1/medical-id/wallet/{uid}"),
    ("get", "/api/v1/medical-id/provider-summary/{uid}"),
]


@pytest.mark.parametrize("method,template", MEDICAL_ROUTES, ids=[r[1] for r in MEDICAL_ROUTES])
def test_anonymous_is_unauthorized(method, template, owner):
    r = getattr(c, method)(template.format(uid=owner))
    assert r.status_code == 401, f"{template} returned {r.status_code} without a token"


@pytest.mark.parametrize("method,template", MEDICAL_ROUTES, ids=[r[1] for r in MEDICAL_ROUTES])
def test_another_user_is_forbidden(method, template, owner, stranger):
    r = getattr(c, method)(template.format(uid=owner), headers=_headers(stranger))
    assert r.status_code == 403, f"{template} let another user in ({r.status_code})"


@pytest.mark.parametrize("method,template", MEDICAL_ROUTES, ids=[r[1] for r in MEDICAL_ROUTES])
def test_owner_is_allowed(method, template, owner):
    r = getattr(c, method)(template.format(uid=owner), headers=_headers(owner))
    assert r.status_code == 200, f"{template} refused the owner ({r.status_code})"


def test_owner_cannot_write_to_another_users_record(owner, stranger):
    r = c.post(
        "/api/v1/medical-id/contact",
        json={"user_id": owner, "contact": {"name": "x", "phone": "1"}},
        headers=_headers(stranger),
    )
    assert r.status_code == 403

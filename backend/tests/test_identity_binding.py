"""
Identity binding across the whole API.

Handlers take `user_id` from the path, the query string or the body, and there
are several hundred of them. IdentityMiddleware rebinds that parameter to the
caller's token before routing, so a request naming someone else reads and
writes the caller's own record instead. These tests pin that down for every
route template the app registers, not just a sampled few.
"""
import json

import pytest
from fastapi.testclient import TestClient

from app.core.auth import create_access_token
from tests.conftest import register_user
from app.core.config import settings
from app.main import app
from app.middleware.identity import CROSS_USER_PREFIXES, _rebind_body, _template_to_regex

c = TestClient(app)


@pytest.fixture(autouse=True)
def _auth_enforced(monkeypatch):
    """The dev bypass deliberately allows addressing any user; turn it off."""
    monkeypatch.setattr(settings, "AUTH_DISABLED", False)


@pytest.fixture(scope="module")
def caller():
    return register_user("bind-caller@example.com", "bind-caller")["user"]["id"]


@pytest.fixture(scope="module")
def victim():
    return register_user("bind-victim@example.com", "bind-victim")["user"]["id"]


def _headers(user_id, role="user"):
    return {"Authorization": f"Bearer {create_access_token(user_id, role=role)}"}


def _user_id_templates():
    paths = app.openapi().get("paths", {})
    return sorted(p for p in paths if "{user_id}" in p and not p.startswith(CROSS_USER_PREFIXES))


def test_the_app_actually_registers_routes_that_name_a_user():
    """A guard on the guard: an empty route list would make the sweep vacuous."""
    assert len(_user_id_templates()) > 50


def test_every_user_id_path_is_rebound_to_the_caller(caller, victim):
    """No registered route may reach a handler holding someone else's id."""
    leaked = []
    for template in _user_id_templates():
        path = template.replace("{user_id}", victim)
        # Remaining placeholders are unrelated ids; any value routes the same.
        path = _fill_other_params(path)
        r = c.get(path, headers=_headers(caller))
        if r.status_code in (401, 403):
            continue  # never reached the handler at all
        if victim in r.text:
            leaked.append(template)
    assert leaked == [], f"routes echoed another user's id: {leaked}"


def _fill_other_params(path: str) -> str:
    out = []
    depth = 0
    for ch in path:
        if ch == "{":
            depth += 1
            continue
        if ch == "}":
            depth -= 1
            out.append("1")
            continue
        if depth == 0:
            out.append(ch)
    return "".join(out)


def test_query_user_id_is_rebound(caller, victim):
    r = c.get(f"/api/v1/decision/today?user_id={victim}", headers=_headers(caller))
    assert r.status_code == 200
    assert r.json()["user_id"] == caller


def test_an_omitted_user_id_is_filled_in_rather_than_defaulted(caller):
    """Handlers default user_id to a shared \"default\" bucket; the caller's id wins."""
    r = c.get("/api/v1/decision/today", headers=_headers(caller))
    assert r.status_code == 200
    assert r.json()["user_id"] == caller


def test_admin_may_still_address_another_user(caller, victim):
    """Support access is the one exemption, and it is role-gated."""
    r = c.get(f"/api/v1/decision/today?user_id={victim}", headers=_headers(caller, role="admin"))
    assert r.status_code == 200
    assert r.json()["user_id"] == victim


def test_cross_user_prefixes_still_enforce_their_own_check(caller, victim):
    """Routes exempt from rebinding must refuse a stranger themselves."""
    r = c.get(f"/api/v1/admin/users/{victim}", headers=_headers(caller))
    assert r.status_code == 403


def test_body_user_id_is_rebound():
    assert _rebind_body(b'{"user_id": "victim", "n": 1}', "caller") == b'{"user_id": "caller", "n": 1}'
    assert json.loads(_rebind_body(b'{"user_id":"caller"}', "caller"))["user_id"] == "caller"


def test_body_rebinding_leaves_non_objects_and_bad_json_alone():
    assert _rebind_body(b'["user_id"]', "caller") == b'["user_id"]'
    assert _rebind_body(b'{"user_id": ', "caller") == b'{"user_id": '
    assert _rebind_body(b"", "caller") == b""


def test_template_matcher_captures_only_the_user_segment():
    matcher = _template_to_regex("/api/v1/x/{user_id}/items/{item_id}")
    found = matcher.match("/api/v1/x/abc/items/99")
    assert found and found.group("user_id") == "abc"
    assert matcher.match("/api/v1/x/abc/items/99/extra") is None

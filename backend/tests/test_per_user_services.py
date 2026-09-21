"""
Feature services keep one state per account.

Most of these services were module-level singletons holding plain dicts, so a
medication list, a hydration total or a sleep log was shared by every account
on the server. `per_user` gives each caller their own instance; these tests
pin that to the request path, not just the proxy.
"""
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.per_user import CURRENT_USER, PerUserProxy, SHARED, current_user_id, per_user
from app.main import app
from tests.conftest import register_user

c = TestClient(app)


class Counter:
    def __init__(self):
        self.items = []

    def add(self, value):
        self.items.append(value)
        return len(self.items)


def test_each_user_gets_their_own_instance():
    proxy = per_user(Counter)
    token = CURRENT_USER.set("alice")
    try:
        proxy.add("a")
        proxy.add("a")
        assert proxy.items == ["a", "a"]
    finally:
        CURRENT_USER.reset(token)

    token = CURRENT_USER.set("bob")
    try:
        assert proxy.items == []
        proxy.add("b")
        assert proxy.items == ["b"]
    finally:
        CURRENT_USER.reset(token)


def test_no_identity_falls_back_to_one_shared_instance():
    assert current_user_id() == SHARED
    proxy = per_user(Counter)
    proxy.add("x")
    assert proxy.instance_for(SHARED).items == ["x"]


def test_attribute_writes_reach_the_callers_own_instance():
    proxy = per_user(Counter)
    token = CURRENT_USER.set("carol")
    try:
        proxy.items = ["set"]
    finally:
        CURRENT_USER.reset(token)
    assert proxy.instance_for("carol").items == ["set"]
    assert proxy.instance_for("dave").items == []


def test_idle_users_are_evicted_rather_than_accumulating():
    proxy = per_user(Counter, max_instances=2)
    for name in ("one", "two", "three"):
        proxy.instance_for(name)
    assert proxy.tracked_users() == 2


def test_reset_clears_one_user_or_everyone():
    proxy = per_user(Counter)
    proxy.instance_for("x").add("1")
    proxy.instance_for("y").add("1")
    proxy.reset("x")
    assert proxy.instance_for("x").items == []
    assert proxy.instance_for("y").items == ["1"]
    proxy.reset()
    assert proxy.tracked_users() == 0


def test_the_proxy_is_recognisable_in_a_traceback():
    assert "Counter" in repr(per_user(Counter))


class TestThroughTheApi:
    @pytest.fixture(autouse=True)
    def _auth_enforced(self, monkeypatch):
        monkeypatch.setattr(settings, "AUTH_DISABLED", False)

    @staticmethod
    def _headers(email, username):
        result = register_user(email, username)
        assert "error" not in result, result
        return {"Authorization": f"Bearer {result['tokens']['access_token']}"}

    def test_one_users_medications_do_not_appear_for_another(self):
        alice = self._headers("meds-alice@example.com", "meds-alice")
        bob = self._headers("meds-bob@example.com", "meds-bob")

        added = c.post(
            "/api/v1/medication/add",
            headers=alice,
            json={"name": "Vitamin D3", "dosage": "2000 IU", "frequency": "daily", "times": ["08:00"]},
        )
        assert added.status_code == 200, added.text

        alice_list = c.get("/api/v1/medication/list", headers=alice).json()["medications"]
        bob_list = c.get("/api/v1/medication/list", headers=bob).json()["medications"]

        assert any("Vitamin D3" in str(m) for m in alice_list)
        assert bob_list == [], f"another account saw Alice's medication: {bob_list}"

    def test_hydration_totals_are_not_shared(self):
        alice = self._headers("water-alice@example.com", "water-alice")
        bob = self._headers("water-bob@example.com", "water-bob")

        logged = c.post("/api/v1/hydration/log", headers=alice, json={"amount_ml": 500})
        assert logged.status_code == 201, logged.text

        alice_today = c.get("/api/v1/hydration/today", headers=alice).json()
        bob_today = c.get("/api/v1/hydration/today", headers=bob).json()
        assert alice_today["total_ml"] == 500
        assert bob_today["total_ml"] == 0, f"another account saw Alice's intake: {bob_today}"

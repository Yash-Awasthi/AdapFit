"""Feature data survives a restart; a tampered row cannot run code."""
import asyncio
import pickle

import pytest
from fastapi.testclient import TestClient

from app.core import durable
from app.core.config import settings
from app.main import app
from tests.conftest import register_user

c = TestClient(app)


@pytest.fixture(autouse=True)
def _auth(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_DISABLED", False)


def _simulate_restart():
    """Drop every in-memory copy, as a new process would start, then reload from the store."""
    for kind, holder in durable._holders.values():
        if kind == "per_user":
            holder.reset()
        elif kind == "shared":
            inst = object.__getattribute__(holder, "_instance")
            object.__setattr__(holder, "_instance", type(inst)())
        else:
            dict.clear(holder)
    durable._saved_hash.clear()
    asyncio.run(durable.load_all())


def test_meals_sleep_and_medical_id_survive_a_restart():
    reg = register_user("durable@example.com", "durable-user")
    uid, h = reg["user"]["id"], {"Authorization": f"Bearer {reg['tokens']['access_token']}"}
    assert c.post("/api/v1/nutrition/meals", headers=h, json={
        "name": "Poha", "calories": 300, "protein_g": 6, "carbs_g": 55, "fat_g": 7, "meal_type": "breakfast"}).status_code == 201
    assert c.post("/api/v1/sleep/logs", headers=h, json={"bedtime": "23:00", "wake_time": "06:30"}).status_code == 201
    assert c.post("/api/v1/medical-id/create", headers=h, json={
        "user_id": uid, "data": {"blood_type": "B+", "allergies": ["penicillin"]}}).status_code == 200

    _simulate_restart()

    assert [m["name"] for m in c.get("/api/v1/nutrition/meals", headers=h).json()] == ["Poha"]
    assert len(c.get("/api/v1/sleep/logs", headers=h).json()) == 1
    assert "penicillin" in str(c.get(f"/api/v1/medical-id/emergency/{uid}", headers=h).json())


def test_a_row_that_would_run_code_is_refused():
    class Evil:
        def __reduce__(self):
            import os
            return (os.system, ("echo pwned",))

    with pytest.raises(pickle.UnpicklingError):
        durable._loads(pickle.dumps(Evil()))


def test_unchanged_state_is_not_rewritten():
    reg = register_user("durable2@example.com", "durable-user2")
    h = {"Authorization": f"Bearer {reg['tokens']['access_token']}"}
    c.post("/api/v1/sleep/logs", headers=h, json={"bedtime": "22:00", "wake_time": "06:00"})
    c.get("/api/v1/sleep/logs", headers=h)
    assert asyncio.run(durable.flush()) == 0


def test_deleting_an_account_erases_its_feature_rows():
    from app.core.auth import user_manager

    reg = register_user("durable3@example.com", "durable-user3")
    uid, h = reg["user"]["id"], {"Authorization": f"Bearer {reg['tokens']['access_token']}"}
    c.post("/api/v1/nutrition/meals", headers=h, json={"name": "Idli", "calories": 200, "meal_type": "breakfast"})
    assert asyncio.run(user_manager.delete_user(uid))["deleted"]
    rows = asyncio.run(durable._store().load_all())
    assert not [r for r in rows if r[1] == uid]

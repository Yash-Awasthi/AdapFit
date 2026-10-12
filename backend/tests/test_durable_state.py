"""Feature data survives a restart; a tampered row cannot run code."""
import asyncio
import json
from collections import OrderedDict, defaultdict, deque
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

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
    """Drop every in-memory copy, as a new process would start; rows load again on first use."""
    for kind, holder in durable._holders.values():
        if kind == "per_user":
            holder.reset()
        else:
            dict.clear(holder)
    durable._rows.clear()
    durable._full.clear()


def test_meals_sleep_and_medical_id_survive_a_restart():
    reg = register_user("durable@example.com", "durable-user")
    uid, h = reg["user"]["id"], {"Authorization": f"Bearer {reg['tokens']['access_token']}"}
    assert c.post("/api/v1/nutrition/meals", headers=h, json={
        "name": "Poha", "calories": 300, "protein_g": 6, "carbs_g": 55, "fat_g": 7, "meal_type": "breakfast"}).status_code == 201
    assert c.post("/api/v1/sleep/logs", headers=h, json={"bedtime": "23:00", "wake_time": "06:30"}).status_code == 201
    assert c.post("/api/v1/emergency/medical-info", headers=h, json={
        "blood_type": "B+", "allergies": ["penicillin"]}).status_code == 200

    _simulate_restart()

    assert [m["name"] for m in c.get("/api/v1/nutrition/meals", headers=h).json()] == ["Poha"]
    assert len(c.get("/api/v1/sleep/logs", headers=h).json()) == 1
    assert "penicillin" in str(c.get("/api/v1/emergency/medical-info", headers=h).json())


@pytest.mark.parametrize("path", ["os:system", "builtins:eval", "app.core.durable:json", "app.core.durable:_class_at"])
def test_a_row_naming_a_class_outside_the_app_is_refused(path):
    with pytest.raises(ValueError):
        durable._loads(json.dumps({"$t": "obj", "c": path, "v": {}}).encode())


def test_stored_values_come_back_with_their_types():
    from app.services.notification_scheduler import NotificationPreference, NotificationType, ScheduledNotification

    note = ScheduledNotification(id="n1", user_id="u1", type=NotificationType.HYDRATION, title="t", body="b",
                                 scheduled_at="09:00", created_at="2026-10-12")
    value = {
        "when": datetime(2026, 10, 12, 7, 30, tzinfo=timezone.utc), "day": date(2026, 10, 12), "gap": timedelta(hours=3),
        1: {"$t": "not a tag"}, ("a", 2): frozenset({3}), "seen": {"x"}, "order": OrderedDict(b=1, a=2),
        "counts": defaultdict(list, {"k": [1]}), "recent": deque([1, 2], maxlen=5), "dose": Decimal("2.50"),
        "id": UUID(int=7), "raw": b"\x00\xff", "kind": NotificationType.HYDRATION, "notes": [note],
        "prefs": NotificationPreference(hydration=True),
    }
    back = durable._loads(durable._dumps(value))
    assert back == value and type(back["counts"]) is defaultdict and back["recent"].maxlen == 5
    assert back["notes"][0].model_fields_set == note.model_fields_set
    assert back["prefs"].model_dump(exclude_unset=True) == {"hydration": True}


def test_a_pickled_row_is_refused_instead_of_being_overwritten():
    from app.core import crypto

    store = durable.durable_dict("tests.durable.old")
    sealed = crypto.seal(b"\x80\x05N.", durable._aad("tests.durable.old", "k"))
    asyncio.run(durable._store().put([("tests.durable.old", "k", sealed)]))
    try:
        with pytest.raises(RuntimeError, match="migrate_feature_state_json"):
            store.get("k")
    finally:
        asyncio.run(durable._store().put([("tests.durable.old", "k", b"")]))


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
    assert [r for r in rows if r[1] == uid] and not [r for r in rows if r[1] == uid and r[2]]


def test_the_migration_script_turns_pickled_rows_into_json():
    import pickle
    from scripts import migrate_feature_state_json as migration
    from app.core import crypto
    from app.services.notification_scheduler import NotificationPreference

    old = {"prefs": NotificationPreference(hydration=True), "when": date(2026, 10, 1), "tags": {"a"}}
    ns = "tests.durable.migrated"
    asyncio.run(durable._store().put([(ns, "k", crypto.seal(pickle.dumps(old, 5), durable._aad(ns, "k")))]))
    try:
        assert asyncio.run(migration.main()) == 0
        sealed = {k: v for n, k, v, _ in asyncio.run(durable._store().load_all()) if n == ns}["k"]
        assert durable._loads(crypto.open_sealed(sealed, durable._aad(ns, "k"))) == old
        assert asyncio.run(migration.main()) == 0
    finally:
        asyncio.run(durable._store().put([(ns, "k", b"")]))


def _write_as_other_worker(ns: str, key: str, value, expected):
    from app.core import crypto
    payload = crypto.seal(durable._dumps(value), durable._aad(ns, key))
    seq, _ = asyncio.run(durable._store().write(ns, key, payload, expected))
    assert seq is not None


def test_a_change_from_another_worker_is_applied_before_the_next_request():
    ns = "tests.durable.follow"
    store = durable.durable_dict(ns)
    store["u"] = {"goal": 1}
    asyncio.run(durable.flush())
    _write_as_other_worker(ns, "u", {"goal": 2}, durable._rows[(ns, "u")].seq)
    asyncio.run(durable.sync())
    assert store.peek("u") == {"goal": 2}


def test_a_row_another_worker_changed_is_merged_not_overwritten():
    ns = "tests.durable.merge"
    store = durable.durable_dict(ns)
    store["u"] = {"meals": ["poha"], "goal": 1}
    asyncio.run(durable.flush())
    _write_as_other_worker(ns, "u", {"meals": ["poha", "dal"], "goal": 2}, durable._rows[(ns, "u")].seq)

    store["u"]["meals"].append("idli")  # this worker has not seen the other write yet
    asyncio.run(durable.flush())

    expected = {"meals": ["poha", "dal", "idli"], "goal": 2}
    assert store.peek("u") == expected
    payload, _ = durable._store().fetch_sync(ns, "u")
    assert durable._decode(durable._open(ns, "u", payload)) == expected


def test_the_migration_script_splits_a_shared_service_row_per_user():
    from scripts import migrate_feature_state_json as migration
    from app.core import crypto
    from app.services.health_notepad import health_notepad

    old_ns = "app.services.health_notepad.health_notepad"
    old = {"notes": {"user-a": [{"id": "n1", "title": "Knee"}], "user-b": [{"id": "n2", "title": "Sleep"}]}}
    asyncio.run(durable._store().put([(old_ns, "_", crypto.seal(durable._dumps(old), durable._aad(old_ns, "_")))]))
    assert asyncio.run(migration.main()) == 0
    _simulate_restart()
    assert health_notepad.notes.peek("user-a") == [{"id": "n1", "title": "Knee"}]
    assert health_notepad.notes.peek("user-b")[0]["title"] == "Sleep"
    assert not durable._store().fetch_sync(old_ns, "_")[0]

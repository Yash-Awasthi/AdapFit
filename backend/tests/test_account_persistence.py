"""
Accounts and sessions outlive the process.

Registrations used to exist only in the API process, so every restart deleted
every account and signed everyone out. These tests stand in for a restart by
building a second UserManager against the same store.
"""
import asyncio

import pytest

from app.core.auth import UserManager, decode_token


@pytest.fixture
def manager():
    return UserManager()


def _run(coro):
    return asyncio.run(coro)


def test_a_fresh_manager_sees_an_account_registered_by_another(manager):
    created = _run(manager.register("persist-a@example.com", "persist-a", "Str0ngPassw0rd!"))
    user_id = created["user"]["id"]

    restarted = UserManager()
    assert _run(restarted.get_user(user_id))["email"] == "persist-a@example.com"


def test_login_works_after_a_restart(manager):
    _run(manager.register("persist-b@example.com", "persist-b", "Str0ngPassw0rd!"))

    restarted = UserManager()
    result = _run(restarted.login("persist-b@example.com", "Str0ngPassw0rd!"))
    assert "error" not in result
    assert decode_token(result["tokens"]["access_token"])["sub"] == result["user"]["id"]


def test_a_refresh_token_still_works_after_a_restart(manager):
    created = _run(manager.register("persist-c@example.com", "persist-c", "Str0ngPassw0rd!"))

    restarted = UserManager()
    refreshed = _run(restarted.refresh(created["tokens"]["refresh_token"]))
    assert "error" not in refreshed, refreshed
    assert refreshed["tokens"]["access_token"]


def test_a_refresh_token_is_single_use(manager):
    created = _run(manager.register("persist-d@example.com", "persist-d", "Str0ngPassw0rd!"))
    token = created["tokens"]["refresh_token"]

    assert "error" not in _run(manager.refresh(token))
    assert _run(manager.refresh(token))["error"] == "Refresh token revoked"


def test_logout_survives_a_restart(manager):
    created = _run(manager.register("persist-e@example.com", "persist-e", "Str0ngPassw0rd!"))
    token = created["tokens"]["refresh_token"]
    _run(manager.logout(token))

    restarted = UserManager()
    assert _run(restarted.refresh(token))["error"] == "Refresh token revoked"


def test_account_ids_are_uuids_so_they_match_the_profile_row(manager):
    import uuid

    created = _run(manager.register("persist-f@example.com", "persist-f", "Str0ngPassw0rd!"))
    uuid.UUID(created["user"]["id"])  # raises if it is not one


def test_deleting_an_account_removes_it_from_the_store(manager):
    created = _run(manager.register("persist-g@example.com", "persist-g", "Str0ngPassw0rd!"))
    user_id = created["user"]["id"]
    _run(manager.delete_user(user_id))

    restarted = UserManager()
    assert _run(restarted.get_user(user_id)) is None


def test_the_stored_record_never_holds_a_plaintext_password(manager):
    from app.core import accounts

    _run(manager.register("persist-h@example.com", "persist-h", "Str0ngPassw0rd!"))
    raw = accounts.ACCOUNTS_FILE.read_text(encoding="utf-8")
    assert "Str0ngPassw0rd!" not in raw

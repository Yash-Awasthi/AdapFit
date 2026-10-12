"""Two server processes on one store agree on accounts, sessions and feature data.

They share a SQLite file, or the Postgres database in ADAPFIT_TEST_DATABASE_URL when it is set
(migrations applied).
"""
import os
import secrets
import socket
import string
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

import httpx
import pytest

BACKEND = Path(__file__).resolve().parent.parent
# Made per run from the three character classes sign-up requires; no credential sits in the source.
PASSWORD = "".join(secrets.choice(c) for c in (string.ascii_uppercase, string.ascii_lowercase, string.digits)) + secrets.token_urlsafe(16)
EMAIL = f"two{uuid.uuid4().hex[:8]}@example.com"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def servers():
    data = tempfile.mkdtemp(prefix="adapfit-two-workers-")
    env = {**os.environ, "ADAPFIT_DATA_DIR": data, "AUTH_DISABLED": "false",
           "DATABASE_URL": os.getenv("ADAPFIT_TEST_DATABASE_URL", ""),
           "RATE_LIMITING_ENABLED": "true", "JWT_SECRET_KEY": "two-workers-" + "k" * 64}
    procs, urls = [], []
    for n in range(2):
        port = _free_port()
        log = open(Path(data) / f"server{n}.log", "wb")
        procs.append(subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=BACKEND, env=env, stdout=log, stderr=subprocess.STDOUT))
        urls.append(f"http://127.0.0.1:{port}")
    try:
        deadline = time.time() + 300
        for url in urls:
            while True:
                try:
                    if httpx.get(f"{url}/health", timeout=2).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                if time.time() > deadline:
                    raise RuntimeError(f"server did not start; see {data}")
                time.sleep(0.5)
        yield [httpx.Client(base_url=f"{u}/api/v1", timeout=30) for u in urls]
    finally:
        for p in procs:
            p.terminate()
            p.wait(timeout=30)


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_an_account_made_on_one_worker_signs_in_on_the_other(servers):
    a, b = servers
    consent = {"health_data": True, "ai": True, "sharing": True, "analytics": False}
    reg = a.post("/auth/register", json={"email": EMAIL, "username": EMAIL.split("@")[0],
                                         "password": PASSWORD, "birth_date": "1990-01-01", "consent": consent})
    assert reg.status_code in (200, 201), reg.text
    login = b.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert login.status_code == 200, login.text


def test_feature_data_written_on_one_worker_is_read_on_the_other(servers):
    a, b = servers
    login = b.post("/auth/login", json={"email": EMAIL, "password": PASSWORD}).json()
    h, uid = _auth(login["tokens"]["access_token"]), login["user"]["id"]

    assert a.post("/nutrition/meals", headers=h, json={"name": "Poha", "calories": 300,
                                                       "meal_type": "breakfast"}).status_code == 201
    assert [m["name"] for m in b.get("/nutrition/meals", headers=h).json()] == ["Poha"]
    assert b.post("/nutrition/meals", headers=h, json={"name": "Dal", "calories": 400,
                                                       "meal_type": "lunch"}).status_code == 201
    assert sorted(m["name"] for m in a.get("/nutrition/meals", headers=h).json()) == ["Dal", "Poha"]

    # A shared service keeps each user's records as that user's own row.
    assert b.post("/notepad/add", headers=h, json={"user_id": uid, "title": "Knee", "content": "Sore"}).status_code == 200
    notes = a.get(f"/notepad/notes/{uid}", headers=h).json()
    assert "Knee" in str(notes)


def test_a_refresh_token_works_once_across_workers(servers):
    a, b = servers
    first = a.post("/auth/login", json={"email": EMAIL, "password": PASSWORD}).json()["tokens"]
    rotated = b.post("/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert rotated.status_code == 200, rotated.text
    newer = rotated.json()["tokens"]
    assert a.get("/auth/me", headers=_auth(newer["access_token"])).status_code == 200

    # The used token again, on the other worker: theft, so every session of the account ends.
    assert a.post("/auth/refresh", json={"refresh_token": first["refresh_token"]}).status_code == 401
    assert b.post("/auth/refresh", json={"refresh_token": newer["refresh_token"]}).status_code == 401
    assert b.get("/auth/me", headers=_auth(newer["access_token"])).status_code == 401


def test_the_sign_in_limit_holds_across_workers(servers):
    """30 sign-in attempts per address in total, not 30 on each worker."""
    a, b = servers
    statuses = []
    for n in range(40):
        worker = (a, b)[n % 2]
        statuses.append(worker.post("/auth/login", json={"email": "nobody@example.com", "password": "x"}).status_code)
        if statuses[-1] == 429:
            break
    # Earlier tests in this module already spent a few attempts from this address.
    assert statuses[-1] == 429 and len(statuses) <= 30, statuses

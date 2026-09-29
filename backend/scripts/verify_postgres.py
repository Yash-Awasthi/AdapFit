"""
End-to-end check against the real Postgres database.

Registers an account, logs a week of check-ins through the API, and then
re-reads everything through a second process-level instance to prove the data
is in the database rather than in the first process's memory.

Run from the backend directory with the project's .env loaded.
"""
import asyncio
import os
import pathlib
import sys
import uuid

BACKEND = pathlib.Path(__file__).resolve()
for line in (pathlib.Path(".env")).read_text(encoding="utf-8").splitlines():
    if line.strip() and not line.startswith("#") and "=" in line:
        key, _, value = line.partition("=")
        os.environ[key.strip()] = value.strip()

os.environ["AUTH_DISABLED"] = "false"
os.environ["RATE_LIMITING_ENABLED"] = "false"
sys.path.insert(0, ".")

from fastapi.testclient import TestClient  # noqa: E402

from app.core.auth import user_manager  # noqa: E402
from app.core.storage import storage  # noqa: E402
from app.main import app  # noqa: E402


def main() -> int:
    suffix = uuid.uuid4().hex[:8]
    email = f"pgcheck-{suffix}@example.com"

    with TestClient(app) as client:
        print("backend storage:", "postgres" if os.environ.get("DATABASE_URL") else "in-memory")

        registered = client.post("/api/v1/auth/register", json={
            "email": email, "username": f"pgcheck{suffix}",
            "password": "Str0ngPassw0rd!", "display_name": "PG Check", "birth_date": "1990-01-01",
            "consent": {"health_data": True, "ai": True, "sharing": False, "analytics": False},
        })
        assert registered.status_code == 200, registered.text
        body = registered.json()
        user_id, token = body["user"]["id"], body["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("registered:", user_id)

        for day in range(1, 8):
            response = client.post("/api/v1/recovery-logs", headers=headers, json={
                "user_id": "someone-else",  # rebound to the caller by the middleware
                "log_date": f"2026-05-{day:02d}",
                "wearable_data": {
                    "hrv_rmssd": 88, "sleep_duration_hours": 8.1,
                    "sleep_efficiency_pct": 92, "resting_heart_rate": 49,
                },
                "subjective_checkin": {"soreness": 2, "fatigue": 2, "stress": 2},
            })
            assert response.status_code == 201, response.text
        print("logged 7 check-ins, last recovery score:", response.json()["recovery_score"])

        bp = client.post("/api/v1/blood-pressure/log", headers=headers,
                         json={"systolic": 118, "diastolic": 76, "pulse": 61})
        assert bp.status_code == 201, bp.text
        print("logged a blood pressure reading (feature_state)")

        # Every value the API accepts must also pass the table's CHECK constraints.
        profile = client.post("/api/v1/users", headers=headers, json={"email": email, "name": "PG Check"})
        assert profile.status_code == 201, profile.text
        for goal in ("strength", "hypertrophy", "endurance", "fat_loss", "general_fitness"):
            for level in ("beginner", "intermediate", "advanced"):
                r = client.patch(f"/api/v1/users/{user_id}", headers=headers,
                                 json={"primary_goal": goal, "fitness_level": level, "preferred_days_per_week": 3})
                assert r.status_code == 200, (goal, level, r.text)
        print("every goal and level the API accepts saves on Postgres")

        generated = client.post("/api/v1/workouts", headers=headers,
                                json={"user_id": "", "target_date": "2026-05-07", "target_duration_minutes": 30})
        assert generated.status_code == 201, generated.text
        workout_id = generated.json()["workout_id"]
        listed = client.get("/api/v1/workouts?days=14", headers=headers).json()
        listed = listed.get("items", listed) if isinstance(listed, dict) else listed
        same = [w for w in listed if w["workout_id"] == workout_id]
        assert same and all(ex["name"] for ex in same[0]["exercises"]), "workout shape differs on Postgres"
        print("generated workout listed under the same id with exercise names")

        decision = client.get("/api/v1/decision/today?day=2026-05-07", headers=headers)
        assert decision.status_code == 200, decision.text
        assert decision.json()["user_id"] == user_id, "identity was not bound"
        print("decision:", decision.json()["decision"], "-", decision.json()["headline"])

        baseline = client.get(f"/api/v1/users/{user_id}/baselines", headers=headers).json()
        print("baseline HRV:", baseline["hrv_mean_rmssd"], "RHR:", baseline["rhr_baseline"])
        # Seven of the fourteen days needed for full confidence, so the
        # baseline sits halfway between the population default and this user.
        assert 60 < baseline["hrv_mean_rmssd"] < 80, baseline["hrv_mean_rmssd"]
        assert baseline["rhr_baseline"] < 65, baseline["rhr_baseline"]

        login = client.post("/api/v1/auth/login", json={"email": email, "password": "Str0ngPassw0rd!"})
        assert login.status_code == 200, login.text
        print("login after registration: ok")

    # Re-read in a fresh process, which is what a restart actually is. Doing
    # it in this one would reuse a connection pool bound to the loop the
    # TestClient already closed.
    import subprocess

    reread = subprocess.run(
        [sys.executable, str(pathlib.Path(__file__).with_name("reread_postgres.py")), user_id, email],
        capture_output=True, text=True, cwd=".",
    )
    sys.stdout.write(reread.stdout)
    if reread.returncode != 0:
        sys.stderr.write(reread.stderr[-2000:])
        return reread.returncode

    print()
    print("OK: accounts, check-ins, baselines and feature state are in the database.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

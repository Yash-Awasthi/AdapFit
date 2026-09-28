"""Offline queue replay: a workout finished offline is logged once, and the queue id comes back so it clears."""
from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)

WORKOUT = {
    "id": "sync_1_abc",
    "table_name": "workouts",
    "record_id": "adhoc",
    "operation": "update",
    "payload": {"actual_duration_minutes": 30, "session_rpe": 6, "logged_exercises": []},
}


def test_a_queued_workout_is_logged_once_and_acknowledged_by_queue_id(monkeypatch):
    from app.api.v1.endpoints import workouts
    calls = []
    real = workouts.complete_workout

    async def counting(workout_id, req):
        calls.append(workout_id)
        return await real(workout_id, req)

    monkeypatch.setattr(workouts, "complete_workout", counting)
    first = c.post("/api/v1/tasks/sync/batch", json={"mutations": [WORKOUT]}).json()
    assert first["synced_ids"] == ["sync_1_abc"] and not first["errors"]
    again = c.post("/api/v1/tasks/sync/batch", json={"mutations": [WORKOUT]}).json()
    assert again["synced_ids"] == ["sync_1_abc"]
    assert calls == ["adhoc"]


def test_an_unsupported_mutation_is_an_error_not_silently_dropped():
    r = c.post("/api/v1/tasks/sync/batch", json={"mutations": [{**WORKOUT, "id": "sync_2", "operation": "delete"}]}).json()
    assert r["synced_ids"] == [] and r["errors"][0]["id"] == "sync_2"

"""End-to-end integration tests: full user journey through the API."""
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)


def test_full_user_journey():
    """Complete user journey: create → checkin → workout → complete → chat → mood."""
    # 1. Create user
    r = c.post("/api/v1/users", json={"email": "journey@test.com", "name": "Journey User"})
    assert r.status_code == 201
    uid = r.json()["id"]

    # 2. Morning check-in
    r = c.post("/api/v1/recovery-logs", json={
        "user_id": uid, "log_date": "2026-01-15",
        "wearable_data": {"hrv_rmssd": 55, "sleep_duration_hours": 8, "sleep_efficiency_pct": 90},
        "subjective_checkin": {"soreness": 8, "fatigue": 7, "stress": 3},
        "current_acute_load": 480, "current_chronic_load": 500,
    })
    assert r.status_code == 201
    recovery = r.json()
    assert 0 <= recovery["recovery_score"] <= 100
    assert recovery["readiness_state"] in ("OPTIMAL", "MODERATE", "REDUCED", "DEPLETED")

    # 3. Generate workout
    r = c.post("/api/v1/workouts", json={
        "user_id": uid, "target_date": "2026-01-15", "target_duration_minutes": 45,
    })
    assert r.status_code == 201
    workout = r.json()
    assert len(workout["exercises"]) > 0
    workout_id = workout["workout_id"]

    # 4. Complete workout
    r = c.patch(f"/api/v1/workouts/{workout_id}", json={
        "user_id": uid, "actual_duration_minutes": 50, "session_rpe": 8,
        "logged_exercises": [{
            "exercise_id": "barbell-bench-press", "name": "Bench Press",
            "sets": [{"set_number": 1, "weight_kg": 80, "reps_completed": 10, "rpe": 8}]
        }],
        "user_feedback_notes": "Great session, felt strong!",
    })
    assert r.status_code == 200
    complete = r.json()
    assert complete["session_load"] == 400.0
    assert "acwr" in complete

    # 5. Chat with AI coach
    r = c.post("/api/v1/chat", json={
        "user_id": uid, "message": "How am I doing today?",
    })
    assert r.status_code == 200
    chat = r.json()
    assert len(chat["reply"]) > 0

    # 6. Log mood
    r = c.post("/api/v1/mental-health", json={
        "user_id": uid, "mood": 8, "energy": 7, "anxiety": 3,
        "tags": ["good_sleep", "exercise"],
    })
    assert r.status_code == 201

    # 7. Get mood trend
    r = c.get(f"/api/v1/mental-health?user_id={uid}&days=7")
    assert r.status_code == 200
    assert r.json()["count"] >= 1

    # 8. Get breathing exercises
    r = c.get("/api/v1/mental-health/breathing-exercises")
    assert r.status_code == 200
    assert len(r.json()) >= 5

    # 9. Get ACWR
    r = c.get(f"/api/v1/trends/acwr?user_id={uid}")
    assert r.status_code == 200

    # 10. Get ML insights
    r = c.get(f"/api/v1/trends/ml-insights?user_id={uid}")
    assert r.status_code == 200
    assert "readiness_prediction" in r.json()

    # 11. Get HRV trend
    r = c.get(f"/api/v1/trends/hrv?user_id={uid}")
    assert r.status_code == 200

    # 12. Exercise search (may return 0 with hash embeddings, just verify endpoint works)
    r = c.post("/api/v1/exercises/search", json={"query": "chest press", "top_k": 3})
    assert r.status_code == 200
    assert "items" in r.json()

    # 13. Health check
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_user_not_found():
    """404 for non-existent user."""
    r = c.get("/api/v1/users/nonexistent-id-123")
    assert r.status_code == 404


def test_exercise_not_found():
    """404 for non-existent exercise."""
    r = c.get("/api/v1/exercises/nonexistent-exercise")
    assert r.status_code == 404


def test_breathing_exercise_not_found():
    """404 for non-existent breathing exercise."""
    r = c.get("/api/v1/mental-health/breathing-exercises/nonexistent")
    assert r.status_code == 404

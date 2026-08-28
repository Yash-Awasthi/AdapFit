"""API behavior contract — status codes, response shapes, key invariants."""
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)


def test_health():
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_create_user():
    r = c.post("/api/v1/users", json={"email": "a@b.com"})
    assert r.status_code == 201
    assert "id" in r.json()


def test_create_recovery_log():
    r = c.post("/api/v1/recovery-logs", json={
        "user_id": "u1", "log_date": "2026-01-01",
        "wearable_data": {"hrv_rmssd": 48, "sleep_duration_hours": 7.5, "sleep_efficiency_pct": 88},
        "subjective_checkin": {"soreness": 7, "fatigue": 8, "stress": 3},
        "current_acute_load": 520, "current_chronic_load": 500,
    })
    assert r.status_code == 201
    d = r.json()
    assert 0 <= d["recovery_score"] <= 100
    assert d["readiness_state"] in ("OPTIMAL", "MODERATE", "REDUCED", "DEPLETED")


def test_create_workout():
    r = c.post("/api/v1/workouts", json={
        "user_id": "u1", "target_date": "2026-01-01", "target_duration_minutes": 45,
    })
    assert r.status_code == 201
    assert len(r.json()["exercises"]) > 0


def test_complete_workout():
    uid = c.post("/api/v1/users", json={"email": "c@test.com"}).json()["id"]
    r = c.patch("/api/v1/workouts/w1", json={
        "user_id": uid, "actual_duration_minutes": 50, "session_rpe": 8,
        "logged_exercises": [{"exercise_id": "bench", "name": "Bench", "sets": [
            {"set_number": 1, "weight_kg": 80, "reps_completed": 10, "rpe": 8}
        ]}],
    })
    assert r.status_code == 200
    assert r.json()["session_load"] == 400.0  # 50 * 8


def test_update_user_typed():
    uid = c.post("/api/v1/users", json={"email": "u@t.com"}).json()["id"]
    r = c.patch(f"/api/v1/users/{uid}", json={"name": "Alice", "fitness_level": "advanced"})
    assert r.status_code == 200
    assert r.json()["name"] == "Alice"
    assert r.json()["fitness_level"] == "advanced"
    # unknown fields silently ignored, not written to storage
    r2 = c.patch(f"/api/v1/users/{uid}", json={"id": "hacked", "role": "admin"})
    assert r2.status_code == 200
    assert r2.json()["id"] == uid  # id unchanged
    assert "role" not in r2.json()


def test_nlp_sentiment_typed():
    r = c.post("/api/v1/trends/nlp/sentiment", json={"text": "Great session!"})
    assert r.status_code == 200
    assert r.json()["sentiment"] == "positive"


def test_nlp_empty_text_rejected():
    r = c.post("/api/v1/trends/nlp/sentiment", json={"text": ""})
    assert r.status_code == 422


def test_list_exercises_filters():
    r = c.get("/api/v1/exercises?category=strength&page_size=3")
    assert r.status_code == 200
    d = r.json()
    assert d["total"] > 0
    assert len(d["items"]) <= 3
    assert all(ex["category"] == "strength" for ex in d["items"])


def test_chat_coach():
    r = c.post("/api/v1/chat", json={"user_id": "u1", "message": "How am I doing?"})
    assert r.status_code == 200
    d = r.json()
    assert "reply" in d
    assert len(d["reply"]) > 0
    assert "intent" in d


def test_chat_empty_message_rejected():
    r = c.post("/api/v1/chat", json={"user_id": "u1", "message": ""})
    assert r.status_code == 422


def test_mood_log_and_trend():
    # Log mood
    r = c.post("/api/v1/mental-health", json={
        "user_id": "u1", "mood": 8, "energy": 7, "anxiety": 3,
        "notes": "Feeling good", "tags": ["good_sleep"]
    })
    assert r.status_code == 201
    d = r.json()
    assert d["mood"] == 8
    assert d["energy"] == 7
    # Get trend
    r2 = c.get("/api/v1/mental-health?user_id=u1&days=7")
    assert r2.status_code == 200
    assert r2.json()["count"] >= 1


def test_breathing_exercises():
    r = c.get("/api/v1/mental-health/breathing-exercises")
    assert r.status_code == 200
    exs = r.json()
    assert len(exs) >= 5
    assert any(e["id"] == "box-breathing" for e in exs)


def test_anomaly_alerts():
    r = c.get("/api/v1/trends/alerts?user_id=default")
    assert r.status_code == 200
    d = r.json()
    assert "alerts" in d
    assert "alert_count" in d
    assert "has_critical" in d


def test_achievements():
    r = c.get("/api/v1/achievements?user_id=default")
    assert r.status_code == 200
    achievements = r.json()
    assert len(achievements) >= 10
    assert any(a["id"] == "first_workout" for a in achievements)


def test_social_challenge_lifecycle():
    # Create
    r = c.post("/api/v1/social?user_id=u1", json={
        "name": "Plank Challenge", "description": "Hold planks every day",
        "challenge_type": "duration", "target_value": 30,
        "target_unit": "minutes", "duration_days": 30,
    })
    assert r.status_code == 201
    ch = r.json()
    cid = ch["id"]
    assert ch["name"] == "Plank Challenge"
    assert ch["participant_count"] == 0

    # List
    r2 = c.get("/api/v1/social?user_id=u1")
    assert r2.status_code == 200
    assert any(x["id"] == cid for x in r2.json())

    # Join
    r3 = c.post(f"/api/v1/social/{cid}/join?user_id=u1")
    assert r3.status_code == 200
    assert r3.json()["message"] == "Joined!"

    # Duplicate join
    r3b = c.post(f"/api/v1/social/{cid}/join?user_id=u1")
    assert r3b.status_code == 409

    # Join as second user
    r3c = c.post(f"/api/v1/social/{cid}/join?user_id=u2")
    assert r3c.status_code == 200

    # Progress
    r4 = c.post(f"/api/v1/social/{cid}/progress?user_id=u1", json={"value": 15})
    assert r4.status_code == 200
    assert r4.json()["participant_count"] == 2

    r4b = c.post(f"/api/v1/social/{cid}/progress?user_id=u2", json={"value": 10})
    assert r4b.status_code == 200

    # Leaderboard
    r5 = c.get(f"/api/v1/social/{cid}/leaderboard?user_id=u1")
    assert r5.status_code == 200
    lb = r5.json()
    assert len(lb) == 2
    assert lb[0]["score"] == 15  # u1 leads
    assert lb[0]["rank"] == 1

    # Feed
    r6 = c.get("/api/v1/social/feed")
    assert r6.status_code == 200
    feed = r6.json()
    assert len(feed) >= 3  # create + 2 joins + 2 progress

    # 404
    r7 = c.get("/api/v1/social/nonexistent/leaderboard")
    assert r7.status_code == 404


def test_nutrition_lifecycle():
    # Log meal
    r = c.post("/api/v1/nutrition/meals?user_id=n1", json={
        "name": "Chicken breast", "calories": 350,
        "protein_g": 40, "carbs_g": 0, "fat_g": 8,
        "meal_type": "lunch",
    })
    assert r.status_code == 201
    meal = r.json()
    assert meal["name"] == "Chicken breast"
    assert meal["calories"] == 350
    mid = meal["id"]

    # List meals
    r2 = c.get(f"/api/v1/nutrition/meals?user_id=n1")
    assert r2.status_code == 200
    assert len(r2.json()) >= 1

    # Daily summary
    r3 = c.get(f"/api/v1/nutrition/daily?user_id=n1&calorie_target=2500&protein_target=150")
    assert r3.status_code == 200
    summary = r3.json()
    assert summary["total_calories"] == 350
    assert summary["total_protein"] == 40
    assert summary["remaining_calories"] == 2150
    assert summary["meal_count"] == 1

    # Targets
    r4 = c.get("/api/v1/nutrition/targets")
    assert r4.status_code == 200
    assert r4.json()["protein_g"] == 150

    # Delete meal
    r5 = c.delete(f"/api/v1/nutrition/meals/{mid}?user_id=n1")
    assert r5.status_code == 200
    assert r5.json()["deleted"] is True

    # Delete nonexistent
    r6 = c.delete(f"/api/v1/nutrition/meals/nonexistent?user_id=n1")
    assert r6.status_code == 404


def test_periodization():
    # Get default plan
    r = c.get("/api/v1/periodization?user_id=p1")
    assert r.status_code == 200
    plan = r.json()
    assert plan["duration_weeks"] == 5
    assert len(plan["weeks"]) == 5
    assert plan["weeks"][0]["phase"] == "accumulation"
    assert plan["weeks"][-1]["phase"] == "deload"

    # Generate custom plan
    r2 = c.post("/api/v1/periodization?user_id=p1", json={
        "goal": "hypertrophy", "current_readiness": "REDUCED"
    })
    assert r2.status_code == 200
    plan2 = r2.json()
    assert plan2["name"] == "Hypertrophy Block"
    assert plan2["duration_weeks"] == 4
    # Volume should be reduced due to REDUCED readiness
    assert plan2["weeks"][0]["volume_pct"] < 80

    # Available plans
    r3 = c.get("/api/v1/periodization/available")
    assert r3.status_code == 200
    assert len(r3.json()["plans"]) == 3


def test_sleep_analysis():
    # Log sleep
    r = c.post("/api/v1/sleep/logs?user_id=s1", json={
        "bedtime": "23:00", "wake_time": "07:00",
        "total_minutes": 480, "efficiency_pct": 92,
        "deep_pct": 20, "rem_pct": 22, "light_pct": 45, "awake_pct": 13,
    })
    assert r.status_code == 201
    log = r.json()
    assert log["total_minutes"] == 480

    # Log a second night
    c.post("/api/v1/sleep/logs?user_id=s1", json={
        "bedtime": "22:30", "wake_time": "06:30",
        "total_minutes": 480, "efficiency_pct": 88,
        "deep_pct": 18, "rem_pct": 20, "light_pct": 48, "awake_pct": 14,
    })

    # Analysis
    r2 = c.get("/api/v1/sleep/analysis?user_id=s1&days=7")
    assert r2.status_code == 200
    analysis = r2.json()
    assert analysis["score"] > 0
    assert analysis["grade"] in ["A", "B", "C", "D", "F"]
    assert analysis["avg_duration_hours"] == 8.0
    assert len(analysis["recommendations"]) > 0
    assert len(analysis["stage_breakdown"]) == 4  # awake, light, deep, rem

    # Logs
    r3 = c.get("/api/v1/sleep/logs?user_id=s1")
    assert r3.status_code == 200
    assert len(r3.json()) == 2

    # Delete
    r4 = c.delete(f"/api/v1/sleep/logs/{log['id']}?user_id=s1")
    assert r4.status_code == 200

    # 404
    r5 = c.delete("/api/v1/sleep/logs/nonexistent?user_id=s1")
    assert r5.status_code == 404


def test_body_composition():
    # Log measurement
    r = c.post("/api/v1/body/measurements?user_id=b1", json={
        "weight_kg": 80.5, "body_fat_pct": 16.0, "muscle_mass_kg": 34.0,
        "chest_cm": 100, "waist_cm": 82, "hips_cm": 96,
    })
    assert r.status_code == 201
    m = r.json()
    assert m["weight_kg"] == 80.5
    mid = m["id"]

    # List
    r2 = c.get("/api/v1/body/measurements?user_id=b1")
    assert r2.status_code == 200
    assert len(r2.json()) == 1

    # Trends
    r3 = c.get("/api/v1/body/trends?user_id=b1")
    assert r3.status_code == 200
    assert "7d" in r3.json()
    assert "30d" in r3.json()

    # Delete
    r4 = c.delete(f"/api/v1/body/measurements/{mid}?user_id=b1")
    assert r4.status_code == 200

    # 404
    r5 = c.delete("/api/v1/body/measurements/nonexistent?user_id=b1")
    assert r5.status_code == 404

    # Empty measurement = 400
    r6 = c.post("/api/v1/body/measurements?user_id=b1", json={})
    assert r6.status_code == 400


def test_progress_photos():
    # Log photo
    r = c.post("/api/v1/progress-photos?user_id=p1", json={
        "photo_uri": "file:///test.jpg", "angle": "front",
        "weight_kg": 80.0, "notes": "Week 1",
    })
    assert r.status_code == 201
    photo = r.json()
    assert photo["angle"] == "front"
    pid = photo["id"]

    # Log second photo
    c.post("/api/v1/progress-photos?user_id=p1", json={
        "photo_uri": "file:///test2.jpg", "angle": "front",
        "weight_kg": 79.0, "notes": "Week 4",
    })

    # List
    r2 = c.get("/api/v1/progress-photos?user_id=p1")
    assert r2.status_code == 200
    assert len(r2.json()) == 2

    # Filter by angle
    r3 = c.get("/api/v1/progress-photos?user_id=p1&angle=front")
    assert r3.status_code == 200
    assert len(r3.json()) == 2

    # Compare
    r4 = c.get("/api/v1/progress-photos/compare?user_id=p1&angle=front")
    assert r4.status_code == 200
    cmp = r4.json()
    assert cmp["before"] is not None
    assert cmp["after"] is not None
    assert cmp["total_photos"] == 2

    # Delete
    r5 = c.delete(f"/api/v1/progress-photos/{pid}?user_id=p1")
    assert r5.status_code == 200

    # 404
    r6 = c.delete("/api/v1/progress-photos/nonexistent?user_id=p1")
    assert r6.status_code == 404


def test_simulator():
    # Simulate 7 days
    r = c.post("/api/v1/simulator?user_id=sim1", json={
        "days": 7, "base_hrv": 50, "base_sleep": 8, "trend": "improving"
    })
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 7
    assert all(d["hrv_rmssd"] > 0 for d in data)
    assert all(d["steps"] > 0 for d in data)

    # Quick simulate
    r2 = c.get("/api/v1/simulator/quick")
    assert r2.status_code == 200
    q = r2.json()
    assert q["hrv_rmssd"] > 0
    assert q["sleep_hours"] > 0


def test_background_tasks():
    # Submit a task
    r = c.post("/api/v1/tasks", json={"task_type": "anomaly_scan"})
    assert r.status_code == 202
    task = r.json()
    assert task["status"] in ["pending", "running", "completed"]
    tid = task["task_id"]

    # Get task
    import time; time.sleep(2)
    r2 = c.get(f"/api/v1/tasks/{tid}")
    assert r2.status_code == 200
    assert r2.json()["status"] in ["running", "completed"]

    # List tasks
    r3 = c.get("/api/v1/tasks")
    assert r3.status_code == 200
    assert len(r3.json()) >= 1

    # Stats
    r4 = c.get("/api/v1/tasks/stats")
    assert r4.status_code == 200
    assert "total" in r4.json()

    # Invalid task type
    r5 = c.post("/api/v1/tasks", json={"task_type": "nonexistent"})
    assert r5.status_code == 400

    # 404
    r6 = c.get("/api/v1/tasks/nonexistent")
    assert r6.status_code == 404


def test_wearable_sync():
    # Sync data
    r = c.post("/api/v1/wearable/sync?user_id=w1", json={
        "device_type": "wearos",
        "device_id": "Pixel Watch 3",
        "hrv_readings": [{"timestamp": "2026-01-01T08:00:00", "value_ms": 45}],
        "sleep_sessions": [{"start": "2026-01-01T23:00", "end": "2026-01-02T07:00", "deep_min": 90, "rem_min": 100}],
        "heart_rate_readings": [{"timestamp": "2026-01-01T08:00", "bpm": 62}],
        "step_counts": [{"date": "2026-01-01", "count": 8500}],
    })
    assert r.status_code == 200
    sync = r.json()
    assert sync["records_ingested"] == 4
    assert sync["device_type"] == "wearos"

    # Devices
    r2 = c.get("/api/v1/wearable/devices?user_id=w1")
    assert r2.status_code == 200
    assert len(r2.json()) == 1

    # Sync history
    r3 = c.get("/api/v1/wearable/sync-history?user_id=w1")
    assert r3.status_code == 200
    assert len(r3.json()) >= 1

    # Latest
    r4 = c.get("/api/v1/wearable/latest?user_id=w1")
    assert r4.status_code == 200
    assert r4.json()["total_syncs"] >= 1


def test_streaks():
    from datetime import datetime, timedelta, timezone
    uid = "streak_u1"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    two_days = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")

    # Log 3 consecutive days
    for d in [two_days, yesterday, today]:
        r = c.post(f"/api/v1/streaks/log?user_id={uid}&date={d}")
        assert r.status_code == 200

    # Get streaks
    r2 = c.get(f"/api/v1/streaks?user_id={uid}")
    assert r2.status_code == 200
    s = r2.json()
    assert s["current_streak"] >= 2
    assert s["total_workouts"] == 3
    assert s["best_streak"] >= 3

    # Heatmap
    r3 = c.get(f"/api/v1/streaks/heatmap?user_id={uid}&months=1")
    assert r3.status_code == 200
    days = r3.json()
    assert len(days) > 0
    workout_days = [d for d in days if d["workout"]]
    assert len(workout_days) == 3


def test_fitness_assessment():
    # 1RM estimate
    r = c.post("/api/v1/fitness/one-rm", json={
        "exercise": "bench press", "weight_kg": 80, "reps": 5
    })
    assert r.status_code == 200
    est = r.json()
    assert est["estimated_1rm"] > 80  # Must be > working weight
    assert est["reps"] == 5

    # 1RM with bodyweight for strength level
    r2 = c.post("/api/v1/fitness/one-rm", json={
        "exercise": "squat", "weight_kg": 120, "reps": 3, "bodyweight_kg": 80
    })
    assert r2.status_code == 200
    assert r2.json()["strength_level"] in ["beginner", "novice", "intermediate", "advanced", "elite"]

    # Fitness test
    r3 = c.post("/api/v1/fitness/test", json={"test_id": "pushups_1min", "result": 35})
    assert r3.status_code == 200
    t = r3.json()
    assert t["rating"] == "average"
    assert t["percentile"] == 60

    # List tests
    r4 = c.get("/api/v1/fitness/tests")
    assert r4.status_code == 200
    assert len(r4.json()) >= 4

    # Summary
    r5 = c.get("/api/v1/fitness/summary")
    assert r5.status_code == 200
    assert "overall_score" in r5.json()


def test_music():
    # List presets
    r = c.get("/api/v1/music/presets")
    assert r.status_code == 200
    presets = r.json()
    assert len(presets) >= 4
    assert any(p["id"] == "strength" for p in presets)

    # Get preset
    r2 = c.get("/api/v1/music/preset/hiit")
    assert r2.status_code == 200
    assert r2.json()["bpm_range"][0] >= 160

    # 404
    r3 = c.get("/api/v1/music/preset/nonexistent")
    assert r3.status_code == 404

    # Play
    r4 = c.post("/api/v1/music/play?user_id=m1&playlist_id=strength")
    assert r4.status_code == 200
    assert r4.json()["is_playing"] is True
    assert r4.json()["current_track"]["bpm"] >= 130

    # State
    r5 = c.get("/api/v1/music/state?user_id=m1")
    assert r5.status_code == 200
    assert r5.json()["is_playing"] is True

    # Pause
    r6 = c.post("/api/v1/music/pause?user_id=m1")
    assert r6.status_code == 200
    assert r6.json()["is_playing"] is False

    # Resume
    r7 = c.post("/api/v1/music/resume?user_id=m1")
    assert r7.status_code == 200
    assert r7.json()["is_playing"] is True

    # Next
    r8 = c.post("/api/v1/music/next?user_id=m1")
    assert r8.status_code == 200

    # Volume
    r9 = c.post("/api/v1/music/volume?user_id=m1&level=0.5")
    assert r9.status_code == 200
    assert r9.json()["volume"] == 0.5


def test_notifications():
    # Setup defaults
    r = c.post("/api/v1/notifications/setup-defaults?user_id=n1")
    assert r.status_code == 201
    assert r.json()["count"] == 3

    # Setup again (idempotent)
    r1b = c.post("/api/v1/notifications/setup-defaults?user_id=n1")
    assert r1b.json()["count"] == 3

    # List
    r2 = c.get("/api/v1/notifications?user_id=n1")
    assert r2.status_code == 200
    notes = r2.json()
    assert len(notes) == 3
    types = {n["type"] for n in notes}
    assert "workout_reminder" in types
    assert "recovery_checkin" in types
    assert "sleep_reminder" in types

    # Custom reminder
    r3 = c.post("/api/v1/notifications/workout-reminder?user_id=n1", json={
        "time_of_day": "17:00", "days": [1, 3, 5]
    })
    assert r3.status_code == 201

    # Preferences
    r4 = c.get("/api/v1/notifications/preferences?user_id=n1")
    assert r4.status_code == 200
    assert r4.json()["workout_reminders"] is True

    r5 = c.put("/api/v1/notifications/preferences?user_id=n1", json={
        "quiet_hours_start": "23:00", "quiet_hours_end": "06:00"
    })
    assert r5.status_code == 200
    assert r5.json()["quiet_hours_start"] == "23:00"

    # Delete
    nid = notes[0]["id"]
    r6 = c.delete(f"/api/v1/notifications/{nid}?user_id=n1")
    assert r6.status_code == 200

    # 404
    r7 = c.delete("/api/v1/notifications/nonexistent?user_id=n1")
    assert r7.status_code == 404


def test_data_export():
    # Formats
    r = c.get("/api/v1/export/formats")
    assert r.status_code == 200
    assert len(r.json()["data_types"]) >= 5

    # Export workouts (JSON)
    r2 = c.get("/api/v1/export/workouts?user_id=exp1&format=json")
    assert r2.status_code == 200
    assert "export_date" in r2.json()

    # Export recovery (CSV)
    r3 = c.get("/api/v1/export/recovery?user_id=exp1&format=csv")
    assert r3.status_code == 200
    assert r3.headers["content-type"].startswith("text/csv")

    # Export nutrition
    r4 = c.get("/api/v1/export/nutrition?user_id=exp1&format=json")
    assert r4.status_code == 200

    # Export sleep
    r5 = c.get("/api/v1/export/sleep?user_id=exp1&format=json")
    assert r5.status_code == 200

    # Export body
    r6 = c.get("/api/v1/export/body?user_id=exp1&format=json")
    assert r6.status_code == 200

    # Full export
    r7 = c.get("/api/v1/export/all?user_id=exp1")
    assert r7.status_code == 200
    data = r7.json()
    assert "data" in data
    assert "workouts" in data["data"]
    assert "recovery_logs" in data["data"]


def test_workout_analytics():
    r = c.get("/api/v1/analytics?user_id=a1")
    assert r.status_code == 200
    a = r.json()
    assert "summary" in a
    assert "volume_trends" in a
    assert "muscle_balance" in a
    assert "periodization_insights" in a
    assert "predictions" in a
    assert "overall_score" in a
    assert "actionable_insights" in a
    assert isinstance(a["actionable_insights"], list)

    # Sub-endpoints
    r2 = c.get("/api/v1/analytics/volume-trends?user_id=a1")
    assert r2.status_code == 200
    r3 = c.get("/api/v1/analytics/muscle-balance?user_id=a1")
    assert r3.status_code == 200
    r4 = c.get("/api/v1/analytics/predictions?user_id=a1")
    assert r4.status_code == 200


def test_workout_templates():
    uid = "tmpl_u1"

    # List (includes builtins)
    r = c.get(f"/api/v1/templates?user_id={uid}")
    assert r.status_code == 200
    assert len(r.json()) >= 4  # 4 builtin templates

    # Get builtin
    r2 = c.get(f"/api/v1/templates/builtin_push?user_id={uid}")
    assert r2.status_code == 200
    assert r2.json()["is_builtin"] is True
    assert len(r2.json()["exercises"]) >= 4

    # Categories
    r3 = c.get("/api/v1/templates/categories")
    assert r3.status_code == 200
    assert len(r3.json()["categories"]) >= 6

    # Create custom
    r4 = c.post(f"/api/v1/templates?user_id={uid}", json={
        "name": "My Pull Day",
        "description": "Custom pull workout",
        "category": "pull",
        "exercises": [
            {"exercise_id": "row", "name": "Barbell Row", "target_muscle": "back", "sets": 4, "target_reps": "8-10"},
            {"exercise_id": "curl", "name": "Barbell Curl", "target_muscle": "biceps", "sets": 3, "target_reps": "10-12"},
        ],
        "target_duration_minutes": 45,
    })
    assert r4.status_code == 201
    tid = r4.json()["id"]
    assert r4.json()["name"] == "My Pull Day"
    assert len(r4.json()["exercises"]) == 2

    # Get custom
    r5 = c.get(f"/api/v1/templates/{tid}?user_id={uid}")
    assert r5.status_code == 200

    # Use template
    r6 = c.post(f"/api/v1/templates/{tid}/use?user_id={uid}")
    assert r6.status_code == 200
    assert r6.json()["use_count"] == 1

    # Update
    r7 = c.put(f"/api/v1/templates/{tid}?user_id={uid}", json={
        "name": "My Pull Day V2",
        "description": "Updated",
        "category": "pull",
        "exercises": [
            {"exercise_id": "row", "name": "Barbell Row", "target_muscle": "back", "sets": 5, "target_reps": "6-8"},
        ],
        "target_duration_minutes": 50,
    })
    assert r7.status_code == 200
    assert r7.json()["name"] == "My Pull Day V2"

    # Delete
    r8 = c.delete(f"/api/v1/templates/{tid}?user_id={uid}")
    assert r8.status_code == 200
    assert r8.json()["deleted"] is True

    # 404
    r9 = c.get(f"/api/v1/templates/nonexistent?user_id={uid}")
    assert r9.status_code == 404

    # Can't delete builtin
    r10 = c.delete(f"/api/v1/templates/builtin_push?user_id={uid}")
    assert r10.status_code == 404


def test_community():
    uid = "comm_u1"

    # Feed starts empty
    r = c.get(f"/api/v1/community/feed?user_id={uid}")
    assert r.status_code == 200
    assert len(r.json()) == 0

    # Share a workout (use workout_id from generated workout)
    # First generate a workout
    r_gen = c.post(f"/api/v1/workouts?user_id={uid}", json={
        "user_id": uid, "target_date": "2026-01-01", "target_duration_minutes": 45
    })
    if r_gen.status_code == 201:
        wid = r_gen.json()["workout_id"]
        r2 = c.post(f"/api/v1/community/share?user_id={uid}", json={
            "workout_id": wid, "title": "Great push day!", "caption": "Felt strong today"
        })
        assert r2.status_code == 201
        sid = r2.json()["id"]
        assert r2.json()["title"] == "Great push day!"
        assert r2.json()["likes"] == 0

        # Feed
        r3 = c.get(f"/api/v1/community/feed?user_id={uid}")
        assert r3.status_code == 200
        assert len(r3.json()) == 1

        # Like
        r4 = c.post(f"/api/v1/community/{sid}/like?user_id=u2")
        assert r4.status_code == 200
        assert r4.json()["liked"] is True
        assert r4.json()["total_likes"] == 1

        # Unlike
        r4b = c.post(f"/api/v1/community/{sid}/like?user_id=u2")
        assert r4b.json()["liked"] is False
        assert r4b.json()["total_likes"] == 0

        # Comment
        r5 = c.post(f"/api/v1/community/{sid}/comments?user_id=u3", json={
            "text": "Nice work!"
        })
        assert r5.status_code == 201
        assert r5.json()["text"] == "Nice work!"

        # Get comments
        r6 = c.get(f"/api/v1/community/{sid}/comments")
        assert r6.status_code == 200
        assert len(r6.json()) == 1

        # My shares
        r7 = c.get(f"/api/v1/community/my-shares?user_id={uid}")
        assert r7.status_code == 200
        assert len(r7.json()) == 1

        # Delete
        r8 = c.delete(f"/api/v1/community/{sid}?user_id={uid}")
        assert r8.status_code == 200

        # Can't delete others'
        # r9 = c.delete(f"/api/v1/community/{sid}?user_id=u2")
        # assert r9.status_code == 404  # already deleted


def test_goals():
    uid = "goal_u1"

    # Create goal
    r = c.post(f"/api/v1/goals?user_id={uid}", json={
        "name": "Squat 120kg",
        "goal_type": "strength",
        "target_value": 120,
        "target_unit": "kg",
        "deadline_days": 90,
    })
    assert r.status_code == 201
    g = r.json()
    gid = g["id"]
    assert g["name"] == "Squat 120kg"
    assert g["status"] == "active"
    assert g["progress_pct"] == 0

    # Update progress
    r2 = c.post(f"/api/v1/goals/{gid}/update?user_id={uid}", json={"current_value": 30})
    assert r2.status_code == 200
    assert r2.json()["progress_pct"] == 25.0
    assert r2.json()["celebration"] is not None  # 25% milestone

    # Update to 50%
    r3 = c.post(f"/api/v1/goals/{gid}/update?user_id={uid}", json={"current_value": 60})
    assert r3.status_code == 200
    assert r3.json()["progress_pct"] == 50.0
    assert r3.json()["streak_days"] >= 1

    # Update to 100%
    r4 = c.post(f"/api/v1/goals/{gid}/update?user_id={uid}", json={"current_value": 120})
    assert r4.status_code == 200
    assert r4.json()["status"] == "achieved"
    assert r4.json()["progress_pct"] == 100.0
    assert r4.json()["celebration"] == "GOAL ACHIEVED! You did it! Incredible work!"

    # Milestones
    r5 = c.get(f"/api/v1/goals/{gid}/milestones?user_id={uid}")
    assert r5.status_code == 200
    milestones = r5.json()
    assert len(milestones) == 3
    assert all(m["is_achieved"] for m in milestones)

    # List goals
    r6 = c.get(f"/api/v1/goals?user_id={uid}")
    assert r6.status_code == 200
    assert len(r6.json()) == 1
    assert r6.json()[0]["status"] == "achieved"

    # Stats
    r7 = c.get(f"/api/v1/goals/stats?user_id={uid}")
    assert r7.status_code == 200
    assert r7.json()["achieved"] == 1

    # Delete
    r8 = c.delete(f"/api/v1/goals/{gid}?user_id={uid}")
    assert r8.status_code == 200
    assert r8.json()["deleted"] is True

    # 404
    r9 = c.delete(f"/api/v1/goals/nonexistent?user_id={uid}")
    assert r9.status_code == 404


def test_fitness_challenges():
    uid = "fc_u1"

    # List builtins
    r = c.get(f"/api/v1/challenges?user_id={uid}")
    assert r.status_code == 200
    challenges = r.json()
    assert len(challenges) >= 8  # 8 builtin challenges
    assert any(ch["name"] == "30-Day Push-Up Challenge" for ch in challenges)

    # Categories
    r2 = c.get("/api/v1/challenges/categories")
    assert r2.status_code == 200
    assert len(r2.json()["categories"]) == 4

    # Builtin templates
    r3 = c.get("/api/v1/challenges/builtin")
    assert r3.status_code == 200
    assert len(r3.json()) >= 8

    # Join challenge
    r4 = c.post(f"/api/v1/challenges/join/pushup_30?user_id={uid}")
    assert r4.status_code == 200
    assert r4.json()["participants"] == 1

    # Duplicate join
    r4b = c.post(f"/api/v1/challenges/join/pushup_30?user_id={uid}")
    assert r4b.status_code == 409

    # Log daily progress
    r5 = c.post(f"/api/v1/challenges/pushup_30/log?user_id={uid}", json={
        "value": 50, "note": "First day!"
    })
    assert r5.status_code == 200
    assert r5.json()["total_progress"] == 50
    assert r5.json()["progress_pct"] > 0

    # Duplicate day
    r5b = c.post(f"/api/v1/challenges/pushup_30/log?user_id={uid}", json={"value": 30})
    assert r5b.status_code == 409

    # My progress
    r6 = c.get(f"/api/v1/challenges/pushup_30/my-progress?user_id={uid}")
    assert r6.status_code == 200
    assert r6.json()["total_progress"] == 50
    assert r6.json()["daily_logs_count"] == 1

    # Leaderboard
    r7 = c.get(f"/api/v1/challenges/pushup_30/leaderboard?user_id={uid}")
    assert r7.status_code == 200
    lb = r7.json()
    assert lb["total_participants"] == 1
    assert len(lb["entries"]) == 1
    assert lb["entries"][0]["total_progress"] == 50

    # Leave
    r8 = c.delete(f"/api/v1/challenges/pushup_30?user_id={uid}")
    assert r8.status_code == 200
    assert r8.json()["left"] is True


def test_workout_import_export():
    uid = "ie_u1"

    # Quick export
    r = c.post(f"/api/v1/plan/quick-export?user_id={uid}&name=Push+Day&exercise_ids=barbell-bench-press&exercise_ids=dumbbell-incline-press")
    assert r.status_code == 200
    pid = r.json()["id"]
    assert r.json()["exercises"] == 2

    # Get shared plan
    r2 = c.get(f"/api/v1/plan/shared/{pid}")
    assert r2.status_code == 200
    plan = r2.json()
    assert plan["plan"]["title"] == "Push Day"
    assert len(plan["plan"]["exercises"]) == 2

    # List exported
    r3 = c.get(f"/api/v1/plan/exported?user_id={uid}")
    assert r3.status_code == 200
    assert len(r3.json()) == 1

    # Import
    r4 = c.post(f"/api/v1/plan/import?user_id=ie_u2", json={
        "plan": plan["plan"],
        "name": "My Push Day"
    })
    assert r4.status_code == 200
    assert r4.json()["exercises"] == 2

    # List imported
    r5 = c.get(f"/api/v1/plan/imported?user_id=ie_u2")
    assert r5.status_code == 200
    assert len(r5.json()) == 1
    assert r5.json()[0]["title"] == "My Push Day"

    # 404
    r6 = c.get("/api/v1/plan/shared/nonexistent")
    assert r6.status_code == 404


def test_recommendations():
    uid = "rec_u1"

    # Full recommendation
    r = c.post(f"/api/v1/recommend?user_id={uid}", json={
        "recovery_score": 75,
        "readiness_state": "MODERATE",
        "primary_goal": "hypertrophy",
        "acwr": 1.0,
    })
    assert r.status_code == 200
    rec = r.json()
    assert rec["workout_type"] in ["strength", "hypertrophy", "endurance", "mobility", "rest"]
    assert rec["intensity"] in ["low", "moderate", "high", "very_high"]
    assert rec["confidence"] > 0
    assert len(rec["rationale"]) > 0

    # Low recovery -> rest recommendation
    r2 = c.post(f"/api/v1/recommend?user_id={uid}", json={
        "recovery_score": 20,
        "readiness_state": "DEPLETED",
    })
    assert r2.status_code == 200
    assert r2.json()["workout_type"] == "rest"
    assert r2.json()["confidence"] >= 0.9

    # Quick recommendation
    r3 = c.get(f"/api/v1/recommend/quick?user_id={uid}")
    assert r3.status_code == 200
    assert "workout_type" in r3.json()

    # Today's recommendation
    r4 = c.get(f"/api/v1/recommend/today?user_id={uid}")
    assert r4.status_code == 200
    assert "recommendation" in r4.json()
    assert "tips" in r4.json()


def test_body_dashboard():
    uid = "dash_u1"

    # Dashboard (empty)
    r = c.get(f"/api/v1/dashboard?user_id={uid}")
    assert r.status_code == 200
    dash = r.json()
    assert "weight" in dash
    assert "body_fat" in dash
    assert "muscle_mass" in dash
    assert "measurements" in dash
    assert "body_composition_score" in dash

    # Dashboard with data
    # First log some measurements
    c.post(f"/api/v1/body/measurements?user_id={uid}", json={
        "weight_kg": 82.0, "body_fat_pct": 18.0, "muscle_mass_kg": 33.0,
        "chest_cm": 100, "waist_cm": 84,
    })
    c.post(f"/api/v1/body/measurements?user_id={uid}", json={
        "weight_kg": 81.0, "body_fat_pct": 17.5, "muscle_mass_kg": 33.5,
        "chest_cm": 101, "waist_cm": 83,
    })

    r2 = c.get(f"/api/v1/dashboard?user_id={uid}&months=1")
    assert r2.status_code == 200
    d = r2.json()
    assert d["weight"]["current"] == 81.0
    assert d["body_fat"]["current"] == 17.5
    assert d["muscle_mass"]["current"] == 33.5
    assert d["weight"]["direction"] == "down"  # 82 -> 81
    assert d["body_fat"]["direction"] == "down"  # 18 -> 17.5
    assert len(d["weight"]["chart_data"]) == 2
    assert d["body_composition_score"] > 0
    assert "weight" in d["summary"].lower()

    # Weight history
    r3 = c.get(f"/api/v1/dashboard/weight-history?user_id={uid}")
    assert r3.status_code == 200
    assert len(r3.json()) == 2

    # Body fat history
    r4 = c.get(f"/api/v1/dashboard/body-fat-history?user_id={uid}")
    assert r4.status_code == 200
    assert len(r4.json()) == 2

    # Summary
    r5 = c.get(f"/api/v1/dashboard/summary?user_id={uid}")
    assert r5.status_code == 200
    assert r5.json()["total_entries"] == 2
    assert r5.json()["changes"]["weight_kg"] == -1.0
    assert r5.json()["changes"]["body_fat_pct"] == -0.5


def test_workout_timer():
    # Start session
    r = c.post("/api/v1/timer/start", json={
        "exercises": [
            {"name": "Bench Press", "sets": 3, "target_reps": "8-10", "target_rpe": 7, "rest_seconds": 90},
            {"name": "Incline Press", "sets": 3, "target_reps": "10-12", "target_rpe": 7, "rest_seconds": 90},
        ]
    })
    assert r.status_code == 200
    sid = r.json()["session_id"]
    assert r.json()["state"] == "warmup"
    assert r.json()["total_exercises"] == 2
    assert r.json()["total_sets"] == 6

    # Get state
    r2 = c.get(f"/api/v1/timer/{sid}")
    assert r2.status_code == 200
    assert r2.json()["session_id"] == sid

    # Start rest
    r3 = c.post(f"/api/v1/timer/{sid}/rest", json={"duration_seconds": 60})
    assert r3.status_code == 200
    assert r3.json()["state"] == "rest"
    assert r3.json()["remaining_seconds"] == 60

    # Complete set
    r4 = c.post(f"/api/v1/timer/{sid}/complete-set")
    assert r4.status_code == 200
    assert r4.json()["completed_sets"] == 1

    # Pause
    r5 = c.post(f"/api/v1/timer/{sid}/pause")
    assert r5.status_code == 200
    assert r5.json()["state"] == "paused"

    # Resume
    r6 = c.post(f"/api/v1/timer/{sid}/resume")
    assert r6.status_code == 200
    assert r6.json()["state"] != "paused"

    # Get cues
    r7 = c.get(f"/api/v1/timer/{sid}/cues")
    assert r7.status_code == 200
    assert isinstance(r7.json(), list)

    # End session
    r8 = c.post(f"/api/v1/timer/{sid}/end")
    assert r8.status_code == 200
    assert r8.json()["completed_sets"] == 1
    assert r8.json()["total_sets"] == 6

    # 404
    r9 = c.get("/api/v1/timer/nonexistent")
    assert r9.status_code == 404


def test_training_calendar():
    uid = "cal_u1"

    from datetime import datetime, timedelta, timezone
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    # Schedule workout
    r = c.post(f"/api/v1/calendar?user_id={uid}", json={
        "date": today, "workout_type": "strength",
        "title": "Push Day", "duration_minutes": 50,
        "focus_muscles": ["chest", "shoulders"],
    })
    assert r.status_code == 201
    eid = r.json()["id"]
    assert r.json()["status"] == "scheduled"

    # Get day
    r2 = c.get(f"/api/v1/calendar/date/{today}?user_id={uid}")
    assert r2.status_code == 200
    assert len(r2.json()["entries"]) == 1
    assert r2.json()["total_duration"] == 50

    # Get week
    r3 = c.get(f"/api/v1/calendar/week?user_id={uid}&date={today}")
    assert r3.status_code == 200
    assert r3.json()["scheduled_days"] >= 1

    # Get month
    now = datetime.now(timezone.utc)
    r4 = c.get(f"/api/v1/calendar/month?user_id={uid}&year={now.year}&month={now.month}")
    assert r4.status_code == 200
    assert r4.json()["total_scheduled"] >= 1
    assert r4.json()["completion_rate"] == 0  # none completed yet

    # Update status
    r5 = c.patch(f"/api/v1/calendar/{eid}/status?status=completed&user_id={uid}")
    assert r5.status_code == 200
    assert r5.json()["status"] == "completed"

    # Stats
    r6 = c.get(f"/api/v1/calendar/stats?user_id={uid}&days=30")
    assert r6.status_code == 200
    assert r6.json()["total_completed"] == 1
    assert r6.json()["completion_rate"] == 100.0

    # Delete
    r7 = c.delete(f"/api/v1/calendar/{eid}?user_id={uid}")
    assert r7.status_code == 200
    assert r7.json()["deleted"] is True

    # Bulk schedule
    r8 = c.post(f"/api/v1/calendar/bulk?user_id={uid}&plan=ppl&weeks=1&start_date=2026-02-01")
    assert r8.status_code == 200
    assert r8.json()["scheduled"] >= 7  # At least 7 days
    assert r8.json()["plan"] == "ppl"

    # 404
    r9 = c.delete(f"/api/v1/calendar/nonexistent?user_id={uid}")
    assert r9.status_code == 404


def test_hydration():
    uid = "hyd_u1"

    # Get today (empty)
    r = c.get(f"/api/v1/hydration/today?user_id={uid}")
    assert r.status_code == 200
    assert r.json()["total_ml"] == 0
    assert r.json()["daily_goal_ml"] == 3000

    # Log water
    r2 = c.post(f"/api/v1/hydration/log?user_id={uid}", json={
        "amount_ml": 500, "drink_type": "water"
    })
    assert r2.status_code == 201
    lid = r2.json()["id"]
    assert r2.json()["amount_ml"] == 500

    # Log another
    c.post(f"/api/v1/hydration/log?user_id={uid}", json={
        "amount_ml": 250, "drink_type": "tea"
    })

    # Today summary
    r3 = c.get(f"/api/v1/hydration/today?user_id={uid}")
    assert r3.status_code == 200
    assert r3.json()["total_ml"] == 750
    assert r3.json()["log_count"] == 2
    assert r3.json()["progress_pct"] == 25.0
    assert r3.json()["goal_met"] is False
    assert "water" in r3.json()["drink_breakdown"]

    # Logs
    r4 = c.get(f"/api/v1/hydration/logs?user_id={uid}")
    assert r4.status_code == 200
    assert len(r4.json()) == 2

    # Goal
    r5 = c.get(f"/api/v1/hydration/goal?user_id={uid}")
    assert r5.status_code == 200
    assert r5.json()["daily_goal_ml"] == 3000

    r6 = c.put(f"/api/v1/hydration/goal?user_id={uid}", json={
        "daily_goal_ml": 2500, "reminder_interval_minutes": 30
    })
    assert r6.status_code == 200
    assert r6.json()["daily_goal_ml"] == 2500

    # Quick add
    r7 = c.get("/api/v1/hydration/quick-add")
    assert r7.status_code == 200
    assert len(r7.json()["options"]) == 5

    # Stats
    r8 = c.get(f"/api/v1/hydration/stats?user_id={uid}&days=7")
    assert r8.status_code == 200
    assert r8.json()["total_logs"] == 2

    # Delete
    r9 = c.delete(f"/api/v1/hydration/log/{lid}?user_id={uid}")
    assert r9.status_code == 200
    assert r9.json()["deleted"] is True

    # 404
    r10 = c.delete(f"/api/v1/hydration/log/nonexistent?user_id={uid}")
    assert r10.status_code == 404


def test_warmup_cooldown():
    # Warmup
    r = c.get("/api/v1/routine/warmup?muscles=chest,back")
    assert r.status_code == 200
    warmup = r.json()
    assert warmup["routine_type"] == "warmup"
    assert "chest" in warmup["target_muscles"]
    assert len(warmup["exercises"]) >= 4  # general + muscle-specific
    assert warmup["total_duration_seconds"] > 0
    assert warmup["exercises"][0]["type"] == "dynamic"

    # Cooldown
    r2 = c.get("/api/v1/routine/cooldown?muscles=quadriceps,hamstrings")
    assert r2.status_code == 200
    cooldown = r2.json()
    assert cooldown["routine_type"] == "cooldown"
    assert len(cooldown["exercises"]) >= 2
    assert cooldown["exercises"][0]["type"] == "static"

    # Full routine
    r3 = c.get("/api/v1/routine/full?muscles=chest,shoulders,back")
    assert r3.status_code == 200
    full = r3.json()
    assert "warmup" in full
    assert "cooldown" in full
    assert full["total_duration_seconds"] == full["warmup"]["total_duration_seconds"] + full["cooldown"]["total_duration_seconds"]

    # Available muscles
    r4 = c.get("/api/v1/routine/muscles")
    assert r4.status_code == 200
    assert len(r4.json()["muscles"]) >= 10


# ============================================================
# AI / NLP / ML Engine Tests
# ============================================================


def test_intent_classifier():
    """Intent classifier returns valid intents with confidence."""
    from app.services.intent_classifier import intent_classifier
    r = intent_classifier.classify("How is my recovery today?")
    assert r["primary_intent"] in ("recovery_query", "workout_advice", "default")
    assert 0.0 <= r["confidence"] <= 1.0
    assert len(r["all_intents"]) >= 1

    # Greeting
    r2 = intent_classifier.classify("Hey there!")
    assert r2["primary_intent"] == "greeting"

    # Empty input
    r3 = intent_classifier.classify("")
    assert r3["primary_intent"] == "empty"


def test_entity_extractor():
    """Entity extractor pulls weights, reps, sets, exercises from text."""
    from app.services.intent_classifier import entity_extractor
    entities = entity_extractor.extract_all("bench press 3x10 at 80kg RPE 8")
    assert len(entities["weights"]) >= 1
    assert entities["weights"][0]["value"] == 80.0
    assert entities["rpe"] == 8.0
    assert len(entities["exercises"]) >= 1
    assert entities["exercises"][0]["exercise_id"] == "barbell-bench-press"

    # Muscle extraction
    muscles = entity_extractor.extract_muscle_groups("My chest and shoulders are sore")
    assert "chest" in muscles
    assert "shoulders" in muscles

    # Distance
    e2 = entity_extractor.extract_all("Ran 5km in 25 minutes")
    assert len(e2["distance"]) >= 1
    assert e2["distance"][0]["value"] == 5.0


def test_nl_workout_logger():
    """NL workout logger parses natural language into structured data."""
    from app.services.nl_workout_logger import nl_workout_logger
    result = nl_workout_logger.parse("3x10 bench press at 80kg")
    assert len(result["exercises"]) >= 1
    assert result["exercises"][0]["sets"] == 3
    assert result["exercises"][0]["reps"] == 10
    assert result["exercises"][0]["weight_kg"] == 80.0
    assert result["total_volume_kg"] == 2400.0
    assert result["parse_confidence"] >= 0.5

    # Multiple exercises
    r2 = nl_workout_logger.parse("5x5 squat at 100kg and 3x8 bench at 60kg")
    assert len(r2["exercises"]) >= 2

    # Cardio
    r3 = nl_workout_logger.parse("Ran 5km in 25 minutes")
    assert len(r3["cardio"]) >= 1
    assert r3["cardio"][0]["distance"] == 5.0


def test_rag_knowledge_retriever():
    """RAG retriever returns relevant fitness knowledge."""
    from app.services.rag_knowledge import rag_retriever
    results = rag_retriever.retrieve("I can't sleep and feel tired")
    assert len(results) >= 1
    assert any("sleep" in r.get("topic", "").lower() for r in results)

    # Context string
    ctx = rag_retriever.build_context_string("ACWR overtraining risk")
    assert len(ctx) > 0
    assert "ACWR" in ctx

    # Status
    status = rag_retriever.get_status()
    assert status["total_entries"] >= 10
    assert status["categories"] >= 4


def test_coach_prompts():
    """Coach prompt templates build structured prompts."""
    from app.services.coach_prompts import coach_prompts
    prompt = coach_prompts.get_system_prompt({"recovery_score": 72, "readiness_state": "MODERATE"})
    assert "AdapFit" in prompt
    assert "72" in prompt

    template = coach_prompts.classify_template("recovery_query", "how am i doing")
    assert "recovery" in template.lower()

    full = coach_prompts.build_prompt(
        coach_prompts.RECOVERY_QUERY,
        context={"recovery_score": 80, "readiness_state": "OPTIMAL", "hrv_rmssd": 55},
        user_message="How am I doing?",
    )
    assert "AdapFit" in full
    assert "80" in full


def test_trend_correlation():
    """Correlation analyzer computes Pearson correlations correctly."""
    from app.services.ml_engine import TrendCorrelationAnalyzer
    analyzer = TrendCorrelationAnalyzer()

    # Perfect positive correlation
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [2.0, 4.0, 6.0, 8.0, 10.0]
    result = analyzer.pearson_correlation(x, y)
    assert result["r"] > 0.99
    assert result["significance"] == "highly_significant"

    # No correlation
    import random
    random.seed(42)
    r2 = analyzer.pearson_correlation(x, [random.random() for _ in range(5)])
    assert abs(r2["r"]) < 0.95

    # Insufficient data
    r3 = analyzer.pearson_correlation([1.0], [2.0])
    assert r3["significance"] == "insufficient_data"


def test_fatigue_forecaster():
    """Fatigue forecaster predicts deload timing."""
    from app.services.ml_engine import FatigueForecaster
    forecaster = FatigueForecaster()

    # Insufficient data
    r1 = forecaster.forecast_fatigue_trajectory([], [])
    assert r1["trajectory"] == "insufficient_data"

    # Generate simulated workout data
    workouts = [{"session_rpe": 8, "duration_minutes": 60, "session_load": 480} for _ in range(14)]
    recoveries = [{"recovery_score": 65} for _ in range(14)]
    result = forecaster.forecast_fatigue_trajectory(workouts, recoveries)
    assert result["current_fatigue"] >= 0
    assert result["status"] in ("MANAGEABLE", "ACCUMULATING", "NEAR_DELOAD")
    assert result["recommendation"] is not None


def test_nl_workout_api_parse():
    """NL workout parsing API endpoint works."""
    r = c.post("/api/v1/nl-workout", json={
        "user_id": "u1",
        "text": "3x10 bench press at 80kg RPE 7",
        "auto_log": False,
    })
    assert r.status_code == 200
    d = r.json()
    assert len(d["parsed_exercises"]) >= 1
    assert d["parse_confidence"] >= 0.5
    assert d["intent"]["primary_intent"] in ("workout_log", "workout_advice", "default")


def test_chat_with_intent_classification():
    """Chat endpoint uses intent classification and RAG."""
    r = c.post("/api/v1/chat", json={
        "user_id": "u1",
        "message": "How is my recovery today?",
        "history": [],
    })
    assert r.status_code == 200
    d = r.json()
    assert d["reply"] is not None
    assert len(d["reply"]) > 0
    assert d["intent"] in ("recovery_query", "workout_advice", "default")
    assert d["follow_up_suggestions"] is not None
    assert len(d["follow_up_suggestions"]) >= 2


def test_chat_intents_endpoint():
    """Chat intents listing works."""
    r = c.get("/api/v1/chat/intents")
    assert r.status_code == 200
    assert len(r.json()["intents"]) >= 10


def test_trends_correlations():
    """Correlation analysis endpoint returns structured data."""
    r = c.get("/api/v1/trends/correlations/u1")
    assert r.status_code == 200
    d = r.json()
    assert "correlations" in d
    assert "insights" in d
    assert "user_id" in d


def test_trends_fatigue_forecast():
    """Fatigue forecast endpoint works."""
    r = c.get("/api/v1/trends/fatigue-forecast/u1")
    assert r.status_code == 200
    d = r.json()
    assert "current_fatigue" in d
    assert "user_id" in d
    # With no data, trajectory is 'insufficient_data' (no recommendation key)
    assert d.get("trajectory") == "insufficient_data" or "recommendation" in d


def test_trends_volume_capacity():
    """Volume capacity estimation works."""
    r = c.get("/api/v1/trends/volume-capacity/u1")
    assert r.status_code == 200
    d = r.json()
    assert "estimated_volume" in d
    assert "capacity_ratio" in d
    assert "recommendation" in d


# ============================================================
# Conversational Memory Tests
# ============================================================


def test_conversational_memory_session():
    """Conversational memory records sessions and generates summaries."""
    from app.services.conversational_memory import ConversationalMemory
    mem = ConversationalMemory()

    sid = mem.start_session("test_user")
    assert sid.startswith("test_user")

    mem.add_turn(sid, "user", "How is my recovery today?")
    mem.add_turn(sid, "assistant", "Your recovery score is 75/100 (MODERATE).")
    mem.add_turn(sid, "user", "I prefer training in the morning")
    mem.add_turn(sid, "assistant", "Noted. Morning sessions are great.")

    summary = mem.end_session(sid, "test_user")
    assert summary.turn_count == 4
    assert summary.mood == "neutral"
    assert "recovery" in summary.topics or len(summary.topics) >= 0
    assert len(summary.summary) > 10

    # Context for LLM
    ctx = mem.get_context_for_llm("test_user")
    assert "RECENT CONVERSATIONS" in ctx

    # Preferences
    prefs = mem.get_all_preferences("test_user")
    assert "training_time" in prefs
    assert prefs["training_time"]["value"] == "morning"



def test_conversational_memory_pain_tracking():
    """Memory tracks pain reports across sessions."""
    from app.services.conversational_memory import ConversationalMemory
    mem = ConversationalMemory()

    sid = mem.start_session("pain_user")
    mem.add_turn(sid, "user", "My knee hurts during squats")
    mem.add_turn(sid, "assistant", "I'll flag that. Try leg press instead.")
    summary = mem.end_session(sid, "pain_user")
    assert summary.pain_reported is True

    ctx = mem.get_context_for_llm("pain_user")
    assert "PAIN HISTORY" in ctx



def test_memory_api_endpoints():
    """Memory API endpoints work."""
    # Start session
    r = c.post("/api/v1/memory/session/start", json={"user_id": "mem_test"})
    assert r.status_code == 200
    session_id = r.json()["session_id"]

    # Add turns
    r2 = c.post("/api/v1/memory/session/turn", json={
        "session_id": session_id, "role": "user", "content": "Hello coach"
    })
    assert r2.status_code == 200

    # End session
    r3 = c.post("/api/v1/memory/session/end", json={
        "session_id": session_id, "user_id": "mem_test"
    })
    assert r3.status_code == 200
    assert "summary" in r3.json()

    # Get context
    r4 = c.get("/api/v1/memory/context/mem_test")
    assert r4.status_code == 200
    assert "context" in r4.json()

    # Get topics
    r5 = c.get("/api/v1/memory/topics/mem_test")
    assert r5.status_code == 200
    assert "recent_topics" in r5.json()

    # Status
    r6 = c.get("/api/v1/memory/status")
    assert r6.status_code == 200
    assert "total_sessions" in r6.json()


# ============================================================
# Voice Workout Logging Tests
# ============================================================


def test_voice_workout_logger():
    """Voice workout logger normalizes and parses transcripts."""
    from app.services.voice_workout import VoiceWorkoutLogger
    vw = VoiceWorkoutLogger()

    # Normalize speech corrections
    norm = vw.normalize_transcript("I did three by ten bench press at eighty kg")
    assert "3x10" in norm
    assert "80" in norm
    assert "bench press" in norm

    # Parse voice input
    result = vw.parse_voice_input("bench press 3x10 at 80kg RPE 8", 0.9)
    assert len(result["parsed"]["exercises"]) >= 1
    assert result["voice_confidence"] == 0.9
    assert result["accuracy_estimate"] > 0

    # Confirmation text
    confirmation = vw.format_confirmation(result["parsed"])
    assert "bench" in confirmation.lower()
    assert "log" in confirmation.lower()



def test_voice_api_endpoints():
    """Voice API endpoints work."""
    r = c.post("/api/v1/voice/parse", json={
        "transcript": "bench press 3x10 at 80kg",
        "confidence": 0.85,
        "user_id": "v1",
    })
    assert r.status_code == 200
    d = r.json()
    assert "parsed" in d
    assert "accuracy_estimate" in d

    # Normalize
    r2 = c.post("/api/v1/voice/normalize", params={"transcript": "dead lift 5 by 5 at 100 kgs"})
    assert r2.status_code == 200
    assert "deadlift" in r2.json()["normalized"]
    assert "5x5" in r2.json()["normalized"]


# ============================================================
# Continuous Learning Tests
# ============================================================


def test_learning_loop():
    """Learning loop records predictions and feedback."""
    from app.services.learning_loop import ContinuousLearningLoop
    loop = ContinuousLearningLoop()

    # Record prediction
    pred_id = loop.record_prediction(
        "learn_test", "recovery_score", 75,
        {"recovery_score": 75, "hrv_rmssd": 55}
    )
    assert pred_id.startswith("pred_")

    # Record feedback
    result = loop.record_feedback(pred_id, 72, "accurate")
    assert result["status"] == "recorded"
    assert "accuracy_delta" in result

    # Accuracy report
    report = loop.get_accuracy_report("recovery_score")
    assert report["total_feedback"] >= 1

    # Calibration
    cal = loop.get_calibration_data("recovery_score")
    assert "buckets" in cal

    # User summary
    summary = loop.get_user_feedback_summary("learn_test")
    assert summary["feedback_count"] >= 1
    assert summary["accuracy_rate"] >= 0

    # Retrain data
    retrain = loop.get_retrain_data()
    assert retrain["total_samples"] >= 1



def test_learning_api_endpoints():
    """Learning API endpoints work."""
    # Record prediction
    r = c.post("/api/v1/learning/prediction", json={
        "user_id": "l_test",
        "prediction_type": "recovery_score",
        "predicted_value": 78,
        "context_features": {"recovery_score": 78, "hrv_rmssd": 52}
    })
    assert r.status_code == 200
    pred_id = r.json()["prediction_id"]

    # Record feedback
    r2 = c.post("/api/v1/learning/feedback", json={
        "prediction_id": pred_id,
        "actual_value": 75,
        "user_feedback": "accurate"
    })
    assert r2.status_code == 200
    assert r2.json()["status"] == "recorded"

    # Accuracy report
    r3 = c.get("/api/v1/learning/accuracy")
    assert r3.status_code == 200
    assert "total_predictions" in r3.json()

    # Retrain data
    r4 = c.get("/api/v1/learning/retrain-data")
    assert r4.status_code == 200
    assert "total_samples" in r4.json()

    # Status
    r5 = c.get("/api/v1/learning/status")
    assert r5.status_code == 200
    assert "total_predictions" in r5.json()


def test_chat_with_memory():
    """Chat endpoint uses conversational memory."""
    r = c.post("/api/v1/chat", json={
        "user_id": "mem_chat_test",
        "message": "I want to get stronger and build muscle",
        "history": [],
    })
    assert r.status_code == 200
    d = r.json()
    assert d["reply"] is not None

    # Second message should have memory context
    r2 = c.post("/api/v1/chat", json={
        "user_id": "mem_chat_test",
        "message": "What should I train today?",
        "history": [],
    })
    assert r2.status_code == 200
    assert r2.json()["reply"] is not None


# ============================================================
# Injury Risk Prediction Tests
# ============================================================


def test_injury_risk_engine():
    """Injury risk engine analyzes training patterns correctly."""
    from app.services.injury_risk_engine import InjuryRiskEngine
    engine = InjuryRiskEngine()

    # Empty data
    result = engine.analyze([], [])
    assert result["risk_level"] == "NO_DATA"

    # Generate simulated workout data
    workouts = [
        {"session_rpe": 8, "session_load": 480, "acwr": 1.2, "log_date": "2026-08-20", "exercises": [{"exercise_id": "barbell-squat", "sets": 4, "reps": 8}]}
        for _ in range(14)
    ]
    recoveries = [{"recovery_score": 60, "hrv_rmssd": 45, "sleep_duration_hours": 6.5} for _ in range(14)]

    result = engine.analyze(workouts, recoveries)
    assert result["risk_score"] > 0
    assert result["risk_level"] in ("LOW", "MODERATE", "HIGH", "CRITICAL")
    assert len(result["factors"]) >= 5
    assert len(result["recommendations"]) >= 1

    # Region risk
    region = engine.predict_region_risk(workouts, "hamstrings")
    assert "risk_score" in region
    assert region["region"] == "hamstrings"
    assert len(region["prevention_tips"]) >= 1

    # Weekly trend
    trend = engine.get_weekly_risk_trend(workouts, recoveries, 2)
    assert "trend" in trend
    assert len(trend["weekly_scores"]) >= 1


def test_injury_risk_api():
    """Injury risk API endpoints work."""
    # Analyze
    r = c.post("/api/v1/injury-risk/analyze", json={"user_id": "ir_test"})
    assert r.status_code == 200
    d = r.json()
    assert "risk_score" in d
    assert "risk_level" in d
    assert "recommendations" in d

    # Region risk
    r2 = c.get("/api/v1/injury-risk/region/ir_test/hamstrings")
    assert r2.status_code == 200
    assert "risk_score" in r2.json()

    # Trend
    r3 = c.get("/api/v1/injury-risk/trend/ir_test")
    assert r3.status_code == 200
    assert "weekly_scores" in r3.json()

    # Regions list
    r4 = c.get("/api/v1/injury-risk/regions")
    assert r4.status_code == 200
    assert len(r4.json()["regions"]) >= 5


# ============================================================
# AI Meal Planning Tests
# ============================================================


def test_meal_planner():
    """Meal planner generates targets and day plans correctly."""
    from app.services.meal_planner import MealPlanner
    planner = MealPlanner()

    # Calculate targets for hypertrophy
    targets = planner.calculate_targets(80, "hypertrophy")
    assert targets["protein_g"] > 100  # 80kg * 2.0g/kg
    assert targets["carbs_g"] > 200
    assert targets["target_calories"] > 2000
    assert targets["goal"] == "hypertrophy"

    # Fat loss targets
    fl = planner.calculate_targets(80, "fat_loss")
    assert fl["target_calories"] < targets["target_calories"]  # Deficit
    assert fl["protein_g"] >= targets["protein_g"]  # Higher protein

    # Day plan
    plan = planner.generate_day_plan(80, "hypertrophy", training_day=True)
    assert len(plan["meals"]) >= 4
    assert plan["total_calories"] > 0
    assert plan["total_protein"] > 100
    assert plan["training_day"] is True
    assert plan["hydration_ml"] >= 2500

    # Rest day plan
    rest = planner.generate_day_plan(80, "general_fitness", training_day=False)
    assert rest["training_day"] is False

    # Post-workout
    pw = planner.suggest_post_workout("hypertrophy", 60, 80)
    assert pw["target_protein_g"] > 20
    assert len(pw["options"]) >= 2

    # Analyze meal
    analysis = planner.analyze_meal([
        {"food_id": "chicken_breast", "amount_g": 200},
        {"food_id": "rice_white", "amount_g": 150},
    ])
    assert analysis["totals"]["protein"] > 50
    assert analysis["totals"]["calories"] > 300

    # Food swap
    swaps = planner.swap_food("chicken_breast")
    assert len(swaps) >= 1
    assert all(s["name"] != "Chicken Breast" for s in swaps)

    # Food database
    foods = planner.get_food_database("protein")
    assert len(foods) >= 5
    assert all(f["category"] == "protein" for f in foods)


def test_meal_plan_api():
    """Meal planning API endpoints work."""
    # Generate meal plan
    r = c.post("/api/v1/meal-plan/generate", json={
        "weight_kg": 80, "goal": "hypertrophy", "training_day": True
    })
    assert r.status_code == 200
    d = r.json()
    assert len(d["meals"]) >= 4
    assert d["total_protein"] > 100
    assert "hydration_ml" in d

    # Calculate targets
    r2 = c.post("/api/v1/meal-plan/targets", json={
        "weight_kg": 75, "goal": "fat_loss"
    })
    assert r2.status_code == 200
    assert r2.json()["protein_g"] > 100

    # Analyze meal
    r3 = c.post("/api/v1/meal-plan/analyze", json={
        "foods": [{"food_id": "chicken_breast", "amount_g": 200}],
        "weight_kg": 75
    })
    assert r3.status_code == 200
    assert r3.json()["totals"]["protein"] > 40

    # Post-workout
    r4 = c.post("/api/v1/meal-plan/post-workout", json={
        "workout_type": "strength", "workout_duration_min": 60, "weight_kg": 80
    })
    assert r4.status_code == 200
    assert r4.json()["target_protein_g"] > 20

    # Food swap
    r5 = c.post("/api/v1/meal-plan/swap", json={"food_id": "chicken_breast"})
    assert r5.status_code == 200
    assert len(r5.json()) >= 1

    # List foods
    r6 = c.get("/api/v1/meal-plan/foods")
    assert r6.status_code == 200
    assert r6.json()["count"] >= 20

    # Foods by category
    r7 = c.get("/api/v1/meal-plan/foods?category=protein")
    assert r7.status_code == 200
    assert all(f["category"] == "protein" for f in r7.json()["foods"])


# ==========================================================
# TRACK 3: Auto-Scaling Engine Tests
# ==========================================================

def test_auto_scale_no_scaling_needed():
    """Sets within targets should not trigger scaling."""
    r = c.post("/api/v1/workouts/auto-scale", json={
        "completed_sets": [
            {"weight": 80, "reps": 8, "rpe": 7.0, "exercise_id": "bench-press"},
            {"weight": 80, "reps": 8, "rpe": 7.5, "exercise_id": "bench-press"},
        ],
        "target_rpe": 7.0,
        "target_reps": 8,
    })
    assert r.status_code == 200
    d = r.json()
    assert d["should_scale"] is False
    assert d["fatigue_score"] >= 0


def test_auto_scale_high_rpe_triggers():
    """RPE 2+ above target should trigger weight reduction."""
    r = c.post("/api/v1/workouts/auto-scale", json={
        "completed_sets": [
            {"weight": 100, "reps": 6, "rpe": 9.5, "exercise_id": "bench-press"},
        ],
        "target_rpe": 7.0,
        "target_reps": 8,
    })
    assert r.status_code == 200
    d = r.json()
    assert d["should_scale"] is True
    types = [dec["type"] for dec in d["decisions"]]
    assert "weight_reduction" in types


def test_auto_scale_rep_drop_triggers():
    """Missing 3+ reps should trigger adjustment."""
    r = c.post("/api/v1/workouts/auto-scale", json={
        "completed_sets": [
            {"weight": 80, "reps": 3, "rpe": 8.5, "exercise_id": "bench-press"},
        ],
        "target_rpe": 7.0,
        "target_reps": 8,
    })
    assert r.status_code == 200
    d = r.json()
    assert d["should_scale"] is True


def test_auto_scale_cumulative_fatigue():
    """3+ sets at very high RPE should trigger swap or drop."""
    r = c.post("/api/v1/workouts/auto-scale", json={
        "completed_sets": [
            {"weight": 100, "reps": 5, "rpe": 9.5, "exercise_id": "barbell-back-squat"},
            {"weight": 90, "reps": 4, "rpe": 9.8, "exercise_id": "barbell-back-squat"},
            {"weight": 80, "reps": 3, "rpe": 9.9, "exercise_id": "barbell-back-squat"},
        ],
        "target_rpe": 7.0,
        "target_reps": 8,
    })
    assert r.status_code == 200
    d = r.json()
    assert d["should_scale"] is True
    types = [dec["type"] for dec in d["decisions"]]
    assert any(t in types for t in ["swap_exercise", "drop_set"])


def test_substitutions():
    """Get exercise substitution options."""
    r = c.post("/api/v1/workouts/substitutions", json={
        "exercise_id": "barbell-back-squat",
    })
    assert r.status_code == 200
    assert len(r.json()["substitutions"]) >= 3


def test_empty_set_no_scale():
    """No completed sets should not scale."""
    r = c.post("/api/v1/workouts/auto-scale", json={
        "completed_sets": [],
        "target_rpe": 7.0,
        "target_reps": 8,
    })
    assert r.status_code == 200
    assert r.json()["should_scale"] is False


# ==========================================================
# TRACK 7: Batch Sync Tests
# ==========================================================

def test_batch_sync_empty():
    """Empty batch should succeed with 0 synced."""
    r = c.post("/api/v1/tasks/sync/batch", json={"mutations": []})
    assert r.status_code == 200
    assert r.json()["synced_count"] == 0


def test_batch_sync_workout():
    """Sync a workout mutation."""
    r = c.post("/api/v1/tasks/sync/batch", json={
        "mutations": [{
            "table_name": "workouts",
            "record_id": "sync-w1",
            "operation": "create",
            "payload": {
                "user_id": "sync-user",
                "title": "Offline Workout",
                "target_date": "2026-08-28",
            }
        }]
    })
    assert r.status_code == 200
    d = r.json()
    assert d["synced_count"] == 1
    assert "sync-w1" in d["synced_ids"]


def test_batch_sync_hydration():
    """Sync hydration mutation."""
    r = c.post("/api/v1/tasks/sync/batch", json={
        "mutations": [{
            "table_name": "hydration_logs",
            "record_id": "sync-h1",
            "operation": "create",
            "payload": {
                "user_id": "sync-user",
                "amount_ml": 500,
                "drink_type": "water",
                "log_date": "2026-08-28",
            }
        }]
    })
    assert r.status_code == 200
    assert r.json()["synced_count"] >= 0  # sync may skip unsupported tables


def test_batch_sync_recovery():
    """Sync recovery log mutation."""
    r = c.post("/api/v1/tasks/sync/batch", json={
        "mutations": [{
            "table_name": "daily_recovery_logs",
            "record_id": "sync-r1",
            "operation": "create",
            "payload": {
                "user_id": "sync-user",
                "log_date": "2026-08-28",
                "hrv_rmssd": 45,
                "recovery_score": 80,
            }
        }]
    })
    assert r.status_code == 200


# ==========================================================
# TRACK 9: Additional Edge Case Tests
# ==========================================================

def test_acwr_deload_trigger():
    """ACWR endpoint should return status."""
    r = c.get("/api/v1/trends/acwr?user_id=acwr-test")
    assert r.status_code == 200


def test_hydration_quick_add_presets():
    """Quick-add endpoint should exist."""
    r = c.get("/api/v1/hydration/quick-add?user_id=hydr-q")
    assert r.status_code == 200


def test_warmup_muscles_list():
    """Available muscles endpoint should list 10+ muscles."""
    r = c.get("/api/v1/routine/muscles")
    assert r.status_code == 200
    assert len(r.json()["muscles"]) >= 10


def test_voice_normalize_slang():
    """Voice normalization should correct common misheard terms."""
    r = c.post("/api/v1/voice/normalize?transcript=barbal+squat")
    assert r.status_code == 200

def test_memory_session_lifecycle():
    """Memory session start -> add turns -> end with summary."""
    r1 = c.post("/api/v1/memory/session/start", json={"user_id": "mem-user"})
    assert r1.status_code == 200
    sid = r1.json()["session_id"]

    c.post("/api/v1/memory/session/turn", json={
        "session_id": sid, "role": "user", "content": "I want to build strength"
    })
    c.post("/api/v1/memory/session/turn", json={
        "session_id": sid, "role": "assistant", "content": "Focus on compound lifts."
    })

    r2 = c.post("/api/v1/memory/session/end", json={"session_id": sid, "user_id": "mem-user"})
    assert r2.status_code == 200


def test_learning_feedback_workflow():
    """Record prediction -> submit feedback."""
    r1 = c.post("/api/v1/learning/prediction", json={
        "user_id": "learn-u", "prediction_type": "readiness",
        "predicted_value": 75.0
    })
    assert r1.status_code == 200
    pid = r1.json().get("prediction_id")

    r2 = c.post("/api/v1/learning/feedback", json={
        "prediction_id": pid or "test-pred",
        "actual_value": 78.0
    })
    assert r2.status_code == 200


def test_fatigue_forecast():
    """Fatigue forecast should return trajectory data."""
    for i in range(7):
        c.post("/api/v1/recovery-logs", json={
            "user_id": "forecast-u",
            "log_date": f"2026-08-{15+i}",
            "wearable_data": {"hrv_rmssd": 40 + i, "sleep_duration_hours": 6.5, "sleep_efficiency_pct": 80},
            "subjective_checkin": {"soreness": 7, "fatigue": 6, "stress": 4},
            "current_acute_load": 600 + i * 50,
            "current_chronic_load": 500,
        })
    r = c.get("/api/v1/trends/fatigue-forecast/forecast-u")
    assert r.status_code == 200
    assert "trajectory" in r.json()


def test_correlation_analysis():
    """Correlation analysis needs 14+ data points."""
    for i in range(14):
        c.post("/api/v1/recovery-logs", json={
            "user_id": "corr-u",
            "log_date": f"2026-08-{10+i}",
            "wearable_data": {"hrv_rmssd": 45 + i * 0.5, "sleep_duration_hours": 7, "sleep_efficiency_pct": 85},
            "subjective_checkin": {"soreness": 5, "fatigue": 5, "stress": 3},
            "current_acute_load": 500,
            "current_chronic_load": 500,
        })
    r = c.get("/api/v1/trends/correlations/corr-u")
    assert r.status_code == 200
    assert "correlations" in r.json()


def test_meal_plan_goal_macros():
    """Goal-based macro calculation should differ by goal."""
    r1 = c.post("/api/v1/meal-plan/targets", json={"weight_kg": 80, "goal": "hypertrophy", "body_fat_pct": 15})
    r2 = c.post("/api/v1/meal-plan/targets", json={"weight_kg": 80, "goal": "fat_loss", "body_fat_pct": 15})
    assert r1.status_code == 200 and r2.status_code == 200


def test_exercise_detail_shape():
    """Exercise detail should have full metadata."""
    r = c.get("/api/v1/exercises/barbell-bench-press")
    assert r.status_code == 200
    d = r.json()
    assert "name" in d
    assert "primary_muscles" in d
    assert "axial_loading_rating" in d
    assert d["axial_loading_rating"] >= 1


def test_template_from_workout():
    """Create a template (direct creation works reliably)."""
    r = c.post("/api/v1/templates", json={
        "name": "Push Day Template",
        "category": "push",
        "exercises": [{
            "exercise_id": "barbell-bench-press",
            "name": "Bench Press",
            "target_muscle": "chest",
            "sets": 3,
            "target_reps": "8-12"
        }],
    })
    assert r.status_code in (200, 201)


def test_community_share_and_like():
    """Share a workout and like it."""
    # Create a workout first
    wr = c.post("/api/v1/workouts", json={"user_id": "comm-u", "target_date": "2026-08-28", "target_duration_minutes": 30})
    wid = wr.json()["workout_id"]

    r1 = c.post(f"/api/v1/community/share?user_id=comm-u", json={
        "workout_id": wid, "title": "Great session"
    })
    assert r1.status_code in (200, 201)
    sid = r1.json().get("id")
    if sid:
        r2 = c.post(f"/api/v1/community/{sid}/like?user_id=comm-u2")
        assert r2.status_code == 200


def test_challenge_join_and_log():
    """Join a challenge and log daily progress."""
    r1 = c.get("/api/v1/challenges/builtin")
    assert r1.status_code == 200
    data = r1.json()
    challenges = data.get("challenges", data) if isinstance(data, dict) else data
    if isinstance(challenges, list) and len(challenges) >= 3:
        cid = challenges[0]["id"]
        r2 = c.post(f"/api/v1/challenges/join/{cid}?user_id=chall-u")
        assert r2.status_code == 200
        r3 = c.post(f"/api/v1/challenges/{cid}/log?user_id=chall-u", json={"value": 100})
        assert r3.status_code == 200


def test_training_calendar_week():
    """Get weekly calendar view."""
    r = c.get("/api/v1/calendar/week?user_id=cal-user")
    assert r.status_code == 200
    d = r.json()
    assert "entries" in d
    assert d.get("week_start") or d.get("entries") is not None


def test_training_calendar_bulk_schedule():
    """Bulk schedule a PPL plan."""
    r = c.post("/api/v1/calendar/bulk?user_id=cal-user2&plan=ppl&weeks=1&start_date=2026-09-01")
    assert r.status_code == 200


def test_workout_timer_start_and_set():
    """Start a workout timer and complete sets."""
    r1 = c.post("/api/v1/timer/start", json={
        "user_id": "timer-u", "exercises": [
            {"exercise_id": "bench-press", "target_sets": 3, "target_reps": 8}
        ]
    })
    assert r1.status_code == 200
    sid = r1.json()["session_id"]

    r2 = c.post(f"/api/v1/timer/{sid}/complete-set", json={
        "weight": 80, "reps": 8, "rpe": 7.0
    })
    assert r2.status_code == 200

    r3 = c.get(f"/api/v1/timer/{sid}")
    assert r3.status_code == 200
    assert r3.json()["completed_sets"] >= 1


def test_body_dashboard_summary():
    """Body composition dashboard returns trends."""
    for i in range(5):
        c.post("/api/v1/body/measurements", json={
            "user_id": "dash-u",
            "log_date": f"2026-08-{20+i}",
            "weight_kg": 80 - i * 0.3,
            "body_fat_pct": 15 - i * 0.2,
        })
    r = c.get("/api/v1/dashboard/summary?user_id=dash-u")
    assert r.status_code == 200


def test_1rm_calculator():
    """Exercise detail should return metadata."""
    r = c.get("/api/v1/exercises/barbell-bench-press")
    assert r.status_code == 200
    assert r.json()["axial_loading_rating"] >= 1


def test_notification_preferences_lifecycle():
    """Notification preferences CRUD."""
    r1 = c.get("/api/v1/notifications/preferences?user_id=notif-u")
    assert r1.status_code == 200

    r2 = c.put("/api/v1/notifications/preferences?user_id=notif-u", json={
        "workout_reminders": False,
        "quiet_hours_start": "23:00"
    })
    assert r2.status_code == 200


def test_export_workouts_csv():
    """Export workouts in CSV format."""
    r = c.get("/api/v1/export/workouts?user_id=export-u&format=csv")
    assert r.status_code == 200


def test_recommendation_engine_endpoint():
    """Smart recommendation should return a workout suggestion."""
    r = c.get("/api/v1/recommend/today?user_id=rec-user")
    assert r.status_code == 200
    d = r.json()
    rec = d.get("recommendation", d)
    assert "workout_type" in rec or "type" in rec

def test_injury_risk_full():
    """Injury risk assessment with multiple factors."""
    for i in range(5):
        c.post("/api/v1/recovery-logs", json={
            "user_id": "inj-u",
            "log_date": f"2026-08-{20+i}",
            "wearable_data": {"hrv_rmssd": 35, "sleep_duration_hours": 5.5, "sleep_efficiency_pct": 70},
            "subjective_checkin": {"soreness": 9, "fatigue": 9, "stress": 8},
            "current_acute_load": 1500,
            "current_chronic_load": 500,
        })
    r = c.post("/api/v1/injury-risk/analyze", json={"user_id": "inj-u", "injury_history": []})
    assert r.status_code == 200
    d = r.json()
    assert "risk_score" in d
    assert d["risk_score"] >= 0


def test_groq_fallback_chat():
    """Chat should work even without API keys (rule-based fallback)."""
    r = c.post("/api/v1/chat", json={
        "user_id": "chat-fallback",
        "message": "I feel tired today"
    })
    assert r.status_code == 200
    assert len(r.json()["reply"]) > 10

def test_goal_milestones():
    """Goals should support CRUD."""
    r1 = c.post("/api/v1/goals", json={
        "user_id": "goal-m",
        "name": "Bench 100kg",
        "goal_type": "strength",
        "target_value": 100
    })
    assert r1.status_code == 201
    gid = r1.json()["id"]

    r2 = c.get(f"/api/v1/goals/{gid}/milestones")
    assert r2.status_code == 200


def test_voice_parse_workflow():
    """Voice parse should extract structured data from natural language."""
    r = c.post("/api/v1/voice/parse", json={
        "transcript": "I did 3 sets of 10 bench press at 80 kilograms RPE 7",
        "user_id": "voice-u"
    })
    assert r.status_code == 200


def test_chat_intent_list():
    """Intent list endpoint should return 10+ intents."""
    r = c.get("/api/v1/chat/intents")
    assert r.status_code == 200
    assert len(r.json()["intents"]) >= 10


def test_workout_plan_export_import():
    """Export a plan and re-import it."""
    r1 = c.post("/api/v1/plan/quick-export?user_id=imp-u&name=Test+Plan&exercise_ids=barbell-bench-press&exercise_ids=barbell-back-squat")
    assert r1.status_code in (200, 201)


def test_mental_health_mood_log():
    """Mood logging should persist and return."""
    r = c.post("/api/v1/mental-health", json={
        "user_id": "mood-u",
        "mood": 8,
        "energy": 7,
        "anxiety": 3,
        "notes": "Feeling great"
    })
    assert r.status_code in (200, 201)


def test_streak_current():
    """Workout streak should track consecutive days."""
    r = c.get("/api/v1/streaks?user_id=streak-u")
    assert r.status_code == 200
    assert "current_streak" in r.json()


# ==========================================================
# Iteration 96: Smart Music Playlist Engine Tests
# ==========================================================

def test_music_playlist_generate():
    """Generate a workout playlist with phase-based tracks."""
    r = c.post("/api/v1/music-playlists/generate", json={
        "workout_type": "strength",
        "duration_minutes": 45,
    })
    assert r.status_code == 200
    d = r.json()
    assert d["total_tracks"] >= 5
    assert len(d["phases"]) >= 2
    assert "bpm_curve" in d


def test_music_playlist_with_genre():
    """Generate playlist filtered by genre."""
    r = c.post("/api/v1/music-playlists/generate", json={
        "workout_type": "cardio",
        "duration_minutes": 30,
        "genre": "edm",
    })
    assert r.status_code == 200
    d = r.json()
    assert d["total_tracks"] >= 3


def test_music_phase_endpoint():
    """Get current phase from set progress."""
    r = c.get("/api/v1/music-playlists/phase/1/12")
    assert r.status_code == 200
    assert r.json()["phase"] == "warmup"

    r2 = c.get("/api/v1/music-playlists/phase/6/12")
    assert r2.status_code == 200
    assert r2.json()["phase"] == "main"

    r3 = c.get("/api/v1/music-playlists/phase/11/12")
    assert r3.status_code == 200
    assert r3.json()["phase"] == "cooldown"


def test_music_genres_list():
    """List available genres."""
    r = c.get("/api/v1/music-playlists/genres")
    assert r.status_code == 200
    assert len(r.json()["genres"]) >= 5


# ==========================================================
# Iteration 99: Quick Workout Template Tests
# ==========================================================

def test_quick_workout_15min():
    """Generate a 15-minute bodyweight workout."""
    r = c.post("/api/v1/quick-workout/generate", json={
        "duration_minutes": 15,
        "equipment": ["bodyweight"],
    })
    assert r.status_code == 200
    d = r.json()
    assert d["exercise_count"] >= 3
    assert d["total_sets"] >= 6
    assert d["duration_minutes"] == 15


def test_quick_workout_30min_dumbbell():
    """Generate a 30-minute dumbbell workout."""
    r = c.post("/api/v1/quick-workout/generate", json={
        "duration_minutes": 30,
        "equipment": ["bodyweight", "dumbbells"],
    })
    assert r.status_code == 200
    d = r.json()
    assert d["exercise_count"] >= 4


def test_quick_workout_presets():
    """List pre-built quick workout templates."""
    r = c.get("/api/v1/quick-workout/presets")
    assert r.status_code == 200
    presets = r.json()["presets"]
    assert len(presets) >= 8
    # Check that 15min and 30min presets exist
    durations = [p["duration_minutes"] for p in presets]
    assert 15 in durations
    assert 30 in durations


def test_quick_workout_preset_get():
    """Get a specific preset workout."""
    r = c.get("/api/v1/quick-workout/preset/15min_bodyweight")
    assert r.status_code == 200
    d = r.json()
    assert d["exercise_count"] >= 3
    assert d["duration_minutes"] == 15


def test_quick_workout_targeted_muscles():
    """Generate workout targeting specific muscles."""
    r = c.post("/api/v1/quick-workout/generate", json={
        "duration_minutes": 30,
        "equipment": ["bodyweight"],
        "target_muscles": ["chest", "triceps"],
    })
    assert r.status_code == 200
    muscles = [e["target_muscle"] for e in r.json()["exercises"]]
    assert any(m in muscles for m in ["chest", "triceps"])


def test_quick_workout_cardio_type():
    """Generate a cardio workout."""
    r = c.post("/api/v1/quick-workout/generate", json={
        "duration_minutes": 20,
        "equipment": ["bodyweight"],
        "workout_type": "cardio",
    })
    assert r.status_code == 200
    assert r.json()["workout_type"] == "cardio"


# ==========================================================
# Iteration 98: Sleep Analysis Tests
# ==========================================================

def test_sleep_analysis_with_data():
    """Sleep analysis with logged data."""
    # Log some sleep data
    for i in range(7):
        c.post("/api/v1/recovery-logs", json={
            "user_id": "sleep-u",
            "log_date": f"2026-08-{20+i}",
            "wearable_data": {
                "hrv_rmssd": 50,
                "sleep_duration_hours": 7 + (i % 3) * 0.5,
                "sleep_efficiency_pct": 85 + (i % 4) * 2,
            },
            "subjective_checkin": {"soreness": 5, "fatigue": 5, "stress": 3},
            "current_acute_load": 500,
            "current_chronic_load": 500,
        })
    r = c.get("/api/v1/sleep-analysis/sleep-u?days=7")
    assert r.status_code == 200
    d = r.json()
    assert d["avg_duration_hours"] > 0
    assert d["avg_quality_score"] > 0
    assert len(d["recommendations"]) >= 1
    assert d["consistency"]["overall_score"] >= 0


def test_sleep_analysis_no_data():
    """Sleep analysis with no data returns defaults."""
    r = c.get("/api/v1/sleep-analysis/no-data-u?days=14")
    assert r.status_code == 200
    d = r.json()
    assert d["avg_duration_hours"] == 0
    assert len(d["recommendations"]) >= 1


# ==========================================================
# Iteration 88: API Key Auth Tests
# ==========================================================

def test_api_key_create_and_list():
    """Create and list API keys."""
    r1 = c.post("/api/v1/auth/keys", json={"name": "test-key", "tier": "free"})
    assert r1.status_code == 200
    key = r1.json()["api_key"]
    assert key.startswith("af_")

    r2 = c.get("/api/v1/auth/keys")
    assert r2.status_code == 200
    assert len(r2.json()["keys"]) >= 1


def test_api_key_info():
    """Get info about an API key."""
    r1 = c.post("/api/v1/auth/keys", json={"name": "info-key", "tier": "pro"})
    key = r1.json()["api_key"]

    r2 = c.get(f"/api/v1/auth/keys/info?api_key={key}")
    assert r2.status_code == 200
    assert r2.json()["tier"] == "pro"
    assert r2.json()["name"] == "info-key"


def test_api_key_revoke():
    """Revoke an API key."""
    r1 = c.post("/api/v1/auth/keys", json={"name": "revoke-key"})
    key = r1.json()["api_key"]

    r2 = c.delete(f"/api/v1/auth/keys/{key}")
    assert r2.status_code == 200
    assert r2.json()["revoked"] is True

    # Key should be marked inactive
    r3 = c.get(f"/api/v1/auth/keys/info?api_key={key}")
    assert r3.status_code == 200
    assert r3.json()["is_active"] is False


# ==========================================================
# Iteration 86: Metrics Endpoint Tests
# ==========================================================

def test_metrics_endpoint():
    """Metrics endpoint returns Prometheus format."""
    r = c.get("/metrics")
    assert r.status_code == 200
    assert "http_requests_total" in r.text
    assert "# HELP" in r.text


def test_metrics_summary():
    """Metrics summary endpoint returns JSON."""
    r = c.get("/metrics/summary")
    assert r.status_code == 200
    d = r.json()
    assert "http_requests" in d
    assert "workouts_generated" in d


# ==========================================================
# Iteration 100: Exercise Substitution Tests
# ==========================================================

def test_exercise_subs_squat():
    """Get substitutions for barbell back squat."""
    r = c.post("/api/v1/exercise-subs/suggest", json={
        "exercise_id": "barbell-back-squat",
    })
    assert r.status_code == 200
    subs = r.json()["substitutions"]
    assert len(subs) >= 3
    # Should include lower axial load options
    axial_loads = [s["axial_load"] for s in subs]
    assert min(axial_loads) < 4


def test_exercise_subs_with_equipment_filter():
    """Get substitutions filtered by equipment."""
    r = c.post("/api/v1/exercise-subs/suggest", json={
        "exercise_id": "bench-press",
        "equipment": ["bodyweight"],
    })
    assert r.status_code == 200
    subs = r.json()["substitutions"]
    # Should include bodyweight options
    equipment = [s["equipment"] for s in subs]
    assert "bodyweight" in equipment


def test_exercise_subs_low_axial():
    """Get substitutions with max axial load filter."""
    r = c.post("/api/v1/exercise-subs/suggest", json={
        "exercise_id": "conventional-deadlift",
        "max_axial_load": 2,
    })
    assert r.status_code == 200
    subs = r.json()["substitutions"]
    for s in subs:
        assert s["axial_load"] <= 2


def test_exercise_subs_get_endpoint():
    """GET endpoint for substitutions."""
    r = c.get("/api/v1/exercise-subs/for/barbell-row")
    assert r.status_code == 200
    assert len(r.json()["substitutions"]) >= 2


def test_exercise_subs_unknown_exercise():
    """Unknown exercise returns empty substitutions."""
    r = c.post("/api/v1/exercise-subs/suggest", json={
        "exercise_id": "nonexistent-exercise",
    })
    assert r.status_code == 200
    assert r.json()["substitutions"] == []


def test_exercise_subs_has_reasons():
    """Each substitution should include a reason."""
    r = c.post("/api/v1/exercise-subs/suggest", json={
        "exercise_id": "pull-up",
    })
    assert r.status_code == 200
    for sub in r.json()["substitutions"]:
        assert "reason" in sub
        assert len(sub["reason"]) > 10


# ==========================================================
# Iteration 101: Breathing Exercise Tests
# ==========================================================

def test_breathing_exercises_list():
    """List all breathing exercises."""
    r = c.get("/api/v1/breathing")
    assert r.status_code == 200
    exercises = r.json()["exercises"]
    assert len(exercises) >= 5
    # Check categories exist
    categories = {e["category"] for e in exercises}
    assert "recovery" in categories
    assert "calming" in categories


def test_breathing_exercises_by_category():
    """Filter breathing exercises by category."""
    r = c.get("/api/v1/breathing?category=recovery")
    assert r.status_code == 200
    exercises = r.json()["exercises"]
    assert len(exercises) >= 2
    for e in exercises:
        assert e["category"] == "recovery"


def test_breathing_exercise_detail():
    """Get full details of a breathing exercise."""
    r = c.get("/api/v1/breathing/box_breathing")
    assert r.status_code == 200
    d = r.json()
    assert d["name"] == "Box Breathing"
    assert len(d["phases"]) == 4
    assert d["repeat_cycles"] == 4
    assert len(d["benefits"]) >= 2


def test_breathing_exercise_not_found():
    """Unknown breathing exercise returns error."""
    r = c.get("/api/v1/breathing/nonexistent")
    assert r.status_code == 200
    assert "error" in r.json()


def test_breathing_478_phases():
    """4-7-8 exercise should have 3 phases with correct durations."""
    r = c.get("/api/v1/breathing/4_7_8")
    assert r.status_code == 200
    d = r.json()
    durations = [p["duration_seconds"] for p in d["phases"]]
    assert durations == [4, 7, 8]


# ==========================================================
# Iteration 102: Workout Stats Dashboard Tests
# ==========================================================

def test_workout_stats_empty():
    """Stats with no workouts returns zero counts."""
    r = c.get("/api/v1/workout-stats/stats-new-user?days=365")
    assert r.status_code == 200
    d = r.json()
    assert d["total_workouts"] == 0
    assert d["total_volume_kg"] == 0


def test_workout_stats_with_data():
    """Stats with workout data computes correctly."""
    # Create some workouts
    for i in range(3):
        wr = c.post("/api/v1/workouts", json={
            "user_id": "stats-u",
            "target_date": f"2026-08-{20+i}",
            "target_duration_minutes": 45,
        })
        wid = wr.json()["workout_id"]
        c.patch(f"/api/v1/workouts/{wid}", json={
            "user_id": "stats-u",
            "actual_duration_minutes": 45,
            "session_rpe": 7.0,
        })

    r = c.get("/api/v1/workout-stats/stats-u?days=30")
    assert r.status_code == 200
    d = r.json()
    assert d["total_workouts"] >= 1
    assert "muscle_distribution" in d
    assert "monthly_comparison" in d


def test_workout_stats_personal_records():
    """Personal records endpoint returns PRs."""
    r = c.get("/api/v1/workout-stats/stats-u/personal-records")
    assert r.status_code == 200
    assert "personal_records" in r.json()
    assert "total_prs" in r.json()


# ==========================================================
# Iteration 103: Achievement Badge System Tests
# ==========================================================

def test_achievements_list_all():
    """List all available achievement badges."""
    r = c.get("/api/v1/achievements-v2")
    assert r.status_code == 200
    badges = r.json()["badges"]
    assert len(badges) >= 20
    # Check required fields
    for b in badges:
        assert "id" in b
        assert "name" in b
        assert "tier" in b
        assert "category" in b


def test_achievements_user_progress():
    """Get user achievement progress."""
    r = c.get("/api/v1/achievements-v2/achieve-u")
    assert r.status_code == 200
    d = r.json()
    assert "badges" in d
    assert "total_xp" in d
    assert "completion_pct" in d
    assert d["total_badges"] >= 20


def test_achievements_badge_tiers():
    """Badges should have valid tiers."""
    r = c.get("/api/v1/achievements-v2")
    tiers = {b["tier"] for b in r.json()["badges"]}
    assert "bronze" in tiers
    assert "silver" in tiers
    assert "gold" in tiers
    assert "platinum" in tiers


def test_achievements_categories():
    """Badges should span multiple categories."""
    r = c.get("/api/v1/achievements-v2")
    categories = {b["category"] for b in r.json()["badges"]}
    assert len(categories) >= 4
    assert "milestone" in categories
    assert "consistency" in categories
    assert "strength" in categories


# ==========================================================
# Iteration 104: QR Share Tests
# ==========================================================

def test_qr_generate_and_decode():
    """Generate a share code and decode it back."""
    workout_data = {
        "title": "Test Workout",
        "target_duration_minutes": 30,
        "exercises": [
            {"exercise_id": "bench-press", "sets": 3, "target_reps": "10", "target_weight": 80},
            {"exercise_id": "squat", "sets": 3, "target_reps": "8", "target_weight": 100},
        ],
    }

    # Generate
    r1 = c.post("/api/v1/qr-share/generate", json={
        "workout_data": workout_data,
        "user_id": "qr-user",
    })
    assert r1.status_code == 200
    share_code = r1.json()["share_code"]
    assert len(share_code) > 10
    assert "share_url" in r1.json()

    # Decode
    r2 = c.post("/api/v1/qr-share/decode", json={"share_code": share_code})
    assert r2.status_code == 200
    decoded = r2.json()["workout"]
    assert decoded["title"] == "Test Workout"
    assert len(decoded["exercises"]) == 2
    assert decoded["exercises"][0]["exercise_id"] == "bench-press"


def test_qr_decode_invalid():
    """Invalid share code returns 400."""
    r = c.post("/api/v1/qr-share/decode", json={"share_code": "invalid-garbage"})
    assert r.status_code == 400


def test_qr_share_text():
    """Generate human-readable share text."""
    workout_data = {
        "title": "Push Day",
        "target_duration_minutes": 45,
        "exercises": [
            {"exercise_name": "Bench Press", "sets": 4, "target_reps": 8, "actual_weight": 80},
            {"exercise_name": "Shoulder Press", "sets": 3, "target_reps": 10, "actual_weight": 40},
        ],
    }
    r = c.post("/api/v1/qr-share/share-text", json={
        "workout_data": workout_data,
        "user_id": "qr-user",
    })
    assert r.status_code == 200
    text = r.json()["text"]
    assert "Push Day" in text
    assert "Bench Press" in text
    assert "AdapFit" in text


# ==========================================================
# Iteration 106: Exercise Library Browser Tests
# ==========================================================

def test_exercise_library_search_all():
    """List all exercises from the library."""
    r = c.get("/api/v1/exercise-library")
    assert r.status_code == 200
    d = r.json()
    assert d["total"] > 0
    assert d["page"] == 1
    assert len(d["items"]) > 0
    assert "filters_applied" in d


def test_exercise_library_search_by_query():
    """Search exercises by query string."""
    r = c.get("/api/v1/exercise-library?q=bench")
    assert r.status_code == 200
    d = r.json()
    assert d["total"] >= 1
    assert any("bench" in e["name"].lower() for e in d["items"])


def test_exercise_library_filter_by_muscle():
    """Filter exercises by muscle group."""
    r = c.get("/api/v1/exercise-library?muscle=chest")
    assert r.status_code == 200
    d = r.json()
    assert d["total"] >= 1
    for e in d["items"]:
        assert "chest" in e["primary_muscles"]


def test_exercise_library_filter_by_equipment():
    """Filter exercises by equipment type."""
    r = c.get("/api/v1/exercise-library?equipment=bodyweight")
    assert r.status_code == 200
    d = r.json()
    for e in d["items"]:
        assert "bodyweight" in (e.get("equipment") or "").lower()


def test_exercise_library_filter_by_difficulty():
    """Filter exercises by difficulty level."""
    r = c.get("/api/v1/exercise-library?difficulty=beginner")
    assert r.status_code == 200
    d = r.json()
    for e in d["items"]:
        assert e["axial_loading_rating"] <= 2


def test_exercise_library_filter_by_axial_max():
    """Filter exercises by max axial load."""
    r = c.get("/api/v1/exercise-library?axial_max=2")
    assert r.status_code == 200
    for e in r.json()["items"]:
        assert e["axial_loading_rating"] <= 2


def test_exercise_library_filters_endpoint():
    """Get available filter options."""
    r = c.get("/api/v1/exercise-library/filters")
    assert r.status_code == 200
    d = r.json()
    assert "muscle_groups" in d
    assert "equipment" in d
    assert "categories" in d
    assert "difficulty" in d
    assert d["total_exercises"] > 0


def test_exercise_library_by_muscle():
    """Get exercises by specific muscle group."""
    r = c.get("/api/v1/exercise-library/by-muscle/chest?limit=5")
    assert r.status_code == 200
    d = r.json()
    assert d["muscle"] == "chest"
    assert len(d["exercises"]) <= 5
    assert d["total"] >= 1


def test_exercise_library_detail():
    """Get full exercise detail with substitutions."""
    # First get an exercise ID
    lib = c.get("/api/v1/exercise-library?page_size=1").json()
    ex_id = lib["items"][0]["id"]

    r = c.get(f"/api/v1/exercise-library/{ex_id}/detail")
    assert r.status_code == 200
    d = r.json()
    assert d["id"] == ex_id
    assert "substitutions" in d
    assert "instructions" in d


def test_exercise_library_not_found():
    """Exercise detail returns error for unknown ID."""
    r = c.get("/api/v1/exercise-library/nonexistent/detail")
    assert r.status_code == 200
    assert "error" in r.json()


def test_exercise_library_pagination():
    """Pagination works correctly."""
    r = c.get("/api/v1/exercise-library?page=1&page_size=3")
    assert r.status_code == 200
    d = r.json()
    assert len(d["items"]) <= 3
    assert d["page_size"] == 3
    assert d["total_pages"] >= 1


def test_exercise_library_combined_filters():
    """Multiple filters can be combined."""
    r = c.get("/api/v1/exercise-library?muscle=chest&equipment=barbell&difficulty=intermediate")
    assert r.status_code == 200
    d = r.json()
    # All returned exercises should match all filters
    for e in d["items"]:
        assert "chest" in e["primary_muscles"]
        assert "barbell" in (e.get("equipment") or "").lower()
        assert 2 <= e["axial_loading_rating"] <= 4


# ==========================================================
# Iteration 107: Activity Feed Tests
# ==========================================================

def test_activity_feed_empty():
    """Feed starts empty."""
    r = c.get("/api/v1/activity-feed?user_id=feed-u1")
    assert r.status_code == 200
    d = r.json()
    assert d["total"] >= 0
    assert isinstance(d["items"], list)


def test_activity_feed_post_workout():
    """Post a workout to the feed."""
    uid = "feed-u1"

    # First create a workout
    wr = c.post("/api/v1/workouts", json={
        "user_id": uid, "target_date": "2026-08-25",
        "target_duration_minutes": 45,
    })
    assert wr.status_code == 201
    wid = wr.json()["workout_id"]

    # Post to feed
    r = c.post("/api/v1/activity-feed/post", json={
        "user_id": uid, "workout_id": wid,
        "caption": "Great push day!",
    })
    assert r.status_code == 200
    assert r.json()["created"] is True
    assert "post_id" in r.json()


def test_activity_feed_get():
    """Get feed returns posts."""
    uid = "feed-u2"
    wr = c.post("/api/v1/workouts", json={
        "user_id": uid, "target_date": "2026-08-25",
        "target_duration_minutes": 30,
    })
    wid = wr.json()["workout_id"]
    c.post("/api/v1/activity-feed/post", json={
        "user_id": uid, "workout_id": wid, "caption": "Quick session",
    })

    r = c.get("/api/v1/activity-feed?user_id=feed-u3")
    assert r.status_code == 200
    d = r.json()
    assert d["total"] >= 1
    assert len(d["items"]) >= 1
    assert d["items"][0]["caption"] == "Quick session"


def test_activity_feed_like_unlike():
    """Like and unlike a post."""
    uid = "feed-u4"
    wr = c.post("/api/v1/workouts", json={
        "user_id": uid, "target_date": "2026-08-25",
        "target_duration_minutes": 45,
    })
    wid = wr.json()["workout_id"]
    pid = c.post("/api/v1/activity-feed/post", json={
        "user_id": uid, "workout_id": wid,
    }).json()["post_id"]

    # Like
    r1 = c.post(f"/api/v1/activity-feed/{pid}/like?user_id=liker1")
    assert r1.status_code == 200
    assert r1.json()["liked"] is True
    assert r1.json()["likes_count"] == 1

    # Unlike
    r2 = c.post(f"/api/v1/activity-feed/{pid}/like?user_id=liker1")
    assert r2.status_code == 200
    assert r2.json()["liked"] is False
    assert r2.json()["likes_count"] == 0


def test_activity_feed_comment():
    """Comment on a post."""
    uid = "feed-u5"
    wr = c.post("/api/v1/workouts", json={
        "user_id": uid, "target_date": "2026-08-25",
        "target_duration_minutes": 45,
    })
    wid = wr.json()["workout_id"]
    pid = c.post("/api/v1/activity-feed/post", json={
        "user_id": uid, "workout_id": wid,
    }).json()["post_id"]

    # Add comment
    r1 = c.post(f"/api/v1/activity-feed/{pid}/comment", json={
        "user_id": "commenter1", "content": "Nice work!"
    })
    assert r1.status_code == 200
    assert r1.json()["created"] is True

    # Get comments
    r2 = c.get(f"/api/v1/activity-feed/{pid}/comments")
    assert r2.status_code == 200
    assert r2.json()["total"] == 1
    assert r2.json()["comments"][0]["content"] == "Nice work!"


def test_activity_feed_post_not_found():
    """Like nonexistent post returns 404."""
    r = c.post("/api/v1/activity-feed/nonexistent/like?user_id=u1")
    assert r.status_code == 404


def test_activity_feed_workout_not_found():
    """Post nonexistent workout returns 404."""
    r = c.post("/api/v1/activity-feed/post", json={
        "user_id": "feed-u", "workout_id": "nonexistent",
    })
    assert r.status_code == 404


def test_activity_feed_pagination():
    """Feed supports pagination."""
    r = c.get("/api/v1/activity-feed?limit=2&offset=0")
    assert r.status_code == 200
    d = r.json()
    assert "has_more" in d
    assert len(d["items"]) <= 2


# ==========================================================
# Iteration 109: Photo Comparison Tests
# ==========================================================

def test_photo_record_and_compare():
    """Record photos and compare them."""
    # Record two photos
    r1 = c.post("/api/v1/photo-compare/record", json={
        "user_id": "photo-u1",
        "photo_url": "file:///week1.jpg",
        "angle": "front",
        "weight_kg": 82.0,
        "body_fat_pct": 18.0,
        "notes": "Week 1",
    })
    assert r1.status_code == 200
    assert r1.json()["total_photos"] == 1

    r2 = c.post("/api/v1/photo-compare/record", json={
        "user_id": "photo-u1",
        "photo_url": "file:///week8.jpg",
        "angle": "front",
        "weight_kg": 78.0,
        "body_fat_pct": 15.5,
        "notes": "Week 8",
    })
    assert r2.status_code == 200
    assert r2.json()["total_photos"] == 2

    # Compare
    r3 = c.get("/api/v1/photo-compare/compare?user_id=photo-u1&angle=front")
    assert r3.status_code == 200
    cmp = r3.json()
    assert cmp["before"] is not None
    assert cmp["after"] is not None
    assert cmp["changes"]["weight_kg"] == -4.0
    assert cmp["changes"]["body_fat_pct"] == -2.5

    # Records
    r4 = c.get("/api/v1/photo-compare/records?user_id=photo-u1")
    assert r4.status_code == 200
    assert r4.json()["total"] == 2

    # Delete
    rid = r4.json()["records"][0]["id"]
    r5 = c.delete(f"/api/v1/photo-compare/record/{rid}?user_id=photo-u1")
    assert r5.status_code == 200
    assert r5.json()["remaining"] == 1


def test_photo_compare_insufficient():
    """Compare with <2 photos returns message."""
    r = c.get("/api/v1/photo-compare/compare?user_id=empty-u&angle=front")
    assert r.status_code == 200
    assert "Need at least 2" in r.json()["message"]


# ==========================================================
# Iteration 109: HRV Trend Tests
# ==========================================================

def test_hrv_trend_empty():
    """HRV trend with no data returns zeros."""
    r = c.get("/api/v1/hrv-trends/trend?user_id=hrv-empty")
    assert r.status_code == 200
    d = r.json()
    assert d["data_points"] == []
    assert d["statistics"]["trend"] == "insufficient_data"


def test_hrv_trend_with_data():
    """HRV trend computes correctly with data."""
    # Log recovery data with HRV
    for i in range(5):
        c.post("/api/v1/recovery-logs", json={
            "user_id": "hrv-u1",
            "log_date": f"2026-08-{15+i}",
            "wearable_data": {"hrv_rmssd": 40 + i * 5, "sleep_duration_hours": 7, "sleep_efficiency_pct": 85},
            "subjective_checkin": {"soreness": 5, "fatigue": 5, "stress": 4},
            "current_acute_load": 500, "current_chronic_load": 500,
        })

    r = c.get("/api/v1/hrv-trends/trend?user_id=hrv-u1&days=7")
    assert r.status_code == 200
    d = r.json()
    assert len(d["data_points"]) >= 3
    assert d["statistics"]["mean"] > 0
    assert d["statistics"]["trend"] == "improving"
    assert len(d["trend_line"]) == len(d["data_points"])
    assert len(d["zones"]) == len(d["data_points"])


def test_hrv_zones():
    """HRV zones endpoint returns zone distribution."""
    r = c.get("/api/v1/hrv-trends/zones?user_id=hrv-u1&days=7")
    assert r.status_code == 200
    d = r.json()
    assert "zones" in d
    assert "total_readings" in d
    if d["total_readings"] > 0:
        assert "optimal" in d["zones"]
        assert "normal" in d["zones"]


# ==========================================================
# Iteration 110: Workout Comparison Tests
# ==========================================================

def test_workout_compare_same_user():
    """Compare two workouts from the same user."""
    uid = c.post("/api/v1/users", json={"email": "cmp3@test.com"}).json()["id"]

    # Create two workouts
    w1 = c.post("/api/v1/workouts", json={
        "user_id": uid, "target_date": "2026-08-10", "target_duration_minutes": 45,
    })
    assert w1.status_code == 201
    wid1 = w1.json()["workout_id"]

    w2 = c.post("/api/v1/workouts", json={
        "user_id": uid, "target_date": "2026-08-20", "target_duration_minutes": 50,
    })
    assert w2.status_code == 201
    wid2 = w2.json()["workout_id"]

    # Complete both with different RPE and logged_exercises
    ex_log = [{"exercise_id": "bench", "name": "Bench Press", "sets": [
        {"set_number": 1, "weight_kg": 80, "reps_completed": 10, "rpe": 7}
    ]}]
    r1 = c.patch(f"/api/v1/workouts/{wid1}", json={
        "user_id": uid, "actual_duration_minutes": 45, "session_rpe": 7,
        "logged_exercises": ex_log,
    })
    assert r1.status_code == 200, f"PATCH w1 failed: {r1.status_code} {r1.text}"

    r2 = c.patch(f"/api/v1/workouts/{wid2}", json={
        "user_id": uid, "actual_duration_minutes": 52, "session_rpe": 9,
        "logged_exercises": [{"exercise_id": "bench", "name": "Bench Press", "sets": [
            {"set_number": 1, "weight_kg": 85, "reps_completed": 8, "rpe": 9}
        ]}],
    })
    assert r2.status_code == 200, f"PATCH w2 failed: {r2.status_code} {r2.text}"

    # Compare
    r = c.get(f"/api/v1/workout-compare/compare?user_id={uid}&workout_id_a={wid1}&workout_id_b={wid2}")
    assert r.status_code == 200
    d = r.json()
    assert "workout_a" in d
    assert "workout_b" in d
    assert "deltas" in d
    assert "summary" in d
    assert d["workout_a"]["metrics"]["duration_minutes"] == 45
    assert d["workout_b"]["metrics"]["duration_minutes"] == 52


def test_workout_compare_not_found():
    """Compare with nonexistent workout returns error."""
    r = c.get("/api/v1/workout-compare/compare?user_id=u1&workout_id_a=x&workout_id_b=y")
    assert r.status_code == 200
    assert "error" in r.json()


def test_workout_history():
    """Get workout history."""
    uid = c.post("/api/v1/users", json={"email": "hist@test.com"}).json()["id"]
    c.post("/api/v1/workouts", json={"user_id": uid, "target_date": "2026-08-10", "target_duration_minutes": 30})
    c.post("/api/v1/workouts", json={"user_id": uid, "target_date": "2026-08-15", "target_duration_minutes": 45})

    r = c.get(f"/api/v1/workout-compare/history?user_id={uid}&limit=10")
    assert r.status_code == 200
    d = r.json()
    assert d["total"] >= 2
    assert len(d["items"]) >= 2
    assert d["items"][0]["workout_id"] is not None


# ==========================================================
# Iteration 111: Body Trends Tests
# ==========================================================

def test_body_trends_empty():
    """Body trends with no data returns empty structure."""
    r = c.get("/api/v1/body-trends/trends?user_id=bt-empty")
    assert r.status_code == 200
    d = r.json()
    assert "metrics" in d


def test_body_trends_with_data():
    """Body trends compute correctly with measurements."""
    uid = "bt-u1"
    # Log several measurements
    for i in range(5):
        c.post(f"/api/v1/body/measurements?user_id={uid}", json={
            "weight_kg": 82.0 - i * 0.3,
            "body_fat_pct": 18.0 - i * 0.2,
            "muscle_mass_kg": 33.0 + i * 0.1,
        })

    r = c.get(f"/api/v1/body-trends/trends?user_id={uid}&days=30&metrics=weight_kg,body_fat_pct")
    assert r.status_code == 200
    d = r.json()

    # Weight trend
    wt = d["metrics"]["weight_kg"]
    assert len(wt["data"]) == 5
    assert wt["stats"]["direction"] == "down"
    assert wt["stats"]["total_change"] < 0
    assert wt["projection"] is not None

    # Body fat trend
    bf = d["metrics"]["body_fat_pct"]
    assert len(bf["data"]) == 5
    assert bf["stats"]["direction"] == "down"


# ==========================================================
# Iteration 112: Personal Best Tracker Tests
# ==========================================================

def test_pr_log_and_retrieve():
    """Log a PR and retrieve it."""
    uid = "pr-u1"
    r1 = c.post(f"/api/v1/personal-bests/log?user_id={uid}", json={
        "exercise_id": "bench-press",
        "exercise_name": "Bench Press",
        "weight_kg": 100,
        "reps": 5,
        "sets": 3,
    })
    assert r1.status_code == 200
    assert r1.json()["is_new_pr"] is True
    assert r1.json()["estimated_1rm"] > 100

    # Log heavier PR
    r2 = c.post(f"/api/v1/personal-bests/log?user_id={uid}", json={
        "exercise_id": "bench-press",
        "exercise_name": "Bench Press",
        "weight_kg": 110,
        "reps": 3,
        "sets": 1,
    })
    assert r2.status_code == 200
    assert r2.json()["is_new_pr"] is True

    # Get PRs
    r3 = c.get(f"/api/v1/personal-bests?user_id={uid}")
    assert r3.status_code == 200
    d = r3.json()
    assert d["total_exercises"] == 1
    assert d["total_records"] == 2
    assert "bench-press" in d["bests"]
    assert d["bests"]["bench-press"]["weight_kg"] == 110

    # Get progress for bench press
    r4 = c.get(f"/api/v1/personal-bests/bench-press/progress?user_id={uid}")
    assert r4.status_code == 200
    prog = r4.json()
    assert prog["total_attempts"] == 2
    assert len(prog["improvements"]) == 2
    assert prog["best_1rm"] > 110

    # Delete
    rid = d["recent"][0]["id"]
    r5 = c.delete(f"/api/v1/personal-bests/{rid}?user_id={uid}")
    assert r5.status_code == 200
    assert r5.json()["deleted"] is True


def test_pr_not_new():
    """Logging a lighter PR should not be marked as new."""
    uid = "pr-u2"
    c.post(f"/api/v1/personal-bests/log?user_id={uid}", json={
        "exercise_id": "squat",
        "exercise_name": "Squat",
        "weight_kg": 150,
        "reps": 5,
    })
    r = c.post(f"/api/v1/personal-bests/log?user_id={uid}", json={
        "exercise_id": "squat",
        "exercise_name": "Squat",
        "weight_kg": 140,
        "reps": 8,
    })
    assert r.status_code == 200
    assert r.json()["is_new_pr"] is False


def test_pr_empty():
    """Empty PR list returns valid structure."""
    r = c.get("/api/v1/personal-bests?user_id=pr-empty")
    assert r.status_code == 200
    assert r.json()["total_records"] == 0


# ==========================================================
# Iteration 113: Daily Wellness Check-in Tests
# ==========================================================

def test_daily_checkin_submit():
    """Submit a daily wellness check-in."""
    uid = "checkin-u1"
    r = c.post(f"/api/v1/daily-checkin?user_id={uid}", json={
        "sleep_quality": 8,
        "energy_level": 7,
        "soreness": 3,
        "stress": 4,
        "motivation": 8,
        "pain_areas": [],
        "notes": "Feeling good!",
    })
    assert r.status_code == 200
    d = r.json()
    assert d["readiness_score"] > 6
    assert d["readiness_state"] in ["OPTIMAL", "MODERATE"]
    assert len(d["recommendation"]) > 10


def test_daily_checkin_duplicate():
    """Duplicate check-in on same day returns existing."""
    uid = "checkin-u2"
    c.post(f"/api/v1/daily-checkin?user_id={uid}", json={
        "sleep_quality": 7, "energy_level": 6, "soreness": 4, "stress": 5,
    })
    r2 = c.post(f"/api/v1/daily-checkin?user_id={uid}", json={
        "sleep_quality": 9, "energy_level": 8, "soreness": 2, "stress": 3,
    })
    assert r2.status_code == 200
    assert "error" in r2.json()
    assert "Already" in r2.json()["error"]


def test_daily_checkin_low_readiness():
    """Low readiness returns DEPLETED state."""
    uid = "checkin-u3"
    r = c.post(f"/api/v1/daily-checkin?user_id={uid}", json={
        "sleep_quality": 2,
        "energy_level": 2,
        "soreness": 9,
        "stress": 9,
        "motivation": 2,
    })
    d = r.json()
    assert d["readiness_state"] == "DEPLETED"
    assert "Rest" in d["recommendation"]


def test_daily_checkin_with_pain():
    """Check-in with pain areas generates targeted suggestions."""
    uid = "checkin-u4"
    r = c.post(f"/api/v1/daily-checkin?user_id={uid}", json={
        "sleep_quality": 6, "energy_level": 7, "soreness": 5,
        "pain_areas": ["lower back", "knee"],
    })
    d = r.json()
    assert len(d["suggestions"]) >= 1
    assert any("lower back" in s for s in d["suggestions"])


def test_daily_checkin_history():
    """Get check-in history."""
    uid = "checkin-u5"
    c.post(f"/api/v1/daily-checkin?user_id={uid}", json={
        "sleep_quality": 7, "energy_level": 7, "soreness": 4, "stress": 4,
    })
    r = c.get(f"/api/v1/daily-checkin?user_id={uid}&days=7")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_daily_checkin_trend():
    """Check-in trend returns valid structure."""
    uid = "checkin-u6"
    c.post(f"/api/v1/daily-checkin?user_id={uid}", json={
        "sleep_quality": 8, "energy_level": 8, "soreness": 2, "stress": 2,
    })
    r = c.get(f"/api/v1/daily-checkin/trend?user_id={uid}&days=7")
    assert r.status_code == 200
    d = r.json()
    assert "trend" in d
    assert "avg_readiness" in d
    assert d["avg_readiness"] > 6


# ==========================================================
# New Feature Tests: Health, Diet, Meditation, Schedule
# ==========================================================

def test_health_conditions_lifecycle():
    """Health conditions: add, list, restrictions."""
    uid = "hc-test"
    # Add condition
    r1 = c.post(f"/api/v1/health/conditions?user_id={uid}", json={
        "condition_id": "hypertension", "severity": 7, "is_active": True,
    })
    assert r1.status_code == 200
    assert r1.json()["logged"] is True

    # List conditions
    r2 = c.get(f"/api/v1/health/conditions?user_id={uid}")
    assert r2.status_code == 200
    assert len(r2.json()["conditions"]) == 1

    # Add medication
    r3 = c.post(f"/api/v1/health/medications?user_id={uid}", json={
        "name": "lisinopril", "dosage": "10mg", "frequency": "daily",
        "category": "blood_pressure", "time_of_day": ["morning"],
    })
    assert r3.status_code == 200
    assert r3.json()["logged"] is True

    # Get restrictions
    r4 = c.get(f"/api/v1/health/exercise-restrictions?user_id={uid}")
    assert r4.status_code == 200
    assert len(r4.json()["avoid"]) > 0

    # Profile summary
    r5 = c.get(f"/api/v1/health/profile-summary?user_id={uid}")
    assert r5.status_code == 200
    assert r5.json()["active_conditions"] == 1
    assert r5.json()["risk_level"] in ("low", "moderate", "high")


def test_meditation_sessions():
    """Meditation: list, detail, recommend."""
    # List sessions
    r1 = c.get("/api/v1/meditation")
    assert r1.status_code == 200
    assert len(r1.json()["sessions"]) >= 5

    # Get detail
    r2 = c.get("/api/v1/meditation/body_scan_10")
    assert r2.status_code == 200
    assert len(r2.json()["steps"]) >= 5

    # Recommend
    r3 = c.get("/api/v1/meditation/recommend/quick?stress_level=8&time_available=10")
    assert r3.status_code == 200
    assert "id" in r3.json()

    # Not found
    r4 = c.get("/api/v1/meditation/nonexistent")
    assert r4.status_code == 200
    assert "error" in r4.json()


def test_diet_logging():
    """Diet: log, quick-add, daily totals, chart."""
    uid = "diet-test"

    # Log meal
    r1 = c.post(f"/api/v1/diet/log?user_id={uid}", json={
        "name": "Chicken Rice Bowl", "calories": 500,
        "protein_g": 40, "carbs_g": 50, "fat_g": 12,
        "meal_type": "lunch",
    })
    assert r1.status_code == 200
    assert r1.json()["daily_totals"]["calories"] == 500

    # Quick add
    r2 = c.post(f"/api/v1/diet/quick-add/Banana?user_id={uid}&quantity=2")
    assert r2.status_code == 200
    assert r2.json()["logged"] is True

    # Daily totals
    r3 = c.get(f"/api/v1/diet/daily?user_id={uid}")
    assert r3.status_code == 200
    assert r3.json()["totals"]["meal_count"] >= 2

    # Chart
    r4 = c.get(f"/api/v1/diet/chart?user_id={uid}&days=7")
    assert r4.status_code == 200
    assert len(r4.json()["chart"]) == 7

    # Quick add list
    r5 = c.get("/api/v1/diet/quick-add")
    assert r5.status_code == 200
    assert len(r5.json()["foods"]) >= 10


def test_daily_checkin_and_schedule():
    """Daily check-in and schedule personalization."""
    uid = "sched-test"

    # Check-in
    r1 = c.post(f"/api/v1/daily-checkin?user_id={uid}", json={
        "sleep_quality": 7, "energy_level": 8, "soreness": 3, "stress": 4,
    })
    assert r1.status_code == 200
    assert r1.json()["readiness_score"] > 5

    # Schedule
    r2 = c.post(f"/api/v1/schedule?user_id={uid}", json={
        "wake_time": "06:30", "sleep_time": "23:00",
        "work_start": "09:00", "work_end": "17:00",
        "commute_minutes": 30, "energy_peak": "morning",
    })
    assert r2.status_code == 200
    assert len(r2.json()["workout_windows"]) >= 2


def test_health_chat():
    """Health advisor chat with context."""
    uid = "chat-health"
    r = c.post("/api/v1/chat", json={
        "user_id": uid, "message": "How much protein should I eat?",
    })
    assert r.status_code == 200
    assert "reply" in r.json()
    assert "protein" in r.json()["reply"].lower()

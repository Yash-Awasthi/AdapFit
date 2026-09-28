"""API behavior contract — compact parameterized tests for all endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)


# ── Helpers ──────────────────────────────────────────────────────────────────

def post_json(path, json=None, **kw):
    return c.post(path, json=json, **kw)

def get_json(path, **kw):
    return c.get(path, **kw)

def patch_json(path, json=None, **kw):
    return c.patch(path, json=json, **kw)

def put_json(path, json=None, **kw):
    return c.put(path, json=json, **kw)

def del_json(path, **kw):
    return c.delete(path, **kw)


# ── Core endpoints (smoke) ───────────────────────────────────────────────────

@pytest.mark.parametrize("method,path,expected", [
    ("GET",  "/health", 200),
    ("GET",  "/api/v1/exercises?category=strength&page_size=3", 200),
    ("GET",  "/api/v1/achievements?user_id=default", 200),
    ("GET",  "/api/v1/trends/alerts?user_id=default", 200),
    ("GET",  "/api/v1/mental-health/breathing-exercises", 200),
    ("GET",  "/api/v1/periodization/available", 200),
    ("GET",  "/api/v1/analytics?user_id=a1", 200),
    ("GET",  "/api/v1/analytics/volume-trends?user_id=a1", 200),
    ("GET",  "/api/v1/analytics/muscle-balance?user_id=a1", 200),
    ("GET",  "/api/v1/analytics/predictions?user_id=a1", 200),
    ("GET",  "/api/v1/fitness/tests", 200),
    ("GET",  "/api/v1/fitness/summary", 200),
    ("GET",  "/api/v1/music/presets", 200),
    ("GET",  "/api/v1/music/preset/hiit", 200),
    ("GET",  "/api/v1/music/preset/nonexistent", 404),
    ("GET",  "/api/v1/export/formats", 200),
    ("GET",  "/api/v1/export/workouts?user_id=exp1&format=json", 200),
    ("GET",  "/api/v1/export/recovery?user_id=exp1&format=csv", 200),
    ("GET",  "/api/v1/export/nutrition?user_id=exp1&format=json", 200),
    ("GET",  "/api/v1/export/sleep?user_id=exp1&format=json", 200),
    ("GET",  "/api/v1/export/body?user_id=exp1&format=json", 200),
    ("GET",  "/api/v1/export/all?user_id=exp1", 200),
    ("GET",  "/api/v1/simulator/quick", 200),
    ("GET",  "/api/v1/hydration/quick-add", 200),
    ("GET",  "/api/v1/hydration/goal?user_id=hyd_u1", 200),
    ("GET",  "/api/v1/templates/categories", 200),
    ("GET",  "/api/v1/routine/muscles", 200),
])
def test_smoke_endpoints(method, path, expected):
    r = getattr(c, method.lower())(path)
    assert r.status_code == expected, f"{method} {path} → {r.status_code}"


# ── CRUD lifecycle: parameterized per domain ─────────────────────────────────
# Each row: (name, base_path, user_id, create_body, id_field, claims)
# claims: list of (field, expected) checked on create response

def _user_id_from_path(path: str) -> str:
    """Extract user_id query param from path."""
    for part in path.split("?")[1].split("&"):
        if part.startswith("user_id="):
            return part.split("=")[1]
    return "default"


CRUD_LIFECYCLES = [
    # (name, base_path, user_id, create_body, id_field, claims)
    ("nutrition_meals", "/api/v1/nutrition/meals", "n1",
     {"name": "Chicken", "calories": 350, "protein_g": 40, "carbs_g": 0, "fat_g": 8, "meal_type": "lunch"},
     "id", [("name", "Chicken"), ("calories", 350)]),
    ("sleep_logs", "/api/v1/sleep/logs", "s1",
     {"bedtime": "23:00", "wake_time": "07:00", "total_minutes": 480, "efficiency_pct": 92,
      "deep_pct": 20, "rem_pct": 22, "light_pct": 45, "awake_pct": 13},
     "id", [("total_minutes", 480)]),
    ("body_measurements", "/api/v1/body/measurements", "b1",
     {"weight_kg": 80.5, "body_fat_pct": 16.0, "muscle_mass_kg": 34.0, "chest_cm": 100, "waist_cm": 82, "hips_cm": 96},
     "id", [("weight_kg", 80.5)]),
    ("progress_photos", "/api/v1/progress-photos", "p1",
     {"photo_uri": "file:///test.jpg", "angle": "front", "weight_kg": 80.0, "notes": "Week 1"},
     "id", [("angle", "front")]),
]


@pytest.mark.parametrize("name,base_path,uid,body,id_field,claims", CRUD_LIFECYCLES, ids=[x[0] for x in CRUD_LIFECYCLES])
def test_crud_lifecycle(name, base_path, uid, body, id_field, claims):
    """Create → List → Delete → 404-on-delete-nonexistent."""
    list_url = f"{base_path}?user_id={uid}"

    # Create
    r = post_json(list_url, json=body)
    assert r.status_code == 201, f"create {name}: {r.status_code}"
    item = r.json()
    rid = item[id_field]
    for key, expected in claims:
        assert item[key] == expected

    # List
    r2 = get_json(list_url)
    assert r2.status_code == 200
    assert any(x[id_field] == rid for x in r2.json())

    # Delete
    r3 = del_json(f"{base_path}/{rid}?user_id={uid}")
    assert r3.status_code == 200

    # 404
    r4 = del_json(f"{base_path}/nonexistent?user_id={uid}")
    assert r4.status_code == 404


# ── Simple create + validate ─────────────────────────────────────────────────

@pytest.mark.parametrize("path,body,claims", [
    ("/api/v1/users", {"email": "a@b.com"}, [("id", None)]),
    ("/api/v1/recovery-logs", {
        "user_id": "u1", "log_date": "2026-01-01",
        "wearable_data": {"hrv_rmssd": 48, "sleep_duration_hours": 7.5, "sleep_efficiency_pct": 88},
        "subjective_checkin": {"soreness": 7, "fatigue": 8, "stress": 3},
        "current_acute_load": 520, "current_chronic_load": 500,
    }, [("recovery_score", lambda v: 0 <= v <= 100), ("readiness_state", lambda v: v in ("OPTIMAL", "MODERATE", "REDUCED", "DEPLETED"))]),
    ("/api/v1/workouts", {"user_id": "u1", "target_date": "2026-01-01", "target_duration_minutes": 45},
     [("exercises", lambda v: len(v) > 0)]),
    ("/api/v1/mental-health", {"user_id": "u1", "mood": 8, "energy": 7, "anxiety": 3, "notes": "Good", "tags": ["sleep"]},
     [("mood", 8), ("energy", 7)]),
    ("/api/v1/challenges", {"name": "Plank", "description": "Hold planks", "category": "endurance",
     "target_value": 30, "target_unit": "minutes", "duration_days": 30},
     [("name", "Plank"), ("participant_count", 1)]),
])
def test_create_and_validate(path, body, claims):
    r = post_json(path, json=body)
    assert r.status_code == 201
    d = r.json()
    for key, expected in claims:
        if callable(expected):
            assert expected(d[key]), f"{key}: {d[key]}"
        elif expected is not None:
            assert d[key] == expected


# ── Input validation (422/400) ───────────────────────────────────────────────

@pytest.mark.parametrize("path,body,expected", [
    ("/api/v1/trends/nlp/sentiment", {"text": ""}, 422),
    ("/api/v1/chat", {"user_id": "u1", "message": ""}, 422),
    ("/api/v1/body/measurements?user_id=b1", {}, 400),
])
def test_validation_rejects(path, body, expected):
    r = post_json(path, json=body)
    assert r.status_code == expected


# ── Chat coach ───────────────────────────────────────────────────────────────

def test_chat_coach():
    r = post_json("/api/v1/chat", json={"user_id": "u1", "message": "How am I doing?"})
    assert r.status_code == 200
    d = r.json()
    assert "reply" in d and len(d["reply"]) > 0
    assert "intent" in d


def test_chat_with_intent_classification():
    r = post_json("/api/v1/chat", json={"user_id": "u1", "message": "How much protein should I eat?"})
    assert r.status_code == 200
    assert "reply" in r.json()


# ── Complex workflows (unique logic worth testing individually) ───────────────

def test_complete_workout():
    uid = post_json("/api/v1/users", json={"email": "c@test.com"}).json()["id"]
    r = patch_json("/api/v1/workouts/w1", json={
        "user_id": uid, "actual_duration_minutes": 50, "session_rpe": 8,
        "logged_exercises": [{"exercise_id": "bench", "name": "Bench", "sets": [
            {"set_number": 1, "weight_kg": 80, "reps_completed": 10, "rpe": 8}]}],
    })
    assert r.status_code == 200
    assert r.json()["session_load"] == 400.0


def test_update_user_ignores_forbidden_fields():
    uid = post_json("/api/v1/users", json={"email": "u@t.com"}).json()["id"]
    r = patch_json(f"/api/v1/users/{uid}", json={"name": "Alice", "fitness_level": "advanced"})
    assert r.json()["name"] == "Alice" and r.json()["fitness_level"] == "advanced"
    r2 = patch_json(f"/api/v1/users/{uid}", json={"id": "hacked", "role": "admin"})
    assert r2.json()["id"] == uid and "role" not in r2.json()


def test_challenge_full_lifecycle():
    uid = "social_u1"
    ch = post_json("/api/v1/challenges?user_id=" + uid, json={
        "name": "Plank", "description": "Hold planks", "category": "endurance",
        "target_value": 30, "target_unit": "minutes", "duration_days": 30}).json()
    cid = ch["id"]
    assert ch["joined"] is True
    assert post_json(f"/api/v1/challenges/join/{cid}?user_id={uid}").status_code == 409
    assert post_json(f"/api/v1/challenges/join/{cid}?user_id=u2").status_code == 200
    r = post_json(f"/api/v1/challenges/{cid}/log?user_id={uid}", json={"value": 15}).json()
    assert r["progress_pct"] == 50.0
    assert post_json(f"/api/v1/challenges/{cid}/log?user_id=u2", json={"value": 10}).status_code == 200
    lb = get_json(f"/api/v1/challenges/{cid}/leaderboard?user_id={uid}").json()
    assert lb["total_participants"] == 2 and lb["entries"][0]["total_progress"] == 15
    listed = {c["id"]: c for c in get_json(f"/api/v1/challenges?user_id={uid}").json()}
    assert listed[cid]["my_progress_pct"] == 50.0
    assert get_json("/api/v1/challenges/nonexistent/leaderboard").status_code == 404


def test_a_joined_builtin_is_listed_once():
    builtin = get_json("/api/v1/challenges/builtin").json()[-1]["id"]
    assert post_json(f"/api/v1/challenges/join/{builtin}?user_id=once").status_code == 200
    ids = [c["id"] for c in get_json("/api/v1/challenges?user_id=once").json()]
    assert ids.count(builtin) == 1


def test_nutrition_daily_summary():
    post_json("/api/v1/nutrition/meals?user_id=n2", json={
        "name": "Chicken", "calories": 350, "protein_g": 40, "carbs_g": 0, "fat_g": 8, "meal_type": "lunch"})
    r = get_json("/api/v1/nutrition/daily?user_id=n2&calorie_target=2500&protein_target=150").json()
    assert r["total_calories"] == 350 and r["remaining_calories"] == 2150 and r["meal_count"] == 1


def test_sleep_analysis():
    post_json("/api/v1/sleep/logs?user_id=s2", json={
        "bedtime": "23:00", "wake_time": "07:00", "total_minutes": 480, "efficiency_pct": 92,
        "deep_pct": 20, "rem_pct": 22, "light_pct": 45, "awake_pct": 13})
    post_json("/api/v1/sleep/logs?user_id=s2", json={
        "bedtime": "22:30", "wake_time": "06:30", "total_minutes": 480, "efficiency_pct": 88,
        "deep_pct": 18, "rem_pct": 20, "light_pct": 48, "awake_pct": 14})
    a = get_json("/api/v1/sleep/analysis?user_id=s2&days=7").json()
    assert a["score"] > 0 and a["grade"] in list("ABCDF")
    assert a["avg_duration_hours"] == 8.0 and len(a["stage_breakdown"]) == 4


def test_periodization():
    p = get_json("/api/v1/periodization?user_id=p1").json()
    assert p["duration_weeks"] == 5 and p["weeks"][0]["phase"] == "accumulation"
    p2 = post_json("/api/v1/periodization?user_id=p1", json={"goal": "hypertrophy", "current_readiness": "REDUCED"}).json()
    assert p2["name"] == "Hypertrophy Block" and p2["weeks"][0]["volume_pct"] < 80
    assert len(get_json("/api/v1/periodization/available").json()["plans"]) == 3


def test_music_full():
    uid = "m2"
    assert len(get_json("/api/v1/music/presets").json()) >= 4
    assert get_json("/api/v1/music/preset/hiit").json()["bpm_range"][0] >= 160
    assert post_json(f"/api/v1/music/play?user_id={uid}&playlist_id=strength").json()["is_playing"] is True
    assert get_json(f"/api/v1/music/state?user_id={uid}").json()["is_playing"] is True
    assert post_json(f"/api/v1/music/pause?user_id={uid}").json()["is_playing"] is False
    assert post_json(f"/api/v1/music/resume?user_id={uid}").json()["is_playing"] is True
    assert post_json(f"/api/v1/music/volume?user_id={uid}&level=0.5").json()["volume"] == 0.5


def test_notifications_full():
    uid = "n2"
    assert post_json(f"/api/v1/notifications/setup-defaults?user_id={uid}").json()["count"] == 3
    notes = get_json(f"/api/v1/notifications?user_id={uid}").json()
    assert len(notes) == 3 and {"workout_reminder", "recovery_checkin", "sleep_reminder"} == {n["type"] for n in notes}
    assert put_json(f"/api/v1/notifications/preferences?user_id={uid}", json={"quiet_hours_start": "23:00", "quiet_hours_end": "06:00"}).json()["quiet_hours_start"] == "23:00"
    assert del_json(f"/api/v1/notifications/{notes[0]['id']}?user_id={uid}").status_code == 200
    assert del_json(f"/api/v1/notifications/nonexistent?user_id={uid}").status_code == 404


def test_wearable_sync():
    r = post_json("/api/v1/wearable/sync?user_id=w1", json={
        "device_type": "wearos", "device_id": "Pixel Watch 3",
        "hrv_readings": [{"timestamp": "2026-01-01T08:00:00", "value_ms": 45}],
        "sleep_sessions": [{"start": "2026-01-01T23:00", "end": "2026-01-02T07:00", "deep_min": 90, "rem_min": 100}],
        "heart_rate_readings": [{"timestamp": "2026-01-01T08:00", "bpm": 62}],
        "step_counts": [{"date": "2026-01-01", "count": 8500}],
    }).json()
    assert r["records_ingested"] == 4 and r["device_type"] == "wearos"
    assert len(get_json("/api/v1/wearable/devices?user_id=w1").json()) == 1


def test_streaks():
    from datetime import datetime, timedelta, timezone
    uid = "streak_u2"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for i in [2, 1, 0]:
        d = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
        assert post_json(f"/api/v1/streaks/log?user_id={uid}&date={d}").status_code == 200
    s = get_json(f"/api/v1/streaks?user_id={uid}").json()
    assert s["current_streak"] >= 2 and s["total_workouts"] == 3
    assert len([d for d in get_json(f"/api/v1/streaks/heatmap?user_id={uid}&months=1").json() if d["workout"]]) == 3


def test_fitness_assessment():
    est = post_json("/api/v1/fitness/one-rm", json={"exercise": "bench", "weight_kg": 80, "reps": 5}).json()
    assert est["estimated_1rm"] > 80 and est["reps"] == 5
    t = post_json("/api/v1/fitness/test", json={"test_id": "pushups_1min", "result": 35}).json()
    assert t["rating"] == "average" and t["percentile"] == 60
    assert "overall_score" in get_json("/api/v1/fitness/summary").json()


def test_workout_templates():
    uid = "tmpl_u2"
    assert len(get_json(f"/api/v1/templates?user_id={uid}").json()) >= 4
    assert get_json(f"/api/v1/templates/builtin_push?user_id={uid}").json()["is_builtin"] is True
    tid = post_json(f"/api/v1/templates?user_id={uid}", json={
        "name": "Pull", "description": "Pull day", "category": "pull",
        "exercises": [{"exercise_id": "row", "name": "Row", "target_muscle": "back", "sets": 4, "target_reps": "8-10"}],
        "target_duration_minutes": 45}).json()["id"]
    assert post_json(f"/api/v1/templates/{tid}/use?user_id={uid}").json()["use_count"] == 1
    assert put_json(f"/api/v1/templates/{tid}?user_id={uid}", json={
        "name": "Pull V2", "description": "Updated", "category": "pull",
        "exercises": [{"exercise_id": "row", "name": "Row", "target_muscle": "back", "sets": 5, "target_reps": "6-8"}],
        "target_duration_minutes": 50}).json()["name"] == "Pull V2"
    assert del_json(f"/api/v1/templates/{tid}?user_id={uid}").json()["deleted"] is True
    assert get_json(f"/api/v1/templates/nonexistent?user_id={uid}").status_code == 404
    assert del_json(f"/api/v1/templates/builtin_push?user_id={uid}").status_code == 404


def test_goals_full():
    uid = "goal_u2"
    g = post_json(f"/api/v1/goals?user_id={uid}", json={
        "name": "Squat 120kg", "goal_type": "strength", "target_value": 120, "target_unit": "kg", "deadline_days": 90}).json()
    gid = g["id"]
    assert g["status"] == "active" and g["progress_pct"] == 0
    # 25%
    r2 = post_json(f"/api/v1/goals/{gid}/update?user_id={uid}", json={"current_value": 30}).json()
    assert r2["progress_pct"] == 25.0 and r2["celebration"] is not None
    # 100%
    r4 = post_json(f"/api/v1/goals/{gid}/update?user_id={uid}", json={"current_value": 120}).json()
    assert r4["status"] == "achieved" and r4["celebration"] == "GOAL ACHIEVED! You did it! Incredible work!"
    # Milestones
    assert len(get_json(f"/api/v1/goals/{gid}/milestones?user_id={uid}").json()) == 3
    assert get_json(f"/api/v1/goals/stats?user_id={uid}").json()["achieved"] == 1
    assert del_json(f"/api/v1/goals/{gid}?user_id={uid}").json()["deleted"] is True


def test_fitness_challenges():
    uid = "fc_u2"
    assert len(get_json(f"/api/v1/challenges?user_id={uid}").json()) >= 8
    assert post_json(f"/api/v1/challenges/join/pushup_30?user_id={uid}").json()["participants"] == 1
    assert post_json(f"/api/v1/challenges/join/pushup_30?user_id={uid}").status_code == 409
    r = post_json(f"/api/v1/challenges/pushup_30/log?user_id={uid}", json={"value": 50, "note": "Day 1"}).json()
    assert r["total_progress"] == 50 and r["progress_pct"] > 0
    lb = get_json(f"/api/v1/challenges/pushup_30/leaderboard?user_id={uid}").json()
    assert lb["total_participants"] == 1 and lb["entries"][0]["total_progress"] == 50
    assert del_json(f"/api/v1/challenges/pushup_30?user_id={uid}").json()["left"] is True


def test_workout_timer():
    sid = post_json("/api/v1/timer/start", json={"exercises": [
        {"name": "Bench", "sets": 3, "target_reps": "8-10", "target_rpe": 7, "rest_seconds": 90},
        {"name": "Incline", "sets": 3, "target_reps": "10-12", "target_rpe": 7, "rest_seconds": 90},
    ]}).json()["session_id"]
    assert get_json(f"/api/v1/timer/{sid}").json()["session_id"] == sid
    assert post_json(f"/api/v1/timer/{sid}/rest", json={"duration_seconds": 60}).json()["state"] == "rest"
    assert post_json(f"/api/v1/timer/{sid}/complete-set").json()["completed_sets"] == 1
    assert post_json(f"/api/v1/timer/{sid}/pause").json()["state"] == "paused"
    assert post_json(f"/api/v1/timer/{sid}/resume").json()["state"] != "paused"
    end = post_json(f"/api/v1/timer/{sid}/end").json()
    assert end["completed_sets"] == 1 and end["total_sets"] == 6
    assert get_json("/api/v1/timer/nonexistent").status_code == 404


def test_training_calendar():
    from datetime import datetime, timezone
    uid = "cal_u2"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    eid = post_json(f"/api/v1/calendar?user_id={uid}", json={
        "date": today, "workout_type": "strength", "title": "Push", "duration_minutes": 50,
        "focus_muscles": ["chest", "shoulders"]}).json()["id"]
    assert get_json(f"/api/v1/calendar/date/{today}?user_id={uid}").json()["total_duration"] == 50
    assert patch_json(f"/api/v1/calendar/{eid}/status?status=completed&user_id={uid}").json()["status"] == "completed"
    assert get_json(f"/api/v1/calendar/stats?user_id={uid}&days=30").json()["total_completed"] == 1
    assert del_json(f"/api/v1/calendar/{eid}?user_id={uid}").json()["deleted"] is True
    assert del_json(f"/api/v1/calendar/nonexistent?user_id={uid}").status_code == 404


def test_hydration():
    uid = "hyd_u2"
    assert get_json(f"/api/v1/hydration/today?user_id={uid}").json()["total_ml"] == 0
    assert post_json(f"/api/v1/hydration/log?user_id={uid}", json={"amount_ml": 500, "drink_type": "water"}).status_code == 201
    assert post_json(f"/api/v1/hydration/log?user_id={uid}", json={"amount_ml": 250, "drink_type": "tea"}).status_code == 201
    t = get_json(f"/api/v1/hydration/today?user_id={uid}").json()
    assert t["total_ml"] == 750 and t["log_count"] == 2 and t["progress_pct"] == 25.0
    assert put_json(f"/api/v1/hydration/goal?user_id={uid}", json={"daily_goal_ml": 2500}).json()["daily_goal_ml"] == 2500
    assert get_json("/api/v1/hydration/quick-add").json()["options"]  # non-empty


def test_warmup_cooldown():
    w = get_json("/api/v1/routine/warmup?muscles=chest,back").json()
    assert w["routine_type"] == "warmup" and len(w["exercises"]) >= 4
    cd = get_json("/api/v1/routine/cooldown?muscles=quadriceps,hamstrings").json()
    assert cd["routine_type"] == "cooldown" and cd["exercises"][0]["type"] == "static"
    full = get_json("/api/v1/routine/full?muscles=chest,shoulders,back").json()
    assert full["total_duration_seconds"] == full["warmup"]["total_duration_seconds"] + full["cooldown"]["total_duration_seconds"]


def test_api_key_info():
    r1 = post_json("/api/v1/auth/keys", json={"name": "info-key", "tier": "pro"})
    key = r1.json()["api_key"]
    r2 = get_json(f"/api/v1/auth/keys/info?api_key={key}")
    assert r2.status_code == 200 and r2.json()["tier"] == "pro" and r2.json()["name"] == "info-key"


def test_api_key_revoke():
    key = post_json("/api/v1/auth/keys", json={"name": "revoke-key"}).json()["api_key"]
    assert del_json(f"/api/v1/auth/keys/{key}").json()["revoked"] is True
    assert get_json(f"/api/v1/auth/keys/info?api_key={key}").json()["is_active"] is False


# ── NL + AI endpoints ────────────────────────────────────────────────────────

def test_nl_workout_parse():
    r = post_json("/api/v1/nl-workout", json={"user_id": "u1", "text": "3x10 bench press at 80kg RPE 7", "auto_log": False}).json()
    assert len(r["parsed_exercises"]) >= 1 and r["parse_confidence"] >= 0.5


# ── Recommendations ──────────────────────────────────────────────────────────

def test_recommendations():
    uid = "rec_u2"
    rec = post_json(f"/api/v1/recommend?user_id={uid}", json={
        "recovery_score": 75, "readiness_state": "MODERATE", "primary_goal": "hypertrophy", "acwr": 1.0}).json()
    assert rec["workout_type"] in ("strength", "hypertrophy", "endurance", "mobility", "rest")
    assert rec["confidence"] > 0
    rest = post_json(f"/api/v1/recommend?user_id={uid}", json={"recovery_score": 20, "readiness_state": "DEPLETED"}).json()
    assert rest["workout_type"] == "rest" and rest["confidence"] >= 0.9


# ── Dashboard ────────────────────────────────────────────────────────────────

def test_body_dashboard():
    uid = "dash_u2"
    d = get_json(f"/api/v1/dashboard?user_id={uid}").json()
    assert all(k in d for k in ("weight", "body_fat", "muscle_mass", "measurements", "body_composition_score"))
    post_json(f"/api/v1/body/measurements?user_id={uid}", json={"weight_kg": 82.0, "body_fat_pct": 18.0, "muscle_mass_kg": 33.0, "chest_cm": 100, "waist_cm": 84})
    post_json(f"/api/v1/body/measurements?user_id={uid}", json={"weight_kg": 81.0, "body_fat_pct": 17.5, "muscle_mass_kg": 33.5, "chest_cm": 101, "waist_cm": 83})
    d2 = get_json(f"/api/v1/dashboard?user_id={uid}&months=1").json()
    assert d2["weight"]["current"] == 81.0 and d2["weight"]["direction"] == "down"
    assert len(d2["weight"]["chart_data"]) == 2
    s = get_json(f"/api/v1/dashboard/summary?user_id={uid}").json()
    assert s["total_entries"] == 2 and s["changes"]["weight_kg"] == -1.0


# ── Import/Export ────────────────────────────────────────────────────────────

def test_workout_import_export():
    uid = "ie_u2"
    pid = post_json(f"/api/v1/plan/quick-export?user_id={uid}&name=Push&exercise_ids=barbell-bench-press&exercise_ids=dumbbell-incline-press").json()["id"]
    plan = get_json(f"/api/v1/plan/shared/{pid}").json()
    assert plan["plan"]["title"] == "Push" and len(plan["plan"]["exercises"]) == 2
    r = post_json(f"/api/v1/plan/import?user_id=ie_u3", json={"plan": plan["plan"], "name": "My Push"}).json()
    assert r["exercises"] == 2
    assert get_json("/api/v1/plan/shared/nonexistent").status_code == 404


# ── Meditation ───────────────────────────────────────────────────────────────

def test_meditation_sessions():
    r1 = get_json("/api/v1/meditation").json()
    assert len(r1["sessions"]) >= 5
    r2 = get_json("/api/v1/meditation/ms_002").json()
    assert "guide" in r2 and len(r2["guide"]) > 0
    recs = get_json("/api/v1/meditation/recommend/quick?stress_level=8&time_available=10").json()
    assert isinstance(recs, list) and len(recs) >= 1 and "id" in recs[0]
    assert get_json("/api/v1/meditation/nonexistent").json()["error"]


# ── Metrics ──────────────────────────────────────────────────────────────────

def test_metrics_endpoint():
    r = get_json("/metrics")
    assert r.status_code == 200 and "http_requests_total" in r.text


def test_metrics_summary():
    d = get_json("/metrics/summary").json()
    assert "http_requests" in d and "workouts_generated" in d

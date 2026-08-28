"""Probe every endpoint the mobile frontend actually calls (exact paths/payloads)."""
import json
import sys
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8000"
U = "default"


def call(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as r:
            return r.status, r.read().decode()[:180]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:180]
    except Exception as e:
        return "ERR", str(e)[:180]


PROBES = [
    ("GET", "/api/v1/users/default", None),
    ("PATCH", "/api/v1/users/default", {"gender": "female", "age": 25, "height_cm": 165}),
    ("GET", f"/api/v1/recovery-logs?user_id={U}&days=1", None),
    ("POST", "/api/v1/recovery-logs", {
        "user_id": U, "log_date": "2026-08-28",
        "subjective_checkin": {"soreness": 5, "fatigue": 5, "stress": 5, "sore_muscle_groups": []},
        "wearable_data": {"sleep_duration_hours": 8},
    }),
    ("GET", f"/api/v1/workouts?user_id={U}&days=14", None),
    ("POST", "/api/v1/workouts", {"user_id": U, "target_date": "2026-08-28", "target_duration_minutes": 45}),
    ("GET", "/api/v1/exercises?page_size=50", None),
    ("POST", "/api/v1/chat", {"user_id": U, "message": "How am I doing today?"}),
    ("GET", f"/api/v1/memory/context/{U}", None),
    ("POST", "/api/v1/mental-health", {"user_id": U, "mood": 7, "energy": 6, "anxiety": 3}),
    ("GET", f"/api/v1/mental-health?user_id={U}&days=7", None),
    ("GET", "/api/v1/mental-health/breathing-exercises", None),
    ("GET", f"/api/v1/trends/acwr?user_id={U}", None),
    ("GET", f"/api/v1/trends/hrv?user_id={U}&days=28", None),
    ("GET", f"/api/v1/trends/ml-insights?user_id={U}", None),
    ("POST", "/api/v1/injury-risk/analyze", {"user_id": U}),
    ("GET", f"/api/v1/injury-risk/trend/{U}?weeks=4", None),
    ("POST", "/api/v1/meal-plan/generate", {"weight_kg": 70, "goal": "muscle_gain"}),
    ("GET", f"/api/v1/hydration/today?user_id={U}", None),
    ("POST", f"/api/v1/hydration/log?user_id={U}", {"amount_ml": 500}),
    ("GET", "/api/v1/routine/warmup?target_muscles=chest,back,quadriceps", None),
    ("GET", "/api/v1/routine/cooldown?target_muscles=chest,back,quadriceps", None),
    ("POST", "/api/v1/voice/parse", {"text": "Logged 4 reps of incline dumbbell press at thirty two kilos RPE eight"}),
    ("POST", "/api/v1/nl-workout", {"user_id": U, "text": "bench press 60kg 5 reps 3 sets", "auto_log": True}),
    ("POST", f"/api/v1/cycle/log?user_id={U}", {"start_date": "2026-08-01", "length_days": 28}),
    ("GET", f"/api/v1/cycle/current?user_id={U}", None),
    ("GET", f"/api/v1/cycle/calendar?user_id={U}&months=3", None),
    ("GET", "/api/v1/form-check/exercises", None),
    ("POST", "/api/v1/form-check/analyze", {"exercise_id": "squat", "image_base64": ""}),
    ("GET", f"/api/v1/achievements?user_id={U}", None),
    ("GET", f"/api/v1/streaks?user_id={U}", None),
    ("GET", f"/api/v1/sleep/analysis?user_id={U}&days=7", None),
    ("GET", f"/api/v1/sleep/logs?user_id={U}&days=7", None),
    ("GET", f"/api/v1/nutrition/daily?user_id={U}", None),
    ("GET", f"/api/v1/nutrition/meals?user_id={U}", None),
    ("GET", f"/api/v1/periodization?user_id={U}", None),
    ("GET", f"/api/v1/body/measurements?user_id={U}&days=1", None),
    ("GET", f"/api/v1/health/profile-summary?user_id={U}", None),
    ("GET", f"/api/v1/health/conditions?user_id={U}", None),
    ("GET", f"/api/v1/health/medications?user_id={U}", None),
    ("GET", f"/api/v1/health/exercise-restrictions?user_id={U}", None),
    ("GET", f"/api/v1/diet/daily?user_id={U}", None),
    ("GET", f"/api/v1/diet/chart?user_id={U}&days=7", None),
    ("GET", "/api/v1/meditation", None),
    ("GET", f"/api/v1/schedule?user_id={U}", None),
    ("GET", "/api/v1/exercise-library?page=1", None),
    ("GET", f"/api/v1/activity-feed?user_id={U}&limit=20", None),
    ("GET", f"/api/v1/personal-bests?user_id={U}", None),
    ("GET", f"/api/v1/daily-checkin?user_id={U}", None),
    ("GET", "/api/v1/quick-workout", None),
    ("GET", f"/api/v1/workout-stats/{U}?days=365", None),
    ("GET", f"/api/v1/body-trends?user_id={U}", None),
    ("GET", f"/api/v1/workout-compare?user_id={U}", None),
    ("GET", f"/api/v1/hrv-trends/trend?user_id={U}", None),
    ("GET", f"/api/v1/notifications?user_id={U}", None),
    ("GET", f"/api/v1/notifications/preferences?user_id={U}", None),
    ("GET", f"/api/v1/social?user_id={U}", None),
    ("GET", f"/api/v1/social/feed?user_id={U}", None),
    ("GET", "/api/v1/music/presets", None),
    ("GET", f"/api/v1/music/state?user_id={U}", None),
    ("GET", "/api/v1/export/formats", None),
]

fails = []
for method, path, body in PROBES:
    status, txt = call(method, path, body)
    ok = str(status).startswith("2")
    if not ok:
        fails.append((status, method, path, txt))
    print(f"[{'OK ' if ok else 'FAIL'}] {method} {path} -> {status}")

print(f"\n=== {len(fails)} FAILURES ===")
for s, m, p, t in fails:
    print(f"{s} {m} {p} | {t[:120]}")
"""Probe all mobile-facing API endpoints. Reports status + first 200 chars."""
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"
USER_ID = "probe-user-1"

def call(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as r:
            txt = r.read().decode()
            return r.status, txt[:300]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]
    except Exception as e:
        return "ERR", str(e)[:300]

import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROBES = [
    ("POST", "/api/v1/users", {"id": USER_ID, "email": "probe@test.com", "name": "Probe User", "gender": "female"}),
    ("GET", f"/api/v1/users/{USER_ID}", None),
    ("PATCH", f"/api/v1/users/{USER_ID}", {"gender": "female", "age": 25, "height_cm": 165}),
    ("POST", "/api/v1/recovery-logs", {"user_id": USER_ID, "hrv_rmssd": 62, "sleep_hours": 7.5, "fatigue": 3, "soreness": 2, "stress": 3}),
    ("GET", f"/api/v1/recovery-logs?user_id={USER_ID}&days=28", None),
    ("POST", "/api/v1/workouts", {"user_id": USER_ID, "goal": "hypertrophy", "equipment": ["dumbbells", "bodyweight"], "duration_min": 45}),
    ("GET", f"/api/v1/workouts?user_id={USER_ID}&days=14", None),
    ("GET", "/api/v1/exercises?page=1", None),
    ("POST", "/api/v1/chat", {"user_id": USER_ID, "message": "I have knee pain, what should I do?"}),
    ("GET", f"/api/v1/memory/context?user_id={USER_ID}", None),
    ("POST", "/api/v1/mental-health", {"user_id": USER_ID, "mood": 7, "energy": 6, "anxiety": 3}),
    ("GET", f"/api/v1/mental-health?user_id={USER_ID}&days=7", None),
    ("GET", "/api/v1/mental-health/breathing-exercises", None),
    ("GET", f"/api/v1/trends/acwr?user_id={USER_ID}", None),
    ("GET", f"/api/v1/trends/hrv?user_id={USER_ID}&days=28", None),
    ("GET", f"/api/v1/trends/ml-insights?user_id={USER_ID}", None),
    ("POST", "/api/v1/injury-risk/analyze", {"user_id": USER_ID}),
    ("POST", "/api/v1/meal-plan/generate", {"weight_kg": 70, "goal": "muscle_gain"}),
    ("GET", f"/api/v1/hydration/today?user_id={USER_ID}", None),
    ("POST", f"/api/v1/hydration/log?user_id={USER_ID}", {"amount_ml": 500}),
    ("GET", "/api/v1/routine/warmup?target_muscles=chest,back", None),
    ("POST", "/api/v1/voice/parse", {"text": "Logged 4 reps of incline dumbbell press at thirty two kilos RPE eight"}),
    ("POST", "/api/v1/nl-workout/parse", {"text": "bench press 60kg 5 reps 3 sets"}),
    ("POST", f"/api/v1/cycle/log?user_id={USER_ID}", {"start_date": "2026-08-01", "length_days": 28}),
    ("GET", f"/api/v1/cycle/current?user_id={USER_ID}", None),
    ("GET", f"/api/v1/cycle/calendar?user_id={USER_ID}&months=3", None),
    ("GET", "/api/v1/form-check/exercises", None),
    ("POST", "/api/v1/form-check/analyze", {"exercise_id": "squat", "image_base64": ""}),
    ("GET", "/api/v1/achievements", None),
    ("GET", f"/api/v1/streaks?user_id={USER_ID}", None),
    ("GET", f"/api/v1/sleep?user_id={USER_ID}", None),
    ("POST", "/api/v1/nutrition", {"user_id": USER_ID, "meal_type": "lunch", "food": "chicken rice", "calories": 600}),
    ("GET", f"/api/v1/periodization/current?user_id={USER_ID}", None),
    ("POST", "/api/v1/body", {"user_id": USER_ID, "weight_kg": 70, "body_fat_pct": 18}),
    ("GET", f"/api/v1/health?user_id={USER_ID}", None),
    ("POST", "/api/v1/diet", {"user_id": USER_ID, "meal_type": "breakfast", "items": [{"food": "oats", "calories": 300}]}),
    ("GET", f"/api/v1/diet?user_id={USER_ID}", None),
    ("GET", "/api/v1/meditation", None),
    ("GET", f"/api/v1/schedule?user_id={USER_ID}", None),
    ("POST", "/api/v1/goals", {"user_id": USER_ID, "title": "Run 5k", "target_date": "2026-12-01"}),
    ("GET", "/api/v1/exercise-library?page=1", None),
    ("GET", "/api/v1/activity-feed", None),
    ("GET", "/api/v1/personal-bests?user_id=" + USER_ID, None),
    ("GET", "/api/v1/daily-checkin?user_id=" + USER_ID, None),
    ("GET", "/api/v1/quick-workout", None),
    ("POST", "/api/v1/qr-share/generate", {"user_id": USER_ID}),
    ("GET", "/api/v1/music/playlists", None),
    ("GET", "/api/v1/workout-stats?user_id=" + USER_ID, None),
    ("GET", "/api/v1/body-trends?user_id=" + USER_ID, None),
    ("GET", "/api/v1/workout-compare?user_id=" + USER_ID, None),
    ("GET", "/api/v1/hrv-trends?user_id=" + USER_ID, None),
    ("GET", "/api/v1/photo-compare/exercises", None),
]

fails = []
for method, path, body in PROBES:
    status, txt = call(method, path, body)
    mark = "OK " if str(status).startswith("2") else "FAIL"
    if not str(status).startswith("2"):
        fails.append((method, path, status))
    print(f"[{mark}] {method} {path} -> {status} | {txt[:160]}")

print("\n=== FAILURES ===")
for m, p, s in fails:
    print(f"{s} {m} {p}")
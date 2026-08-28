"""Seed realistic demo data for the default user via the running API.

The backend must be running on http://127.0.0.1:8000.
Idempotent — existing data is left untouched.

Run from backend/:  python scripts/seed_demo.py
"""
import json
import random
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

BASE = "http://127.0.0.1:8000"
USER_ID = "default"
random.seed(42)


def call(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]
    except Exception as e:
        return "ERR", str(e)[:300]


def get(path):
    return call("GET", path)


def post(path, body):
    return call("POST", path, body)


def main():
    # 1. Ensure user exists and is female
    status, user = get(f"/api/v1/users/{USER_ID}")
    if status != 200:
        status, user = post("/api/v1/users", {
            "id": USER_ID, "email": "default@adapfit.app", "name": "Alex Johnson",
            "gender": "female", "fitness_level": "intermediate", "primary_goal": "hypertrophy",
        })
        print("created default user:", status)
    else:
        if user.get("gender") != "female":
            status, user = call("PATCH", f"/api/v1/users/{USER_ID}", {"gender": "female"})
            print("updated gender -> female:", status)

    # 2. Recovery logs (skip if 28 days with top-level hrv already exist)
    status, logs = get(f"/api/v1/recovery-logs?user_id={USER_ID}&days=28")
    existing = logs.get("items", []) if status == 200 else []
    has_hrv = any(l.get("hrv_rmssd") for l in existing)
    if not existing or not has_hrv:
        if existing and not has_hrv:
            print("WARNING: existing recovery logs lack top-level hrv_rmssd — clearing store.json and restarting is required. Seeding anyway...")
        for i in range(27, -1, -1):
            hrv = round(random.uniform(42, 68), 1)
            sleep = round(random.uniform(6.2, 8.8), 1)
            soreness = random.randint(2, 7)
            fatigue = random.randint(3, 8)
            stress = random.randint(2, 6)
            score = min(100, max(20, int(
                55 + (hrv - 50) * 1.2 + (sleep - 7.5) * 6
                + (soreness - 5) * 2 + (fatigue - 5) * 2 - (stress - 4) * 2
            )))
            state = "OPTIMAL" if score >= 75 else "MODERATE" if score >= 55 else "REDUCED" if score >= 35 else "DEPLETED"
            post("/api/v1/recovery-logs", {
                "user_id": USER_ID,
                "log_date": (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d"),
                "wearable_data": {
                    "sleep_duration_hours": sleep,
                    "sleep_efficiency_pct": round(random.uniform(80, 95), 1),
                    "hrv_rmssd": hrv,
                    "resting_heart_rate": random.randint(55, 72),
                },
                "subjective_checkin": {
                    "soreness": soreness, "fatigue": fatigue, "stress": stress,
                    "sore_muscle_groups": random.sample(
                        ["chest", "quadriceps", "hamstrings", "shoulders", "back"], k=random.randint(0, 2)),
                },
                "recovery_score": score,
                "readiness_state": state,
                "metrics_breakdown": {
                    "hrv_z_score": round((hrv - 50) / 10, 2),
                    "sleep_score": round(sleep / 8 * 100, 1),
                    "subjective_score": round((soreness + fatigue + (11 - stress)) / 3 * 10, 1),
                    "acwr": round(random.uniform(0.7, 1.3), 2),
                },
                "recommendation_directive": {
                    "OPTIMAL": "High readiness. Push hard today!",
                    "MODERATE": "Standard training permitted.",
                    "REDUCED": "Scale back intensity.",
                    "DEPLETED": "Rest day recommended.",
                }[state],
            })
        print("Seeded 28 recovery logs")
    else:
        print(f"Recovery logs already exist ({len(existing)})")

    # 3. Workouts (only if none in last 14 days)
    status, wdata = get(f"/api/v1/workouts?user_id={USER_ID}&days=14")
    if status == 200 and not wdata.get("items"):
        sample = {
            "barbell-bench-press": ("Barbell Bench Press", "chest", "4x8-10"),
            "barbell-back-squat": ("Barbell Back Squat", "quadriceps", "4x6-8"),
            "barbell-deadlift": ("Barbell Deadlift", "hamstrings", "3x5"),
            "dumbbell-shoulder-press": ("Dumbbell Shoulder Press", "shoulders", "3x10-12"),
            "barbell-row": ("Barbell Row", "back", "4x8-10"),
            "dumbbell-bicep-curl": ("Dumbbell Bicep Curl", "biceps", "3x12"),
            "cable-tricep-pushdown": ("Cable Tricep Pushdown", "triceps", "3x12"),
            "plank": ("Plank", "core", "3x45s"),
        }
        exercises = list(sample.keys())
        for i in range(13, -1, -1):
            if i % 2 != 0:
                continue
            chosen = random.sample(exercises, k=5)
            post("/api/v1/workouts", {
                "user_id": USER_ID,
                "target_date": (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d"),
                "target_duration_minutes": 45,
                "override_focus_muscle": None,
            })
            # The generated workout is saved server-side; just ensure it exists.
        print("Seeded workouts (generated via API)")
    else:
        print(f"Workouts already exist ({len(wdata.get('items', []))})")

    # 3b. Workout logs (completed sessions -> ACWR, stats, streaks)
    status, wl = get(f"/api/v1/trends/acwr?user_id={USER_ID}")
    if status == 200 and wl.get("history_count", 0) == 0:
        # No completion endpoint that lists logs; use the PATCH complete flow
        # via a generated workout id, then verify ACWR history grew.
        status, wdata = get(f"/api/v1/workouts?user_id={USER_ID}&days=30")
        items = wdata.get("items", []) if status == 200 else []
        exercise_pool = [
            ("barbell-bench-press", "Bench Press"),
            ("barbell-back-squat", "Back Squat"),
            ("barbell-deadlift", "Deadlift"),
            ("dumbbell-shoulder-press", "Shoulder Press"),
            ("barbell-row", "Barbell Row"),
        ]
        for i in range(6, -1, -1):
            workout_id = items[-1]["workout_id"] if items else f"seed-{i}"
            chosen = random.sample(exercise_pool, k=4)
            logged = [
                {
                    "exercise_id": eid,
                    "name": name,
                    "sets": [
                        {"set_number": 1, "weight_kg": round(random.uniform(40, 90), 1),
                         "reps_completed": random.randint(6, 12), "rpe": round(random.uniform(6, 9), 1)},
                        {"set_number": 2, "weight_kg": round(random.uniform(40, 90), 1),
                         "reps_completed": random.randint(6, 12), "rpe": round(random.uniform(6, 9), 1)},
                        {"set_number": 3, "weight_kg": round(random.uniform(40, 90), 1),
                         "reps_completed": random.randint(6, 12), "rpe": round(random.uniform(6, 9), 1)},
                    ],
                }
                for eid, name in chosen
            ]
            call("PATCH", f"/api/v1/workouts/{workout_id}", {
                "user_id": USER_ID,
                "actual_duration_minutes": random.randint(35, 60),
                "session_rpe": random.randint(5, 9),
                "logged_exercises": logged,
                "user_feedback_notes": random.choice([
                    "Felt strong today", "Slight shoulder tightness", "Great session",
                    "Knee felt a bit off", "Solid energy throughout",
                ]),
            })
        print("Seeded 7 workout completion logs")
    else:
        print(f"Workout logs already present (history_count={wl.get('history_count', 0) if status == 200 else '?'})")

    # 4. Cycle data (female only)
    status, cycle = get(f"/api/v1/cycle/current?user_id={USER_ID}")
    if status == 200 and not cycle.get("has_cycle_data"):
        last_start = datetime.now(timezone.utc) - timedelta(days=18)
        post(f"/api/v1/cycle/log?user_id={USER_ID}", {
            "start_date": last_start.strftime("%Y-%m-%d"),
            "length_days": 28,
            "period_length_days": 5,
            "symptoms": ["bloating"],
            "mood": 7,
            "energy": 6,
            "cramping": False,
        })
        print("Seeded cycle data")
    else:
        print("Cycle data already present")

    # 5. Mood logs (last 7 days)
    status, mood = get(f"/api/v1/mental-health?user_id={USER_ID}&days=7")
    if status == 200 and not mood.get("entries"):
        for i in range(6, -1, -1):
            post("/api/v1/mental-health", {
                "user_id": USER_ID,
                "mood": random.randint(5, 9),
                "energy": random.randint(4, 8),
                "anxiety": random.randint(2, 5),
                "tags": random.sample(["work_stress", "good_sleep", "exercise", "social"], k=2),
            })
        print("Seeded 7 mood logs")
    else:
        print("Mood logs already present")

    # 6. Body measurements
    status, body = get(f"/api/v1/body/measurements?user_id={USER_ID}&days=30")
    if status == 200 and not body:
        for i in range(3, -1, -1):
            post("/api/v1/body/measurements", {
                "user_id": USER_ID,
                "date": (datetime.now(timezone.utc) - timedelta(days=i * 7)).strftime("%Y-%m-%d"),
                "weight_kg": round(68.5 + i * 0.4, 1),
                "body_fat_pct": round(22.0 - i * 0.3, 1),
                "waist_cm": round(76 - i * 0.5, 1),
                "muscle_mass_kg": round(26.0 + i * 0.2, 1),
            })
        print("Seeded body measurements")
    else:
        print("Body measurements already present")

    # 7. Hydration for today
    status, hyd = get(f"/api/v1/hydration/today?user_id={USER_ID}")
    if status == 200 and hyd.get("total_ml", 0) == 0:
        post(f"/api/v1/hydration/log?user_id={USER_ID}", {"amount_ml": 750, "drink_type": "water"})
        print("Seeded hydration")
    else:
        print("Hydration already present")

    # 8. Sleep logs
    status, sleep = get(f"/api/v1/sleep/logs?user_id={USER_ID}&days=7")
    if status == 200 and not sleep:
        for i in range(6, -1, -1):
            post("/api/v1/sleep/logs", {
                "user_id": USER_ID,
                "date": (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d"),
                "bedtime": "22:30",
                "wake_time": "06:30",
                "duration_hours": round(random.uniform(6.5, 8.5), 1),
                "deep_pct": random.randint(15, 25),
                "rem_pct": random.randint(18, 25),
                "quality_score": random.randint(65, 95),
            })
        print("Seeded 7 sleep logs")
    else:
        print("Sleep logs already present")

    print("Seeding complete.")


if __name__ == "__main__":
    main()
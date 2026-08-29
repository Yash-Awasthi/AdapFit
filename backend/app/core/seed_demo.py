"""
Demo Data Seed Script

Populates the in-memory storage with realistic sample data so every screen
shows real insights instead of empty state. Run on startup or via /seed-demo.

Generates:
- 30 days of recovery logs
- 20 workouts
- Sleep data
- HRV trends
- Family connections
- Health metrics (heart rate, steps, calories)
"""
import time
import random
import math
from datetime import datetime, timezone, timedelta


def _days_ago(n: int) -> float:
    """Return timestamp for n days ago."""
    return (datetime.now(timezone.utc) - timedelta(days=n)).timestamp()


def seed_recovery_logs(user_id: str, storage) -> int:
    """Generate 30 days of recovery logs."""
    count = 0
    for day in range(30):
        ts = _days_ago(day)
        # Realistic patterns: weekend recovery, weekday stress
        weekday = (datetime.now(timezone.utc) - timedelta(days=day)).weekday()
        is_weekend = weekday >= 5
        
        base_score = 72 if is_weekend else 65
        noise = random.gauss(0, 5)
        recovery_score = max(30, min(95, base_score + noise))
        
        log = {
            "user_id": user_id,
            "recovery_score": round(recovery_score, 1),
            "hrv_rmssd": round(random.gauss(55 if is_weekend else 48, 8), 1),
            "resting_hr": round(random.gauss(56 if is_weekend else 62, 4), 0),
            "sleep_hours": round(random.gauss(7.8 if is_weekend else 6.9, 0.8), 1),
            "sleep_quality": round(random.gauss(82 if is_weekend else 72, 10), 0),
            "deep_sleep_pct": round(random.gauss(18 if is_weekend else 14, 3), 1),
            "stress_level": round(random.gauss(25 if is_weekend else 45, 12), 0),
            "soreness": round(random.gauss(3 if is_weekend else 5, 1.5), 0),
            "fatigue": round(random.gauss(3 if is_weekend else 5, 1.2), 0),
            "mood": round(random.gauss(8 if is_weekend else 6, 1), 0),
            "energy": round(random.gauss(8 if is_weekend else 6, 1.2), 0),
            "timestamp": ts,
            "log_date": datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d"),
        }
        if not hasattr(storage, 'recovery_logs'):
            storage.recovery_logs = {}
        user_logs = storage.recovery_logs.setdefault(user_id, [])
        user_logs.append(log)
        count += 1
    return count


def seed_workouts(user_id: str, storage) -> int:
    """Generate 20 workouts over the past 30 days."""
    exercises_by_day = [
        [("Barbell Bench Press", "chest", 4, [8, 8, 6, 6], 80),
         ("Incline Dumbbell Press", "chest", 3, [10, 10, 8], 30),
         ("Cable Flyes", "chest", 3, [12, 12, 10], 15)],
        [("Barbell Back Squat", "quads", 5, [5, 5, 5, 3, 3], 120),
         ("Romanian Deadlift", "hamstrings", 4, [8, 8, 8, 8], 100),
         ("Leg Press", "quads", 3, [12, 12, 10], 180)],
        [("Deadlift", "back", 5, [5, 5, 3, 3, 3], 140),
         ("Barbell Row", "back", 4, [8, 8, 8, 8], 70),
         ("Pull-ups", "back", 3, [10, 8, 6], 0)],
        [("Overhead Press", "shoulders", 4, [8, 8, 6, 6], 40),
         ("Lateral Raise", "shoulders", 3, [12, 12, 12], 10),
         ("Face Pull", "shoulders", 3, [15, 15, 15], 15)],
        [("Running", "cardio", 1, [30], 0),
         ("Plank", "core", 3, [60, 45, 45], 0)],
    ]
    
    count = 0
    workout_days = sorted(random.sample(range(30), 20))
    
    for i, day in enumerate(workout_days):
        ts = _days_ago(day)
        template = exercises_by_day[i % len(exercises_by_day)]
        
        rpe = random.gauss(7, 1)
        duration = random.gauss(55, 10)
        total_volume = sum(sets * sum(reps) * weight for _, _, sets, reps, weight in template)
        
        workout = {
            "user_id": user_id,
            "workout_id": f"wk_{i:03d}",
            "type": "strength",
            "name": f"Day {i+1} — {template[0][1].title()} Focus",
            "duration_minutes": round(max(20, duration), 0),
            "session_rpe": round(max(1, min(10, rpe)), 1),
            "session_load": round(max(100, rpe * duration), 0),
            "total_volume_kg": round(total_volume, 0),
            "exercises": [
                {"name": name, "muscle": muscle, "sets": sets, "reps": reps, "weight_kg": weight}
                for name, muscle, sets, reps, weight in template
            ],
            "timestamp": ts,
            "created_at": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
        }
        if not hasattr(storage, 'workouts'):
            storage.workouts = {}
        user_workouts = storage.workouts.setdefault(user_id, [])
        user_workouts.append(workout)
        count += 1
    return count


def seed_health_metrics(user_id: str, storage) -> int:
    """Generate 30 days of health metrics (heart rate, steps, calories)."""
    count = 0
    for day in range(30):
        ts = _days_ago(day)
        weekday = (datetime.now(timezone.utc) - timedelta(days=day)).weekday()
        is_weekend = weekday >= 5
        
        metrics = [
            ("heart_rate", random.gauss(62 if is_weekend else 68, 8), "bpm"),
            ("steps", random.gauss(9000 if is_weekend else 7500, 2000), "steps"),
            ("calories", random.gauss(2200 if is_weekend else 2000, 300), "kcal"),
            ("weight", 78.5 + random.gauss(0, 0.3), "kg"),
            ("blood_oxygen", random.gauss(97, 1.5), "%"),
        ]
        
        for mtype, value, unit in metrics:
            metric = {
                "user_id": user_id,
                "measurement_type": mtype,
                "value": round(max(0, value), 1),
                "unit": unit,
                "source": "wearable",
                "timestamp": ts + random.uniform(0, 3600),  # Spread within day
                "record_id": f"hm_{day}_{mtype}",
            }
            if not hasattr(storage, 'health_metrics'):
                storage.health_metrics = {}
            user_metrics = storage.health_metrics.setdefault(user_id, [])
            user_metrics.append(metric)
            count += 1
    return count


def seed_meals(user_id: str, storage) -> int:
    """Generate 10 meals."""
    meals = [
        {"name": "Grilled Chicken Salad", "calories": 450, "protein_g": 42, "carbs_g": 25, "fat_g": 18},
        {"name": "Salmon with Quinoa", "calories": 520, "protein_g": 38, "carbs_g": 45, "fat_g": 22},
        {"name": "Greek Yogurt Bowl", "calories": 280, "protein_g": 20, "carbs_g": 35, "fat_g": 8},
        {"name": "Steak and Vegetables", "calories": 580, "protein_g": 45, "carbs_g": 20, "fat_g": 32},
        {"name": "Oatmeal with Berries", "calories": 350, "protein_g": 12, "carbs_g": 55, "fat_g": 8},
        {"name": "Turkey Wrap", "calories": 400, "protein_g": 30, "carbs_g": 35, "fat_g": 15},
        {"name": "Tuna Poke Bowl", "calories": 480, "protein_g": 35, "carbs_g": 50, "fat_g": 14},
        {"name": "Protein Smoothie", "calories": 320, "protein_g": 30, "carbs_g": 30, "fat_g": 8},
        {"name": "Chicken Stir Fry", "calories": 460, "protein_g": 35, "carbs_g": 40, "fat_g": 18},
        {"name": "Egg and Avocado Toast", "calories": 380, "protein_g": 18, "carbs_g": 30, "fat_g": 22},
    ]
    
    count = 0
    for i, meal in enumerate(meals):
        entry = {
            "user_id": user_id,
            "meal_id": f"meal_{i:03d}",
            "name": meal["name"],
            "calories": meal["calories"],
            "protein_g": meal["protein_g"],
            "carbs_g": meal["carbs_g"],
            "fat_g": meal["fat_g"],
            "logged_at": _days_ago(i % 10),
            "timestamp": _days_ago(i % 10),
        }
        if not hasattr(storage, 'meals'):
            storage.meals = {}
        user_meals = storage.meals.setdefault(user_id, [])
        user_meals.append(entry)
        count += 1
    return count


def seed_sleep_sessions(user_id: str, storage) -> int:
    """Generate 30 days of sleep sessions."""
    count = 0
    for day in range(30):
        ts = _days_ago(day)
        weekday = (datetime.now(timezone.utc) - timedelta(days=day)).weekday()
        is_weekend = weekday >= 5
        
        hours = random.gauss(7.8 if is_weekend else 6.9, 0.8)
        quality = random.gauss(82 if is_weekend else 72, 10)
        
        session = {
            "user_id": user_id,
            "sleep_id": f"sleep_{day:03d}",
            "duration_hours": round(max(4, min(10, hours)), 1),
            "quality_score": round(max(20, min(100, quality)), 0),
            "deep_sleep_pct": round(random.gauss(18 if is_weekend else 14, 3), 1),
            "rem_sleep_pct": round(random.gauss(22, 4), 1),
            "light_sleep_pct": round(random.gauss(45, 5), 1),
            "awakenings": random.randint(0, 4),
            "bedtime": f"{random.randint(22, 24) % 24:02d}:{random.randint(0, 59):02d}",
            "wake_time": f"{random.randint(6, 8):02d}:{random.randint(0, 59):02d}",
            "recorded_at": ts,
            "timestamp": ts,
        }
        if not hasattr(storage, 'sleep_sessions'):
            storage.sleep_sessions = {}
        user_sleep = storage.sleep_sessions.setdefault(user_id, [])
        user_sleep.append(session)
        count += 1
    return count


def seed_family_connections(user_id: str, storage) -> int:
    """Generate sample family connections."""
    members = [
        {"id": "partner_01", "name": "Alex Partner", "relationship": "partner"},
        {"id": "parent_01", "name": "Jordan Parent", "relationship": "parent"},
        {"id": "sibling_01", "name": "Casey Sibling", "relationship": "sibling"},
    ]
    
    count = 0
    for i, member in enumerate(members):
        conn = {
            "connection_id": f"conn_{i:03d}",
            "user_a": user_id,
            "user_b": member["id"],
            "user_b_name": member["name"],
            "relationship": member["relationship"],
            "status": "active",
            "permissions": {"heart_rate": True, "steps": True, "sleep": True, "workouts": False},
            "created_at": _days_ago(30 - i * 5),
        }
        if not hasattr(storage, 'family_connections'):
            storage.family_connections = {}
        user_family = storage.family_connections.setdefault(user_id, [])
        user_family.append(conn)
        count += 1
    return count


def seed_all(user_id: str = "demo_user", storage=None) -> dict:
    """Seed all demo data. Returns summary of what was created."""
    if storage is None:
        from app.core.storage import storage
    
    results = {}
    results["recovery_logs"] = seed_recovery_logs(user_id, storage)
    results["workouts"] = seed_workouts(user_id, storage)
    results["health_metrics"] = seed_health_metrics(user_id, storage)
    results["meals"] = seed_meals(user_id, storage)
    results["sleep_sessions"] = seed_sleep_sessions(user_id, storage)
    results["family_connections"] = seed_family_connections(user_id, storage)
    results["total_records"] = sum(results.values())
    
    return results

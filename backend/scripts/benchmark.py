"""TRACK 9: Performance benchmarking script for AdapFit API endpoints.

Measures response times for critical paths:
- Recovery score calculation (< 5ms target)
- Exercise semantic search (< 15ms target)
- Intent classification & NL workout parsing (< 2ms target)
"""

import time
import json
import statistics
from fastapi.testclient import TestClient

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")

from app.main import app

c = TestClient(app)

ENDPOINTS = {
    "health": {"method": "GET", "url": "/health"},
    "exercises_list": {"method": "GET", "url": "/api/v1/exercises?page_size=50"},
    "exercise_detail": {"method": "GET", "url": "/api/v1/exercises/barbell-bench-press"},
    "recovery_log": {
        "method": "POST",
        "url": "/api/v1/recovery-logs",
        "json": {
            "user_id": "bench-user",
            "log_date": "2026-08-28",
            "wearable_data": {"hrv_rmssd": 45, "sleep_duration_hours": 7.5, "sleep_efficiency_pct": 85},
            "subjective_checkin": {"soreness": 5, "fatigue": 5, "stress": 3},
            "current_acute_load": 600,
            "current_chronic_load": 500,
        },
    },
    "workout_generate": {
        "method": "POST",
        "url": "/api/v1/workouts",
        "json": {"user_id": "bench-user", "target_date": "2026-08-28", "target_duration_minutes": 45},
    },
    "auto_scale": {
        "method": "POST",
        "url": "/api/v1/workouts/auto-scale",
        "json": {
            "completed_sets": [
                {"weight": 80, "reps": 6, "rpe": 9.2, "exercise_id": "barbell-bench-press"},
            ],
            "target_rpe": 7.0,
            "target_reps": 8,
        },
    },
    "intent_classify": {
        "method": "POST",
        "url": "/api/v1/chat/classify",
        "json": {"message": "I feel tired today, should I train?"},
    },
    "voice_parse": {
        "method": "POST",
        "url": "/api/v1/voice/parse",
        "json": {"transcript": "3 sets of 10 bench press at 80 kg RPE 7", "user_id": "bench-user"},
    },
    "trends_acwr": {"method": "GET", "url": "/api/v1/trends/acwr?user_id=bench-user"},
    "nl_workout_parse": {
        "method": "POST",
        "url": "/api/v1/nl-workout",
        "json": {"text": "I did 4 sets of 8 squats at 100kg RPE 8"},
    },
    "meal_plan_targets": {
        "method": "POST",
        "url": "/api/v1/meal-plan/targets",
        "json": {"weight_kg": 80, "goal": "hypertrophy"},
    },
    "injury_risk": {
        "method": "POST",
        "url": "/api/v1/injury-risk/analyze",
        "json": {"user_id": "bench-user", "injury_history": []},
    },
    "hydration_log": {
        "method": "POST",
        "url": "/api/v1/hydration/log",
        "json": {"user_id": "bench-user", "amount_ml": 500},
    },
    "template_list": {"method": "GET", "url": "/api/v1/templates"},
    "calendar_week": {"method": "GET", "url": "/api/v1/calendar/week?user_id=bench-user"},
    "routine_warmup": {"method": "GET", "url": "/api/v1/routine/warmup?muscles=chest&muscles=back"},
}


def benchmark(name: str, config: dict, iterations: int = 50) -> dict:
    """Run a single endpoint benchmark."""
    times = []
    errors = 0

    for _ in range(iterations):
        start = time.perf_counter()
        try:
            if config["method"] == "GET":
                r = c.get(config["url"])
            else:
                r = c.post(config["url"], json=config.get("json", {}))
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)
            if r.status_code >= 500:
                errors += 1
        except Exception:
            errors += 1
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)

    if not times:
        return {"name": name, "error": "no data"}

    return {
        "name": name,
        "method": config["method"],
        "url": config["url"],
        "iterations": iterations,
        "mean_ms": round(statistics.mean(times), 2),
        "median_ms": round(statistics.median(times), 2),
        "p95_ms": round(sorted(times)[int(len(times) * 0.95)], 2),
        "min_ms": round(min(times), 2),
        "max_ms": round(max(times), 2),
        "stdev_ms": round(statistics.stdev(times), 2) if len(times) > 1 else 0,
        "errors": errors,
    }


def main():
    print("=" * 80)
    print("AdapFit API Performance Benchmark")
    print("=" * 80)
    print()

    results = []
    for name, config in ENDPOINTS.items():
        result = benchmark(name, config, iterations=30)
        results.append(result)

    # Print results table
    print(f"{'Endpoint':<25} {'Method':<6} {'Mean':>8} {'Median':>8} {'P95':>8} {'Min':>8} {'Max':>8} {'Errors':>7}")
    print("-" * 80)

    for r in results:
        print(
            f"{r['name']:<25} {r['method']:<6} "
            f"{r.get('mean_ms', 0):>7.1f}ms "
            f"{r.get('median_ms', 0):>7.1f}ms "
            f"{r.get('p95_ms', 0):>7.1f}ms "
            f"{r.get('min_ms', 0):>7.1f}ms "
            f"{r.get('max_ms', 0):>7.1f}ms "
            f"{r.get('errors', 0):>6}"
        )

    print()
    print("=" * 80)

    # Performance targets
    targets = {
        "recovery_log": 5.0,
        "exercise_detail": 15.0,
        "intent_classify": 2.0,
        "voice_parse": 2.0,
        "nl_workout_parse": 2.0,
        "auto_scale": 2.0,
    }

    passed = 0
    failed = 0
    for r in results:
        name = r["name"]
        if name in targets:
            target = targets[name]
            actual = r.get("median_ms", 0)
            status = "PASS" if actual <= target else "FAIL"
            if status == "PASS":
                passed += 1
            else:
                failed += 1
            print(f"  {name}: {actual:.1f}ms (target: <{target}ms) -> {status}")

    print(f"\nPerformance targets: {passed}/{passed + failed} passed")
    print()

    # Save results
    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved to benchmark_results.json")


if __name__ == "__main__":
    main()

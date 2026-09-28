"""
Load test of the core loop: sign up, profile, check-in, today's decision,
generate a workout, complete it. Each virtual user repeats the loop.

    python -m scripts.load_test http://127.0.0.1:8010 --users 20 --seconds 60

Run against a server started with RATE_LIMITING_ENABLED=false: every virtual
user shares one address, so the sign-in limits would otherwise be measured.
"""
import argparse
import asyncio
import statistics
import time
import uuid
from collections import defaultdict

import httpx

PASSWORD = "Str0ngPassw0rd!"


async def user_loop(client: httpx.AsyncClient, deadline: float, timings: dict, errors: dict) -> None:
    async def call(name, method, path, **kw):
        start = time.perf_counter()
        try:
            r = await client.request(method, path, **kw)
            ok = r.status_code < 400
        except httpx.HTTPError:
            r, ok = None, False
        timings[name].append(time.perf_counter() - start)
        if not ok:
            errors[name] += 1
            return None
        return r.json()

    tag = uuid.uuid4().hex[:10]
    reg = await call("register", "POST", "/api/v1/auth/register", json={
        "email": f"load-{tag}@example.com", "username": f"load{tag}", "password": PASSWORD,
        "birth_date": "1992-04-01", "consent": {"health_data": True, "ai": True}})
    if not reg:
        return
    headers = {"Authorization": f"Bearer {reg['tokens']['access_token']}"}
    uid = reg["user"]["id"]
    await call("profile", "POST", "/api/v1/users", headers=headers,
               json={"email": f"load-{tag}@example.com", "name": "Load User"})
    day = 0
    while time.monotonic() < deadline:
        day += 1
        date = f"2026-0{1 + day // 28 % 9}-{1 + day % 28:02d}"
        await call("check-in", "POST", "/api/v1/recovery-logs", headers=headers, json={
            "user_id": uid, "log_date": date,
            "wearable_data": {"hrv_rmssd": 60, "sleep_duration_hours": 7.5, "resting_heart_rate": 55},
            "subjective_checkin": {"soreness": 3, "fatigue": 3, "stress": 3}})
        await call("decision", "GET", "/api/v1/decision/today", headers=headers)
        workout = await call("generate", "POST", "/api/v1/workouts", headers=headers,
                             json={"user_id": uid, "target_date": date, "target_duration_minutes": 45})
        if workout:
            await call("complete", "PATCH", f"/api/v1/workouts/{workout['workout_id']}", headers=headers,
                       json={"user_id": uid, "actual_duration_minutes": 40, "session_rpe": 6, "logged_exercises": []})


async def main(base: str, users: int, seconds: int) -> int:
    timings, errors = defaultdict(list), defaultdict(int)
    deadline = time.monotonic() + seconds
    async with httpx.AsyncClient(base_url=base, timeout=30) as client:
        await asyncio.gather(*(user_loop(client, deadline, timings, errors) for _ in range(users)))
    total = sum(len(v) for v in timings.values())
    print(f"{users} users, {seconds}s, {total} requests, {total / seconds:.1f} req/s")
    for name, values in timings.items():
        values.sort()
        p95 = values[int(len(values) * 0.95) - 1] if len(values) > 1 else values[0]
        print(f"  {name:10} n={len(values):5}  p50={statistics.median(values) * 1000:6.0f} ms  "
              f"p95={p95 * 1000:6.0f} ms  errors={errors[name]}")
    return 1 if sum(errors.values()) else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("--users", type=int, default=20)
    ap.add_argument("--seconds", type=int, default=60)
    a = ap.parse_args()
    raise SystemExit(asyncio.run(main(a.base, a.users, a.seconds)))

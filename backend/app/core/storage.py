"""
AdapFit Storage Layer
Postgres (direct asyncpg or Supabase) when configured, in-memory fallback otherwise.

Follows Supabase Postgres Best Practices:
  - conn-pooling: uses the shared asyncpg pool (app.core.db)
  - lock-short-transactions: minimal lock scope
  - data-pagination: cursor-based pagination for time-series queries
"""
import json
import os
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path

from app.core.config import settings

# SUPABASE_URL/KEY selects the "supabase" backend label; DATABASE_URL selects "postgres".
# Both are served by the same asyncpg-backed repository layer, which requires DATABASE_URL —
# supabase mode without it fails loudly on first use rather than silently dropping writes.
_USE_SUPABASE = bool(settings.SUPABASE_URL and settings.SUPABASE_KEY)
_USE_POSTGRES = bool(settings.DATABASE_URL)
_USE_DB = _USE_SUPABASE or _USE_POSTGRES

DATA_DIR = Path(os.path.dirname(__file__)).parent / "data"
STORE_FILE = DATA_DIR / "store.json"


class StorageEngine:
    """Async-safe storage with Postgres (asyncpg) or in-memory fallback."""

    def __init__(self):
        self._lock = asyncio.Lock()
        # In-memory state (used when no database backend is configured)
        self.users: Dict[str, dict] = {}
        self.baselines: Dict[str, dict] = {}
        self.recovery_logs: Dict[str, List[dict]] = {}
        self.workouts: Dict[str, List[dict]] = {}
        self.workout_logs: Dict[str, List[dict]] = {}
        self.workload_history: Dict[str, List[dict]] = {}
        self.agent_memory: Dict[str, dict] = {}
        self.diet_plans: Dict[str, dict] = {}
        if not _USE_DB:
            self._load()

    def _load(self):
        if STORE_FILE.exists():
            try:
                with open(STORE_FILE, "r") as f:
                    data = json.load(f)
                self.users = data.get("users", {})
                self.baselines = data.get("baselines", {})
                self.recovery_logs = data.get("recovery_logs", {})
                self.workouts = data.get("workouts", {})
                self.workout_logs = data.get("workout_logs", {})
                self.workload_history = data.get("workload_history", {})
                self.agent_memory = data.get("agent_memory", {})
                self.diet_plans = data.get("diet_plans", {})
            except (json.JSONDecodeError, KeyError):
                pass
        self.users.setdefault("default", {
            "id": "default",
            "email": "default@adapfit.app",
            "name": "Alex Johnson",
            "gender": "female",
            "fitness_level": "intermediate",
            "primary_goal": "hypertrophy",
            "preferred_days_per_week": 4,
            "equipment_access": ["bodyweight", "dumbbells", "barbell"],
            "health_connect_enabled": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    async def _save(self):
        if _USE_DB:
            return
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "users": self.users,
            "baselines": self.baselines,
            "recovery_logs": self.recovery_logs,
            "workouts": self.workouts,
            "workout_logs": self.workout_logs,
            "workload_history": self.workload_history,
            "agent_memory": self.agent_memory,
            "diet_plans": self.diet_plans,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(STORE_FILE, "w") as f:
            json.dump(data, f, indent=2, default=str)

    # --- User Operations ---
    async def create_user(self, user_data: dict) -> dict:
        if _USE_DB:
            from app.core.repository import user_repo
            return await user_repo.create(user_data)
        async with self._lock:
            uid = user_data.get("id", str(uuid.uuid4()))
            user_data["id"] = uid
            user_data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
            self.users[uid] = user_data
            await self._save()
            return user_data

    async def get_user(self, user_id: str) -> Optional[dict]:
        if _USE_DB:
            from app.core.repository import user_repo
            return await user_repo.get(user_id)
        return self.users.get(user_id)

    async def update_user(self, user_id: str, updates: dict) -> Optional[dict]:
        if _USE_DB:
            from app.core.repository import user_repo
            return await user_repo.update(user_id, updates)
        async with self._lock:
            if user_id not in self.users:
                return None
            self.users[user_id].update(updates)
            await self._save()
            return self.users[user_id]

    # --- Baseline Operations ---
    async def set_baseline(self, user_id: str, baseline: dict) -> dict:
        if _USE_DB:
            from app.core.repository import baseline_repo
            return await baseline_repo.set(user_id, baseline)
        async with self._lock:
            baseline["user_id"] = user_id
            baseline.setdefault("updated_at", datetime.now(timezone.utc).isoformat())
            self.baselines[user_id] = baseline
            await self._save()
            return baseline

    async def get_baseline(self, user_id: str) -> Optional[dict]:
        if _USE_DB:
            from app.core.repository import baseline_repo
            return await baseline_repo.get(user_id)
        return self.baselines.get(user_id)

    # --- Diet Plan Operations ---
    async def save_diet_plan(self, user_id: str, plan: dict) -> dict:
        if _USE_DB:
            from app.core.repository import diet_plan_repo
            return await diet_plan_repo.save(user_id, plan)
        async with self._lock:
            plan["user_id"] = user_id
            plan.setdefault("created_at", datetime.now(timezone.utc).isoformat())
            self.diet_plans[user_id] = plan
            await self._save()
            return plan

    async def get_diet_plan(self, user_id: str) -> Optional[dict]:
        if _USE_DB:
            from app.core.repository import diet_plan_repo
            return await diet_plan_repo.get(user_id)
        return self.diet_plans.get(user_id)

    # --- Recovery Log Operations ---
    async def add_recovery_log(self, user_id: str, log: dict) -> dict:
        if _USE_DB:
            from app.core.repository import recovery_log_repo
            return await recovery_log_repo.add(user_id, log)
        async with self._lock:
            log.setdefault("id", str(uuid.uuid4()))
            log.setdefault("created_at", datetime.now(timezone.utc).isoformat())
            if user_id not in self.recovery_logs:
                self.recovery_logs[user_id] = []
            self.recovery_logs[user_id].append(log)
            if len(self.recovery_logs[user_id]) > 90:
                self.recovery_logs[user_id] = self.recovery_logs[user_id][-90:]
            await self._save()
            return log

    async def get_recovery_logs(self, user_id: str, days: int = 28) -> List[dict]:
        if _USE_DB:
            from app.core.repository import recovery_log_repo
            return await recovery_log_repo.get(user_id, days)
        logs = self.recovery_logs.get(user_id, [])
        return logs[-days:] if logs else []

    # --- Workout Operations ---
    async def save_workout(self, user_id: str, workout: dict) -> dict:
        if _USE_DB:
            from app.core.repository import workout_repo
            return await workout_repo.save(user_id, workout)
        async with self._lock:
            workout.setdefault("id", str(uuid.uuid4()))
            workout.setdefault("created_at", datetime.now(timezone.utc).isoformat())
            if user_id not in self.workouts:
                self.workouts[user_id] = []
            self.workouts[user_id].append(workout)
            await self._save()
            return workout

    async def get_workouts(self, user_id: str, days: int = 14) -> List[dict]:
        if _USE_DB:
            from app.core.repository import workout_repo
            return await workout_repo.get(user_id, days)
        workouts = self.workouts.get(user_id, [])
        return workouts[-days:] if workouts else []

    async def get_latest_workouts(self, user_id: str, count: int = 3) -> List[dict]:
        if _USE_DB:
            from app.core.repository import workout_repo
            return await workout_repo.get_latest(user_id, count)
        workouts = self.workouts.get(user_id, [])
        return workouts[-count:] if workouts else []

    # --- Workout Log (Completion) Operations ---
    async def add_workout_log(self, user_id: str, log: dict) -> dict:
        if _USE_DB:
            from app.core.repository import workout_log_repo
            return await workout_log_repo.add(user_id, log)
        async with self._lock:
            log.setdefault("id", str(uuid.uuid4()))
            log.setdefault("completed_at", datetime.now(timezone.utc).isoformat())
            if user_id not in self.workout_logs:
                self.workout_logs[user_id] = []
            self.workout_logs[user_id].append(log)
            await self._save()
            return log

    async def get_workout_logs(self, user_id: str, days: int = 28) -> List[dict]:
        if _USE_DB:
            from app.core.repository import workout_log_repo
            return await workout_log_repo.get(user_id, days)
        logs = self.workout_logs.get(user_id, [])
        return logs[-days:] if logs else []

    # --- Workload History ---
    async def add_workload_entry(self, user_id: str, entry: dict) -> dict:
        if _USE_DB:
            from app.core.repository import workload_repo
            return await workload_repo.add(user_id, entry)
        async with self._lock:
            entry.setdefault("recorded_at", datetime.now(timezone.utc).isoformat())
            if user_id not in self.workload_history:
                self.workload_history[user_id] = []
            self.workload_history[user_id].append(entry)
            if len(self.workload_history[user_id]) > 60:
                self.workload_history[user_id] = self.workload_history[user_id][-60:]
            await self._save()
            return entry

    async def get_workload_history(self, user_id: str, days: int = 28) -> List[dict]:
        if _USE_DB:
            from app.core.repository import workload_repo
            return await workload_repo.get(user_id, days)
        history = self.workload_history.get(user_id, [])
        return history[-days:] if history else []

    # --- Agent Memory ---
    async def get_agent_memory(self, user_id: str) -> dict:
        if _USE_DB:
            from app.core.repository import agent_memory_repo
            return await agent_memory_repo.get(user_id)
        if user_id not in self.agent_memory:
            self.agent_memory[user_id] = {
                "exercise_preferences": {},
                "accepted_workouts": 0,
                "rejected_workouts": 0,
                "pain_flags": [],
                "great_exercises": [],
                "adaptation_history": [],
                "nlp_feedback_history": [],
                "evolution_version": 1,
            }
        return self.agent_memory[user_id]

    async def update_agent_memory(self, user_id: str, updates: dict) -> dict:
        if _USE_DB:
            from app.core.repository import agent_memory_repo
            return await agent_memory_repo.update(user_id, updates)
        async with self._lock:
            memory = await self.get_agent_memory(user_id)
            memory.update(updates)
            self.agent_memory[user_id] = memory
            await self._save()
            return memory

    # --- Utility ---
    async def clear_all(self):
        async with self._lock:
            self.users.clear()
            self.baselines.clear()
            self.recovery_logs.clear()
            self.workouts.clear()
            self.workout_logs.clear()
            self.workload_history.clear()
            self.agent_memory.clear()
            await self._save()

    async def get_sleep_logs(self, user_id: str, days: int = 14) -> list[dict]:
        """Recovery logs that carry sleep data, most recent `days` entries in chronological order."""
        if _USE_DB:
            from app.core.repository import recovery_log_repo
            return await recovery_log_repo.get_sleep(user_id, days)
        logs = self.recovery_logs.get(user_id, [])
        sleep_logs = [
            l for l in logs
            if l.get("wearable_data", {}).get("sleep_duration_hours")
            or l.get("sleep_score")
        ]
        return sleep_logs[-days:]

    async def get_stats(self) -> dict:
        backend = "supabase" if _USE_SUPABASE else ("postgres" if _USE_POSTGRES else "in_memory")

        if _USE_SUPABASE or _USE_POSTGRES:
            # Counting the in-memory dicts while a database backs the store
            # reports zero for a populated database, which reads as data loss.
            from app.core.db import get_pool

            pool = await get_pool()
            if pool is not None:
                async with pool.acquire() as conn:
                    counts = await conn.fetchrow(
                        "SELECT (SELECT count(*) FROM users) AS users,"
                        " (SELECT count(*) FROM daily_recovery_logs) AS recovery_logs,"
                        " (SELECT count(*) FROM workouts) AS workouts,"
                        " (SELECT count(*) FROM workout_logs) AS workout_logs"
                    )
                return {
                    "users": counts["users"],
                    "total_recovery_logs": counts["recovery_logs"],
                    "total_workouts": counts["workouts"],
                    "total_workout_logs": counts["workout_logs"],
                    "backend": backend,
                }

        return {
            "users": len(self.users),
            "total_recovery_logs": sum(len(v) for v in self.recovery_logs.values()),
            "total_workouts": sum(len(v) for v in self.workouts.values()),
            "total_workout_logs": sum(len(v) for v in self.workout_logs.values()),
            "backend": backend,
        }


# Singleton
storage = StorageEngine()

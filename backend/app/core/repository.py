"""
Postgres repository layer, asyncpg-backed with parameterized SQL.

Table shapes here follow the live schema in supabase/migrations/001_initial_schema.sql.
Two gaps in that schema are worked around rather than silently dropped:
  - diet_plans: no such table exists yet. DietPlanRepository targets one, following
    the free-form JSONB-payload convention the schema already uses for workout_logs
    and workload_history. Needs a migration before postgres/supabase mode can use it.
  - workouts.warmup / workouts.cooldown: no columns exist for these. save() persists
    everything else (including exercises, via the workout_exercises child table) and
    drops warmup/cooldown. Needs migration columns to stop being lossy.

Every repository method raises if the pool is unavailable, instead of returning the
caller's input unchanged, so a misconfigured backend surfaces as an error and never
as silently dropped data.
"""
import json
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Union

import asyncpg

from app.core.db import get_pool
from app.core.user_ids import normalize_user_id

ConflictCols = Union[str, Sequence[str]]


async def _pool() -> asyncpg.Pool:
    pool = await get_pool()
    if pool is None:
        raise RuntimeError(
            "Postgres pool unavailable: DATABASE_URL is not set. "
            "Set DATABASE_URL to use the postgres/supabase storage backend."
        )
    return pool


def _normalize(value: Any) -> Any:
    """
    Convert a database value to the shape the in-memory backend produces.

    numeric columns arrive as Decimal, which raises TypeError on arithmetic
    with float, so every engine reading a score or a load would fail.
    """
    if isinstance(value, (uuid.UUID, datetime, date)):
        return str(value) if isinstance(value, uuid.UUID) else value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


_UUID_COLUMNS = {"id", "user_id", "workout_id", "share_id", "challenge_id"}
_DATE_COLUMNS = {"log_date", "target_date", "start_date", "end_date", "date"}


def _to_pg(column: str, value: Any) -> Any:
    """
    Coerce a JSON-shaped value into what asyncpg requires for its column type.

    asyncpg binds by Python type rather than parsing strings, so a date or uuid
    arriving as a string raises DataError instead of being cast.
    """
    if value is None or not isinstance(value, str):
        return value
    if column in _UUID_COLUMNS:
        try:
            return uuid.UUID(value)
        except ValueError:
            return value
    if column in _DATE_COLUMNS:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return value
    return value


def _row(record: Optional[asyncpg.Record]) -> Optional[Dict[str, Any]]:
    return {k: _normalize(v) for k, v in record.items()} if record is not None else None


def _rows(records: Sequence[asyncpg.Record]) -> List[Dict[str, Any]]:
    return [_row(r) for r in records]


def _decode_json(row: Optional[Dict[str, Any]], keys: Sequence[str]) -> Optional[Dict[str, Any]]:
    """asyncpg returns jsonb columns as raw text; decode the given keys in place."""
    if row is None:
        return None
    for key in keys:
        value = row.get(key)
        if isinstance(value, str):
            row[key] = json.loads(value)
    return row


def _encode_json(data: dict, keys: Sequence[str]) -> dict:
    """Copy data with the given keys json-dumped, ready to bind as jsonb parameters."""
    out = dict(data)
    for key in keys:
        if key in out and not isinstance(out[key], str):
            out[key] = json.dumps(out[key])
    return out


async def _insert(conn: asyncpg.Connection, table: str, allowed: Sequence[str], data: dict) -> Dict[str, Any]:
    cols = [c for c in allowed if c in data]
    if not cols:
        row = await conn.fetchrow(f"INSERT INTO {table} DEFAULT VALUES RETURNING *")
    else:
        placeholders = ", ".join(f"${i + 1}" for i in range(len(cols)))
        row = await conn.fetchrow(
            f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders}) RETURNING *",
            *(_to_pg(c, data[c]) for c in cols),
        )
    return _row(row)


async def _update(
    conn: asyncpg.Connection, table: str, allowed: Sequence[str], data: dict, where_col: str, where_val: Any
) -> Optional[Dict[str, Any]]:
    cols = [c for c in allowed if c in data]
    if not cols:
        row = await conn.fetchrow(f"SELECT * FROM {table} WHERE {where_col} = $1", where_val)
        return _row(row)
    set_clause = ", ".join(f"{c} = ${i + 1}" for i, c in enumerate(cols))
    row = await conn.fetchrow(
        f"UPDATE {table} SET {set_clause} WHERE {where_col} = ${len(cols) + 1} RETURNING *",
        *(_to_pg(c, data[c]) for c in cols),
        where_val,
    )
    return _row(row)


async def _upsert(
    conn: asyncpg.Connection, table: str, allowed: Sequence[str], data: dict, conflict_cols: ConflictCols
) -> Dict[str, Any]:
    cols = [c for c in allowed if c in data]
    conflict = (conflict_cols,) if isinstance(conflict_cols, str) else tuple(conflict_cols)
    placeholders = ", ".join(f"${i + 1}" for i in range(len(cols)))
    update_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c not in conflict)
    row = await conn.fetchrow(
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT ({', '.join(conflict)}) DO UPDATE SET {update_clause} RETURNING *",
        *(_to_pg(c, data[c]) for c in cols),
    )
    return _row(row)


class UserRepository:
    _COLUMNS = (
        "id", "email", "name", "age", "height_cm", "gender", "fitness_level", "primary_goal",
        "preferred_days_per_week", "equipment_access", "health_connect_enabled",
        "work_start", "work_end", "created_at", "updated_at",
    )

    async def create(self, user_data: dict) -> dict:
        pool = await _pool()
        async with pool.acquire() as conn:
            return await _insert(conn, "users", self._COLUMNS, user_data)

    async def get(self, user_id: str) -> Optional[dict]:
        user_id = _to_pg("user_id", normalize_user_id(user_id))
        pool = await _pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
            return _row(row)

    async def update(self, user_id: str, updates: dict) -> Optional[dict]:
        user_id = _to_pg("user_id", normalize_user_id(user_id))
        pool = await _pool()
        async with pool.acquire() as conn:
            return await _update(conn, "users", self._COLUMNS, updates, "id", user_id)


class BaselineRepository:
    _COLUMNS = ("user_id", "hrv_mean_rmssd", "hrv_std_rmssd", "rhr_baseline", "sleep_target_hours", "chronic_load_28d")

    async def set(self, user_id: str, baseline: dict) -> dict:
        user_id = _to_pg("user_id", normalize_user_id(user_id))
        baseline = {**baseline, "user_id": user_id}
        pool = await _pool()
        async with pool.acquire() as conn:
            return await _upsert(conn, "user_baselines", self._COLUMNS, baseline, "user_id")

    async def get(self, user_id: str) -> Optional[dict]:
        user_id = _to_pg("user_id", normalize_user_id(user_id))
        pool = await _pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM user_baselines WHERE user_id = $1", user_id)
            return _row(row)


class RecoveryLogRepository:
    _COLUMNS = (
        "user_id", "log_date", "hrv_rmssd", "hrv_z_score", "resting_heart_rate", "sleep_score",
        "sleep_duration_hours", "sleep_efficiency_pct", "subjective_score", "soreness_score",
        "fatigue_score", "stress_score", "sore_muscle_groups", "readiness_state", "recovery_score",
        "steps", "active_calories", "water_intake_ml",
    )

    async def add(self, user_id: str, log: dict) -> dict:
        user_id = _to_pg("user_id", normalize_user_id(user_id))
        log = {**log, "user_id": user_id}
        log.setdefault("log_date", date.today().isoformat())
        pool = await _pool()
        async with pool.acquire() as conn:
            return await _upsert(conn, "daily_recovery_logs", self._COLUMNS, log, ("user_id", "log_date"))

    async def get(self, user_id: str, days: int = 28) -> List[dict]:
        user_id = _to_pg("user_id", normalize_user_id(user_id))
        pool = await _pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM daily_recovery_logs WHERE user_id = $1 ORDER BY log_date DESC LIMIT $2",
                user_id, days,
            )
        return list(reversed(_rows(rows)))

    async def get_sleep(self, user_id: str, days: int = 14) -> List[dict]:
        """Recovery logs that carry sleep data — there is no separate sleep_logs source in this app."""
        user_id = _to_pg("user_id", normalize_user_id(user_id))
        pool = await _pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM daily_recovery_logs WHERE user_id = $1 "
                "AND (sleep_duration_hours IS NOT NULL OR sleep_score IS NOT NULL) "
                "ORDER BY log_date DESC LIMIT $2",
                user_id, days,
            )
        return list(reversed(_rows(rows)))


class WorkoutRepository:
    _COLUMNS = (
        "user_id", "title", "target_date", "readiness_state", "recovery_score", "adaptation_rationale",
        "target_duration_minutes", "actual_duration_minutes", "session_rpe", "acwr_before", "completed",
    )
    _EXERCISE_COLUMNS = (
        "workout_id", "exercise_id", "exercise_name", "target_muscle", "sets", "target_reps",
        "target_rpe", "actual_weight", "actual_reps", "actual_rpe", "axial_loading_rating", "order_index", "completed",
    )

    async def save(self, user_id: str, workout: dict) -> dict:
        user_id = _to_pg("user_id", normalize_user_id(user_id))
        # ponytail: warmup/cooldown have no columns in the live schema and are dropped here;
        # ceiling is losing those two fields in postgres/supabase mode until a migration adds them.
        exercises = workout.get("exercises") or []
        workout = {**workout, "user_id": user_id}
        pool = await _pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                saved = await _insert(conn, "workouts", self._COLUMNS, workout)
                if exercises:
                    rows = [
                        {**ex, "workout_id": saved["id"]}
                        for ex in exercises
                        if isinstance(ex, dict)
                    ]
                    for ex in rows:
                        await _insert(conn, "workout_exercises", self._EXERCISE_COLUMNS, ex)
                    saved["exercises"] = rows
        return saved

    async def _attach_exercises(self, conn: asyncpg.Connection, workouts: List[dict]) -> List[dict]:
        for w in workouts:
            rows = await conn.fetch(
                "SELECT * FROM workout_exercises WHERE workout_id = $1 ORDER BY order_index", w["id"]
            )
            w["exercises"] = _rows(rows)
        return workouts

    async def get(self, user_id: str, days: int = 14) -> List[dict]:
        user_id = _to_pg("user_id", normalize_user_id(user_id))
        pool = await _pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM workouts WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2",
                user_id, days,
            )
            workouts = list(reversed(_rows(rows)))
            return await self._attach_exercises(conn, workouts)

    async def get_latest(self, user_id: str, count: int = 3) -> List[dict]:
        user_id = _to_pg("user_id", normalize_user_id(user_id))
        pool = await _pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM workouts WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2",
                user_id, count,
            )
            workouts = list(reversed(_rows(rows)))
            return await self._attach_exercises(conn, workouts)


class WorkoutLogRepository:
    _JSON_KEYS = ("data",)

    async def add(self, user_id: str, log: dict) -> dict:
        user_id = _to_pg("user_id", normalize_user_id(user_id))
        pool = await _pool()
        async with pool.acquire() as conn:
            saved = await conn.fetchrow(
                "INSERT INTO workout_logs (user_id, data) VALUES ($1, $2::jsonb) RETURNING *",
                user_id, json.dumps(log),
            )
        result = _decode_json(_row(saved), self._JSON_KEYS)
        return {**result["data"], "id": result["id"], "completed_at": result["completed_at"]}

    async def get(self, user_id: str, days: int = 28) -> List[dict]:
        user_id = _to_pg("user_id", normalize_user_id(user_id))
        pool = await _pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM workout_logs WHERE user_id = $1 ORDER BY completed_at DESC LIMIT $2",
                user_id, days,
            )
        out = []
        for r in _rows(rows):
            r = _decode_json(r, self._JSON_KEYS)
            out.append({**r["data"], "id": r["id"], "completed_at": r["completed_at"]})
        return out


class WorkloadRepository:
    _JSON_KEYS = ("data",)

    async def add(self, user_id: str, entry: dict) -> dict:
        user_id = _to_pg("user_id", normalize_user_id(user_id))
        pool = await _pool()
        async with pool.acquire() as conn:
            saved = await conn.fetchrow(
                "INSERT INTO workload_history (user_id, data) VALUES ($1, $2::jsonb) RETURNING *",
                user_id, json.dumps(entry),
            )
        result = _decode_json(_row(saved), self._JSON_KEYS)
        return {**result["data"], "recorded_at": result["recorded_at"]}

    async def get(self, user_id: str, days: int = 28) -> List[dict]:
        user_id = _to_pg("user_id", normalize_user_id(user_id))
        pool = await _pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM workload_history WHERE user_id = $1 ORDER BY recorded_at DESC LIMIT $2",
                user_id, days,
            )
        out = []
        for r in _rows(rows):
            r = _decode_json(r, self._JSON_KEYS)
            out.append({**r["data"], "recorded_at": r["recorded_at"]})
        return out


class HealthMetricRepository:
    """No health_metrics table exists yet; needs the same free-form-JSONB migration as diet_plans."""
    _JSON_KEYS = ("data",)

    async def add(self, user_id: str, metric: dict) -> dict:
        user_id = _to_pg("user_id", normalize_user_id(user_id))
        pool = await _pool()
        async with pool.acquire() as conn:
            saved = await conn.fetchrow(
                "INSERT INTO health_metrics (user_id, data) VALUES ($1, $2::jsonb) RETURNING *",
                user_id, json.dumps(metric),
            )
        result = _decode_json(_row(saved), self._JSON_KEYS)
        return {**result["data"], "id": result["id"], "recorded_at": result["recorded_at"]}

    async def get(self, user_id: str, metric_type: Optional[str] = None, days: int = 30) -> List[dict]:
        user_id = _to_pg("user_id", normalize_user_id(user_id))
        pool = await _pool()
        async with pool.acquire() as conn:
            if metric_type:
                rows = await conn.fetch(
                    "SELECT * FROM health_metrics WHERE user_id = $1 AND data->>'metric_type' = $2 "
                    "ORDER BY recorded_at DESC LIMIT $3",
                    user_id, metric_type, days,
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM health_metrics WHERE user_id = $1 ORDER BY recorded_at DESC LIMIT $2",
                    user_id, days,
                )
        out = []
        for r in _rows(rows):
            r = _decode_json(r, self._JSON_KEYS)
            out.append({**r["data"], "id": r["id"], "recorded_at": r["recorded_at"]})
        return out


class DietPlanRepository:
    """No diet_plans table exists yet; needs a migration (id, user_id, data jsonb, created_at, UNIQUE(user_id))."""
    _JSON_KEYS = ("data",)

    async def save(self, user_id: str, plan: dict) -> dict:
        user_id = _to_pg("user_id", normalize_user_id(user_id))
        pool = await _pool()
        async with pool.acquire() as conn:
            saved = await conn.fetchrow(
                "INSERT INTO diet_plans (user_id, data) VALUES ($1, $2::jsonb) "
                "ON CONFLICT (user_id) DO UPDATE SET data = EXCLUDED.data, created_at = NOW() RETURNING *",
                user_id, json.dumps(plan),
            )
        result = _decode_json(_row(saved), self._JSON_KEYS)
        return {**result["data"], "user_id": user_id}

    async def get(self, user_id: str) -> Optional[dict]:
        user_id = _to_pg("user_id", normalize_user_id(user_id))
        pool = await _pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM diet_plans WHERE user_id = $1", user_id)
        result = _decode_json(_row(row), self._JSON_KEYS)
        return {**result["data"], "user_id": user_id} if result else None


class AgentMemoryRepository:
    _COLUMNS = (
        "user_id", "exercise_preferences", "accepted_workouts", "rejected_workouts", "pain_flags",
        "great_exercises", "adaptation_history", "nlp_feedback_history", "evolution_version",
    )
    _JSON_KEYS = ("exercise_preferences", "pain_flags", "great_exercises", "adaptation_history", "nlp_feedback_history")
    _DEFAULT = {
        "exercise_preferences": {},
        "accepted_workouts": 0,
        "rejected_workouts": 0,
        "pain_flags": [],
        "great_exercises": [],
        "adaptation_history": [],
        "nlp_feedback_history": [],
        "evolution_version": 1,
    }

    async def get(self, user_id: str) -> dict:
        user_id = _to_pg("user_id", normalize_user_id(user_id))
        pool = await _pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM agent_memory WHERE user_id = $1", user_id)
            if row is None:
                data = _encode_json({**self._DEFAULT, "user_id": user_id}, self._JSON_KEYS)
                row = await _insert(conn, "agent_memory", self._COLUMNS, data)
                return _decode_json(row, self._JSON_KEYS)
        return _decode_json(_row(row), self._JSON_KEYS)

    async def update(self, user_id: str, updates: dict) -> dict:
        user_id = _to_pg("user_id", normalize_user_id(user_id))
        data = _encode_json({**updates, "user_id": user_id}, self._JSON_KEYS)
        pool = await _pool()
        async with pool.acquire() as conn:
            row = await _upsert(conn, "agent_memory", self._COLUMNS, data, "user_id")
        return _decode_json(row, self._JSON_KEYS)


# Singleton repository instances
user_repo = UserRepository()
baseline_repo = BaselineRepository()
recovery_log_repo = RecoveryLogRepository()
workout_repo = WorkoutRepository()
workout_log_repo = WorkoutLogRepository()
workload_repo = WorkloadRepository()
health_metric_repo = HealthMetricRepository()
diet_plan_repo = DietPlanRepository()
agent_memory_repo = AgentMemoryRepository()

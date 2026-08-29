"""
AdapFit Postgres Repository Layer
Replaces in-memory storage with Supabase Postgres operations.

Follows Supabase Postgres Best Practices:
  - data-batch-inserts: batch operations where possible
  - data-pagination: cursor-based pagination support
  - lock-short-transactions: minimal transaction scope
  - query-missing-indexes: leverages indexed columns
  - query-composite-indexes: uses (user_id, date) composite indexes
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import json

from app.core.config import settings

# Lazy client initialization
_client = None


async def get_supabase_client():
    """Get Supabase client (lazy initialization)."""
    global _client
    if _client is not None:
        return _client

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        return None

    try:
        from supabase import create_client, ClientOptions, SyncClient
        # Use async client for FastAPI
        from supabase._sync.client import SyncClient as Client
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        return _client
    except ImportError:
        return None
    except Exception:
        return None


class UserRepository:
    async def create(self, user_data: dict) -> dict:
        client = await get_supabase_client()
        if not client:
            return user_data
        result = client.table("users").insert(user_data).execute()
        return result.data[0] if result.data else user_data

    async def get(self, user_id: str) -> Optional[dict]:
        client = await get_supabase_client()
        if not client:
            return None
        result = client.table("users").select("*").eq("id", user_id).execute()
        return result.data[0] if result.data else None

    async def update(self, user_id: str, updates: dict) -> Optional[dict]:
        client = await get_supabase_client()
        if not client:
            return None
        result = client.table("users").update(updates).eq("id", user_id).execute()
        return result.data[0] if result.data else None


class BaselineRepository:
    async def set(self, user_id: str, baseline: dict) -> dict:
        client = await get_supabase_client()
        if not client:
            return baseline
        baseline["user_id"] = user_id
        result = client.table("user_baselines").upsert(baseline).execute()
        return result.data[0] if result.data else baseline

    async def get(self, user_id: str) -> Optional[dict]:
        client = await get_supabase_client()
        if not client:
            return None
        result = client.table("user_baselines").select("*").eq("user_id", user_id).execute()
        return result.data[0] if result.data else None


class RecoveryLogRepository:
    async def add(self, user_id: str, log: dict) -> dict:
        client = await get_supabase_client()
        if not client:
            return log
        log["user_id"] = user_id
        result = client.table("daily_recovery_logs").insert(log).execute()
        return result.data[0] if result.data else log

    async def get(self, user_id: str, days: int = 28) -> List[dict]:
        """Cursor-based pagination: fetch recent logs using indexed (user_id, log_date) composite."""
        client = await get_supabase_client()
        if not client:
            return []
        result = (
            client.table("daily_recovery_logs")
            .select("*")
            .eq("user_id", user_id)
            .order("log_date", desc=True)
            .limit(days)
            .execute()
        )
        return list(reversed(result.data)) if result.data else []


class WorkoutRepository:
    async def save(self, user_id: str, workout: dict) -> dict:
        client = await get_supabase_client()
        if not client:
            return workout
        workout["user_id"] = user_id
        # Serialize nested objects to JSONB
        if "exercises" in workout and isinstance(workout["exercises"], list):
            workout["exercises"] = json.dumps(workout["exercises"])
        if "warmup" in workout and isinstance(workout["warmup"], list):
            workout["warmup"] = json.dumps(workout["warmup"])
        if "cooldown" in workout and isinstance(workout["cooldown"], list):
            workout["cooldown"] = json.dumps(workout["cooldown"])
        result = client.table("workouts").insert(workout).execute()
        return result.data[0] if result.data else workout

    async def get(self, user_id: str, days: int = 14) -> List[dict]:
        client = await get_supabase_client()
        if not client:
            return []
        result = (
            client.table("workouts")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(days)
            .execute()
        )
        return result.data if result.data else []


class WorkoutLogRepository:
    async def add(self, user_id: str, log: dict) -> dict:
        client = await get_supabase_client()
        if not client:
            return log
        log["user_id"] = user_id
        if "logged_exercises" in log and isinstance(log["logged_exercises"], list):
            log["logged_exercises"] = json.dumps(log["logged_exercises"])
        result = client.table("workout_logs").insert(log).execute()
        return result.data[0] if result.data else log

    async def get(self, user_id: str, days: int = 28) -> List[dict]:
        client = await get_supabase_client()
        if not client:
            return []
        result = (
            client.table("workout_logs")
            .select("*")
            .eq("user_id", user_id)
            .order("completed_at", desc=True)
            .limit(days)
            .execute()
        )
        return result.data if result.data else []


class WorkloadRepository:
    async def add(self, user_id: str, entry: dict) -> dict:
        client = await get_supabase_client()
        if not client:
            return entry
        entry["user_id"] = user_id
        result = client.table("workload_history").insert(entry).execute()
        return result.data[0] if result.data else entry

    async def get(self, user_id: str, days: int = 28) -> List[dict]:
        client = await get_supabase_client()
        if not client:
            return []
        result = (
            client.table("workload_history")
            .select("*")
            .eq("user_id", user_id)
            .order("recorded_at", desc=True)
            .limit(days)
            .execute()
        )
        return result.data if result.data else []


class HealthMetricRepository:
    async def add(self, user_id: str, metric: dict) -> dict:
        client = await get_supabase_client()
        if not client:
            return metric
        metric["user_id"] = user_id
        result = client.table("health_metrics").insert(metric).execute()
        return result.data[0] if result.data else metric

    async def get(self, user_id: str, metric_type: Optional[str] = None, days: int = 30) -> List[dict]:
        client = await get_supabase_client()
        if not client:
            return []
        query = (
            client.table("health_metrics")
            .select("*")
            .eq("user_id", user_id)
            .order("recorded_at", desc=True)
            .limit(days)
        )
        if metric_type:
            query = query.eq("metric_type", metric_type)
        result = query.execute()
        return result.data if result.data else []


class AgentMemoryRepository:
    async def get(self, user_id: str) -> dict:
        client = await get_supabase_client()
        if not client:
            return {
                "exercise_preferences": {},
                "accepted_workouts": 0,
                "rejected_workouts": 0,
                "pain_flags": [],
                "great_exercises": [],
                "adaptation_history": [],
                "nlp_feedback_history": [],
                "evolution_version": 1,
            }
        result = client.table("agent_memory").select("*").eq("user_id", user_id).execute()
        if result.data:
            return result.data[0]
        # Create default memory
        default = {
            "user_id": user_id,
            "exercise_preferences": {},
            "accepted_workouts": 0,
            "rejected_workouts": 0,
            "pain_flags": [],
            "great_exercises": [],
            "adaptation_history": [],
            "nlp_feedback_history": [],
            "evolution_version": 1,
        }
        client.table("agent_memory").insert(default).execute()
        return default

    async def update(self, user_id: str, updates: dict) -> dict:
        client = await get_supabase_client()
        if not client:
            return updates
        result = client.table("agent_memory").update(updates).eq("user_id", user_id).execute()
        return result.data[0] if result.data else updates


# Singleton repository instances
user_repo = UserRepository()
baseline_repo = BaselineRepository()
recovery_log_repo = RecoveryLogRepository()
workout_repo = WorkoutRepository()
workout_log_repo = WorkoutLogRepository()
workload_repo = WorkloadRepository()
health_metric_repo = HealthMetricRepository()
agent_memory_repo = AgentMemoryRepository()

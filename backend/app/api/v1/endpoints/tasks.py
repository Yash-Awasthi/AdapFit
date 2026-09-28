"""Offline-first batch sync from the mobile client."""
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.durable import durable_dict

router = APIRouter()

# Queue ids already applied, per user: a replay after a lost response must not log a workout twice.
_applied = durable_dict("app.api.v1.endpoints.tasks._applied")


# --- Batch Sync for Offline-First Client ---

class SyncMutation(BaseModel):
    id: Optional[str] = None  # the client's queue id, echoed back in synced_ids
    table_name: str
    record_id: str
    operation: str  # create, update, delete
    payload: dict = {}

class BatchSyncRequest(BaseModel):
    mutations: list[SyncMutation]


@router.post("/sync/batch")
async def batch_sync(req: BatchSyncRequest):
    """Apply queued offline mutations to the caller's own records."""
    from app.core.per_user import current_user_id
    from app.core.storage import storage

    # The owner is the authenticated caller; a user_id inside a payload is ignored.
    from app.api.v1.endpoints.workouts import complete_workout
    from app.models.schemas import WorkoutCompleteRequest

    user_id = current_user_id()
    applied = set(_applied.get(user_id, []))
    synced_ids, errors = [], []
    for m in req.mutations:
        done_id = m.id or m.record_id
        if m.id and m.id in applied:
            synced_ids.append(done_id)
            continue
        payload = {k: v for k, v in m.payload.items() if k != "user_id"}
        try:
            # A queued workout is a completion that failed offline; replay it through the same route.
            if m.table_name == "workouts" and m.operation == "update":
                await complete_workout(m.record_id, WorkoutCompleteRequest(**payload, user_id=user_id))
            elif m.table_name == "daily_recovery_logs" and m.operation == "create":
                await storage.add_recovery_log(user_id, {**payload, "id": m.record_id, "synced": True})
            else:
                errors.append({"id": done_id, "error": f"Unsupported: {m.operation} on {m.table_name}"})
                continue
        except Exception as e:
            errors.append({"id": done_id, "error": str(e)})
            continue
        synced_ids.append(done_id)
        if m.id:
            applied.add(m.id)
    _applied[user_id] = sorted(applied)[-1000:]

    return {"synced_count": len(synced_ids), "synced_ids": synced_ids, "errors": errors}

"""Offline-first batch sync from the mobile client."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


# --- Batch Sync for Offline-First Client ---

class SyncMutation(BaseModel):
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
    user_id = current_user_id()
    writers = {"workouts": storage.save_workout, "daily_recovery_logs": storage.add_recovery_log}
    synced_ids, errors = [], []
    for m in req.mutations:
        if m.operation == "delete":
            continue
        writer = writers.get(m.table_name)
        if writer is None:
            errors.append({"record_id": m.record_id, "error": f"Unsupported table: {m.table_name}"})
            continue
        payload = {k: v for k, v in m.payload.items() if k != "user_id"}
        try:
            await writer(user_id, {**payload, "id": m.record_id, "synced": True})
            synced_ids.append(m.record_id)
        except Exception as e:
            errors.append({"record_id": m.record_id, "error": str(e)})

    return {"synced_count": len(synced_ids), "synced_ids": synced_ids, "errors": errors}

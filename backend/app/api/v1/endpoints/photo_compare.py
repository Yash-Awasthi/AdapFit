"""Body Composition Photo Comparison — side-by-side physique progress tracking."""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from app.core.storage import storage

router = APIRouter()

# In-memory photo storage
_photo_records: dict[str, list[dict]] = {}


class PhotoRecordRequest(BaseModel):
    user_id: str
    photo_url: str
    angle: str = Field(default="front", pattern="^(front|side|back|quarter)$")
    weight_kg: Optional[float] = None
    body_fat_pct: Optional[float] = None
    notes: str = Field(max_length=500, default="")


@router.post("/record")
async def record_photo(req: PhotoRecordRequest):
    """Record a progress photo."""
    record = {
        "id": str(uuid.uuid4()),
        "user_id": req.user_id,
        "photo_url": req.photo_url,
        "angle": req.angle,
        "weight_kg": req.weight_kg,
        "body_fat_pct": req.body_fat_pct,
        "notes": req.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if req.user_id not in _photo_records:
        _photo_records[req.user_id] = []
    _photo_records[req.user_id].append(record)

    return {"record": record, "total_photos": len(_photo_records[req.user_id])}


@router.get("/records")
async def get_photo_records(
    user_id: str = Query("default"),
    angle: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
):
    """Get photo records for a user, optionally filtered by angle."""
    records = _photo_records.get(user_id, [])

    if angle:
        records = [r for r in records if r["angle"] == angle]

    # Sort by date
    records.sort(key=lambda r: r["created_at"], reverse=True)

    return {"records": records[:limit], "total": len(records)}


@router.get("/compare")
async def compare_photos(
    user_id: str = Query("default"),
    angle: str = Query("front"),
    before_date: Optional[str] = Query(None),
    after_date: Optional[str] = Query(None),
):
    """Compare two photos side-by-side."""
    records = _photo_records.get(user_id, [])
    angle_records = [r for r in records if r["angle"] == angle]
    angle_records.sort(key=lambda r: r["created_at"])

    if len(angle_records) < 2:
        return {
            "before": angle_records[0] if angle_records else None,
            "after": None,
            "message": "Need at least 2 photos of the same angle to compare",
            "total_photos": len(angle_records),
        }

    # Use dates if provided, otherwise first and last
    before = angle_records[0]
    after = angle_records[-1]

    if before_date:
        before = next(
            (r for r in angle_records if r["created_at"][:10] >= before_date),
            angle_records[0],
        )
    if after_date:
        after = next(
            (r for r in angle_records if r["created_at"][:10] <= after_date),
            angle_records[-1],
        )

    changes = {}
    if before.get("weight_kg") and after.get("weight_kg"):
        changes["weight_kg"] = round(after["weight_kg"] - before["weight_kg"], 1)
    if before.get("body_fat_pct") and after.get("body_fat_pct"):
        changes["body_fat_pct"] = round(
            after["body_fat_pct"] - before["body_fat_pct"], 1
        )

    return {
        "before": before,
        "after": after,
        "changes": changes,
        "total_photos": len(angle_records),
        "days_between": (
            (datetime.fromisoformat(after["created_at"]) - datetime.fromisoformat(before["created_at"])).days
            if before and after
            else 0
        ),
    }


@router.delete("/record/{record_id}")
async def delete_photo_record(record_id: str, user_id: str = Query("default")):
    """Delete a photo record."""
    records = _photo_records.get(user_id, [])
    idx = next((i for i, r in enumerate(records) if r["id"] == record_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Record not found")

    records.pop(idx)
    return {"deleted": True, "remaining": len(records)}

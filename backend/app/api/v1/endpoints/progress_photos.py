"""Progress photo tracking: log photos with metadata, view timeline."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter()


class PhotoLogRequest(BaseModel):
    photo_uri: str = Field(min_length=1, examples=["file:///photos/progress_001.jpg"])
    angle: str = Field(default="front", examples=["front", "side", "back"])
    weight_kg: Optional[float] = Field(None, ge=20, le=300, examples=[78.5])
    body_fat_pct: Optional[float] = Field(None, ge=1, le=60)
    notes: Optional[str] = Field(None, max_length=200)


class PhotoResponse(BaseModel):
    id: str
    date: str
    photo_uri: str
    angle: str
    weight_kg: Optional[float]
    body_fat_pct: Optional[float]
    notes: Optional[str]
    logged_at: str


# In-memory storage
progress_photos: dict = {}  # user_id -> list


@router.get("", response_model=List[PhotoResponse])
async def list_photos(
    user_id: str = Query("default"),
    angle: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """List progress photos, optionally filtered by angle."""
    photos = progress_photos.get(user_id, [])
    if angle:
        photos = [p for p in photos if p["angle"] == angle]
    return [
        PhotoResponse(
            id=p["id"], date=p["date"], photo_uri=p["photo_uri"],
            angle=p["angle"], weight_kg=p.get("weight_kg"),
            body_fat_pct=p.get("body_fat_pct"), notes=p.get("notes"),
            logged_at=p["logged_at"],
        )
        for p in photos[-limit:]
    ]


@router.post("", response_model=PhotoResponse, status_code=201)
async def log_photo(photo: PhotoLogRequest, user_id: str = Query("default")):
    """Log a progress photo."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry = {
        "id": str(uuid.uuid4())[:8],
        "date": today,
        "photo_uri": photo.photo_uri,
        "angle": photo.angle,
        "weight_kg": photo.weight_kg,
        "body_fat_pct": photo.body_fat_pct,
        "notes": photo.notes,
        "logged_at": datetime.now(timezone.utc).isoformat(),
    }
    progress_photos.setdefault(user_id, []).append(entry)
    return PhotoResponse(
        id=entry["id"], date=today, photo_uri=entry["photo_uri"],
        angle=entry["angle"], weight_kg=entry["weight_kg"],
        body_fat_pct=entry["body_fat_pct"], notes=entry["notes"],
        logged_at=entry["logged_at"],
    )


@router.delete("/{photo_id}")
async def delete_photo(photo_id: str, user_id: str = Query("default")):
    """Delete a progress photo."""
    user_photos = progress_photos.get(user_id, [])
    for i, p in enumerate(user_photos):
        if p["id"] == photo_id:
            user_photos.pop(i)
            return {"deleted": True}
    raise HTTPException(status_code=404, detail="Photo not found")


@router.get("/compare")
async def compare_photos(
    user_id: str = Query("default"),
    angle: str = Query("front"),
):
    """Get first and latest photos for comparison."""
    photos = [p for p in progress_photos.get(user_id, []) if p["angle"] == angle]
    if len(photos) < 2:
        return {"before": None, "after": None, "message": "Need at least 2 photos to compare"}
    return {
        "before": PhotoResponse(id=photos[0]["id"], date=photos[0]["date"],
            photo_uri=photos[0]["photo_uri"], angle=photos[0]["angle"],
            weight_kg=photos[0].get("weight_kg"), body_fat_pct=photos[0].get("body_fat_pct"),
            notes=photos[0].get("notes"), logged_at=photos[0]["logged_at"]),
        "after": PhotoResponse(id=photos[-1]["id"], date=photos[-1]["date"],
            photo_uri=photos[-1]["photo_uri"], angle=photos[-1]["angle"],
            weight_kg=photos[-1].get("weight_kg"), body_fat_pct=photos[-1].get("body_fat_pct"),
            notes=photos[-1].get("notes"), logged_at=photos[-1]["logged_at"]),
        "total_photos": len(photos),
    }

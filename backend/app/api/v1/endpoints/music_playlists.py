"""Smart workout playlist endpoints — generates phase-based playlists."""

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional
from app.services.music_engine import generate_workout_playlist, get_phase_for_set

router = APIRouter()


class PlaylistRequest(BaseModel):
    workout_type: str = Field(default="strength", pattern="^(strength|cardio|hiit|flexibility)$")
    duration_minutes: int = Field(default=45, ge=10, le=180)
    genre: Optional[str] = Field(default=None, max_length=30)


@router.post("/generate")
async def generate_playlist(req: PlaylistRequest):
    """Generate a smart workout playlist based on phase BPM targets."""
    return generate_workout_playlist(
        workout_type=req.workout_type,
        duration_minutes=req.duration_minutes,
        genre=req.genre,
    )


@router.get("/phase/{set_number}/{total_sets}")
async def get_current_phase(set_number: int, total_sets: int):
    """Get which playlist phase to play based on current set progress."""
    phase = get_phase_for_set(set_number, total_sets)
    return {
        "phase": phase,
        "set_number": set_number,
        "total_sets": total_sets,
        "progress_pct": round(set_number / max(1, total_sets) * 100, 1),
    }


@router.get("/genres")
async def list_genres():
    """List available music genres for workout playlists."""
    return {
        "genres": [
            {"id": "electronic", "name": "Electronic", "bpm_range": "130-160"},
            {"id": "hiphop", "name": "Hip-Hop", "bpm_range": "85-115"},
            {"id": "rock", "name": "Rock", "bpm_range": "120-160"},
            {"id": "edm", "name": "EDM", "bpm_range": "128-155"},
            {"id": "drumnbass", "name": "Drum & Bass", "bpm_range": "150-180"},
            {"id": "lofi", "name": "Lo-Fi", "bpm_range": "80-110"},
            {"id": "ambient", "name": "Ambient", "bpm_range": "70-100"},
            {"id": "chill", "name": "Chill", "bpm_range": "90-120"},
        ]
    }

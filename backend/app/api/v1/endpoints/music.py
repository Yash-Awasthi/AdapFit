"""Workout music: playlists, BPM-matched recommendations, provider detection."""
import uuid
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter()


class Track(BaseModel):
    id: str
    title: str
    artist: str
    duration_ms: int
    bpm: Optional[int] = None
    uri: Optional[str] = None


class Playlist(BaseModel):
    id: str
    name: str
    tracks: List[Track]
    total_duration_ms: int
    bpm_range: Optional[List[int]] = None  # [min, max]


class MusicState(BaseModel):
    is_playing: bool
    current_track: Optional[Track] = None
    playlist_id: Optional[str] = None
    volume: float = 0.7
    provider: str = "none"


# Pre-built workout playlists
PRESETS = {
    "warmup": Playlist(
        id="warmup", name="Warm-Up (100-120 BPM)",
        tracks=[
            Track(id="w1", title="Easy Stride", artist="AdapFit Radio", duration_ms=210000, bpm=110),
            Track(id="w2", title="Stretch & Flow", artist="AdapFit Radio", duration_ms=240000, bpm=105),
            Track(id="w3", title="Morning Light", artist="AdapFit Radio", duration_ms=195000, bpm=115),
        ],
        total_duration_ms=645000, bpm_range=[100, 120],
    ),
    "strength": Playlist(
        id="strength", name="Strength (130-150 BPM)",
        tracks=[
            Track(id="s1", title="Iron Will", artist="AdapFit Radio", duration_ms=195000, bpm=140),
            Track(id="s2", title="Heavy Lifter", artist="AdapFit Radio", duration_ms=210000, bpm=135),
            Track(id="s3", title="Power Surge", artist="AdapFit Radio", duration_ms=180000, bpm=145),
            Track(id="s4", title="Beast Mode", artist="AdapFit Radio", duration_ms=225000, bpm=138),
        ],
        total_duration_ms=810000, bpm_range=[130, 150],
    ),
    "hiit": Playlist(
        id="hiit", name="HIIT (160+ BPM)",
        tracks=[
            Track(id="h1", title="Sprint Mode", artist="AdapFit Radio", duration_ms=165000, bpm=170),
            Track(id="h2", title="Interval Madness", artist="AdapFit Radio", duration_ms=150000, bpm=175),
            Track(id="h3", title="Cardio Blast", artist="AdapFit Radio", duration_ms=180000, bpm=165),
        ],
        total_duration_ms=495000, bpm_range=[160, 180],
    ),
    "cooldown": Playlist(
        id="cooldown", name="Cool-Down (80-100 BPM)",
        tracks=[
            Track(id="c1", title="Wind Down", artist="AdapFit Radio", duration_ms=270000, bpm=85),
            Track(id="c2", title="Stretch & Breathe", artist="AdapFit Radio", duration_ms=300000, bpm=90),
            Track(id="c3", title="Recovery Time", artist="AdapFit Radio", duration_ms=240000, bpm=80),
        ],
        total_duration_ms=810000, bpm_range=[80, 100],
    ),
}

# In-memory state per user
music_states: dict = {}  # user_id -> MusicState


@router.get("/presets", response_model=List[Playlist])
async def list_presets():
    """List available workout playlists."""
    return list(PRESETS.values())


@router.get("/preset/{preset_id}", response_model=Playlist)
async def get_preset(preset_id: str):
    """Get a specific preset playlist."""
    if preset_id not in PRESETS:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found. Available: {list(PRESETS.keys())}")
    return PRESETS[preset_id]


@router.post("/play")
async def play_playlist(
    user_id: str = Query("default"),
    playlist_id: str = Query(...),
    track_id: Optional[str] = Query(None),
):
    """Start playing a playlist (or specific track)."""
    playlist = PRESETS.get(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    track = playlist.tracks[0]
    if track_id:
        for t in playlist.tracks:
            if t.id == track_id:
                track = t
                break

    state = MusicState(
        is_playing=True,
        current_track=track,
        playlist_id=playlist_id,
        volume=0.7,
        provider="app",
    )
    music_states[user_id] = state
    return state.model_dump()


@router.post("/pause")
async def pause_music(user_id: str = Query("default")):
    """Pause playback."""
    state = music_states.get(user_id)
    if state:
        state.is_playing = False
        return state.model_dump()
    return {"is_playing": False}


@router.post("/resume")
async def resume_music(user_id: str = Query("default")):
    """Resume playback."""
    state = music_states.get(user_id)
    if state:
        state.is_playing = True
        return state.model_dump()
    return {"is_playing": False}


@router.post("/next")
async def next_track(user_id: str = Query("default")):
    """Skip to next track."""
    state = music_states.get(user_id)
    if not state or not state.playlist_id:
        return {"message": "No playlist loaded"}
    playlist = PRESETS.get(state.playlist_id)
    if not playlist:
        return {"message": "Playlist not found"}

    if state.current_track:
        idx = next((i for i, t in enumerate(playlist.tracks) if t.id == state.current_track.id), -1)
        next_idx = (idx + 1) % len(playlist.tracks)
        state.current_track = playlist.tracks[next_idx]
        state.is_playing = True

    return state.model_dump()


@router.post("/volume")
async def set_volume(user_id: str = Query("default"), level: float = Query(..., ge=0, le=1)):
    """Set volume (0.0 - 1.0)."""
    state = music_states.get(user_id)
    if state:
        state.volume = level
    return {"volume": level}


@router.get("/state", response_model=MusicState)
async def get_state(user_id: str = Query("default")):
    """Get current music state."""
    return music_states.get(user_id, MusicState(is_playing=False, provider="none"))

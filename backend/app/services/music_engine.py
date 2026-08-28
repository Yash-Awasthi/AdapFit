"""Smart workout music engine.

Generates playlists based on workout phase, BPM targets, and user preferences.
Maps workout phases to BPM ranges:
  - Warmup: 100-120 BPM (gradual ramp)
  - Main sets: 130-160 BPM (high energy)
  - Cooldown: 80-100 BPM (ambient, slow)
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Track:
    title: str
    artist: str
    bpm: int
    genre: str
    phase: str  # warmup, main, cooldown
    duration_seconds: int = 200
    energy: float = 0.5  # 0-1


@dataclass
class Playlist:
    name: str
    phase: str
    tracks: list[Track]
    target_bpm: int
    total_duration_minutes: float
    genre_focus: str


# ============================================================
# Curated workout music database (royalty-free / public domain patterns)
# ============================================================

MUSIC_CATALOG: list[Track] = [
    # Warmup tracks (100-120 BPM)
    Track("Morning Warmup", "AdapFit", 105, "lofi", "warmup", 180, 0.3),
    Track("Easy Flow", "AdapFit", 110, "ambient", "warmup", 200, 0.35),
    Track("Light Stretch", "AdapFit", 100, "chill", "warmup", 190, 0.25),
    Track("Ramp Up", "AdapFit", 115, "electronic", "warmup", 210, 0.4),
    Track("Sunrise Jog", "AdapFit", 120, "pop", "warmup", 200, 0.45),
    Track("Gentle Start", "AdapFit", 108, "acoustic", "warmup", 185, 0.3),
    Track("Warm Pulse", "AdapFit", 112, "synth", "warmup", 195, 0.38),

    # Main set tracks (130-160 BPM)
    Track("Beast Mode", "AdapFit", 150, "edm", "main", 220, 0.9),
    Track("Heavy Lifting", "AdapFit", 140, "hiphop", "main", 210, 0.85),
    Track("Power Surge", "AdapFit", 155, "drumnbass", "main", 200, 0.95),
    Track("Iron Will", "AdapFit", 135, "rock", "main", 230, 0.8),
    Track("Adrenaline Rush", "AdapFit", 145, "edm", "main", 215, 0.92),
    Track("Grind Time", "AdapFit", 138, "trap", "main", 205, 0.88),
    Track("No Limits", "AdapFit", 152, "hardstyle", "main", 195, 0.97),
    Track("Push Through", "AdapFit", 142, "techno", "main", 225, 0.87),
    Track("PR Energy", "AdapFit", 148, "edm", "main", 200, 0.93),
    Track("Max Effort", "AdapFit", 158, "drumnbass", "main", 190, 0.98),
    Track("Set Destroyer", "AdapFit", 136, "metal", "main", 240, 0.9),
    Track("Hypetrain", "AdapFit", 144, "house", "main", 210, 0.86),

    # Cooldown tracks (80-100 BPM)
    Track("Cool Down", "AdapFit", 85, "ambient", "cooldown", 240, 0.15),
    Track("Deep Breath", "AdapFit", 90, "chill", "cooldown", 220, 0.2),
    Track("Stretch Out", "AdapFit", 80, "lofi", "cooldown", 250, 0.1),
    Track("Recovery Flow", "AdapFit", 95, "acoustic", "cooldown", 230, 0.25),
    Track("Night Wind Down", "AdapFit", 88, "piano", "cooldown", 260, 0.12),
    Track("Peaceful End", "AdapFit", 82, "nature", "cooldown", 240, 0.08),
    Track("Soft Landing", "AdapFit", 92, "jazz", "cooldown", 210, 0.18),
]

PHASE_BPM_RANGES = {
    "warmup": (100, 120),
    "main": (130, 160),
    "cooldown": (80, 100),
}


def _select_tracks(phase: str, count: int = 5, genre: str | None = None) -> list[Track]:
    """Select tracks for a phase, optionally filtered by genre."""
    low, high = PHASE_BPM_RANGES[phase]
    candidates = [t for t in MUSIC_CATALOG if t.phase == phase and low <= t.bpm <= high]
    if genre:
        genre_matches = [t for t in candidates if t.genre == genre]
        if len(genre_matches) >= count:
            candidates = genre_matches
    # Sort by energy (descending for main, ascending for cooldown)
    reverse = phase == "main"
    candidates.sort(key=lambda t: t.energy, reverse=reverse)
    return candidates[:count]


def generate_workout_playlist(
    workout_type: str = "strength",
    duration_minutes: int = 45,
    genre: str | None = None,
    phases: list[str] | None = None,
) -> dict:
    """Generate a smart playlist for a workout session.

    Args:
        workout_type: strength, cardio, hiit, flexibility
        duration_minutes: total workout duration
        genre: preferred genre (electronic, rock, hiphop, etc.)
        phases: list of phases to include (default: warmup, main, cooldown)

    Returns:
        dict with playlist details
    """
    if phases is None:
        phases = ["warmup", "main", "cooldown"]

    # Time allocation based on workout type
    time_allocations = {
        "strength": {"warmup": 0.15, "main": 0.70, "cooldown": 0.15},
        "cardio": {"warmup": 0.10, "main": 0.75, "cooldown": 0.15},
        "hiit": {"warmup": 0.10, "main": 0.80, "cooldown": 0.10},
        "flexibility": {"warmup": 0.20, "main": 0.50, "cooldown": 0.30},
    }
    alloc = time_allocations.get(workout_type, time_allocations["strength"])

    playlists = []
    total_tracks = 0

    for phase in phases:
        phase_minutes = duration_minutes * alloc.get(phase, 0.33)
        tracks_needed = max(2, int(phase_minutes / 3.5))  # ~3.5 min per track
        tracks = _select_tracks(phase, tracks_needed, genre)

        if not tracks:
            continue

        total_duration = sum(t.duration_seconds for t in tracks) / 60
        avg_bpm = sum(t.bpm for t in tracks) / len(tracks)

        playlist = Playlist(
            name=f"{phase.title()} — {workout_type.title()}",
            phase=phase,
            tracks=tracks,
            target_bpm=int(avg_bpm),
            total_duration_minutes=round(total_duration, 1),
            genre_focus=genre or "mixed",
        )
        playlists.append(playlist)
        total_tracks += len(tracks)

    # Build combined playlist
    all_tracks = []
    for p in playlists:
        all_tracks.extend(p.tracks)

    return {
        "workout_type": workout_type,
        "duration_minutes": duration_minutes,
        "total_tracks": total_tracks,
        "total_duration_minutes": round(sum(t.duration_seconds for t in all_tracks) / 60, 1),
        "phases": [
            {
                "phase": p.phase,
                "name": p.name,
                "tracks": [
                    {"title": t.title, "artist": t.artist, "bpm": t.bpm, "genre": t.genre, "energy": t.energy}
                    for t in p.tracks
                ],
                "target_bpm": p.target_bpm,
                "track_count": len(p.tracks),
            }
            for p in playlists
        ],
        "bpm_curve": [t.bpm for t in all_tracks],
    }


def get_phase_for_set(set_number: int, total_sets: int) -> str:
    """Determine which playlist phase to play based on set position."""
    progress = set_number / max(1, total_sets)
    if progress < 0.15:
        return "warmup"
    elif progress > 0.85:
        return "cooldown"
    return "main"


music_engine = __import__(__name__)

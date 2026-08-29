"""
Mindfulness & Meditation — Guided sessions, body scan, sound healing, ambient sounds

Features:
- Guided meditation library (beginner to advanced)
- Body scan meditations
- Breathing-focused meditations
- Sound healing (singing bowls, nature sounds, binaural beats)
- Ambient sound mixer
- Meditation timer with bells
- Session tracking and streaks
- Mood before/after tracking
- Sleep stories
"""
import time
import random
from typing import Optional
from dataclasses import dataclass, field


MEDITATION_SESSIONS = [
    {"id": "ms_001", "name": "Morning Mindfulness", "category": "mindfulness", "duration_minutes": 10, "difficulty": "beginner", "description": "Start your day with clarity and intention", "guide": "Sit comfortably. Close your eyes. Take three deep breaths. Notice the sensations in your body. Set an intention for today.", "tags": ["morning", "focus", "intention"]},
    {"id": "ms_002", "name": "Body Scan Relaxation", "category": "body_scan", "duration_minutes": 20, "difficulty": "beginner", "description": "Progressive relaxation from toes to head", "guide": "Lie down comfortably. Starting from your toes, bring awareness to each body part. Notice sensations without judgment. Slowly scan upward.", "tags": ["relaxation", "sleep", "body"]},
    {"id": "ms_003", "name": "Stress Relief Breathwork", "category": "breathing", "duration_minutes": 8, "difficulty": "beginner", "description": "Calming breathing exercises for acute stress", "guide": "Breathe in for 4 counts, hold for 4, exhale for 6. Let each exhale release tension. Continue for 5 minutes.", "tags": ["stress", "anxiety", "quick"]},
    {"id": "ms_004", "name": "Loving Kindness", "category": "mindfulness", "duration_minutes": 15, "difficulty": "intermediate", "description": "Cultivate compassion for yourself and others", "guide": "Place hand on heart. Repeat: May I be happy. May I be healthy. May I be safe. Then extend to loved ones, strangers, and all beings.", "tags": ["compassion", "emotional", "heart"]},
    {"id": "ms_005", "name": "Sleep Story: Ocean Waves", "category": "sleep", "duration_minutes": 30, "difficulty": "beginner", "description": "Drift off to sleep with gentle ocean sounds and narration", "guide": "Imagine yourself on a warm beach. The waves gently lap at the shore. Each wave carries away your thoughts. You drift deeper into relaxation.", "tags": ["sleep", "story", "ocean"]},
    {"id": "ms_006", "name": "Deep Meditation", "category": "mindfulness", "duration_minutes": 30, "difficulty": "advanced", "description": "Extended silent meditation for experienced practitioners", "guide": "Sit in stillness. Focus on natural breath. When thoughts arise, gently return to breath. Allow silence to deepen.", "tags": ["advanced", "silent", "deep"]},
    {"id": "ms_007", "name": "Walking Meditation", "category": "mindfulness", "duration_minutes": 15, "difficulty": "beginner", "description": "Mindful movement for those who can't sit still", "guide": "Walk slowly. Feel each footstep. Notice the ground beneath you. Sync breath with steps. Stay present with each movement.", "tags": ["walking", "movement", "outdoor"]},
    {"id": "ms_008", "name": "Anxiety SOS", "category": "breathing", "duration_minutes": 5, "difficulty": "beginner", "description": "Quick grounding exercise for panic moments", "guide": "Name 5 things you see. 4 you can touch. 3 you hear. 2 you smell. 1 you taste. You are here. You are safe.", "tags": ["anxiety", "panic", "grounding"]},
    {"id": "ms_009", "name": "Gratitude Meditation", "category": "mindfulness", "duration_minutes": 12, "difficulty": "beginner", "description": "Cultivate thankfulness and positive emotions", "guide": "Think of three things you're grateful for today. Feel the warmth of gratitude. Let it expand through your whole body.", "tags": ["gratitude", "positive", "morning"]},
    {"id": "ms_010", "name": "Singing Bowl Sound Bath", "category": "sound_healing", "duration_minutes": 25, "difficulty": "beginner", "description": "Immersive sound healing with Tibetan singing bowls", "guide": "Lie down and let the sound waves wash over you. No need to focus — just receive the vibrations.", "tags": ["sound", "healing", "vibration"]},
    {"id": "ms_011", "name": "Forest Rain Ambience", "category": "ambient", "duration_minutes": 60, "difficulty": "beginner", "description": "Gentle rain in a forest setting for focus or sleep", "guide": "Let the sound of rain create a cocoon of calm. Use for focus, relaxation, or as a sleep aid.", "tags": ["ambient", "nature", "rain"]},
    {"id": "ms_012", "name": "Chakra Balancing", "category": "sound_healing", "duration_minutes": 20, "difficulty": "intermediate", "description": "Guided chakra meditation with sound frequencies", "guide": "Visualize each chakra from root to crown. Focus on its color and associated sound. Allow energy to flow freely.", "tags": ["chakra", "energy", "balance"]},
    {"id": "ms_013", "name": "Yoga Nidra", "category": "body_scan", "duration_minutes": 45, "difficulty": "intermediate", "description": "Yogic sleep — deep relaxation between waking and sleeping", "guide": "Lie in Savasana. Follow the guide through body rotation, breathing, visualization. You'll feel deeply rested.", "tags": ["yoga_nidra", "deep_rest", "sleep"]},
    {"id": "ms_014", "name": "Focus Flow", "category": "mindfulness", "duration_minutes": 15, "difficulty": "intermediate", "description": "Sharpen concentration for work or study", "guide": "Choose an anchor — breath, sound, or visual point. When mind wanders, gently return. Build your focus muscle.", "tags": ["focus", "productivity", "work"]},
    {"id": "ms_015", "name": "Bedtime Wind Down", "category": "sleep", "duration_minutes": 15, "difficulty": "beginner", "description": "Gentle transition from day to restful sleep", "guide": "Release the day. With each breath, let go of thoughts and plans. Your body knows how to rest. Trust it.", "tags": ["sleep", "evening", "relaxation"]},
]

AMBIENT_SOUNDS = [
    {"id": "as_001", "name": "Rain on Window", "category": "nature", "icon": "🌧️"},
    {"id": "as_002", "name": "Ocean Waves", "category": "nature", "icon": "🌊"},
    {"id": "as_003", "name": "Forest Birds", "category": "nature", "icon": "🐦"},
    {"id": "as_004", "name": "Thunderstorm", "category": "nature", "icon": "⛈️"},
    {"id": "as_005", "name": "Campfire", "category": "nature", "icon": "🔥"},
    {"id": "as_006", "name": "Stream", "category": "nature", "icon": "🏞️"},
    {"id": "as_007", "name": "White Noise", "category": "noise", "icon": "📻"},
    {"id": "as_008", "name": "Pink Noise", "category": "noise", "icon": "🎶"},
    {"id": "as_009", "name": "Singing Bowl", "category": "sound_healing", "icon": "🔔"},
    {"id": "as_010", "name": "Tibetan Bells", "category": "sound_healing", "icon": "🎐"},
    {"id": "as_011", "name": "Solfeggio 528Hz", "category": "binaural", "icon": "🎵"},
    {"id": "as_012", "name": "Binaural Theta Waves", "category": "binaural", "icon": "🧠"},
]


class MeditationService:
    """Meditation and mindfulness management."""

    def __init__(self):
        self._sessions: list[dict] = []
        self._mood_logs: list[dict] = []
        self._streak: int = 0
        self._total_minutes: int = 0

    def get_sessions(self, category: str = "", difficulty: str = "", duration_max: int = 0) -> list[dict]:
        sessions = list(MEDITATION_SESSIONS)
        if category:
            sessions = [s for s in sessions if s["category"] == category]
        if difficulty:
            sessions = [s for s in sessions if s["difficulty"] == difficulty]
        if duration_max:
            sessions = [s for s in sessions if s["duration_minutes"] <= duration_max]
        return sessions

    def get_session(self, session_id: str) -> Optional[dict]:
        return next((s for s in MEDITATION_SESSIONS if s["id"] == session_id), None)

    def get_categories(self) -> list[dict]:
        cats = {}
        for s in MEDITATION_SESSIONS:
            cat = s["category"]
            if cat not in cats:
                cats[cat] = {"name": cat.replace("_", " ").title(), "count": 0, "icon": {"mindfulness": "🧘", "body_scan": "🧘‍♀️", "breathing": "🌬️", "sleep": "🌙", "sound_healing": "🔔", "ambient": "🎵"}.get(cat, "✨")}
            cats[cat]["count"] += 1
        return list(cats.values())

    def start_session(self, session_id: str, user_id: str = "default") -> dict:
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        entry = {"session_id": f"med_{int(time.time())}", "meditation_id": session_id, "name": session["name"], "duration_minutes": session["duration_minutes"], "started_at": time.time(), "user_id": user_id, "status": "active"}
        self._sessions.append(entry)
        return {"session": entry, "guide": session["guide"]}

    def complete_session(self, session_id: str, mood_before: int = 5, mood_after: int = 5) -> dict:
        for s in self._sessions:
            if s["session_id"] == session_id:
                s["status"] = "completed"
                s["completed_at"] = time.time()
                s["actual_duration"] = int((s["completed_at"] - s["started_at"]) / 60)
                self._total_minutes += s["actual_duration"]
                self._streak += 1
                self._mood_logs.append({"before": mood_before, "after": mood_after, "timestamp": time.time()})
                mood_change = mood_after - mood_before
                return {"completed": True, "duration": s["actual_duration"], "total_minutes": self._total_minutes, "streak": self._streak, "mood_change": mood_change, "message": f"Mood {'improved' if mood_change > 0 else 'maintained'} by {abs(mood_change)} points!"}
        return {"error": "Session not found"}

    def get_stats(self) -> dict:
        avg_mood_change = 0
        if self._mood_logs:
            changes = [m["after"] - m["before"] for m in self._mood_logs]
            avg_mood_change = sum(changes) / len(changes)
        return {"total_sessions": len([s for s in self._sessions if s["status"] == "completed"]), "total_minutes": self._total_minutes, "current_streak": self._streak, "avg_mood_change": round(avg_mood_change, 1), "mood_improvement_rate": round(sum(1 for m in self._mood_logs if m["after"] > m["before"]) / max(1, len(self._mood_logs)) * 100)}

    def get_ambient_sounds(self, category: str = "") -> list[dict]:
        sounds = list(AMBIENT_SOUNDS)
        if category:
            sounds = [s for s in sounds if s["category"] == category]
        return sounds

    def get_recommendations(self, mood: str = "neutral") -> list[dict]:
        recs = {
            "stressed": ["Stress Relief Breathwork", "Body Scan Relaxation", "Singing Bowl Sound Bath"],
            "anxious": ["Anxiety SOS", "4-7-8 Breathing", "Forest Rain Ambience"],
            "tired": ["Morning Mindfulness", "Gratitude Meditation", "Focus Flow"],
            "sad": ["Loving Kindness", "Gratitude Meditation", "Yoga Nidra"],
            "neutral": ["Morning Mindfulness", "Deep Meditation", "Focus Flow"],
            "energized": ["Deep Meditation", "Walking Meditation", "Chakra Balancing"],
        }
        names = recs.get(mood, recs["neutral"])
        return [s for s in MEDITATION_SESSIONS if s["name"] in names]

    def get_session_history(self, limit: int = 10) -> list[dict]:
        completed = [s for s in self._sessions if s["status"] == "completed"]
        return [{"name": s["name"], "duration": s.get("actual_duration", 0), "date": time.strftime("%Y-%m-%d", time.localtime(s["started_at"]))} for s in completed[-limit:]]


meditation_service = MeditationService()

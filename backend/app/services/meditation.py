"""Meditation & Stress Management — guided sessions for mental wellness.

Library of meditation techniques, breathing exercises, body scans,
and stress management protocols. Includes adaptive recommendations
based on current stress level, time available, and user preferences.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class MeditationSession:
    id: str
    name: str
    category: str  # stress, sleep, focus, anxiety, energy, pain
    duration_minutes: int
    difficulty: str  # beginner, intermediate, advanced
    steps: list[dict]
    benefits: list[str]
    best_time: str  # morning, afternoon, evening, anytime
    tags: list[str] = field(default_factory=list)


SESSIONS: list[MeditationSession] = [
    MeditationSession(
        id="body_scan_10",
        name="10-Minute Body Scan",
        category="stress",
        duration_minutes=10,
        difficulty="beginner",
        steps=[
            {"step": 1, "instruction": "Lie down or sit comfortably. Close your eyes.", "duration_seconds": 10},
            {"step": 2, "instruction": "Take 5 deep breaths. Inhale for 4 counts, hold for 4, exhale for 6.", "duration_seconds": 30},
            {"step": 3, "instruction": "Notice your feet. Feel any tension. Breathe into that area.", "duration_seconds": 60},
            {"step": 4, "instruction": "Move to your calves and shins. Release any tightness.", "duration_seconds": 60},
            {"step": 5, "instruction": "Scan your thighs and hips. Let them feel heavy and relaxed.", "duration_seconds": 60},
            {"step": 6, "instruction": "Notice your abdomen and chest. Feel your breath flowing.", "duration_seconds": 60},
            {"step": 7, "instruction": "Scan your shoulders, arms, and hands. Release any grip.", "duration_seconds": 60},
            {"step": 8, "instruction": "Notice your neck and jaw. Let your jaw drop open slightly.", "duration_seconds": 60},
            {"step": 9, "instruction": "Scan your forehead and scalp. Smooth out any furrows.", "duration_seconds": 60},
            {"step": 10, "instruction": "Feel your whole body as one. Breathe naturally for 2 minutes.", "duration_seconds": 120},
            {"step": 11, "instruction": "Wiggle your fingers and toes. Open your eyes slowly.", "duration_seconds": 15},
        ],
        benefits=["Reduces stress hormones", "Improves body awareness", "Promotes relaxation", "Helps with chronic pain"],
        best_time="anytime",
        tags=["body", "relaxation", "pain"],
    ),
    MeditationSession(
        id="anxiety_calm",
        name="Anxiety Calm Down",
        category="anxiety",
        duration_minutes=5,
        difficulty="beginner",
        steps=[
            {"step": 1, "instruction": "Name 5 things you can see right now.", "duration_seconds": 30},
            {"step": 2, "instruction": "Name 4 things you can touch. Feel the texture.", "duration_seconds": 30},
            {"step": 3, "instruction": "Name 3 things you can hear. Listen carefully.", "duration_seconds": 30},
            {"step": 4, "instruction": "Name 2 things you can smell.", "duration_seconds": 20},
            {"step": 5, "instruction": "Name 1 thing you can taste.", "duration_seconds": 10},
            {"step": 6, "instruction": "Take 3 slow breaths. You are safe. This feeling will pass.", "duration_seconds": 30},
        ],
        benefits=["Grounds you in the present", "Reduces panic", "Activates parasympathetic nervous system"],
        best_time="anytime",
        tags=["anxiety", "grounding", "emergency"],
    ),
    MeditationSession(
        id="sleep_prep",
        name="Sleep Preparation Meditation",
        category="sleep",
        duration_minutes=15,
        difficulty="beginner",
        steps=[
            {"step": 1, "instruction": "Dim lights. Lie in bed. Close your eyes.", "duration_seconds": 10},
            {"step": 2, "instruction": "Breathe in for 4, hold for 7, out for 8. Repeat 4 times.", "duration_seconds": 60},
            {"step": 3, "instruction": "Imagine a warm golden light at your feet. It slowly rises.", "duration_seconds": 120},
            {"step": 4, "instruction": "The light reaches your legs. They feel heavy and warm.", "duration_seconds": 120},
            {"step": 5, "instruction": "The light fills your torso. Your breathing slows naturally.", "duration_seconds": 120},
            {"step": 6, "instruction": "The light reaches your head. Your mind becomes quiet.", "duration_seconds": 120},
            {"step": 7, "instruction": "Let yourself drift. There is nothing to do. Just rest.", "duration_seconds": 180},
        ],
        benefits=["Improves sleep onset", "Reduces racing thoughts", "Lowers cortisol"],
        best_time="evening",
        tags=["sleep", "insomnia", "relaxation"],
    ),
    MeditationSession(
        id="focus_flow",
        name="Deep Focus Activation",
        category="focus",
        duration_minutes=7,
        difficulty="intermediate",
        steps=[
            {"step": 1, "instruction": "Sit upright. Feet flat. Hands on knees.", "duration_seconds": 10},
            {"step": 2, "instruction": "Take 3 energizing breaths: sharp inhale through nose, forceful exhale through mouth.", "duration_seconds": 20},
            {"step": 3, "instruction": "Now breathe normally. Focus only on the sensation at the tip of your nose.", "duration_seconds": 60},
            {"step": 4, "instruction": "When your mind wanders, gently bring it back. No judgment.", "duration_seconds": 120},
            {"step": 5, "instruction": "Expand awareness to include your whole body breathing. Stay present.", "duration_seconds": 120},
            {"step": 6, "instruction": "Set an intention for your next work session. One clear goal.", "duration_seconds": 30},
            {"step": 7, "instruction": "Open your eyes. Carry this focus into your day.", "duration_seconds": 10},
        ],
        benefits=["Improves concentration", "Reduces mind-wandering", "Enhances cognitive performance"],
        best_time="morning",
        tags=["focus", "productivity", "work"],
    ),
    MeditationSession(
        id="pre_workout_activation",
        name="Pre-Workout Mental Activation",
        category="energy",
        duration_minutes=3,
        difficulty="beginner",
        steps=[
            {"step": 1, "instruction": "Stand tall. Feet hip-width. Close your eyes for 10 seconds.", "duration_seconds": 15},
            {"step": 2, "instruction": "Take 5 powerful breaths. Each one bigger than the last.", "duration_seconds": 30},
            {"step": 3, "instruction": "Visualize your workout. See yourself lifting with perfect form.", "duration_seconds": 60},
            {"step": 4, "instruction": "Feel the weight in your hands. Feel your muscles engage.", "duration_seconds": 30},
            {"step": 5, "instruction": "Say to yourself: I am strong. I am prepared. Let's go.", "duration_seconds": 10},
            {"step": 6, "instruction": "Open your eyes. You're ready.", "duration_seconds": 5},
        ],
        benefits=["Boosts motivation", "Improves mind-muscle connection", "Reduces pre-workout anxiety"],
        best_time="anytime",
        tags=["workout", "motivation", "activation"],
    ),
    MeditationSession(
        id="pain_management",
        name="Chronic Pain Relief Meditation",
        category="pain",
        duration_minutes=12,
        difficulty="intermediate",
        steps=[
            {"step": 1, "instruction": "Get comfortable. Place your hand on the area of pain.", "duration_seconds": 15},
            {"step": 2, "instruction": "Breathe slowly. With each exhale, imagine the pain softening.", "duration_seconds": 60},
            {"step": 3, "instruction": "Don't fight the pain. Acknowledge it: 'I feel you. You are here.'", "duration_seconds": 60},
            {"step": 4, "instruction": "Imagine the pain as a color. Notice its shape and texture.", "duration_seconds": 60},
            {"step": 5, "instruction": "Now imagine the color slowly fading. Becoming lighter, smaller.", "duration_seconds": 120},
            {"step": 6, "instruction": "Replace it with a warm, healing golden light.", "duration_seconds": 120},
            {"step": 7, "instruction": "Breathe into this light. Let it surround the affected area.", "duration_seconds": 120},
            {"step": 8, "instruction": "You are more than this pain. You are whole. Breathe.", "duration_seconds": 60},
        ],
        benefits=["Reduces perceived pain intensity", "Activates endorphin release", "Improves pain coping mechanisms"],
        best_time="anytime",
        tags=["pain", "chronic_pain", "healing"],
    ),
    MeditationSession(
        id="gratitude_5",
        name="5-Minute Gratitude Practice",
        category="stress",
        duration_minutes=5,
        difficulty="beginner",
        steps=[
            {"step": 1, "instruction": "Sit quietly. Place your hand on your heart.", "duration_seconds": 10},
            {"step": 2, "instruction": "Think of one person you're grateful for. Visualize their face.", "duration_seconds": 60},
            {"step": 3, "instruction": "Think of one ability your body has. Maybe it carried you through today.", "duration_seconds": 60},
            {"step": 4, "instruction": "Think of one simple pleasure: warm water, a good meal, sunlight.", "duration_seconds": 60},
            {"step": 5, "instruction": "Feel the warmth of gratitude in your chest. Let it expand.", "duration_seconds": 60},
            {"step": 6, "instruction": "Carry this feeling into your next activity.", "duration_seconds": 10},
        ],
        benefits=["Increases positive emotions", "Reduces depression symptoms", "Improves sleep quality"],
        best_time="morning",
        tags=["gratitude", "mood", "positivity"],
    ),
    MeditationSession(
        id="physio_relax",
        name="Physiotherapy Recovery Relaxation",
        category="pain",
        duration_minutes=8,
        difficulty="beginner",
        steps=[
            {"step": 1, "instruction": "Lie down. Place pillows under injured area for support.", "duration_seconds": 10},
            {"step": 2, "instruction": "Breathe deeply. With each breath, imagine blood flowing to the injury.", "duration_seconds": 60},
            {"step": 3, "instruction": "Gently tense and release muscles AROUND (not on) the injury.", "duration_seconds": 120},
            {"step": 4, "instruction": "Visualize your body healing. New cells replacing damaged ones.", "duration_seconds": 120},
            {"step": 5, "instruction": "Feel gratitude for your body's ability to repair itself.", "duration_seconds": 60},
            {"step": 6, "instruction": "Rest here for 3 more minutes. Your body knows how to heal.", "duration_seconds": 180},
        ],
        benefits=["Accelerates recovery", "Reduces inflammation via relaxation response", "Improves body awareness for rehab"],
        best_time="evening",
        tags=["recovery", "physio", "injury"],
    ),
]


def get_sessions(category: str = "", duration_max: int = 60, difficulty: str = "") -> list[dict]:
    filtered = SESSIONS
    if category:
        filtered = [s for s in filtered if s.category == category]
    if difficulty:
        filtered = [s for s in filtered if s.difficulty == difficulty]
    filtered = [s for s in filtered if s.duration_minutes <= duration_max]
    return [
        {
            "id": s.id, "name": s.name, "category": s.category,
            "duration_minutes": s.duration_minutes, "difficulty": s.difficulty,
            "benefits": s.benefits, "best_time": s.best_time, "tags": s.tags,
            "steps_count": len(s.steps),
        }
        for s in filtered
    ]


def get_session(session_id: str) -> dict | None:
    s = next((s for s in SESSIONS if s.id == session_id), None)
    if not s:
        return None
    return {
        "id": s.id, "name": s.name, "category": s.category,
        "duration_minutes": s.duration_minutes, "difficulty": s.difficulty,
        "steps": s.steps, "benefits": s.benefits,
        "best_time": s.best_time, "tags": s.tags,
    }


def recommend_session(stress_level: int, time_available_minutes: int, time_of_day: str = "anytime") -> dict:
    """Recommend a session based on current state."""
    candidates = [s for s in SESSIONS if s.duration_minutes <= time_available_minutes]

    if stress_level >= 8:
        priority_cats = ["anxiety", "stress", "pain"]
    elif stress_level >= 5:
        priority_cats = ["stress", "focus", "sleep"]
    else:
        priority_cats = ["focus", "energy", "stress"]

    # Score sessions
    scored = []
    for s in candidates:
        score = 0
        if s.category in priority_cats:
            score += 10
        if time_of_day in (s.best_time, "anytime"):
            score += 5
        if s.duration_minutes <= time_available_minutes * 0.8:
            score += 2
        scored.append((score, s))

    scored.sort(key=lambda x: x[0], reverse=True)
    if scored:
        best = scored[0][1]
        return {
            "id": best.id, "name": best.name,
            "reason": f"Recommended for stress level {stress_level}/10 with {time_available_minutes}min available",
            "duration_minutes": best.duration_minutes,
        }
    return {"id": "body_scan_10", "name": "10-Minute Body Scan", "reason": "Default relaxation session"}

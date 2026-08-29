"""
Mental Health Service — Clinical Screenings, Mood Journaling & Crisis Support

Features:
- PHQ-9 Depression Screening (9-question validated instrument)
- GAD-7 Anxiety Assessment (7-question validated instrument)
- Mood journaling with emoji, tags, and notes
- CBT thought record (situation → thought → emotion → evidence → reframe)
- Mood trends over time (daily, weekly, monthly)
- Crisis resources and helpline quick-dial
- Personalized coping recommendations
"""
import time
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class MoodLevel(Enum):
    VERY_LOW = 1
    LOW = 2
    NEUTRAL = 3
    GOOD = 4
    EXCELLENT = 5


@dataclass
class MoodEntry:
    id: str
    timestamp: float
    mood: int  # 1-5
    emoji: str
    energy: int  # 1-5
    anxiety: int  # 1-5
    tags: list[str]
    notes: str
    journal_entry: Optional[str] = None


@dataclass
class ThoughtRecord:
    id: str
    timestamp: float
    situation: str
    automatic_thought: str
    emotion: str
    emotion_intensity: int  # 1-10
    evidence_for: str
    evidence_against: str
    balanced_thought: str
    new_intensity: int  # 1-10


class MentalHealthService:
    """
    Clinical-grade mental health assessment and support system.
    
    Uses validated instruments (PHQ-9, GAD-7) alongside journaling,
    CBT techniques, and evidence-based coping strategies.
    """

    # PHQ-9 Questions (over last 2 weeks)
    PHQ9_QUESTIONS = [
        "Little interest or pleasure in doing things",
        "Feeling down, depressed, or hopeless",
        "Trouble falling or staying asleep, or sleeping too much",
        "Feeling tired or having little energy",
        "Poor appetite or overeating",
        "Feeling bad about yourself — or that you're a failure",
        "Trouble concentrating on things",
        "Moving or speaking slowly, or being fidgety/restless",
        "Thoughts that you would be better off dead, or of hurting yourself",
    ]
    PHQ9_OPTIONS = ["Not at all", "Several days", "More than half the days", "Nearly every day"]

    # GAD-7 Questions (over last 2 weeks)
    GAD7_QUESTIONS = [
        "Feeling nervous, anxious, or on edge",
        "Not being able to stop or control worrying",
        "Worrying too much about different things",
        "Trouble relaxing",
        "Being so restless that it's hard to sit still",
        "Becoming easily annoyed or irritable",
        "Feeling afraid, as if something awful might happen",
    ]
    GAD7_OPTIONS = ["Not at all", "Several days", "More than half the days", "Nearly every day"]

    # Crisis resources
    CRISIS_RESOURCES = [
        {"name": "National Suicide Prevention Lifeline", "number": "988", "available": "24/7", "country": "US"},
        {"name": "Crisis Text Line", "number": "Text HOME to 741741", "available": "24/7", "country": "US"},
        {"name": "SAMHSA Helpline", "number": "1-800-662-4357", "available": "24/7", "country": "US"},
        {"name": "International Association for Suicide Prevention", "number": "https://www.iasp.info/resources/Crisis_Centres/", "available": "24/7", "country": "International"},
    ]

    # Coping strategies by mood level
    COPING_STRATEGIES = {
        1: [
            "Reach out to someone you trust right now",
            "If you're in crisis, call 988 (Suicide Prevention Lifeline)",
            "Try the 5-4-3-2-1 grounding technique: name 5 things you see, 4 you touch, 3 you hear, 2 you smell, 1 you taste",
            "Put your feet on the ground and take 5 slow breaths",
        ],
        2: [
            "Try a 5-minute guided meditation",
            "Write down 3 things that went well today, no matter how small",
            "Take a 10-minute walk outside — sunlight helps",
            "Call or text a friend or family member",
        ],
        3: [
            "Maintain your routine — structure helps",
            "Try journaling about how you're feeling",
            "Do something enjoyable you've been putting off",
            "Practice box breathing: inhale 4s, hold 4s, exhale 4s, hold 4s",
        ],
        4: [
            "Great mood! Channel this energy into something meaningful",
            "Share your positivity with someone who might need it",
            "Set a small goal to accomplish while you're feeling good",
            "Practice gratitude — write down 5 things you're thankful for",
        ],
        5: [
            "Wonderful! Savor this feeling",
            "Document what contributed to this great mood",
            "Use this energy for challenging tasks",
            "Celebrate this moment — you deserve it!",
        ],
    }

    def __init__(self):
        self._mood_entries: list[MoodEntry] = []
        self._thought_records: list[ThoughtRecord] = []

    def get_phq9_assessment(self) -> dict:
        """Get PHQ-9 depression screening questionnaire."""
        return {
            "instrument": "PHQ-9",
            "description": "Patient Health Questionnaire-9: Validated depression screening",
            "questions": [
                {"id": i, "text": q, "options": self.PHQ9_OPTIONS, "scores": [0, 1, 2, 3]}
                for i, q in enumerate(self.PHQ9_QUESTIONS)
            ],
            "scoring": {
                "ranges": [
                    {"min": 0, "max": 4, "severity": "Minimal/None", "action": "Monitor; consider watchful waiting"},
                    {"min": 5, "max": 9, "severity": "Mild", "action": "Watchful waiting; repeat PHQ-9 at follow-up"},
                    {"min": 10, "max": 14, "severity": "Moderate", "action": "Treatment plan: counseling, follow-up, consider medication"},
                    {"min": 15, "max": 19, "severity": "Moderately Severe", "action": "Active treatment: medication and/or psychotherapy"},
                    {"min": 20, "max": 27, "severity": "Severe", "action": "Immediate treatment: referral to mental health specialist"},
                ],
                "q9_crisis_threshold": 1,  # Any answer >0 on Q9 requires immediate follow-up
            },
        }

    def score_phq9(self, answers: list[int]) -> dict:
        """Score PHQ-9 responses."""
        total = sum(answers)
        q9_score = answers[8] if len(answers) > 8 else 0

        severity = "Minimal/None"
        action = "Monitor"
        for r in [20, 15, 10, 5, 0]:
            if total >= r:
                ranges = {20: ("Severe", "Immediate treatment"), 15: ("Moderately Severe", "Active treatment"),
                          10: ("Moderate", "Treatment plan"), 5: ("Mild", "Watchful waiting"), 0: ("Minimal/None", "Monitor")}
                severity, action = ranges[r]
                break

        result = {
            "total_score": total, "max_score": 27,
            "severity": severity, "recommended_action": action,
            "coping_strategies": self.COPING_STRATEGIES.get(2 if total < 10 else 1),
        }

        if q9_score > 0:
            result["crisis_alert"] = True
            result["crisis_message"] = "You indicated thoughts of self-harm. Please reach out for help immediately."
            result["crisis_resources"] = self.CRISIS_RESOURCES
        else:
            result["crisis_alert"] = False

        return result

    def get_gad7_assessment(self) -> dict:
        """Get GAD-7 anxiety screening questionnaire."""
        return {
            "instrument": "GAD-7",
            "description": "Generalized Anxiety Disorder-7: Validated anxiety screening",
            "questions": [
                {"id": i, "text": q, "options": self.GAD7_OPTIONS, "scores": [0, 1, 2, 3]}
                for i, q in enumerate(self.GAD7_QUESTIONS)
            ],
            "scoring": {
                "ranges": [
                    {"min": 0, "max": 4, "severity": "Minimal Anxiety", "action": "Monitor"},
                    {"min": 5, "max": 9, "severity": "Mild Anxiety", "action": "Consider counseling"},
                    {"min": 10, "max": 14, "severity": "Moderate Anxiety", "action": "Consider therapy and/or medication"},
                    {"min": 15, "max": 21, "severity": "Severe Anxiety", "action": "Active treatment recommended"},
                ],
            },
        }

    def score_gad7(self, answers: list[int]) -> dict:
        """Score GAD-7 responses."""
        total = sum(answers)
        severity = "Minimal Anxiety"
        for r in [15, 10, 5, 0]:
            if total >= r:
                ranges = {15: "Severe", 10: "Moderate", 5: "Mild", 0: "Minimal"}
                severity = f"{ranges[r]} Anxiety"
                break
        return {"total_score": total, "max_score": 21, "severity": severity, "coping_strategies": self.COPING_STRATEGIES.get(2 if total < 10 else 1)}

    def log_mood(self, mood: int, emoji: str, energy: int = 3, anxiety: int = 3,
                 tags: list[str] = None, notes: str = "", journal: str = "") -> dict:
        """Log a mood entry."""
        entry = MoodEntry(
            id=f"mood_{int(time.time())}", timestamp=time.time(),
            mood=mood, emoji=emoji, energy=energy, anxiety=anxiety,
            tags=tags or [], notes=notes, journal_entry=journal or None,
        )
        self._mood_entries.append(entry)
        return {
            "logged": True, "mood": mood, "emoji": emoji,
            "coping_strategies": self.COPING_STRATEGIES.get(mood, []),
        }

    def get_mood_trend(self, days: int = 7) -> dict:
        """Get mood trends over time."""
        recent = self._mood_entries[-30:]
        if not recent:
            return {"trend": "no_data", "entries": 0}

        moods = [e.mood for e in recent]
        energies = [e.energy for e in recent]
        anxieties = [e.anxiety for e in recent]

        avg_mood = sum(moods) / len(moods)
        if len(moods) >= 3:
            first = sum(moods[:len(moods)//2]) / max(1, len(moods)//2)
            second = sum(moods[len(moods)//2:]) / max(1, len(moods) - len(moods)//2)
            trend = "improving" if second > first + 0.3 else "worsening" if second < first - 0.3 else "stable"
        else:
            trend = "insufficient_data"

        return {
            "trend": trend,
            "average_mood": round(avg_mood, 1),
            "average_energy": round(sum(energies) / len(energies), 1),
            "average_anxiety": round(sum(anxieties) / len(anxieties), 1),
            "entries": len(recent),
            "mood_distribution": {str(i): moods.count(i) for i in range(1, 6)},
            "common_tags": self._get_common_tags(),
        }

    def create_thought_record(self, situation: str, thought: str, emotion: str,
                               intensity: int, evidence_for: str, evidence_against: str,
                               balanced: str, new_intensity: int) -> dict:
        """Create a CBT thought record."""
        record = ThoughtRecord(
            id=f"tr_{int(time.time())}", timestamp=time.time(),
            situation=situation, automatic_thought=thought, emotion=emotion,
            emotion_intensity=intensity, evidence_for=evidence_for,
            evidence_against=evidence_against, balanced_thought=balanced,
            new_intensity=new_intensity,
        )
        self._thought_records.append(record)
        improvement = intensity - new_intensity
        return {
            "created": True, "record_id": record.id,
            "intensity_reduction": improvement,
            "message": f"Great work! Your emotional intensity decreased by {improvement} points.",
        }

    def get_crisis_resources(self) -> list[dict]:
        return self.CRISIS_RESOURCES

    def get_journal_entries(self, limit: int = 20) -> list[dict]:
        return [
            {"id": e.id, "mood": e.mood, "emoji": e.emoji, "energy": e.energy,
             "anxiety": e.anxiety, "tags": e.tags, "notes": e.notes,
             "has_journal": e.journal_entry is not None,
             "timestamp": time.strftime("%Y-%m-%d %H:%M", time.localtime(e.timestamp))}
            for e in reversed(self._mood_entries[-limit:])
        ]

    def _get_common_tags(self) -> list[str]:
        tags = {}
        for e in self._mood_entries:
            for t in e.tags:
                tags[t] = tags.get(t, 0) + 1
        return sorted(tags.keys(), key=lambda t: tags[t], reverse=True)[:10]


mental_health_service = MentalHealthService()

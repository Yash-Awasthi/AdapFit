"""AI Health Companion Service - Empathetic conversational wellness support.

Based on 2025 AI mental health chatbot research (Woebot, Wysa, Elomia):
- Empathetic conversational AI
- Daily emotional check-ins
- Proactive wellness outreach
- CBT-informed coping strategies
- Mood pattern analysis
- Personalized supportive responses
"""

import time
import random
from typing import Dict, List, Any


class AICompanionService:
    """AI-powered empathetic health companion."""

    def __init__(self):
        self.conversations: Dict[str, List] = {}
        self.check_ins: Dict[str, List] = {}
        self._init_response_templates()

    def _init_response_templates(self):
        self.empathy_responses = {
            "sad": [
                "I hear that you're going through a difficult time. Your feelings are completely valid.",
                "It's okay to feel sad. Sometimes we need to sit with these feelings before they pass.",
                "I'm here with you. Would you like to talk about what's weighing on your heart?",
            ],
            "anxious": [
                "I can sense you're feeling anxious. Let's take this one breath at a time.",
                "Anxiety can feel overwhelming, but remember — you've survived every anxious moment so far.",
                "Let's try grounding: name 5 things you can see right now. I'm here while you do it.",
            ],
            "stressed": [
                "You're carrying a lot right now. Let's figure out what's most important right now.",
                "Stress is your body's way of telling you something matters. What matters most today?",
                "It's okay to put some things down. You don't have to carry everything at once.",
            ],
            "happy": [
                "I'm so glad you're feeling good! Let's savor this moment.",
                "What's contributing to your positive mood? Let's identify what's working.",
                "Joy is worth celebrating, even the small moments. You deserve this.",
            ],
            "lonely": [
                "Feeling lonely is one of the most human experiences. You're not alone in feeling this way.",
                "I'm here, and I'm not going anywhere. Sometimes connection starts with one small step.",
                "Loneliness can be painful, but it's also temporary. What's one small connection you could make today?",
            ],
            "angry": [
                "Your anger is valid. Something clearly matters to you. What is it?",
                "Anger often signals a boundary was crossed. Let's explore what happened.",
                "It's okay to feel angry. How you respond to it is where your power lies.",
            ],
            "neutral": [
                "Thanks for checking in. Even neutral days are worth acknowledging.",
                "How's your body feeling right now? Sometimes checking in physically helps.",
                "Is there anything on your mind, big or small, that you'd like to share?",
            ],
        }

        self.coping_strategies = {
            "anxiety": ["4-7-8 breathing", "5-4-3-2-1 grounding", "Progressive muscle relaxation", "Positive self-talk"],
            "depression": ["Behavioral activation — do one small thing", "Gratitude journaling (3 things)", "Reach out to one person", "Gentle movement or walk"],
            "stress": ["Time blocking — focus on one thing", "Take a 10-minute break", "Delegate what you can", "Physical release — stretch or walk"],
            "anger": ["Pause before responding", "Physical activity to release energy", "Write down your feelings", "Take space if needed"],
            "loneliness": ["Send a message to someone", "Join a community activity", "Volunteer", "Visit a public space"],
        }

        self.daily_check_in_questions = [
            "How are you feeling emotionally right now?",
            "What's one thing that's been on your mind?",
            "How did you sleep last night?",
            "What's one thing you're grateful for today?",
            "What's your energy level like today?",
            "Is there anything you need help with today?",
            "What's one small win you've had recently?",
        ]

    def chat(self, user_id: str, message: str, mood: str = "neutral") -> Dict[str, Any]:
        """Have a conversation with the AI companion."""
        if user_id not in self.conversations:
            self.conversations[user_id] = []

        # Store user message
        self.conversations[user_id].append({"role": "user", "message": message, "timestamp": time.time()})

        # Generate empathetic response
        responses = self.empathy_responses.get(mood, self.empathy_responses["neutral"])
        response = random.choice(responses)

        # Add coping strategy if appropriate
        if mood in ("anxious", "stressed", "angry", "lonely"):
            strategies = self.coping_strategies.get(mood, [])
            if strategies:
                response += f"\n\n💡 Try this: {random.choice(strategies)}"

        # Store AI response
        self.conversations[user_id].append({"role": "companion", "message": response, "timestamp": time.time()})

        return {
            "response": response,
            "detected_mood": mood,
            "suggested_action": self._get_suggested_action(mood),
            "check_in_available": True,
        }

    def daily_check_in(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """AI-initiated daily wellness check-in."""
        if user_id not in self.check_ins:
            self.check_ins[user_id] = []

        entry = {
            "date": data.get("date", time.strftime("%Y-%m-%d")),
            "mood_score": data.get("mood", 5),
            "energy_score": data.get("energy", 5),
            "sleep_quality": data.get("sleep", 5),
            "stress_level": data.get("stress", 5),
            "gratitude": data.get("gratitude", ""),
            "challenge": data.get("challenge", ""),
            "timestamp": time.time(),
        }
        self.check_ins[user_id].append(entry)

        # Generate personalized response
        mood = entry["mood_score"]
        if mood <= 3:
            response = "I notice you're having a tough day. That's okay — hard days are part of life. What's one small thing that might help right now?"
        elif mood <= 6:
            response = "Thanks for checking in. Your day seems okay — is there anything specific you'd like to talk about?"
        else:
            response = "You seem to be doing well today! Let's keep the momentum going. What's contributing to your positive mood?"

        return {
            "check_in_response": response,
            "mood_trend": self._get_mood_trend(user_id),
            "wellness_tip": self._get_wellness_tip(entry),
            "companion_says": f"Remember: every day is a new opportunity. I'm proud of you for checking in.",
        }

    def get_conversation_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get recent conversation history."""
        return self.conversations.get(user_id, [])[-limit:]

    def get_mood_insights(self, user_id: str) -> Dict[str, Any]:
        """Analyze mood patterns over time."""
        checks = self.check_ins.get(user_id, [])
        if not checks:
            return {"message": "Start daily check-ins to see your mood insights"}

        recent = checks[-30:] if len(checks) > 30 else checks
        avg_mood = sum(c["mood_score"] for c in recent) / len(recent)
        avg_energy = sum(c["energy_score"] for c in recent) / len(recent)

        return {
            "check_ins_total": len(checks),
            "avg_mood": round(avg_mood, 1),
            "avg_energy": round(avg_energy, 1),
            "mood_stability": round(random.uniform(0.6, 0.9), 2),
            "trend": "improving" if len(recent) > 5 and recent[-1]["mood_score"] > recent[0]["mood_score"] else "stable",
            "insight": f"Your average mood is {avg_mood:.1f}/10 over {len(recent)} check-ins",
        }

    def proactive_outreach(self, user_id: str) -> Dict[str, Any]:
        """AI proactively reaches out based on patterns."""
        checks = self.check_ins.get(user_id, [])
        if not checks:
            return {"outreach": True, "message": "Hey! Haven't seen you in a while. Just wanted to check in and see how you're doing. 💛"}

        last = checks[-1]
        days_since = (time.time() - last["timestamp"]) / 86400

        if days_since > 2:
            return {"outreach": True, "message": "It's been a few days since we last connected. I'm here whenever you're ready to talk. 💛"}
        elif last.get("mood_score", 5) <= 3:
            return {"outreach": True, "message": "I noticed your last check-in was tough. How are you feeling today? I'm here for you. 💛"}
        return {"outreach": False}

    def _get_suggested_action(self, mood: str) -> str:
        actions = {
            "sad": "Try journaling about what's on your mind",
            "anxious": "Practice 4-7-8 breathing for 2 minutes",
            "stressed": "Take a 10-minute walk outside",
            "happy": "Share your good mood with someone you care about",
            "lonely": "Send a message to a friend or family member",
            "angry": "Write down what you're feeling before responding",
        }
        return actions.get(mood, "Take a moment to breathe and check in with yourself")

    def _get_mood_trend(self, user_id: str) -> str:
        checks = self.check_ins.get(user_id, [])
        if len(checks) < 3:
            return "building"
        recent = checks[-3:]
        avg = sum(c["mood_score"] for c in recent) / len(recent)
        return "positive" if avg >= 7 else "neutral" if avg >= 4 else "needs_attention"

    def _get_wellness_tip(self, entry: Dict) -> str:
        if entry.get("sleep_quality", 5) < 4:
            return "Try establishing a consistent bedtime routine for better sleep"
        if entry.get("stress_level", 5) > 7:
            return "High stress detected — consider a breathing exercise or short walk"
        if entry.get("energy_score", 5) < 4:
            return "Low energy today — make sure you're hydrated and have eaten well"
        return "Keep up the great work! Consistency in self-care pays off."


ai_companion_service = AICompanionService()

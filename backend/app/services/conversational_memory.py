"""
AdapFit Conversational Memory
Persistent conversation memory across sessions.
Stores summaries, user preferences, key decisions, and coaching context
so the AI coach remembers prior conversations.
"""
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field, asdict


@dataclass
class ConversationTurn:
    role: str
    content: str
    timestamp: str
    intent: Optional[str] = None
    entities: Optional[Dict] = None


@dataclass
class ConversationSummary:
    session_id: str
    user_id: str
    started_at: str
    ended_at: str
    turn_count: int
    topics: List[str]
    key_decisions: List[str]
    user_preferences_discovered: Dict[str, Any]
    summary: str
    mood: str = "neutral"
    pain_reported: bool = False
    goals_mentioned: List[str] = field(default_factory=list)


@dataclass
class UserPreference:
    key: str
    value: Any
    confidence: float  # 0-1, higher = more certain
    source: str  # "conversation", "explicit", "inferred"
    last_updated: str
    times_observed: int = 1


class ConversationalMemory:
    """
    Manages persistent conversational memory for the AI coach.
    Stores conversation summaries, user preferences, and contextual cues
    for personalized multi-session coaching.
    """

    def __init__(self):
        # In-memory stores (replace with Supabase in production)
        self._summaries: Dict[str, List[ConversationSummary]] = {}  # user_id -> summaries
        self._preferences: Dict[str, Dict[str, UserPreference]] = {}  # user_id -> prefs
        self._active_sessions: Dict[str, List[ConversationTurn]] = {}  # session_id -> turns
        self._user_facts: Dict[str, List[Dict]] = {}  # user_id -> extracted facts

        # Topic detection keywords
        self._topic_keywords = {
            "strength_training": ["squat", "bench", "deadlift", "press", "strength", "1rm", "pr", "powerlifting"],
            "cardio": ["run", "jog", "cycle", "bike", "swim", "cardio", "endurance", "marathon", "5k", "10k"],
            "recovery": ["recovery", "hrv", "sleep", "rest", "deload", "fatigue", "soreness"],
            "nutrition": ["eat", "diet", "protein", "calories", "meal", "macros", "bulk", "cut"],
            "injury": ["pain", "hurt", "injury", "sore", "strain", "doctor", "physio"],
            "motivation": ["motivation", "lazy", "consistency", "mindset", "discipline", "goal"],
            "body_composition": ["weight", "body fat", "lean", "muscle mass", "bmi", "measurements"],
            "sleep_hygiene": ["sleep", "insomnia", "bedtime", "melatonin", "screen", "caffeine"],
            "technique": ["form", "technique", "execute", "proper", "range of motion"],
            "periodization": ["periodization", "mesocycle", "phase", "programming", "volume", "intensity"],
        }

    def start_session(self, user_id: str) -> str:
        """Start a new conversation session. Returns session_id."""
        session_id = f"{user_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        self._active_sessions[session_id] = []
        return session_id

    def add_turn(
        self, session_id: str, role: str, content: str,
        intent: Optional[str] = None, entities: Optional[Dict] = None
    ):
        """Record a conversation turn."""
        if session_id not in self._active_sessions:
            self._active_sessions[session_id] = []

        turn = ConversationTurn(
            role=role,
            content=content,
            timestamp=datetime.now(timezone.utc).isoformat(),
            intent=intent,
            entities=entities,
        )
        self._active_sessions[session_id].append(turn)

    def end_session(self, session_id: str, user_id: str) -> ConversationSummary:
        """End a session and generate a summary."""
        turns = self._active_sessions.pop(session_id, [])
        if not turns:
            return ConversationSummary(
                session_id=session_id, user_id=user_id,
                started_at="", ended_at="", turn_count=0,
                topics=[], key_decisions=[], user_preferences_discovered={},
                summary="Empty session",
            )

        # Analyze the conversation
        topics = self._detect_topics(turns)
        key_decisions = self._extract_key_decisions(turns)
        preferences = self._extract_preferences(turns)
        mood = self._detect_mood(turns)
        pain_reported = self._check_pain(turns)
        goals = self._extract_goals(turns)
        summary = self._generate_summary(turns, topics, key_decisions)

        conv_summary = ConversationSummary(
            session_id=session_id,
            user_id=user_id,
            started_at=turns[0].timestamp,
            ended_at=turns[-1].timestamp,
            turn_count=len(turns),
            topics=topics,
            key_decisions=key_decisions,
            user_preferences_discovered=preferences,
            summary=summary,
            mood=mood,
            pain_reported=pain_reported,
            goals_mentioned=goals,
        )

        # Store summary
        if user_id not in self._summaries:
            self._summaries[user_id] = []
        self._summaries[user_id].append(conv_summary)

        # Update preferences
        self._update_preferences(user_id, preferences)

        # Extract and store facts
        facts = self._extract_facts(turns)
        if user_id not in self._user_facts:
            self._user_facts[user_id] = []
        self._user_facts[user_id].extend(facts)

        return conv_summary

    def get_context_for_llm(self, user_id: str, max_tokens: int = 600) -> str:
        """Build a context string from memory for LLM injection."""
        parts = []

        # Recent summaries (last 3 sessions)
        summaries = self._summaries.get(user_id, [])[-3:]
        if summaries:
            parts.append("RECENT CONVERSATIONS:")
            for s in summaries:
                date = s.started_at[:10] if s.started_at else "unknown"
                parts.append(f"  [{date}] {s.summary}")

        # Key preferences
        prefs = self._preferences.get(user_id, {})
        high_conf = {k: v for k, v in prefs.items() if v.confidence >= 0.6}
        if high_conf:
            parts.append("\nUSER PREFERENCES (confirmed):")
            for k, v in high_conf.items():
                parts.append(f"  - {k}: {v.value}")

        # Known facts
        facts = self._user_facts.get(user_id, [])
        recent_facts = facts[-5:] if facts else []
        if recent_facts:
            parts.append("\nKNOWN FACTS:")
            for f in recent_facts:
                parts.append(f"  - {f.get('fact', '')}")

        # Pain history
        pain_sessions = [s for s in summaries if s.pain_reported]
        if pain_sessions:
            parts.append(f"\nPAIN HISTORY: {len(pain_sessions)} session(s) with pain reports")
            last_pain = pain_sessions[-1]
            if last_pain.topics:
                parts.append(f"  Last pain area: {', '.join(last_pain.topics[:2])}")

        context = "\n".join(parts)
        # Rough token limit
        if len(context) > max_tokens * 4:
            context = context[:max_tokens * 4]
        return context

    def get_preference(self, user_id: str, key: str) -> Optional[Any]:
        """Get a specific user preference."""
        prefs = self._preferences.get(user_id, {})
        pref = prefs.get(key)
        return pref.value if pref and pref.confidence >= 0.5 else None

    def get_all_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get all user preferences."""
        prefs = self._preferences.get(user_id, {})
        return {k: {"value": v.value, "confidence": v.confidence, "source": v.source}
                for k, v in prefs.items()}

    def get_conversation_count(self, user_id: str) -> int:
        return len(self._summaries.get(user_id, []))

    def get_last_topics(self, user_id: str, n: int = 3) -> List[str]:
        """Get topics from last N sessions."""
        summaries = self._summaries.get(user_id, [])[-n:]
        topics = []
        for s in summaries:
            topics.extend(s.topics)
        # Deduplicate preserving order
        seen = set()
        unique = []
        for t in topics:
            if t not in seen:
                seen.add(t)
                unique.append(t)
        return unique[:10]

    def get_status(self) -> Dict[str, Any]:
        return {
            "total_users": len(self._summaries),
            "total_sessions": sum(len(s) for s in self._summaries.values()),
            "total_preferences": sum(len(p) for p in self._preferences.values()),
            "total_facts": sum(len(f) for f in self._user_facts.values()),
        }

    # --- Internal analysis methods ---

    def _detect_topics(self, turns: List[ConversationTurn]) -> List[str]:
        """Detect topics discussed in the conversation."""
        all_text = " ".join(t.content.lower() for t in turns)
        topics = []
        for topic, keywords in self._topic_keywords.items():
            if any(kw in all_text for kw in keywords):
                topics.append(topic)
        return topics[:5]

    def _extract_key_decisions(self, turns: List[ConversationTurn]) -> List[str]:
        """Extract key decisions or action items from conversation."""
        decisions = []
        decision_phrases = [
            "i'll", "i will", "going to", "plan to", "decided",
            "let's", "should", "recommend", "suggest", "prescribe",
            "switch to", "change to", "start", "stop", "increase", "decrease",
        ]
        for turn in turns:
            if turn.role == "assistant":
                content_lower = turn.content.lower()
                for phrase in decision_phrases:
                    if phrase in content_lower:
                        # Extract the sentence containing the phrase
                        sentences = turn.content.split(".")
                        for sent in sentences:
                            if phrase in sent.lower():
                                clean = sent.strip()
                                if len(clean) > 10 and len(clean) < 150:
                                    decisions.append(clean)
                        break
        return decisions[:3]

    def _extract_preferences(self, turns: List[ConversationTurn]) -> Dict[str, Any]:
        """Extract user preferences from conversation."""
        prefs = {}
        for turn in turns:
            if turn.role != "user":
                continue
            content_lower = turn.content.lower()

            # Training preference
            if any(w in content_lower for w in ["i prefer", "i like", "i love", "favorite"]):
                if "morning" in content_lower:
                    prefs["training_time"] = "morning"
                elif "evening" in content_lower or "night" in content_lower:
                    prefs["training_time"] = "evening"
                if "heavy" in content_lower or "heavy lifting" in content_lower:
                    prefs["training_style"] = "heavy"
                elif "light" in content_lower:
                    prefs["training_style"] = "light"

            # Equipment
            if any(w in content_lower for w in ["i have", "my gym has", "i use"]):
                if "dumbbell" in content_lower:
                    prefs["equipment_dumbbells"] = True
                if "barbell" in content_lower:
                    prefs["equipment_barbell"] = True
                if "cable" in content_lower:
                    prefs["equipment_cables"] = True

            # Goals
            if any(w in content_lower for w in ["my goal", "i want to", "trying to"]):
                if "lose weight" in content_lower or "fat loss" in content_lower:
                    prefs["primary_goal"] = "fat_loss"
                elif "muscle" in content_lower or "bulk" in content_lower:
                    prefs["primary_goal"] = "hypertrophy"
                elif "strong" in content_lower or "strength" in content_lower:
                    prefs["primary_goal"] = "strength"
                elif "endurance" in content_lower or "run" in content_lower:
                    prefs["primary_goal"] = "endurance"

            # Injuries/limitations
            if any(w in content_lower for w in ["can't do", "cannot do", "avoid", "injury", "bad shoulder", "bad knee"]):
                if "shoulder" in content_lower:
                    prefs["limitation"] = "shoulder"
                elif "knee" in content_lower:
                    prefs["limitation"] = "knee"
                elif "back" in content_lower:
                    prefs["limitation"] = "lower_back"

            # Experience
            if any(w in content_lower for w in ["been training", "years of", "i'm a beginner", "new to"]):
                if "beginner" in content_lower or "new to" in content_lower:
                    prefs["experience_level"] = "beginner"
                elif "years" in content_lower or "advanced" in content_lower:
                    prefs["experience_level"] = "advanced"
                else:
                    prefs["experience_level"] = "intermediate"

        return prefs

    def _detect_mood(self, turns: List[ConversationTurn]) -> str:
        """Detect overall user mood from conversation."""
        user_texts = " ".join(t.content.lower() for t in turns if t.role == "user")
        positive = sum(1 for w in ["great", "amazing", "awesome", "love", "good", "happy", "excited", "motivated"] if w in user_texts)
        negative = sum(1 for w in ["tired", "exhausted", "hate", "terrible", "bad", "sad", "unmotivated", "lazy", "pain"] if w in user_texts)

        if positive > negative + 1:
            return "positive"
        elif negative > positive + 1:
            return "negative"
        return "neutral"

    def _check_pain(self, turns: List[ConversationTurn]) -> bool:
        """Check if pain was reported."""
        user_texts = " ".join(t.content.lower() for t in turns if t.role == "user")
        return any(w in user_texts for w in ["pain", "hurt", "hurts", "sore", "injury", "strain"])

    def _extract_goals(self, turns: List[ConversationTurn]) -> List[str]:
        """Extract goals mentioned."""
        goals = []
        user_texts = " ".join(t.content.lower() for t in turns if t.role == "user")
        goal_map = {
            "lose weight": "fat_loss",
            "fat loss": "fat_loss",
            "build muscle": "hypertrophy",
            "get strong": "strength",
            "run a marathon": "marathon",
            "bench 100kg": "bench_100kg",
            "deadlift 200kg": "deadlift_200kg",
            "squat 150kg": "squat_150kg",
        }
        for phrase, goal in goal_map.items():
            if phrase in user_texts:
                goals.append(goal)
        return goals

    def _generate_summary(
        self, turns: List[ConversationTurn], topics: List[str], decisions: List[str]
    ) -> str:
        """Generate a concise conversation summary."""
        user_turns = [t for t in turns if t.role == "user"]
        assistant_turns = [t for t in turns if t.role == "assistant"]

        topic_str = ", ".join(topics[:3]) if topics else "general fitness"
        turn_count = len(turns)

        summary = f"Discussed {topic_str} across {turn_count} exchanges."
        if decisions:
            summary += f" Key decision: {decisions[0]}."
        if len(user_turns) > 0:
            # First user message as context
            first_msg = user_turns[0].content[:80]
            summary += f" Started with: \"{first_msg}\""

        return summary[:300]

    def _extract_facts(self, turns: List[ConversationTurn]) -> List[Dict]:
        """Extract verifiable facts from conversation."""
        facts = []
        now = datetime.now(timezone.utc).isoformat()

        for turn in turns:
            if turn.role != "user":
                continue
            content = turn.content.lower()

            # Age
            import re
            age_match = re.search(r"i(?:'m| am) (\d{2}) years? old", content)
            if age_match:
                facts.append({"fact": f"User is {age_match.group(1)} years old", "source": "conversation", "timestamp": now})

            # Weight
            weight_match = re.search(r"(?:i(?:'m| am)|weigh(?:s|t)?) (?:about )?(\d{2,3})\s*(?:kg|lbs?)", content)
            if weight_match:
                facts.append({"fact": f"User weight: {weight_match.group(1)}", "source": "conversation", "timestamp": now})

            # Training experience
            years_match = re.search(r"(?:been|training for) (\d+) years?", content)
            if years_match:
                facts.append({"fact": f"Training experience: {years_match.group(1)} years", "source": "conversation", "timestamp": now})

        return facts[:5]

    def _update_preferences(self, user_id: str, new_prefs: Dict[str, Any]):
        """Update user preferences with confidence scoring."""
        if user_id not in self._preferences:
            self._preferences[user_id] = {}

        now = datetime.now(timezone.utc).isoformat()

        for key, value in new_prefs.items():
            existing = self._preferences[user_id].get(key)
            if existing:
                if existing.value == value:
                    # Same value repeated = higher confidence
                    existing.times_observed += 1
                    existing.confidence = min(1.0, existing.confidence + 0.15)
                    existing.last_updated = now
                else:
                    # Conflicting = lower confidence or update
                    existing.confidence -= 0.1
                    if existing.confidence < 0.3:
                        existing.value = value
                        existing.confidence = 0.5
                        existing.source = "inferred"
                        existing.times_observed = 1
                        existing.last_updated = now
            else:
                self._preferences[user_id][key] = UserPreference(
                    key=key, value=value, confidence=0.6,
                    source="conversation", last_updated=now, times_observed=1
                )


# Singleton
conversational_memory = ConversationalMemory()

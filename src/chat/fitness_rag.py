"""
Fitness RAG Chatbot Engine — AI-powered fitness guidance using retrieval-augmented generation.
Provides personalized workout, nutrition, and recovery recommendations.

Inspired by: agentic-rag-chatbot (LangGraph fitness chatbot)
"""
from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class QueryIntent(Enum):
    WORKOUT = "workout"
    NUTRITION = "nutrition"
    RECOVERY = "recovery"
    INJURY = "injury"
    PROGRAMMING = "programming"
    GENERAL = "general"


class ResponseConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class KnowledgeChunk:
    """A single piece of fitness knowledge."""
    id: str
    content: str
    source: str
    category: str
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGResponse:
    """Response from the RAG fitness chatbot."""
    answer: str
    sources: list[str]
    confidence: ResponseConfidence
    intent: QueryIntent
    suggestions: list[str] = field(default_factory=list)
    disclaimers: list[str] = field(default_factory=list)


class FitnessKnowledgeBase:
    """In-memory fitness knowledge base with keyword-based retrieval."""

    def __init__(self) -> None:
        self._chunks: dict[str, KnowledgeChunk] = {}
        self._index: dict[str, set[str]] = defaultdict(set)  # word -> chunk_ids
        self._seed_knowledge()

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization for keyword matching."""
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return [w for w in text.split() if len(w) > 2]

    def _seed_knowledge(self) -> None:
        """Seed the knowledge base with core fitness knowledge."""
        seeds = [
            KnowledgeChunk(
                id="squat_form",
                content=(
                    "Barbell Back Squat form: Stand with feet shoulder-width apart, "
                    "toes slightly turned out. Brace core, push hips back, and descend "
                    "until thighs are at least parallel to the floor. Drive through "
                    "the full foot to stand. Keep chest up and knees tracking over toes. "
                    "Common mistakes: knees caving in, excessive forward lean, heels rising."
                ),
                source="NSCA Essentials of Strength Training",
                category="exercise_form",
                tags=["squat", "compound", "legs", "form"],
            ),
            KnowledgeChunk(
                id="deadlift_form",
                content=(
                    "Conventional Deadlift: Stand with feet hip-width apart, shins touching "
                    "the bar. Grip the bar just outside knees. Flatten back, engage lats, "
                    "brace core. Drive through the floor, keeping bar close to body. Lock "
                    "out at the top with glutes. Common mistakes: rounding the lower back, "
                    "bar drifting forward, hyperextending at the top."
                ),
                source="NSCA Essentials of Strength Training",
                category="exercise_form",
                tags=["deadlift", "compound", "back", "form"],
            ),
            KnowledgeChunk(
                id="protein_timing",
                content=(
                    "Protein intake for muscle building: Aim for 1.6-2.2g per kg bodyweight "
                    "per day. Distribute across 3-5 meals. Post-workout protein within 2 "
                    "hours is beneficial but not critical. Leucine threshold for muscle "
                    "protein synthesis is approximately 2.5g per meal. Whole food sources "
                    "are preferred over supplements for most of intake."
                ),
                source="ISSN Position Stand on Protein",
                category="nutrition",
                tags=["protein", "muscle", "nutrition", "timing"],
            ),
            KnowledgeChunk(
                id="hrv_recovery",
                content=(
                    "Heart Rate Variability (HRV) is a key recovery metric. Higher HRV "
                    "generally indicates better recovery. Morning HRV measurements are most "
                    "reliable. A sudden drop of >15% from baseline may indicate overtraining, "
                    "illness, or excessive stress. RMSSD is the most commonly used time-domain "
                    "HRV metric for fitness applications. 7-night rolling averages smooth "
                    "out nightly variations."
                ),
                source="Journal of Sports Sciences",
                category="recovery",
                tags=["hrv", "recovery", "monitoring", "overtraining"],
            ),
            KnowledgeChunk(
                id="sleep_hygiene",
                content=(
                    "Sleep for recovery: Adults need 7-9 hours. Key sleep hygiene practices: "
                    "consistent sleep schedule, cool room (65-68°F/18-20°C), no screens "
                    "1 hour before bed, avoid caffeine after 2 PM, limit alcohol. Deep sleep "
                    "is when most Growth Hormone is released. REM sleep is critical for "
                    "motor learning and memory consolidation of new运动patterns."
                ),
                source="National Sleep Foundation",
                category="recovery",
                tags=["sleep", "recovery", "growth_hormone", "rest"],
            ),
            KnowledgeChunk(
                id="progressive_overload",
                content=(
                    "Progressive Overload Principle: To continue making gains, systematically "
                    "increase one of: load (weight), volume (sets × reps), intensity (RPE), "
                    "or frequency. A reasonable weekly load increase is 2.5-5% for upper "
                    "body and 5-10% for lower body. Deload every 4-6 weeks by reducing "
                    "volume by 40-60% while maintaining intensity."
                ),
                source="NSCA Essentials of Strength Training",
                category="programming",
                tags=["progressive_overload", "programming", "periodization"],
            ),
            KnowledgeChunk(
                id="cardio_zones",
                content=(
                    "Heart Rate Training Zones: Zone 1 (50-60% max HR) - Recovery/easy; "
                    "Zone 2 (60-70%) - Aerobic base/fat burning; Zone 3 (70-80%) - "
                    "Aerobic capacity; Zone 4 (80-90%) - Lactate threshold; Zone 5 "
                    "(90-100%) - VO2max/sprint. Most training should be in Zone 2 "
                    "(approximately 80% of total volume) for optimal aerobic development."
                ),
                source="ACSM Guidelines",
                category="programming",
                tags=["cardio", "heart_rate", "zones", "aerobic"],
            ),
            KnowledgeChunk(
                id="shoulder_pain",
                content=(
                    "Common shoulder pain causes in lifters: impingement (anterior shoulder "
                    "pain during overhead movements), rotator cuff strain (weakness with "
                    "external rotation), labral tear (clicking/locking). Prevention: balance "
                    "push/pull ratio (2:1 pull:push), include face pulls and external "
                    "rotations, avoid excessive behind-neck pressing, maintain thoracic "
                    "mobility. Seek medical evaluation for persistent pain."
                ),
                source="ACSM Clinical Sports Medicine",
                category="injury_prevention",
                tags=["shoulder", "injury", "prevention", "pain"],
            ),
            KnowledgeChunk(
                id="beginner_program",
                content=(
                    "Beginner Strength Program (3 days/week full body): Day A - Squat 3×8, "
                    "Bench Press 3×8, Barbell Row 3×8, Plank 3×30s. Day B - Deadlift 3×5, "
                    "Overhead Press 3×8, Pull-ups 3×max, Lunges 3×10. Alternate A/B with "
                    "rest day between. Add 2.5kg to upper body and 5kg to lower body lifts "
                    "each session. When you can't complete all reps, keep the weight and "
                    "try again next session."
                ),
                source="Starting Strength / Practical Programming",
                category="programming",
                tags=["beginner", "program", "full_body", "strength"],
            ),
        ]
        for chunk in seeds:
            self._chunks[chunk.id] = chunk
            for word in self._tokenize(chunk.content + " " + " ".join(chunk.tags)):
                self._index[word].add(chunk.id)

    def add_chunk(self, chunk: KnowledgeChunk) -> None:
        """Add a knowledge chunk to the base."""
        self._chunks[chunk.id] = chunk
        for word in self._tokenize(chunk.content + " " + " ".join(chunk.tags)):
            self._index[word].add(chunk.id)

    def search(self, query: str, top_k: int = 5) -> list[KnowledgeChunk]:
        """Keyword-based search returning top-k relevant chunks."""
        query_words = self._tokenize(query)
        scores: dict[str, float] = {}

        for word in query_words:
            for chunk_id in self._index.get(word, set()):
                scores[chunk_id] = scores.get(chunk_id, 0) + 1.0

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [self._chunks[cid] for cid, _ in ranked if cid in self._chunks]


class FitnessRAGChatbot:
    """RAG-powered fitness chatbot with intent classification and safety checks."""

    SAFETY_DISCLAIMERS = [
        "This is AI-generated guidance, not medical advice. Consult a healthcare professional before starting any new exercise program.",
        "If you experience sharp pain, dizziness, or chest discomfort, stop exercising immediately and seek medical attention.",
    ]

    INTENT_KEYWORDS: dict[QueryIntent, list[str]] = {
        QueryIntent.WORKOUT: [
            "workout", "exercise", "training", "lift", "squat", "deadlift",
            "bench", "press", "rep", "set", "gym", "strength", "muscle",
        ],
        QueryIntent.NUTRITION: [
            "eat", "food", "diet", "protein", "calorie", "meal", "nutrition",
            "supplement", "macro", "carb", "fat", "vitamin",
        ],
        QueryIntent.RECOVERY: [
            "recovery", "sleep", "rest", "hrv", "fatigue", "sore",
            "stretch", "foam roll", "deload", "overtraining",
        ],
        QueryIntent.INJURY: [
            "pain", "injury", "hurt", "sore", "strain", "sprain",
            "tendon", "ligament", "doctor", "physio", "rehab",
        ],
        QueryIntent.PROGRAMMING: [
            "program", "routine", "split", "periodization", "plan",
            "schedule", "beginner", "intermediate", "advanced",
        ],
    }

    def __init__(self, knowledge_base: FitnessKnowledgeBase | None = None) -> None:
        self.kb = knowledge_base or FitnessKnowledgeBase()

    def classify_intent(self, query: str) -> QueryIntent:
        """Classify the intent of a fitness query."""
        query_lower = query.lower()
        scores: dict[QueryIntent, int] = defaultdict(int)

        for intent, keywords in self.INTENT_KEYWORDS.items():
            for kw in keywords:
                if kw in query_lower:
                    scores[intent] += 1

        if not scores:
            return QueryIntent.GENERAL

        return max(scores, key=lambda x: scores[x])

    def _format_response(
        self,
        query: str,
        chunks: list[KnowledgeChunk],
        intent: QueryIntent,
    ) -> RAGResponse:
        """Format retrieved knowledge into a response."""
        if not chunks:
            return RAGResponse(
                answer=(
                    "I don't have specific information about that in my knowledge base. "
                    "Could you rephrase your question or ask about a specific topic "
                    "like workouts, nutrition, recovery, or injury prevention?"
                ),
                sources=[],
                confidence=ResponseConfidence.LOW,
                intent=intent,
            )

        # Build answer from top chunks
        answer_parts = [c.content for c in chunks[:3]]
        answer = "\n\n".join(answer_parts)

        sources = list(set(c.source for c in chunks[:3]))

        # Generate suggestions based on intent
        suggestions = self._generate_suggestions(intent, chunks)

        # Add disclaimers for injury-related queries
        disclaimers = []
        if intent == QueryIntent.INJURY:
            disclaimers = self.SAFETY_DISCLAIMERS[:1]
        elif intent == QueryIntent.WORKOUT:
            disclaimers = [self.SAFETY_DISCLAIMERS[0]]

        confidence = (
            ResponseConfidence.HIGH if len(chunks) >= 3
            else ResponseConfidence.MEDIUM if len(chunks) >= 1
            else ResponseConfidence.LOW
        )

        return RAGResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            intent=intent,
            suggestions=suggestions,
            disclaimers=disclaimers,
        )

    def _generate_suggestions(
        self,
        intent: QueryIntent,
        chunks: list[KnowledgeChunk],
    ) -> list[str]:
        """Generate follow-up suggestions based on context."""
        suggestions: dict[QueryIntent, list[str]] = {
            QueryIntent.WORKOUT: [
                "Ask about proper form for a specific exercise",
                "Get a beginner-friendly training program",
                "Learn about progressive overload",
            ],
            QueryIntent.NUTRITION: [
                "Ask about pre/post-workout nutrition",
                "Get protein intake recommendations",
                "Learn about meal timing strategies",
            ],
            QueryIntent.RECOVERY: [
                "Ask about HRV and recovery monitoring",
                "Get sleep optimization tips",
                "Learn about deload week strategies",
            ],
            QueryIntent.INJURY: [
                "Ask about prevention strategies",
                "Learn about common lifting injuries",
                "Get stretching routine recommendations",
            ],
            QueryIntent.PROGRAMMING: [
                "Get a beginner training split",
                "Learn about periodization",
                "Ask about training frequency",
            ],
            QueryIntent.GENERAL: [
                "Ask about workout routines",
                "Get nutrition advice",
                "Learn about recovery strategies",
            ],
        }
        return suggestions.get(intent, suggestions[QueryIntent.GENERAL])

    def chat(self, query: str) -> RAGResponse:
        """Process a fitness query and return a RAG response."""
        intent = self.classify_intent(query)
        chunks = self.kb.search(query, top_k=5)
        return self._format_response(query, chunks, intent)

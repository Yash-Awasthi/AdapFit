"""
Fitness RAG Chatbot for ZFIT
Extracted from: agentic-rag-chatbot (AI-powered fitness guidance)
Patterns: RAG pipeline, query refinement, retrieval system,
          response generation, video recommendations, knowledge base
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class QueryIntent(Enum):
    WORKOUT_RECOMMENDATION = "workout_recommendation"
    EXERCISE_FORM = "exercise_form"
    NUTRITION_ADVICE = "nutrition_advice"
    RECOVERY_GUIDANCE = "recovery_guidance"
    GENERAL_FITNESS = "general_fitness"
    SAFETY_QUESTION = "safety_question"
    PROGRESS_TRACKING = "progress_tracking"


@dataclass
class ChatMessage:
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    metadata: dict = field(default_factory=dict)


@dataclass
class RetrievedDocument:
    content: str
    source: str
    relevance_score: float
    metadata: dict = field(default_factory=dict)


@dataclass
class VideoRecommendation:
    title: str
    url: str
    thumbnail_url: str
    duration_seconds: int
    transcript: str = ""
    relevance_score: float = 0.0


@dataclass
class ChatResponse:
    answer: str
    sources: list[RetrievedDocument]
    video_recommendations: list[VideoRecommendation]
    intent: QueryIntent
    confidence: float
    safety_warnings: list[str] = field(default_factory=list)


# ─── Knowledge Base ────────────────────────────────────────────────────

KNOWLEDGE_BASE = [
    {"content": "For beginners, start with 3 days per week of full-body workouts with at least one rest day between sessions.", "source": "fitness_guidelines", "category": "workout"},
    {"content": "Aim for 150 minutes of moderate-intensity aerobic activity or 75 minutes of vigorous activity per week.", "source": "WHO_guidelines", "category": "cardio"},
    {"content": "Progressive overload means gradually increasing the weight, frequency, or number of repetitions in your training.", "source": "strength_training", "category": "workout"},
    {"content": "Sleep 7-9 hours per night for optimal recovery and muscle growth.", "source": "sleep_science", "category": "recovery"},
    {"content": "Consume 1.6-2.2g of protein per kilogram of body weight for muscle building.", "source": "nutrition_science", "category": "nutrition"},
    {"content": "Always warm up for 5-10 minutes before exercise to prevent injury.", "source": "safety_guidelines", "category": "safety"},
    {"content": "If you feel sharp pain during exercise, stop immediately and consult a healthcare professional.", "source": "safety_guidelines", "category": "safety"},
    {"content": "Hydrate with 500ml of water per hour of exercise.", "source": "hydration_guidelines", "category": "nutrition"},
    {"content": "Rest days are when your muscles grow. Take at least 1-2 rest days per week.", "source": "recovery_science", "category": "recovery"},
    {"content": "For weight loss, focus on creating a caloric deficit through diet and exercise combined.", "source": "weight_management", "category": "nutrition"},
]


# ─── Query Processing ──────────────────────────────────────────────────

def classify_intent(query: str) -> QueryIntent:
    """Classify user query intent."""
    query_lower = query.lower()

    if any(w in query_lower for w in ["workout", "exercise", "training", "set", "rep"]):
        return QueryIntent.WORKOUT_RECOMMENDATION
    if any(w in query_lower for w in ["form", "technique", "how to", "proper"]):
        return QueryIntent.EXERCISE_FORM
    if any(w in query_lower for w in ["eat", "food", "protein", "calorie", "diet", "nutrition"]):
        return QueryIntent.NUTRITION_ADVICE
    if any(w in query_lower for w in ["recover", "rest", "sleep", "soreness"]):
        return QueryIntent.RECOVERY_GUIDANCE
    if any(w in query_lower for w in ["pain", "hurt", "injury", "safe", "danger"]):
        return QueryIntent.SAFETY_QUESTION
    if any(w in query_lower for w in ["progress", "track", "improve", "goal"]):
        return QueryIntent.PROGRESS_TRACKING
    return QueryIntent.GENERAL_FITNESS


def refine_query(query: str) -> list[str]:
    """Generate refined search queries from user input."""
    refined = [query]
    # Add keyword variations
    keywords = query.lower().split()
    if "how" in keywords:
        refined.append(query.replace("how to", "").replace("how do i", ""))
    if any(w in keywords for w in ["best", "top", "recommended"]):
        refined.append(query.replace("best", "good").replace("top", "effective"))
    return refined


# ─── Retrieval ─────────────────────────────────────────────────────────

def retrieve_documents(query: str, top_k: int = 5) -> list[RetrievedDocument]:
    """Retrieve relevant documents from the knowledge base."""
    query_words = set(query.lower().split())
    scored = []

    for doc in KNOWLEDGE_BASE:
        doc_words = set(doc["content"].lower().split())
        overlap = len(query_words & doc_words)
        score = overlap / max(len(query_words), 1)

        if doc["category"] in query.lower():
            score += 0.3

        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [
        RetrievedDocument(
            content=doc["content"],
            source=doc["source"],
            relevance_score=round(score, 3),
            metadata={"category": doc["category"]},
        )
        for score, doc in scored[:top_k]
        if score > 0
    ]


# ─── Response Generation ───────────────────────────────────────────────

def generate_response(query: str, documents: list[RetrievedDocument]) -> ChatResponse:
    """Generate a response from retrieved documents."""
    intent = classify_intent(query)

    # Build answer from retrieved documents
    if documents:
        answer_parts = [doc.content for doc in documents[:3]]
        answer = " ".join(answer_parts)
    else:
        answer = "I don't have specific information about that. Please consult a fitness professional."

    # Check for safety concerns
    safety_warnings = []
    if intent == QueryIntent.SAFETY_QUESTION:
        safety_warnings.append("If you're experiencing pain or injury, please consult a healthcare professional.")

    # Generate video recommendations based on intent
    videos = _get_video_recommendations(intent)

    return ChatResponse(
        answer=answer,
        sources=documents,
        video_recommendations=videos,
        intent=intent,
        confidence=min(1.0, len(documents) * 0.2 + 0.3),
        safety_warnings=safety_warnings,
    )


def _get_video_recommendations(intent: QueryIntent) -> list[VideoRecommendation]:
    """Get relevant video recommendations based on intent."""
    video_db = {
        QueryIntent.WORKOUT_RECOMMENDATION: [
            VideoRecommendation("Full Body Workout for Beginners", "https://example.com/full-body", "", 600),
            VideoRecommendation("Strength Training Basics", "https://example.com/strength", "", 480),
        ],
        QueryIntent.EXERCISE_FORM: [
            VideoRecommendation("Perfect Squat Form", "https://example.com/squat-form", "", 300),
            VideoRecommendation("Deadlift Technique Guide", "https://example.com/deadlift", "", 360),
        ],
        QueryIntent.NUTRITION_ADVICE: [
            VideoRecommendation("Meal Prep for Fitness", "https://example.com/meal-prep", "", 540),
        ],
        QueryIntent.RECOVERY_GUIDANCE: [
            VideoRecommendation("Post-Workout Recovery Tips", "https://example.com/recovery", "", 420),
        ],
    }
    return video_db.get(intent, [])


# ─── Chat Session ──────────────────────────────────────────────────────

class FitnessChatSession:
    def __init__(self):
        self.history: list[ChatMessage] = []
        self.user_profile: dict = {}

    def set_profile(self, age: int = 30, weight_kg: float = 70, fitness_level: str = "beginner"):
        self.user_profile = {"age": age, "weight_kg": weight_kg, "fitness_level": fitness_level}

    def chat(self, user_message: str) -> ChatResponse:
        self.history.append(ChatMessage(role="user", content=user_message, timestamp=datetime.now()))

        documents = retrieve_documents(user_message)
        response = generate_response(user_message, documents)

        self.history.append(ChatMessage(
            role="assistant",
            content=response.answer,
            timestamp=datetime.now(),
            metadata={"intent": response.intent.value, "confidence": response.confidence},
        ))

        return response

    def get_history(self) -> list[ChatMessage]:
        return self.history

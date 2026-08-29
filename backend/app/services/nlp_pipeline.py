"""
AdapFit NLP Pipeline
Sentiment analysis, goal parsing, exercise feedback extraction, weekly report generation.
Uses HuggingFace Transformers + Google Gemini for advanced NLP tasks.
"""
import json
import re
import httpx
from typing import Dict, List, Any, Optional
from core_engine import compute_subjective_score

# Lazy-loaded HuggingFace pipeline — loaded on first use
_SENTIMENT_PIPE = None
_HAS_HF = None  # None = not checked yet


def _ensure_hf_pipeline():
    """Lazily load the HuggingFace sentiment pipeline on first use."""
    global _SENTIMENT_PIPE, _HAS_HF
    if _HAS_HF is not None:
        return
    try:
        from transformers import pipeline as hf_pipeline
        _SENTIMENT_PIPE = hf_pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
        _HAS_HF = True
    except Exception:
        _SENTIMENT_PIPE = None
        _HAS_HF = False

from app.core.config import settings


class NLPPipeline:
    """Enterprise NLP pipeline for fitness feedback processing."""
    
    # Keywords for exercise feedback classification
    POSITIVE_KEYWORDS = [
        "great", "amazing", "love", "awesome", "strong", "pump", "perfect",
        "effective", "challenging", "good", "nice", "solid", "powerful",
    ]
    NEGATIVE_KEYWORDS = [
        "pain", "hurt", "awkward", "discomfort", "terrible", "bad", "weak",
        "strain", "joint", "weird", "uncomfortable", "hate", "annoying",
    ]
    
    # Muscle group synonyms
    MUSCLE_SYNONYMS = {
        "chest": ["chest", "pecs", "pec", "breast"],
        "back": ["back", "lats", "lat", "upper back", "lower back", "traps"],
        "shoulders": ["shoulders", "delts", "deltoids", "shoulder"],
        "biceps": ["biceps", "bicep", "arms", "bicep curl"],
        "triceps": ["triceps", "tricep", "tricep extension"],
        "quads": ["quads", "quadriceps", "thighs", "thigh", "leg press"],
        "hamstrings": ["hamstrings", "hamstring", "hams"],
        "glutes": ["glutes", "glute", "butt", "buttocks"],
        "core": ["core", "abs", "abdominal", "stomach", "midsection"],
        "calves": ["calves", "calf"],
        "forearms": ["forearms", "forearm", "grip"],
    }
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of workout feedback text."""
        text_lower = text.lower().strip()
        
        if not text_lower:
            return {"sentiment": "neutral", "confidence": 0.5, "method": "empty"}
        
        _ensure_hf_pipeline()

        # Method 1: HuggingFace Transformers
        if _HAS_HF and _SENTIMENT_PIPE:
            try:
                result = _SENTIMENT_PIPE(text[:512])[0]
                label = result["label"].lower()
                return {
                    "sentiment": label,
                    "confidence": round(result["score"], 3),
                    "method": "huggingface_distilbert",
                }
            except Exception:
                pass
        
        # Method 2: Keyword-based fallback
        pos_count = sum(1 for w in self.POSITIVE_KEYWORDS if w in text_lower)
        neg_count = sum(1 for w in self.NEGATIVE_KEYWORDS if w in text_lower)
        
        total = pos_count + neg_count
        if total == 0:
            return {"sentiment": "neutral", "confidence": 0.5, "method": "keyword"}
        
        if pos_count > neg_count:
            return {"sentiment": "positive", "confidence": round(pos_count / total, 3), "method": "keyword"}
        elif neg_count > pos_count:
            return {"sentiment": "negative", "confidence": round(neg_count / total, 3), "method": "keyword"}
        else:
            return {"sentiment": "neutral", "confidence": 0.5, "method": "keyword"}
    
    def extract_exercise_feedback(self, text: str) -> Dict[str, Any]:
        """Extract per-exercise feedback tags from free text."""
        text_lower = text.lower()
        
        tags = []
        for kw in self.POSITIVE_KEYWORDS:
            if kw in text_lower:
                tags.append({"tag": "positive", "keyword": kw})
        for kw in self.NEGATIVE_KEYWORDS:
            if kw in text_lower:
                tags.append({"tag": "negative", "keyword": kw})
        
        pain_indicated = any(w in text_lower for w in ["pain", "hurt", "strain", "joint"])
        
        return {
            "tags": tags,
            "pain_flagged": pain_indicated,
            "overall_sentiment": "negative" if pain_indicated else ("positive" if len([t for t in tags if t["tag"] == "positive"]) > len([t for t in tags if t["tag"] == "negative"]) else "neutral"),
            "raw_text": text,
        }
    
    def extract_mentioned_muscles(self, text: str) -> List[str]:
        """Extract mentioned muscle groups from free text."""
        text_lower = text.lower()
        found = []
        for muscle, synonyms in self.MUSCLE_SYNONYMS.items():
            for syn in synonyms:
                if syn in text_lower:
                    if muscle not in found:
                        found.append(muscle)
                    break
        return found
    
    async def parse_goals_from_text(self, text: str) -> Dict[str, Any]:
        """Use LLM to parse fitness goals from free-text input."""
        if not settings.GEMINI_API_KEY:
            return self._rule_based_goal_parse(text)
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            prompt = f"""Parse the following fitness goal description into structured JSON.
Return ONLY valid JSON with these fields:
- primary_goal: one of ["hypertrophy", "strength", "endurance", "fat_loss", "general_fitness"]
- experience_level: one of ["beginner", "intermediate", "advanced"]
- target_timeline: short description (e.g., "3 months", "ongoing")
- specific_focus: list of specific areas mentioned
- motivation_notes: any motivation context

User input: "{text}"
"""
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    text_content = data["candidates"][0]["content"]["parts"][0]["text"]
                    return json.loads(text_content)
        except Exception:
            pass
        
        return self._rule_based_goal_parse(text)
    
    def _rule_based_goal_parse(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["lose weight", "fat loss", "shred", "lean", "cut"]):
            goal = "fat_loss"
        elif any(w in text_lower for w in ["muscle", "bulk", "size", "hypertrophy", "gain"]):
            goal = "hypertrophy"
        elif any(w in text_lower for w in ["strong", "strength", "powerlifting", "deadlift", "squat max"]):
            goal = "strength"
        elif any(w in text_lower for w in ["run", "cardio", "endurance", "marathon", "stamina"]):
            goal = "endurance"
        else:
            goal = "general_fitness"
        
        if any(w in text_lower for w in ["beginner", "new", "starting", "first time"]):
            level = "beginner"
        elif any(w in text_lower for w in ["advanced", "experienced", "years", "veteran"]):
            level = "advanced"
        else:
            level = "intermediate"
        
        return {
            "primary_goal": goal,
            "experience_level": level,
            "target_timeline": "ongoing",
            "specific_focus": self.extract_mentioned_muscles(text),
            "motivation_notes": text[:200],
            "method": "rule_based",
        }
    
    async def generate_weekly_summary(self, user_data: dict, recovery_logs: list, workout_logs: list) -> str:
        """Generate a natural language weekly progress summary."""
        if settings.GEMINI_API_KEY:
            return await self._generate_summary_llm(user_data, recovery_logs, workout_logs)
        return self._generate_summary_rule_based(recovery_logs, workout_logs)
    
    async def _generate_summary_llm(self, user_data, recovery_logs, workout_logs):
        if not settings.GEMINI_API_KEY:
            return self._generate_summary_rule_based(recovery_logs, workout_logs)
        try:
            avg_score = sum(r.get("recovery_score", 70) for r in recovery_logs) / max(len(recovery_logs), 1) if recovery_logs else 70
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            prompt = f"You are AdapFit AI coach. Avg recovery: {avg_score:.0f}/100. Workouts: {len(workout_logs)}. Write 2-3 sentence summary."
            payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.5, "maxOutputTokens": 200}}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            pass
        return self._generate_summary_rule_based(recovery_logs, workout_logs)
    
    def _generate_summary_rule_based(self, recovery_logs, workout_logs):
        if not recovery_logs and not workout_logs:
            return "No data yet. Start logging to see insights!"
        avg_score = sum(r.get("recovery_score", 70) for r in recovery_logs) / max(len(recovery_logs), 1) if recovery_logs else 70
        trend = "excellent" if avg_score >= 80 else ("steady" if avg_score >= 65 else "below average")
        return f"Recovery has been {trend} (avg {avg_score:.0f}/100). {len(workout_logs)} workout(s) completed."
    
    def get_status(self):
        return {"huggingface_available": _HAS_HF, "gemini_configured": bool(settings.GEMINI_API_KEY)}


nlp_pipeline = NLPPipeline()

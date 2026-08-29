"""
Health Wellness Hub — Unified wellness tracking across all domains
Combines physical, mental, social, and spiritual wellness into one cohesive experience.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid


class WellnessHub:
    WELLNESS_DIMENSIONS = {
        "physical": {"name": "Physical Wellness", "icon": "💪", "weight": 0.30, "metrics": ["activity", "sleep", "nutrition", "vitals", "exercise"]},
        "mental": {"name": "Mental Wellness", "icon": "🧠", "weight": 0.25, "metrics": ["stress", "mood", "cognitive", "mindfulness"]},
        "emotional": {"name": "Emotional Wellness", "icon": "❤️", "weight": 0.20, "metrics": ["emotional_regulation", "self_awareness", "resilience", "gratitude"]},
        "social": {"name": "Social Wellness", "icon": "👥", "weight": 0.15, "metrics": ["relationships", "community", "communication", "support_network"]},
        "spiritual": {"name": "Spiritual Wellness", "icon": "🧘", "weight": 0.10, "metrics": ["purpose", "meditation", "values_alignment", "nature_connection"]},
    }

    DAILY_CHALLENGES = [
        {"id": "gratitude", "title": "Gratitude Journal", "description": "Write 3 things you're grateful for", "dimension": "emotional", "points": 10, "duration_min": 5},
        {"id": "walk", "title": "10-Minute Walk", "description": "Take a 10-minute walk outside", "dimension": "physical", "points": 15, "duration_min": 10},
        {"id": "meditate", "title": "5-Minute Meditation", "description": "Practice mindful breathing for 5 minutes", "dimension": "spiritual", "points": 10, "duration_min": 5},
        {"id": "connect", "title": "Reach Out", "description": "Send a kind message to someone you care about", "dimension": "social", "points": 10, "duration_min": 2},
        {"id": "hydrate", "title": "Hydration Boost", "description": "Drink 2 glasses of water right now", "dimension": "physical", "points": 5, "duration_min": 1},
        {"id": "stretch", "title": "Desk Stretch", "description": "Do a 3-minute desk stretch routine", "dimension": "physical", "points": 10, "duration_min": 3},
        {"id": "breathe", "title": "Box Breathing", "description": "Practice box breathing (4-4-4-4) for 2 minutes", "dimension": "mental", "points": 10, "duration_min": 2},
        {"id": "smile", "title": "Random Act of Kindness", "description": "Do something kind for a stranger or colleague", "dimension": "social", "points": 15, "duration_min": 5},
        {"id": "nature", "title": "Nature Connection", "description": "Spend 5 minutes in nature or looking at nature", "dimension": "spiritual", "points": 10, "duration_min": 5},
        {"id": "journal", "title": "Reflect & Journal", "description": "Write about your day and how you feel", "dimension": "emotional", "points": 10, "duration_min": 10},
    ]

    WEEKLY_THEMES = {
        1: "Foundation Week — Establish basic wellness habits",
        2: "Movement Week — Focus on physical activity",
        3: "Mindfulness Week — Practice meditation and awareness",
        4: "Connection Week — Strengthen social bonds",
        5: "Balance Week — Harmonize all wellness dimensions",
        6: "Challenge Week — Push your boundaries",
        7: "Recovery Week — Rest and restore",
        8: "Growth Week — Learn something new",
    }

    def __init__(self):
        self.wellness_logs: Dict[str, List[dict]] = {}
        self.challenge_completions: Dict[str, List[dict]] = {}
        self.streaks: Dict[str, dict] = {}
        self.goals: Dict[str, List[dict]] = {}

    def log_wellness(self, user_id: str, dimension: str, metric: str, value: float, notes: str = "") -> dict:
        entry = {
            "id": str(uuid.uuid4()),
            "dimension": dimension,
            "metric": metric,
            "value": value,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
        }
        self.wellness_logs.setdefault(user_id, []).append(entry)
        return entry

    def get_wellness_score(self, user_id: str) -> dict:
        logs = self.wellness_logs.get(user_id, [])
        recent = [l for l in logs if datetime.fromisoformat(l["timestamp"]) > datetime.now() - timedelta(days=7)]
        
        dimension_scores = {}
        for dim_key, dim_info in self.WELLNESS_DIMENSIONS.items():
            dim_logs = [l for l in recent if l["dimension"] == dim_key]
            if dim_logs:
                avg = sum(l["value"] for l in dim_logs) / len(dim_logs)
                dimension_scores[dim_key] = {"score": round(avg, 1), "name": dim_info["name"], "icon": dim_info["icon"], "weight": dim_info["weight"]}
            else:
                dimension_scores[dim_key] = {"score": 50, "name": dim_info["name"], "icon": dim_info["icon"], "weight": dim_info["weight"], "note": "No data this week"}
        
        overall = sum(d["score"] * d["weight"] for d in dimension_scores.values())
        return {"overall_score": round(overall, 1), "dimensions": dimension_scores, "period": "7d", "generated_at": datetime.now().isoformat()}

    def complete_challenge(self, user_id: str, challenge_id: str) -> dict:
        challenge = next((c for c in self.DAILY_CHALLENGES if c["id"] == challenge_id), None)
        if not challenge:
            return {"error": "Challenge not found"}
        
        completion = {
            "id": str(uuid.uuid4()),
            "challenge_id": challenge_id,
            "challenge_title": challenge["title"],
            "points_earned": challenge["points"],
            "dimension": challenge["dimension"],
            "completed_at": datetime.now().isoformat(),
        }
        self.challenge_completions.setdefault(user_id, []).append(completion)
        
        streak = self.streaks.get(user_id, {"current": 0, "best": 0, "last_date": None})
        today = datetime.now().date().isoformat()
        if streak["last_date"] != today:
            yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
            streak["current"] = streak["current"] + 1 if streak["last_date"] == yesterday else 1
            streak["best"] = max(streak["best"], streak["current"])
            streak["last_date"] = today
        self.streaks[user_id] = streak
        
        total_points = sum(c["points_earned"] for c in self.challenge_completions.get(user_id, []))
        return {**completion, "total_points": total_points, "streak": streak}

    def get_daily_challenges(self, user_id: str, count: int = 5) -> List[dict]:
        import random
        completed_today = {c["challenge_id"] for c in self.challenge_completions.get(user_id, []) if datetime.fromisoformat(c["completed_at"]).date() == datetime.now().date()}
        available = [c for c in self.DAILY_CHALLENGES if c["id"] not in completed_today]
        return random.sample(available, min(count, len(available)))

    def get_wellness_history(self, user_id: str, days: int = 30) -> dict:
        logs = self.wellness_logs.get(user_id, [])
        cutoff = datetime.now() - timedelta(days=days)
        recent = [l for l in logs if datetime.fromisoformat(l["timestamp"]) >= cutoff]
        
        daily = {}
        for log in recent:
            day = log["timestamp"][:10]
            daily.setdefault(day, []).append(log)
        
        return {"days": days, "total_entries": len(recent), "daily_data": {d: {"count": len(entries), "avg_value": round(sum(e["value"] for e in entries) / len(entries), 1)} for d, entries in daily.items()}}


wellness_hub = WellnessHub()

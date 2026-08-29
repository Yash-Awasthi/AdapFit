"""
Social Sharing & Viral Health Challenges

Features:
- Generate shareable health cards (workout, achievement, streak)
- Social media share templates (Instagram, Twitter, Facebook)
- Viral health challenges (30-day push-up, hydration, meditation)
- Challenge invitations and tracking
- Shareable progress reports
- Health transformation stories
"""
import time
import secrets
from typing import Optional
from dataclasses import dataclass, field


CHALLENGE_TEMPLATES = [
    {"id": "ch_001", "name": "30-Day Push-Up Challenge", "description": "Start with 10, add 2 each day. Reach 68 by day 30!", "type": "fitness", "duration_days": 30, "difficulty": "intermediate", "participants": 1247, "hashtags": ["#PushUpChallenge", "#30DayFit", "#AdapFit"]},
    {"id": "ch_002", "name": "Hydration Hero Week", "description": "Drink 3L of water every day for 7 days", "type": "nutrition", "duration_days": 7, "difficulty": "beginner", "participants": 3421, "hashtags": ["#HydrationHero", "#WaterChallenge", "#HealthyHabits"]},
    {"id": "ch_003", "name": "Mindful March", "description": "Meditate for 10 minutes every day this month", "type": "mental", "duration_days": 31, "difficulty": "beginner", "participants": 892, "hashtags": ["#MindfulMarch", "#MeditationChallenge", "#MentalHealth"]},
    {"id": "ch_004", "name": "10K Steps Daily", "description": "Walk 10,000 steps every day for 2 weeks", "type": "fitness", "duration_days": 14, "difficulty": "beginner", "participants": 5678, "hashtags": ["#10KSteps", "#WalkChallenge", "#ActiveLife"]},
    {"id": "ch_005", "name": "No Sugar Week", "description": "Zero added sugar for 7 days", "type": "nutrition", "duration_days": 7, "difficulty": "intermediate", "participants": 2134, "hashtags": ["#NoSugarWeek", "#SugarFree", "#CleanEating"]},
    {"id": "ch_006", "name": "Sleep Champion", "description": "Get 8+ hours of sleep every night for 2 weeks", "type": "sleep", "duration_days": 14, "difficulty": "beginner", "participants": 1876, "hashtags": ["#SleepChampion", "#RestWell", "#SleepHygiene"]},
    {"id": "ch_007", "name": "Core Crusher", "description": "Plank every day: start at 30s, add 10s daily", "type": "fitness", "duration_days": 21, "difficulty": "intermediate", "participants": 967, "hashtags": ["#CoreCrusher", "#PlankChallenge", "#StrongCore"]},
    {"id": "ch_008", "name": "Gratitude Journal", "description": "Write 3 things you're grateful for every day", "type": "mental", "duration_days": 30, "difficulty": "beginner", "participants": 1543, "hashtags": ["#GratitudeJournal", "#Thankful", "#MentalWellness"]},
]


class SocialSharingService:
    """Social sharing, viral challenges, and health content generation."""

    def __init__(self):
        self._challenges = {c["id"]: c for c in CHALLENGE_TEMPLATES}
        self._user_challenges: dict[str, list[dict]] = {}
        self._shared_cards: list[dict] = []
        self._stories: list[dict] = []

    def get_challenges(self, challenge_type: str = "", trending: bool = False) -> list[dict]:
        challenges = list(self._challenges.values())
        if challenge_type:
            challenges = [c for c in challenges if c["type"] == challenge_type]
        if trending:
            challenges = sorted(challenges, key=lambda c: c["participants"], reverse=True)
        return challenges

    def join_challenge(self, user_id: str, challenge_id: str) -> dict:
        challenge = self._challenges.get(challenge_id)
        if not challenge:
            return {"error": "Challenge not found"}
        user_challenges = self._user_challenges.setdefault(user_id, [])
        existing = [uc for uc in user_challenges if uc["challenge_id"] == challenge_id]
        if existing:
            return {"already_joined": True}
        entry = {"challenge_id": challenge_id, "name": challenge["name"], "joined_at": time.time(), "progress": 0, "completed": False, "days_completed": 0}
        user_challenges.append(entry)
        challenge["participants"] = challenge.get("participants", 0) + 1
        return {"joined": True, "challenge": challenge["name"], "duration": challenge["duration_days"]}

    def log_challenge_day(self, user_id: str, challenge_id: str) -> dict:
        user_challenges = self._user_challenges.get(user_id, [])
        for uc in user_challenges:
            if uc["challenge_id"] == challenge_id:
                uc["days_completed"] += 1
                challenge = self._challenges.get(challenge_id, {})
                total_days = challenge.get("duration_days", 30)
                uc["progress"] = min(100, int(uc["days_completed"] / total_days * 100))
                if uc["days_completed"] >= total_days:
                    uc["completed"] = True
                return {"logged": True, "days_completed": uc["days_completed"], "progress": uc["progress"], "completed": uc["completed"]}
        return {"error": "Not joined this challenge"}

    def get_user_challenges(self, user_id: str) -> list[dict]:
        return self._user_challenges.get(user_id, [])

    def generate_share_card(self, user_id: str, card_type: str, data: dict) -> dict:
        card_templates = {
            "workout": {"title": "Workout Complete!", "subtitle": f"{data.get('duration', 0)} min | {data.get('calories', 0)} cal", "color": "#10B981", "icon": "🏋️"},
            "achievement": {"title": "Achievement Unlocked!", "subtitle": data.get("badge_name", "New Badge"), "color": "#EAB308", "icon": data.get("icon", "🏆")},
            "streak": {"title": f"{data.get('streak', 0)}-Day Streak!", "subtitle": "Keep it going!", "color": "#F97316", "icon": "🔥"},
            "milestone": {"title": "Milestone Reached!", "subtitle": data.get("milestone", "Great progress"), "color": "#6366F1", "icon": "🎯"},
            "transformation": {"title": "Health Transformation", "subtitle": data.get("summary", "Amazing progress"), "color": "#EC4899", "icon": "✨"},
        }
        template = card_templates.get(card_type, card_templates["achievement"])
        card = {
            "id": f"card_{secrets.token_hex(6)}", "user_id": user_id, "type": card_type,
            "title": template["title"], "subtitle": template["subtitle"],
            "color": template["color"], "icon": template["icon"],
            "share_text": f"{template['title']} {template['subtitle']} #AdapFit #HealthJourney",
            "created_at": time.time(),
        }
        self._shared_cards.append(card)
        return {"card": card, "share_urls": {
            "twitter": f"https://twitter.com/intent/tweet?text={card['share_text'].replace(' ', '%20')}",
            "facebook": f"https://www.facebook.com/sharer/sharer.php?quote={card['share_text'].replace(' ', '%20')}",
            "instagram": "Copy text and share to Instagram Stories",
        }}

    def get_share_cards(self, user_id: str) -> list[dict]:
        return [c for c in self._shared_cards if c["user_id"] == user_id]

    def create_transformation_story(self, user_id: str, before: dict, after: dict, summary: str) -> dict:
        story = {
            "id": f"story_{secrets.token_hex(6)}", "user_id": user_id,
            "before": before, "after": after, "summary": summary,
            "weight_change": after.get("weight", 0) - before.get("weight", 0),
            "duration_days": after.get("days", 0),
            "created_at": time.time(),
        }
        self._stories.append(story)
        return {"story": story}

    def get_trending_challenges(self, limit: int = 5) -> list[dict]:
        return sorted(self._challenges.values(), key=lambda c: c["participants"], reverse=True)[:limit]


social_sharing_service = SocialSharingService()

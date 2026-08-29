"""
Health Community V2 — Enhanced social features for health engagement
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid


class HealthCommunityV2:
    CHALLENGE_TYPES = {
        "step": {"name": "Step Challenge", "unit": "steps", "daily_goal": 10000, "icon": "🚶"},
        "water": {"name": "Hydration Challenge", "unit": "glasses", "daily_goal": 8, "icon": "💧"},
        "sleep": {"name": "Sleep Challenge", "unit": "hours", "daily_goal": 8, "icon": "😴"},
        "exercise": {"name": "Exercise Challenge", "unit": "minutes", "daily_goal": 30, "icon": "💪"},
        "meditation": {"name": "Mindfulness Challenge", "unit": "minutes", "daily_goal": 10, "icon": "🧘"},
        "weight_loss": {"name": "Weight Loss Challenge", "unit": "lbs", "daily_goal": 0.5, "icon": "⚖️"},
    }

    ACHIEVEMENT_BADGES = [
        {"id": "first_workout", "title": "First Workout", "description": "Complete your first workout", "icon": "🎉", "points": 10},
        {"id": "week_streak", "title": "Week Warrior", "description": "7-day activity streak", "icon": "🔥", "points": 50},
        {"id": "month_streak", "title": "Monthly Master", "description": "30-day activity streak", "icon": "🏆", "points": 200},
        {"id": "10k_steps", "title": "10K Club", "description": "Hit 10,000 steps in a day", "icon": "👟", "points": 25},
        {"id": "hydrated", "title": "Hydration Hero", "description": "Drink 8 glasses of water for 7 days", "icon": "💧", "points": 30},
        {"id": "early_bird", "title": "Early Bird", "description": "Exercise before 7 AM", "icon": "🌅", "points": 15},
        {"id": "night_owl", "title": "Night Owl", "description": "Log a late evening workout", "icon": "🦉", "points": 15},
        {"id": "social_butterfly", "title": "Social Butterfly", "description": "Join 3 challenges", "icon": "🦋", "points": 20},
        {"id": "mentor", "title": "Mentor", "description": "Help 5 other users", "icon": "🎓", "points": 50},
        {"id": "centurion", "title": "Centurion", "description": "Earn 100 total points", "icon": "💯", "points": 100},
    ]

    def __init__(self):
        self.challenges: Dict[str, dict] = {}
        self.participants: Dict[str, List[dict]] = {}
        self.leaderboards: Dict[str, List[dict]] = {}
        self.user_achievements: Dict[str, List[dict]] = {}
        self.user_points: Dict[str, int] = {}
        self.posts: Dict[str, List[dict]] = {}

    def create_challenge(self, creator_id: str, challenge_type: str, title: str, description: str, duration_days: int = 7, max_participants: int = 50) -> dict:
        challenge_config = self.CHALLENGE_TYPES.get(challenge_type, {})
        challenge = {
            "id": str(uuid.uuid4()),
            "creator_id": creator_id,
            "type": challenge_type,
            "title": title,
            "description": description,
            "goal": challenge_config.get("daily_goal", 10),
            "unit": challenge_config.get("unit", "units"),
            "icon": challenge_config.get("icon", "🏅"),
            "duration_days": duration_days,
            "max_participants": max_participants,
            "participants_count": 1,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "ends_at": (datetime.now() + timedelta(days=duration_days)).isoformat(),
        }
        self.challenges[challenge["id"]] = challenge
        self.participants[challenge["id"]] = [{"user_id": creator_id, "joined_at": datetime.now().isoformat(), "progress": [], "total": 0}]
        self.leaderboards[challenge["id"]] = [{"user_id": creator_id, "total": 0, "rank": 1}]
        return challenge

    def join_challenge(self, user_id: str, challenge_id: str) -> dict:
        challenge = self.challenges.get(challenge_id)
        if not challenge:
            return {"error": "Challenge not found"}
        if challenge["status"] != "active":
            return {"error": "Challenge is not active"}
        
        participants = self.participants.get(challenge_id, [])
        if any(p["user_id"] == user_id for p in participants):
            return {"error": "Already participating"}
        if len(participants) >= challenge["max_participants"]:
            return {"error": "Challenge is full"}
        
        participant = {"user_id": user_id, "joined_at": datetime.now().isoformat(), "progress": [], "total": 0}
        participants.append(participant)
        self.participants[challenge_id] = participants
        challenge["participants_count"] = len(participants)
        self.leaderboards.setdefault(challenge_id, []).append({"user_id": user_id, "total": 0, "rank": len(participants)})
        return {"status": "joined", "challenge": challenge["title"]}

    def log_progress(self, user_id: str, challenge_id: str, value: float) -> dict:
        participants = self.participants.get(challenge_id, [])
        for p in participants:
            if p["user_id"] == user_id:
                p["progress"].append({"value": value, "date": datetime.now().date().isoformat()})
                p["total"] += value
                
                leaderboard = self.leaderboards.get(challenge_id, [])
                for entry in leaderboard:
                    if entry["user_id"] == user_id:
                        entry["total"] = p["total"]
                leaderboard.sort(key=lambda x: x["total"], reverse=True)
                for i, entry in enumerate(leaderboard):
                    entry["rank"] = i + 1
                
                return {"status": "logged", "total": p["total"], "rank": next((e["rank"] for e in leaderboard if e["user_id"] == user_id), None)}
        return {"error": "Not participating"}

    def get_leaderboard(self, challenge_id: str) -> List[dict]:
        return self.leaderboards.get(challenge_id, [])

    def get_user_challenges(self, user_id: str) -> List[dict]:
        result = []
        for cid, participants in self.participants.items():
            if any(p["user_id"] == user_id for p in participants):
                challenge = self.challenges.get(cid)
                if challenge:
                    result.append(challenge)
        return result

    def create_post(self, user_id: str, content: str, post_type: str = "update", tags: List[str] = None) -> dict:
        post = {"id": str(uuid.uuid4()), "user_id": user_id, "content": content, "type": post_type, "tags": tags or [], "likes": 0, "comments": [], "created_at": datetime.now().isoformat()}
        self.posts.setdefault(user_id, []).append(post)
        return post

    def like_post(self, post_id: str) -> dict:
        for user_posts in self.posts.values():
            for post in user_posts:
                if post["id"] == post_id:
                    post["likes"] += 1
                    return {"post_id": post_id, "likes": post["likes"]}
        return {"error": "Post not found"}

    def get_community_feed(self, limit: int = 20) -> List[dict]:
        all_posts = []
        for posts in self.posts.values():
            all_posts.extend(posts)
        return sorted(all_posts, key=lambda x: x["created_at"], reverse=True)[:limit]

    def award_achievement(self, user_id: str, badge_id: str) -> dict:
        badge = next((b for b in self.ACHIEVEMENT_BADGES if b["id"] == badge_id), None)
        if not badge:
            return {"error": "Badge not found"}
        achievement = {"id": str(uuid.uuid4()), "badge_id": badge_id, "title": badge["title"], "icon": badge["icon"], "points": badge["points"], "earned_at": datetime.now().isoformat()}
        self.user_achievements.setdefault(user_id, []).append(achievement)
        self.user_points[user_id] = self.user_points.get(user_id, 0) + badge["points"]
        return {**achievement, "total_points": self.user_points[user_id]}

    def get_user_stats(self, user_id: str) -> dict:
        achievements = self.user_achievements.get(user_id, [])
        return {"total_points": self.user_points.get(user_id, 0), "badges_earned": len(achievements), "challenges_joined": len(self.get_user_challenges(user_id)), "posts_created": sum(len(posts) for uid, posts in self.posts.items() if uid == user_id)}


health_community_v2 = HealthCommunityV2()

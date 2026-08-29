"""
Community Service — Health Challenges, Leaderboards & Social Features

Features:
- Health challenges (step, hydration, sleep, meditation)
- Challenge creation and management
- Leaderboard rankings
- Team formation and management
- Challenge progress tracking
- Community feed with shared activities
- Achievement sharing
"""
import time
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class ChallengeType(Enum):
    STEPS = "steps"
    HYDRATION = "hydration"
    SLEEP = "sleep"
    MEDITATION = "meditation"
    WORKOUT = "workout"
    CUSTOM = "custom"


class ChallengeStatus(Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"


@dataclass
class Challenge:
    id: str
    title: str
    description: str
    challenge_type: ChallengeType
    target: float
    unit: str
    duration_days: int
    created_by: str
    status: ChallengeStatus
    participants: list[str]
    start_date: float
    end_date: float


@dataclass
class Participant:
    user_id: str
    display_name: str
    avatar_emoji: str
    progress: float
    rank: int
    team: Optional[str] = None


class CommunityService:
    """Social health challenges and community features system."""

    CHALLENGE_TEMPLATES = {
        "steps": {"title": "Step Challenge", "description": "Walk 10,000 steps daily for a week", "target": 70000, "unit": "steps", "duration": 7},
        "hydration": {"title": "Hydration Hero", "description": "Drink 8 glasses of water daily for 5 days", "target": 40, "unit": "glasses", "duration": 5},
        "sleep": {"title": "Sleep Champion", "description": "Get 7+ hours of sleep for 10 nights", "target": 10, "unit": "nights", "duration": 10},
        "meditation": {"title": "Mindful Week", "description": "Meditate for 10 minutes daily for 7 days", "target": 7, "unit": "sessions", "duration": 7},
        "workout": {"title": "Workout Warrior", "description": "Complete 5 workouts in 7 days", "target": 5, "unit": "workouts", "duration": 7},
    }

    def __init__(self):
        self._challenges: list[Challenge] = []
        self._participants: dict[str, list[Participant]] = {}  # challenge_id -> participants
        self._feed: list[dict] = []
        self._init_demo_challenges()

    def _init_demo_challenges(self):
        """Initialize with sample active challenges."""
        now = time.time()
        templates = [
            ("challenge_1", "steps", now - 86400 * 3),
            ("challenge_2", "hydration", now - 86400 * 1),
            ("challenge_3", "meditation", now - 86400 * 5),
        ]
        for cid, ttype, start in templates:
            t = self.CHALLENGE_TEMPLATES[ttype]
            self._challenges.append(Challenge(
                id=cid, title=t["title"], description=t["description"],
                challenge_type=ChallengeType(ttype), target=t["target"],
                unit=t["unit"], duration_days=t["duration"], created_by="system",
                status=ChallengeStatus.ACTIVE,
                participants=["user_1", "user_2", "user_3", "user_4", "user_5"],
                start_date=start, end_date=start + t["duration"] * 86400,
            ))
            self._participants[cid] = [
                Participant("user_1", "You", "🏋️", 45000 if ttype == "steps" else 28, 1),
                Participant("user_2", "Alex", "🏃", 38000 if ttype == "steps" else 24, 2),
                Participant("user_3", "Sarah", "💪", 35000 if ttype == "steps" else 22, 3),
                Participant("user_4", "Mike", "🚴", 30000 if ttype == "steps" else 18, 4),
                Participant("user_5", "Emma", "🧘", 25000 if ttype == "steps" else 15, 5),
            ]

    def get_active_challenges(self) -> list[dict]:
        """Get all active challenges."""
        return [
            {"id": c.id, "title": c.title, "description": c.description,
             "type": c.challenge_type.value, "target": c.target, "unit": c.unit,
             "duration_days": c.duration_days, "participants": len(c.participants),
             "status": c.status.value,
             "days_remaining": max(0, round((c.end_date - time.time()) / 86400)),
             "progress_pct": round(self._get_user_progress(c.id) / c.target * 100, 1)}
            for c in self._challenges if c.status == ChallengeStatus.ACTIVE
        ]

    def get_leaderboard(self, challenge_id: str) -> dict:
        """Get leaderboard for a challenge."""
        participants = self._participants.get(challenge_id, [])
        challenge = next((c for c in self._challenges if c.id == challenge_id), None)
        return {
            "challenge": challenge.title if challenge else "Unknown",
            "rankings": [
                {"rank": p.rank, "name": p.display_name, "avatar": p.avatar_emoji,
                 "progress": p.progress, "team": p.team}
                for p in sorted(participants, key=lambda x: x.progress, reverse=True)
            ],
        }

    def join_challenge(self, challenge_id: str, user_id: str = "user_1") -> dict:
        """Join a challenge."""
        challenge = next((c for c in self._challenges if c.id == challenge_id), None)
        if not challenge:
            return {"error": "Challenge not found"}
        if user_id not in challenge.participants:
            challenge.participants.append(user_id)
        return {"joined": True, "challenge": challenge.title, "participants": len(challenge.participants)}

    def get_community_feed(self, limit: int = 20) -> list[dict]:
        """Get community activity feed."""
        return [
            {"user": "Alex", "avatar": "🏃", "action": "completed a 5K walk", "time": "2 hours ago", "likes": 12},
            {"user": "Sarah", "avatar": "💪", "action": "hit a new personal best: 15K steps", "time": "4 hours ago", "likes": 24},
            {"user": "Mike", "avatar": "🚴", "action": "joined the Step Challenge", "time": "6 hours ago", "likes": 8},
            {"user": "Emma", "avatar": "🧘", "action": "completed 7-day meditation streak!", "time": "1 day ago", "likes": 31},
            {"user": "You", "avatar": "🏋️", "action": "logged a workout: Upper Body", "time": "1 day ago", "likes": 15},
        ]

    def create_challenge(self, title: str, description: str, challenge_type: str,
                         target: float, unit: str, duration_days: int) -> dict:
        """Create a new community challenge."""
        try:
            ct = ChallengeType(challenge_type)
        except ValueError:
            ct = ChallengeType.CUSTOM
        now = time.time()
        challenge = Challenge(
            id=f"challenge_{int(now)}", title=title, description=description,
            challenge_type=ct, target=target, unit=unit, duration_days=duration_days,
            created_by="user_1", status=ChallengeStatus.ACTIVE,
            participants=["user_1"], start_date=now, end_date=now + duration_days * 86400,
        )
        self._challenges.append(challenge)
        self._participants[challenge.id] = [Participant("user_1", "You", "🏋️", 0, 1)]
        return {"created": True, "challenge_id": challenge.id, "title": title}

    def get_team_standings(self) -> list[dict]:
        """Get team standings."""
        return [
            {"team": "Alpha", "emoji": " alpha", "members": 5, "total_points": 1250, "avg_steps": 8200},
            {"team": "Beta", "emoji": " beta", "members": 4, "total_points": 980, "avg_steps": 7500},
            {"team": "Gamma", "emoji": " gamma", "members": 6, "total_points": 1100, "avg_steps": 7000},
        ]

    def get_challenge_types(self) -> list[dict]:
        """Get available challenge templates."""
        return [
            {"type": k, "title": v["title"], "description": v["description"],
             "target": v["target"], "unit": v["unit"], "duration": v["duration"]}
            for k, v in self.CHALLENGE_TEMPLATES.items()
        ]

    def _get_user_progress(self, challenge_id: str) -> float:
        participants = self._participants.get(challenge_id, [])
        user = next((p for p in participants if p.user_id == "user_1"), None)
        return user.progress if user else 0


community_service = CommunityService()

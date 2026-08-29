"""Peer Support Matching & Accountability Partner Service.

Based on 2025 peer support research:
- AI-powered peer matching algorithm
- Support circles with shared goals
- Anonymous sharing and daily check-ins
- Crisis escalation to professional help
- Accountability partner system
- Progress sharing and encouragement
"""

import time
import random
from typing import Dict, List, Any


class PeerSupportService:
    """Peer support matching and accountability partnerships."""

    def __init__(self):
        self.profiles: Dict[str, Dict] = {}
        self.matches: Dict[str, List] = {}
        self.circles: Dict[str, Dict] = {}
        self.check_ins: Dict[str, List] = {}

    def create_profile(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create peer support profile."""
        self.profiles[user_id] = {
            "user_id": user_id,
            "goals": data.get("goals", ["mental_health"]),
            "challenges": data.get("challenges", []),
            "communication_style": data.get("style", "supportive"),
            "availability": data.get("availability", "flexible"),
            "preferences": data.get("preferences", {}),
            "anonymous_name": data.get("anonymous_name", f"User_{random.randint(1000,9999)}"),
            "created_at": time.time(),
        }
        return self.profiles[user_id]

    def find_peer(self, user_id: str) -> Dict[str, Any]:
        """Find a compatible peer match using AI matching."""
        profile = self.profiles.get(user_id, {})
        goals = set(profile.get("goals", []))

        # Simulate AI matching — find similar goals
        candidates = []
        for uid, p in self.profiles.items():
            if uid != user_id:
                common = len(goals.intersection(set(p.get("goals", []))))
                if common > 0:
                    candidates.append({"user_id": uid, "anonymous_name": p.get("anonymous_name", "Anonymous"), "compatibility_score": min(100, 50 + common * 15), "shared_goals": list(goals.intersection(set(p.get("goals", []))))})

        candidates.sort(key=lambda x: x["compatibility_score"], reverse=True)
        best_match = candidates[0] if candidates else None

        if best_match:
            if user_id not in self.matches:
                self.matches[user_id] = []
            self.matches[user_id].append({"partner": best_match["user_id"], "matched_at": time.time(), "status": "active"})

        return {"match_found": best_match is not None, "match": best_match, "message": f"Found a match: {best_match['anonymous_name']}" if best_match else "No matches available right now — we'll notify you when someone compatible joins"}

    def check_in(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Daily check-in with peer."""
        if user_id not in self.check_ins:
            self.check_ins[user_id] = []

        entry = {
            "date": data.get("date", time.strftime("%Y-%m-%d")),
            "mood": data.get("mood", 5),
            "energy": data.get("energy", 5),
            "gratitude": data.get("gratitude", ""),
            "challenge_today": data.get("challenge", ""),
            "completed_goal": data.get("completed", False),
            "message_for_partner": data.get("message", ""),
            "anonymous": True,
            "timestamp": time.time(),
        }
        self.check_ins[user_id].append(entry)

        streak = len(self.check_ins.get(user_id, []))
        return {
            "check_in_logged": True,
            "streak": streak,
            "encouragement": f"Day {streak} of daily check-ins! Consistency is key." if streak > 1 else "First check-in! Welcome to your support journey.",
            "partner_notified": True,
        }

    def create_circle(self, creator_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a support circle."""
        circle_id = f"circle_{int(time.time())}"
        self.circles[circle_id] = {
            "circle_id": circle_id,
            "name": data.get("name", "Support Circle"),
            "topic": data.get("topic", "general"),
            "members": [creator_id],
            "created_by": creator_id,
            "max_members": data.get("max_members", 8),
            "created_at": time.time(),
            "daily_prompt": data.get("prompt", "What's one thing you're grateful for today?"),
        }
        return self.circles[circle_id]

    def join_circle(self, user_id: str, circle_id: str) -> Dict[str, Any]:
        """Join a support circle."""
        circle = self.circles.get(circle_id)
        if not circle:
            return {"error": "Circle not found"}
        if len(circle["members"]) >= circle["max_members"]:
            return {"error": "Circle is full"}
        circle["members"].append(user_id)
        return {"joined": True, "circle_name": circle["name"], "members": len(circle["members"])}

    def escalate_crisis(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Escalate to professional help when crisis detected."""
        return {
            "escalated": True,
            "resources": [
                {"name": "National Suicide Prevention Lifeline", "number": "988", "available": "24/7"},
                {"name": "Crisis Text Line", "number": "Text HOME to 741741", "available": "24/7"},
                {"name": "SAMHSA Helpline", "number": "1-800-662-4357", "available": "24/7"},
                {"name": "NAMI Helpline", "number": "1-800-950-6264", "available": "Mon-Fri 10am-10pm ET"},
            ],
            "message": "You're not alone. Professional help is available 24/7. Please reach out.",
        }

    def get_partner_messages(self, user_id: str) -> List[Dict]:
        """Get recent messages from support partner."""
        partner_checks = []
        for partner_id, checks in self.check_ins.items():
            if partner_id != user_id:
                for check in checks[-3:]:
                    partner_checks.append({"from": partner_id, "date": check["date"], "mood": check["mood"], "message": check.get("message_for_partner", ""), "gratitude": check.get("gratitude", "")})
        return partner_checks


peer_support_service = PeerSupportService()

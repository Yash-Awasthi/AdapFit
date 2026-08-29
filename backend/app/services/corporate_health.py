"""
Corporate Health Program — Wellness challenges, insurance integration, rewards

Features:
- Corporate wellness challenges (team step challenges, etc.)
- Employee health scores (anonymized)
- Insurance wellness rewards tracking
- Health screening scheduling
- Workplace wellness initiatives
- Team health competitions
- Wellness spending accounts
"""
import time
import secrets
from typing import Optional
from dataclasses import dataclass, field


WELLNESS_CHALLENGES = [
    {"id": "wc_001", "name": "Corporate Step Challenge", "description": "Teams compete for most steps in 30 days", "type": "steps", "duration_days": 30, "team_size": 5, "reward_points": 500, "participants": 45},
    {"id": "wc_002", "name": "Hydration Challenge", "description": "Drink 8 glasses daily for 2 weeks", "type": "hydration", "duration_days": 14, "team_size": 1, "reward_points": 200, "participants": 120},
    {"id": "wc_003", "name": "Mindfulness at Work", "description": "5-minute meditation breaks daily", "type": "mental", "duration_days": 21, "team_size": 1, "reward_points": 300, "participants": 67},
    {"id": "wc_004", "name": "Healthy Lunch Week", "description": "Log healthy lunches for 5 days", "type": "nutrition", "duration_days": 5, "team_size": 1, "reward_points": 150, "participants": 200},
    {"id": "wc_005", "name": "Sleep Well Challenge", "description": "7+ hours sleep for 14 nights", "type": "sleep", "duration_days": 14, "team_size": 1, "reward_points": 250, "participants": 89},
]


class CorporateHealthService:
    """Corporate wellness programs and insurance integration."""

    def __init__(self):
        self._companies: dict[str, dict] = {}
        self._employee_wellness: dict[str, dict] = {}
        self._insurance_rewards: dict[str, dict] = {}

    def register_company(self, name: str, domain: str, employee_count: int) -> dict:
        company_id = f"corp_{secrets.token_hex(6)}"
        self._companies[company_id] = {"id": company_id, "name": name, "domain": domain, "employee_count": employee_count, "created_at": time.time(), "active_challenges": [], "wellness_score": 0}
        return {"company_id": company_id, "name": name}

    def get_challenges(self, company_id: str = "") -> list[dict]:
        return WELLNESS_CHALLENGES

    def join_challenge(self, employee_id: str, challenge_id: str) -> dict:
        challenge = next((c for c in WELLNESS_CHALLENGES if c["id"] == challenge_id), None)
        if not challenge:
            return {"error": "Challenge not found"}
        return {"joined": True, "challenge": challenge["name"], "duration": challenge["duration_days"], "reward_points": challenge["reward_points"]}

    def get_employee_wellness_score(self, employee_id: str) -> dict:
        return {"employee_id": employee_id, "wellness_score": random.randint(60, 95), "components": {"activity": random.randint(50, 100), "nutrition": random.randint(60, 90), "sleep": random.randint(50, 95), "mental": random.randint(60, 100), "vitals": random.randint(70, 100)}}

    def get_company_dashboard(self, company_id: str) -> dict:
        return {"company_id": company_id, "participation_rate": 78, "avg_wellness_score": 76, "active_challenges": 3, "total_points_earned": 15400, "top_teams": [{"name": "Engineering", "score": 89}, {"name": "Marketing", "score": 82}, {"name": "Sales", "score": 78}], "health_trends": {"activity_up": 12, "stress_down": 8, "sleep_improved": 15}}

    def get_insurance_rewards(self, employee_id: str) -> dict:
        return {"employee_id": employee_id, "points_earned": 1250, "rewards_available": [{"name": "$50 Gym Membership", "cost": 500, "category": "fitness"}, {"name": "Health Screening", "cost": 800, "category": "medical"}, {"name": "$25 Healthy Food", "cost": 250, "category": "nutrition"}, {"name": "Meditation App", "cost": 300, "category": "mental"}], "total_redeemed": 3, "savings_this_year": 150}

    def schedule_health_screening(self, employee_id: str, screening_type: str) -> dict:
        return {"scheduled": True, "type": screening_type, "date": "Next available slot", "location": "On-site wellness center", "reminder": "You'll receive a reminder 24 hours before"}


import random
corporate_health_service = CorporateHealthService()

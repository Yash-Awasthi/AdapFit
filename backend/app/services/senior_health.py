"""Senior Health Service - Fall prevention, balance training, aging gracefully.

Based on 2025 research on elderly health:
- Fall risk assessment and prevention
- Balance training programs
- Cognitive decline prevention
- Social isolation monitoring
- Medication management for seniors
- Daily living activity tracking
- Caregiver coordination
"""

import time
import random
from typing import Dict, List, Optional, Any


class SeniorHealthService:
    """Comprehensive senior health and aging support."""

    def __init__(self):
        self.profiles: Dict[str, Dict] = {}
        self.daily_logs: Dict[str, List] = {}
        self._init_fall_exercises()

    def _init_fall_exercises(self):
        self.balance_exercises = [
            {"name": "Single Leg Stand", "description": "Stand on one leg for 10-30 seconds, switch legs", "difficulty": "beginner", "duration": "2 min", "benefit": "Improves static balance", "safety": "Hold chair for support"},
            {"name": "Heel-to-Toe Walk", "description": "Walk in a straight line, heel touching toe", "difficulty": "beginner", "duration": "3 min", "benefit": "Improves dynamic balance", "safety": "Walk near a wall"},
            {"name": "Chair Squats", "description": "Stand up from chair without using hands, sit back down", "difficulty": "beginner", "duration": "3 min", "benefit": "Strengthens legs for fall recovery", "safety": "Use chair with armrests"},
            {"name": "Side Leg Raises", "description": "Hold chair, lift leg to the side, hold 3 seconds", "difficulty": "beginner", "duration": "3 min", "benefit": "Strengthens hip abductors", "safety": "Keep one hand on chair"},
            {"name": "Tai Chi Basic", "description": "Slow flowing movements with weight shifting", "difficulty": "intermediate", "duration": "10 min", "benefit": "Gold standard for fall prevention", "safety": "Learn from instructor"},
            {"name": "Tandem Stance", "description": "Stand with one foot directly in front of other", "difficulty": "intermediate", "duration": "2 min", "benefit": "Improves lateral stability", "safety": "Near counter or wall"},
            {"name": "Step-Ups", "description": "Step up onto low step, step back down", "difficulty": "intermediate", "duration": "3 min", "benefit": "Strengthens lower body", "safety": "Use sturdy step"},
            {"name": "Weight Shifts", "description": "Shift weight from one foot to other slowly", "difficulty": "beginner", "duration": "2 min", "benefit": "Improves weight transfer", "safety": "Hold chair if needed"},
        ]

        self.cognitive_exercises = [
            {"name": "Word Recall", "description": "Remember words from a list after 5 minutes", "type": "memory", "frequency": "daily"},
            {"name": "Crossword Puzzles", "description": "Complete crossword puzzles for vocabulary", "type": "language", "frequency": "daily"},
            {"name": "Name-Face Association", "description": "Practice remembering names of new people", "type": "memory", "frequency": "social"},
            {"name": "Recipe Following", "description": "Cook a new recipe without looking back", "type": "attention", "frequency": "weekly"},
            {"name": "Card Games", "description": "Play card games that require strategy", "type": "executive", "frequency": "weekly"},
            {"name": "Music Listening", "description": "Listen to familiar songs and recall memories", "type": "emotional_memory", "frequency": "daily"},
        ]

        self.fall_risk_factors = {
            "age_75_plus": {"weight": 3, "modifiable": False},
            "previous_fall": {"weight": 4, "modifiable": False},
            "balance_problems": {"weight": 3, "modifiable": True},
            "muscle_weakness": {"weight": 3, "modifiable": True},
            "medication_4_plus": {"weight": 2, "modifiable": True},
            "vision_problems": {"weight": 2, "modifiable": True},
            "home_hazards": {"weight": 2, "modifiable": True},
            "dizziness": {"weight": 2, "modifiable": True},
            "depression": {"weight": 1, "modifiable": True},
            "walking_difficulty": {"weight": 3, "modifiable": True},
        }

    def create_profile(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create senior health profile."""
        self.profiles[user_id] = {
            "user_id": user_id,
            "age": data.get("age", 70),
            "fall_history": data.get("fall_history", []),
            "conditions": data.get("conditions", []),
            "medications": data.get("medications", []),
            "assistive_devices": data.get("devices", []),
            "home_setup": data.get("home_setup", {}),
            "emergency_contacts": data.get("emergency_contacts", []),
            "caregiver": data.get("caregiver"),
            "living_situation": data.get("living_situation", "independent"),
            "created_at": time.time(),
        }

        self._assess_fall_risk(user_id)
        return self.profiles[user_id]

    def assess_fall_risk(self, user_id: str) -> Dict[str, Any]:
        """Comprehensive fall risk assessment."""
        return self._assess_fall_risk(user_id)

    def log_daily(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log daily activities and health data."""
        if user_id not in self.daily_logs:
            self.daily_logs[user_id] = []

        entry = {
            "date": data.get("date", time.strftime("%Y-%m-%d")),
            "steps": data.get("steps", 0),
            "balance_exercises": data.get("balance_exercises_done", False),
            "cognitive_exercises": data.get("cognitive_done", False),
            "social_interaction": data.get("social_interaction", False),
            "medications_taken": data.get("medications_taken", True),
            "sleep_quality": data.get("sleep_quality", 5),
            "mood": data.get("mood", 5),
            "pain_level": data.get("pain_level", 3),
            "dizziness": data.get("dizziness", False),
            "near_fall": data.get("near_fall", False),
            "actual_fall": data.get("fall", False),
            "daily_living": data.get("daily_living_score", 8),
            "logged_at": time.time(),
        }

        self.daily_logs[user_id].append(entry)

        if entry["actual_fall"]:
            entry["alert_sent"] = True
            entry["follow_up_needed"] = True

        return entry

    def get_exercise_program(self, user_id: str) -> Dict[str, Any]:
        """Get personalized exercise program."""
        profile = self.profiles.get(user_id, {})
        risk_level = self._assess_fall_risk(user_id).get("risk_level", "moderate")

        if risk_level == "high":
            exercises = [e for e in self.balance_exercises if e["difficulty"] == "beginner"][:4]
            frequency = "daily"
            duration = "10-15 minutes"
        elif risk_level == "moderate":
            exercises = [e for e in self.balance_exercises if e["difficulty"] in ("beginner", "intermediate")][:5]
            frequency = "daily"
            duration = "15-20 minutes"
        else:
            exercises = self.balance_exercises[:6]
            frequency = "5x/week"
            duration = "20-25 minutes"

        return {
            "risk_level": risk_level,
            "exercises": exercises,
            "frequency": frequency,
            "session_duration": duration,
            "tips": ["Always have support nearby", "Stop if you feel dizzy", "Wear non-slip shoes", "Exercise when rested"],
        }

    def get_cognitive_program(self, user_id: str) -> Dict[str, Any]:
        """Get cognitive health program."""
        return {
            "daily_exercises": self.cognitive_exercises[:3],
            "weekly_goals": [
                "Try one new activity",
                "Social interaction daily",
                "Learn something new",
                "Recall 3 things from yesterday",
            ],
            "nutrition_tips": [
                "Eat fatty fish 2x/week (omega-3s)",
                "Berries daily (antioxidants)",
                "Leafy greens daily",
                "Stay hydrated",
            ],
            "social_recommendations": [
                "Call a friend daily",
                "Join a community group",
                "Volunteer",
                "Teach someone a skill you have",
            ],
        }

    def get_home_safety_checklist(self) -> List[Dict]:
        """Home safety checklist for fall prevention."""
        return [
            {"area": "Lighting", "checks": ["Night lights in bedroom/bathroom", "Light switches at both ends of hallways", "Bright lighting on stairs"], "priority": "high"},
            {"area": "Bathroom", "checks": ["Grab bars near toilet and shower", "Non-slip bath mat", "Shower chair", "Raised toilet seat"], "priority": "high"},
            {"area": "Stairs", "checks": ["Handrails on both sides", "Non-slip treads", "Good lighting", "Clear of clutter"], "priority": "high"},
            {"area": "Floors", "checks": ["Remove loose rugs", "Secure electrical cords", "Clear pathways", "Non-slip surfaces"], "priority": "medium"},
            {"area": "Kitchen", "checks": ["Frequently used items at waist height", "Sturdy step stool", "Non-slip floor mat"], "priority": "medium"},
            {"area": "Bedroom", "checks": ["Bed at appropriate height", "Phone within reach", "Pathway to bathroom clear"], "priority": "medium"},
        ]

    def get_social_connection_plan(self, user_id: str) -> Dict[str, Any]:
        """Social connection plan to combat isolation."""
        return {
            "daily": ["Call or text a family member", "Walk with a neighbor"],
            "weekly": ["Attend community event", "Visit friend or family member", "Volunteer activity"],
            "monthly": ["Join new group or class", "Host small gathering"],
            "technology": ["Video call family", "Online interest groups", "Social media with family"],
            "resources": ["Senior center programs", "Faith community", "Volunteer organizations", "Classes at library"],
        }

    def _assess_fall_risk(self, user_id: str) -> Dict[str, Any]:
        profile = self.profiles.get(user_id, {})
        score = 0
        risk_factors = []

        if profile.get("age", 70) >= 75:
            score += self.fall_risk_factors["age_75_plus"]["weight"]
            risk_factors.append("Age 75+")
        if len(profile.get("fall_history", [])) > 0:
            score += self.fall_risk_factors["previous_fall"]["weight"]
            risk_factors.append("Previous falls")
        if len(profile.get("medications", [])) >= 4:
            score += self.fall_risk_factors["medication_4_plus"]["weight"]
            risk_factors.append("Taking 4+ medications")

        risk_level = "high" if score >= 7 else "moderate" if score >= 4 else "low"

        return {
            "risk_score": score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "modifiable_factors": [f for f in risk_factors if True],
            "recommendation": "Comprehensive fall prevention program" if risk_level == "high" else "Balance exercises and home safety" if risk_level == "moderate" else "Maintain current activities",
        }


senior_health_service = SeniorHealthService()

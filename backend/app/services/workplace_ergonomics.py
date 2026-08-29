"""Workplace Ergonomics Service - Desk worker health, posture, RSI prevention.

Based on 2025 AI ergonomics research:
- Desk setup assessment
- Posture scoring and correction
- Sitting timer with break reminders
- Repetitive strain injury prevention
- Eye strain management (20-20-20 rule)
- Desk exercise routines
- Work wellness scoring
"""

import time
import random
from typing import Dict, List, Optional, Any


class WorkplaceErgonomicsService:
    """Workplace ergonomics, desk health, and RSI prevention."""

    def __init__(self):
        self.profiles: Dict[str, Dict] = {}
        self.sessions: Dict[str, List] = {}
        self._init_desk_exercises()

    def _init_desk_exercises(self):
        self.desk_exercises = [
            {"name": "Neck Rolls", "description": "Slowly roll head in circles, 5 each direction", "duration": "1 min", "frequency": "every_hour", "target": "neck"},
            {"name": "Shoulder Shrugs", "description": "Raise shoulders to ears, hold 5s, release", "duration": "1 min", "frequency": "every_hour", "target": "shoulders"},
            {"name": "Wrist Circles", "description": "Rotate wrists 10x each direction", "duration": "1 min", "frequency": "every_2_hours", "target": "wrists"},
            {"name": "Seated Spinal Twist", "description": "Twist torso left and right, hold 15s each", "duration": "2 min", "frequency": "every_2_hours", "target": "spine"},
            {"name": "Standing Calf Raises", "description": "Stand and raise up on toes, 15 reps", "duration": "1 min", "frequency": "every_2_hours", "target": "legs"},
            {"name": "Desk Push-ups", "description": "Hands on desk, push-ups at angle, 10 reps", "duration": "1 min", "frequency": "every_3_hours", "target": "chest"},
            {"name": "Hip Flexor Stretch", "description": "Stand, one foot forward, push hips forward", "duration": "2 min", "frequency": "every_3_hours", "target": "hips"},
            {"name": "Eye Palming", "description": "Rub hands warm, cover eyes, breathe 30s", "duration": "1 min", "frequency": "every_hour", "target": "eyes"},
            {"name": "Chin Tucks", "description": "Pull chin straight back, hold 5s, 10 reps", "duration": "1 min", "frequency": "every_hour", "target": "neck"},
            {"name": "Thoracic Extension", "description": "Hands behind head, arch upper back over chair", "duration": "1 min", "frequency": "every_2_hours", "target": "spine"},
        ]

        self.ergonomic_checklist = {
            "chair": {
                "height": "Feet flat on floor, thighs parallel to ground",
                "backrest": "Supports natural lumbar curve",
                "armrests": "Elbows at 90° when typing",
                "seat_depth": "2-3 finger gap between seat edge and knees",
            },
            "desk": {
                "height": "Elbows at 90° when typing",
                "clearance": "Room for legs to move freely",
                "reach": "Most-used items within arm's reach",
            },
            "monitor": {
                "distance": "Arm's length (20-26 inches)",
                "height": "Top of screen at eye level",
                "tilt": "Slight backward tilt (10-20°)",
                "glare": "No reflections or bright light behind",
            },
            "keyboard_mouse": {
                "position": "Elbows close to body, wrists neutral",
                "height": "Wrists straight, not bent up or down",
                "type": "Ergonomic keyboard if available",
            },
        }

        self.rsi_prevention = {
            "carpal_tunnel": [
                "Keep wrists neutral while typing",
                "Take breaks every 30 minutes",
                "Do wrist stretches and exercises",
                "Use ergonomic keyboard and mouse",
            ],
            "text_neck": [
                "Keep phone at eye level",
                "Look up every 20 minutes",
                "Do chin tucks and neck stretches",
                "Strengthen upper back muscles",
            ],
            "tech_shoulder": [
                "Keep shoulders relaxed, not hunched",
                "Adjust chair and desk height",
                "Do shoulder rolls and stretches",
                "Use monitor at proper height",
            ],
        }

    def create_profile(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create workplace ergonomics profile."""
        self.profiles[user_id] = {
            "user_id": user_id,
            "work_hours": data.get("work_hours", 8),
            "sitting_hours": data.get("sitting_hours", 6),
            "standing_desk": data.get("standing_desk", False),
            "monitor_count": data.get("monitors", 1),
            "work_type": data.get("work_type", "desk"),
            "existing_conditions": data.get("conditions", []),
            "setup_photo": data.get("setup_photo"),
            "created_at": time.time(),
        }
        return self.profiles[user_id]

    def assess_desk_setup(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess desk setup from user-provided data."""
        issues = []
        score = 100

        if not data.get("feet_flat"):
            issues.append({"item": "Feet not flat on floor", "fix": "Adjust chair height or use footrest", "severity": "high"})
            score -= 15
        if not data.get("lumbar_support"):
            issues.append({"item": "No lumbar support", "fix": "Add lumbar pillow or adjust chair", "severity": "high"})
            score -= 15
        if data.get("monitor_too_low"):
            issues.append({"item": "Monitor too low", "fix": "Raise monitor to eye level with stand", "severity": "medium"})
            score -= 10
        if data.get("monitor_too_far"):
            issues.append({"item": "Monitor too far", "fix": "Position arm's length away", "severity": "medium"})
            score -= 10
        if not data.get("wrists_neutral"):
            issues.append({"item": "Wrists bent while typing", "fix": "Adjust keyboard height or use wrist rest", "severity": "high"})
            score -= 15
        if data.get("screen_glare"):
            issues.append({"item": "Screen glare detected", "fix": "Reposition monitor or use anti-glare screen", "severity": "low"})
            score -= 5

        return {
            "score": max(0, score),
            "issues": issues,
            "checklist": self.ergonomic_checklist,
            "priority_fixes": [i for i in issues if i["severity"] == "high"],
            "recommendation": "Your setup looks good!" if not issues else f"Fix {len(issues)} issues for better ergonomics",
        }

    def start_sitting_session(self, user_id: str) -> Dict[str, Any]:
        """Start a sitting timer with break reminders."""
        session_id = f"sit_{user_id}_{int(time.time())}"
        if user_id not in self.sessions:
            self.sessions[user_id] = []
        self.sessions[user_id].append({"session_id": session_id, "start": time.time(), "breaks": 0})
        return {
            "session_id": session_id,
            "message": "Sitting timer started",
            "reminder_interval_minutes": 30,
            "next_reminder": "30 minutes",
            "break_exercises": random.sample(self.desk_exercises, 3),
        }

    def log_break(self, user_id: str, session_id: str, exercise_done: str) -> Dict[str, Any]:
        """Log a break taken during sitting session."""
        for session in self.sessions.get(user_id, []):
            if session["session_id"] == session_id:
                session["breaks"] += 1
                return {
                    "breaks_taken": session["breaks"],
                    "message": f"Great! You've taken {session['breaks']} break(s). Keep it up!",
                    "next_exercise": random.choice(self.desk_exercises),
                }
        return {"error": "Session not found"}

    def get_work_wellness_score(self, user_id: str) -> Dict[str, Any]:
        """Calculate work wellness score."""
        profile = self.profiles.get(user_id, {})
        sessions = self.sessions.get(user_id, [])

        sitting_hours = profile.get("sitting_hours", 6)
        total_breaks = sum(s.get("breaks", 0) for s in sessions)

        score = 100
        if sitting_hours > 8: score -= 20
        elif sitting_hours > 6: score -= 10
        if total_breaks == 0 and sessions: score -= 15
        if not profile.get("standing_desk"): score -= 5

        return {
            "wellness_score": max(0, min(100, score)),
            "sitting_hours": sitting_hours,
            "breaks_today": total_breaks,
            "recommendations": [
                "Take a 5-min break every 30 minutes" if sitting_hours > 6 else "Good sitting balance",
                "Consider a standing desk" if not profile.get("standing_desk") else "Great — using a standing desk",
                "Do the 20-20-20 eye rule every 20 minutes",
            ],
        }

    def get_20_20_20_timer(self) -> Dict[str, Any]:
        """Get 20-20-20 eye rule timer."""
        return {
            "rule": "Every 20 minutes, look at something 20 feet away for 20 seconds",
            "benefits": ["Reduces eye strain", "Prevents dry eyes", "Relieves focused vision fatigue"],
            "how_to": [
                "Set a timer for 20 minutes",
                "When it rings, look at a distant object (20+ feet away)",
                "Focus on it for 20 seconds",
                "Blink several times to re-moisten eyes",
                "Resume work",
            ],
        }


workplace_ergonomics_service = WorkplaceErgonomicsService()

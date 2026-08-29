"""
Vision Health & Eye Care Tracking
Eye exam reminders, prescription tracking, screen time eye strain, vision exercises.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid


class VisionHealthService:
    VISION_EXERCISES = [
        {"id": "20_20_20", "name": "20-20-20 Rule", "duration_sec": 20, "description": "Every 20 min, look at something 20 feet away for 20 seconds", "frequency": "every_20_min", "difficulty": "beginner"},
        {"id": "palming", "name": "Palming", "duration_sec": 60, "description": "Rub hands together, cup over closed eyes, relax for 1 minute", "frequency": "as_needed", "difficulty": "beginner"},
        {"id": "figure_eight", "name": "Figure Eight Tracking", "duration_sec": 120, "description": "Trace a large figure eight with your eyes, 5 times each direction", "frequency": "daily", "difficulty": "beginner"},
        {"id": "near_far_focus", "name": "Near-Far Focus", "duration_sec": 120, "description": "Hold thumb 10 inches away, focus 5 sec, then focus on distant object 5 sec, repeat 10 times", "frequency": "daily", "difficulty": "beginner"},
        {"id": "blink_exercise", "name": "Conscious Blinking", "duration_sec": 60, "description": "Blink slowly 10 times, squeezing eyelids gently each time", "frequency": "every_hour", "difficulty": "beginner"},
        {"id": "eye_rolling", "name": "Eye Rolls", "duration_sec": 60, "description": "Roll eyes clockwise 5 times, then counterclockwise 5 times", "frequency": "daily", "difficulty": "beginner"},
        {"id": "cross_eye", "name": "Cross-Eye Exercise", "duration_sec": 120, "description": "Hold finger 12 inches from nose, focus on finger and slowly move toward nose until double, repeat 10 times", "frequency": "daily", "difficulty": "intermediate"},
        {"id": "accommodation", "name": "Accommodation Training", "duration_sec": 180, "description": "Focus on near object 30 sec, then far object 30 sec, repeat 3 times", "frequency": "daily", "difficulty": "intermediate"},
    ]

    BLUE_LIGHT_TIPS = [
        "Use night shift mode after 8 PM",
        "Keep screen brightness equal to ambient light",
        "Position screen slightly below eye level",
        "Increase text size to reduce squinting",
        "Take a 5-minute screen break every hour",
        "Consider blue-light blocking glasses for extended use",
    ]

    def __init__(self):
        self.prescriptions: Dict[str, List[dict]] = {}
        self.eye_exams: Dict[str, List[dict]] = {}
        self.screen_time_logs: Dict[str, List[dict]] = {}
        self.exercise_logs: Dict[str, List[dict]] = {}
        self.strain_logs: Dict[str, List[dict]] = {}

    def add_prescription(self, user_id: str, right_eye: dict, left_eye: dict, pupillary_distance: float, doctor: str, date_issued: str, expiry: str) -> dict:
        rx = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "right_eye": right_eye,
            "left_eye": left_eye,
            "pupillary_distance_mm": pupillary_distance,
            "doctor": doctor,
            "date_issued": date_issued,
            "expiry_date": expiry,
            "created_at": datetime.now().isoformat(),
        }
        self.prescriptions.setdefault(user_id, []).append(rx)
        return rx

    def log_eye_exam(self, user_id: str, exam_type: str, date: str, visual_acuity_right: str, visual_acuity_left: str, intraocular_pressure: Optional[float] = None, notes: str = "") -> dict:
        exam = {
            "id": str(uuid.uuid4()),
            "exam_type": exam_type,
            "date": date,
            "visual_acuity_right": visual_acuity_right,
            "visual_acuity_left": visual_acuity_left,
            "iop_right": intraocular_pressure,
            "notes": notes,
        }
        self.eye_exams.setdefault(user_id, []).append(exam)
        return exam

    def log_screen_time(self, user_id: str, hours: float, breaks_taken: int, strain_level: int) -> dict:
        entry = {
            "id": str(uuid.uuid4()),
            "hours": hours,
            "breaks_taken": breaks_taken,
            "strain_level": min(max(strain_level), 10),
            "recommended_breaks": max(int(hours * 3), 1),
            "break_compliance": min(breaks_taken / max(int(hours * 3), 1) * 100, 100),
            "timestamp": datetime.now().isoformat(),
        }
        self.screen_time_logs.setdefault(user_id, []).append(entry)
        return entry

    def log_strain(self, user_id: str, symptoms: List[str], severity: int, duration_hours: float) -> dict:
        entry = {
            "id": str(uuid.uuid4()),
            "symptoms": symptoms,
            "severity": min(max(severity), 10),
            "duration_hours": duration_hours,
            "timestamp": datetime.now().isoformat(),
        }
        self.strain_logs.setdefault(user_id, []).append(entry)
        return entry

    def get_exercise_plan(self, strain_level: int) -> List[dict]:
        if strain_level >= 7:
            return [e for e in self.VISION_EXERCISES if e["difficulty"] == "beginner"][:3]
        elif strain_level >= 4:
            return [e for e in self.VISION_EXERCISES if e["difficulty"] in ("beginner", "intermediate")][:5]
        return self.VISION_EXERCISES

    def log_exercise(self, user_id: str, exercise_id: str, completed: bool) -> dict:
        entry = {
            "id": str(uuid.uuid4()),
            "exercise_id": exercise_id,
            "completed": completed,
            "timestamp": datetime.now().isoformat(),
        }
        self.exercise_logs.setdefault(user_id, []).append(entry)
        return entry

    def get_vision_health_score(self, user_id: str) -> dict:
        strain = self.strain_logs.get(user_id, [])
        screen = self.screen_time_logs.get(user_id, [])
        exercises = self.exercise_logs.get(user_id, [])
        score = 100
        if screen:
            avg_strain = sum(s["strain_level"] for s in strain) / max(len(strain), 1)
            score -= avg_strain * 3
        if exercises:
            recent_exercises = [e for e in exercises if datetime.fromisoformat(e["timestamp"]) > datetime.now() - timedelta(days=7)]
            score += min(len(recent_exercises) * 2, 20)
        if screen:
            avg_breaks = sum(s["break_compliance"] for s in screen) / len(screen)
            score += (avg_breaks - 50) * 0.2
        score = max(0, min(100, score))
        return {
            "score": round(score, 1),
            "grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F",
            "total_strain_episodes": len(strain),
            "total_exercises": len(exercises),
            "blue_light_tips": self.BLUE_LIGHT_TIPS[:3],
        }

    def get_prescription_expiry_alert(self, user_id: str) -> List[dict]:
        rxs = self.prescriptions.get(user_id, [])
        alerts = []
        for rx in rxs:
            expiry = datetime.fromisoformat(rx["expiry_date"])
            days_left = (expiry - datetime.now()).days
            if days_left <= 90:
                alerts.append({"prescription_id": rx["id"], "days_until_expiry": days_left, "doctor": rx["doctor"], "urgent": days_left <= 30})
        return alerts


vision_health_service = VisionHealthService()

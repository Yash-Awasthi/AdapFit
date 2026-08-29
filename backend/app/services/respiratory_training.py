"""
Respiratory Training — Breathing exercises, COPD/asthma management, biofeedback

Features:
- Guided breathing exercises (box, 4-7-8, diaphragmatic, pursed lip)
- COPD management programs
- Asthma management programs
- Breathing rate biofeedback
- Lung capacity estimation
- Respiratory muscle training
- Breath hold time tracking
- Breathing pattern analysis
"""
import time
import math
from typing import Optional
from dataclasses import dataclass, field


BREATHING_EXERCISES = [
    {"id": "be_001", "name": "Box Breathing", "category": "stress", "difficulty": "beginner", "duration_seconds": 120, "description": "Equal inhale, hold, exhale, hold — used by Navy SEALs", "steps": ["Inhale for 4 seconds", "Hold for 4 seconds", "Exhale for 4 seconds", "Hold for 4 seconds"], "benefits": ["Reduces stress", "Improves focus", "Regulates nervous system"], "icon": "◻️"},
    {"id": "be_002", "name": "4-7-8 Breathing", "category": "sleep", "difficulty": "beginner", "duration_seconds": 90, "description": "Dr. Andrew Weil's natural tranquilizer for the nervous system", "steps": ["Inhale through nose for 4 seconds", "Hold breath for 7 seconds", "Exhale through mouth for 8 seconds"], "benefits": ["Promotes sleep", "Reduces anxiety", "Lowers heart rate"], "icon": "🌙"},
    {"id": "be_003", "name": "Diaphragmatic Breathing", "category": "copd", "difficulty": "beginner", "duration_seconds": 300, "description": "Belly breathing to strengthen diaphragm — essential for COPD", "steps": ["Place one hand on chest, one on belly", "Inhale through nose, expanding belly", "Exhale slowly through pursed lips", "Feel belly fall as you exhale"], "benefits": ["Strengthens diaphragm", "Improves lung efficiency", "Reduces work of breathing"], "icon": "🫁"},
    {"id": "be_004", "name": "Pursed Lip Breathing", "category": "copd", "difficulty": "beginner", "duration_seconds": 300, "description": "Slows breathing and improves oxygen exchange — key for COPD", "steps": ["Inhale slowly through nose for 2 counts", "Purse lips as if blowing through a straw", "Exhale slowly and gently for 4 counts", "Repeat 10-15 times"], "benefits": ["Reduces shortness of breath", "Keeps airways open longer", "Improves oxygen saturation"], "icon": "💨"},
    {"id": "be_005", "name": "Alternate Nostril Breathing", "category": "stress", "difficulty": "intermediate", "duration_seconds": 180, "description": "Yogic pranayama for balance and calm", "steps": ["Close right nostril with thumb", "Inhale through left nostril for 4 seconds", "Close left nostril, release right", "Exhale through right for 4 seconds", "Inhale right, switch, exhale left"], "benefits": ["Balances nervous system", "Improves focus", "Reduces blood pressure"], "icon": "🧘"},
    {"id": "be_006", "name": "Wim Hof Breathwork", "category": "energy", "difficulty": "advanced", "duration_seconds": 600, "description": "Powerful breathing technique for energy and immune boost", "steps": ["Take 30 deep breaths (in through nose, out through mouth)", "On last exhale, hold breath as long as possible", "Inhale deeply and hold for 15 seconds", "Repeat 3-4 rounds"], "benefits": ["Boosts energy", "Improves immune function", "Increases cold tolerance"], "icon": "⚡"},
    {"id": "be_007", "name": "Resonance Frequency Breathing", "category": "biofeedback", "difficulty": "intermediate", "duration_seconds": 300, "description": "Breathing at your personal resonance frequency for optimal HRV", "steps": ["Find your comfortable breathing rate (typically 4.5-6.5 breaths/min)", "Use a visual pacer to guide breathing", "Inhale and exhale at equal intervals", "Monitor HRV for coherence"], "benefits": ["Optimizes heart rate variability", "Maximizes autonomic balance", "Reduces stress hormones"], "icon": "💓"},
    {"id": "be_008", "name": "Asthma Relief Breathing", "category": "asthma", "difficulty": "beginner", "duration_seconds": 300, "description": "Gentle breathing to manage asthma symptoms", "steps": ["Sit upright, relax shoulders", "Breathe slowly through nose (not mouth)", "Exhale completely through pursed lips", "Practice 5-10 minutes twice daily"], "benefits": ["Reduces asthma symptoms", "Improves breathing control", "Decreases rescue inhaler use"], "icon": "🌬️"},
]


class RespiratoryTrainingService:
    """Respiratory training and breathing exercise management."""

    def __init__(self):
        self._sessions: list[dict] = []
        self._breath_holds: list[dict] = []
        self._lung_capacity_estimates: list[dict] = []
        self._breathing_rates: list[dict] = []

    def get_exercises(self, category: str = "", difficulty: str = "") -> list[dict]:
        exercises = list(BREATHING_EXERCISES)
        if category:
            exercises = [e for e in exercises if e["category"] == category]
        if difficulty:
            exercises = [e for e in exercises if e["difficulty"] == difficulty]
        return exercises

    def get_exercise(self, exercise_id: str) -> Optional[dict]:
        return next((e for e in BREATHING_EXERCISES if e["id"] == exercise_id), None)

    def start_session(self, exercise_id: str, user_id: str = "default") -> dict:
        exercise = self.get_exercise(exercise_id)
        if not exercise:
            return {"error": "Exercise not found"}
        session = {
            "session_id": f"breath_{int(time.time())}", "exercise_id": exercise_id,
            "exercise_name": exercise["name"], "started_at": time.time(),
            "user_id": user_id, "status": "active",
        }
        self._sessions.append(session)
        return {"session": session, "exercise": exercise, "instruction": f"Starting {exercise['name']}. Follow the guided breathing pattern."}

    def complete_session(self, session_id: str, breaths_completed: int = 0, avg_breathing_rate: float = 0) -> dict:
        for s in self._sessions:
            if s["session_id"] == session_id:
                s["status"] = "completed"
                s["completed_at"] = time.time()
                s["duration_seconds"] = int(s["completed_at"] - s["started_at"])
                s["breaths_completed"] = breaths_completed
                s["avg_breathing_rate"] = avg_breathing_rate
                self._breathing_rates.append({"rate": avg_breathing_rate, "timestamp": time.time()})
                return {"completed": True, "duration": s["duration_seconds"], "breaths": breaths_completed, "message": f"Great session! {breaths_completed} breath cycles completed."}
        return {"error": "Session not found"}

    def log_breath_hold(self, hold_time_seconds: float) -> dict:
        entry = {"hold_time": hold_time_seconds, "timestamp": time.time()}
        self._breath_holds.append(entry)
        avg = sum(b["hold_time"] for b in self._breath_holds) / len(self._breath_holds)
        if hold_time_seconds >= 120:
            level = "Elite"
        elif hold_time_seconds >= 90:
            level = "Advanced"
        elif hold_time_seconds >= 60:
            level = "Good"
        elif hold_time_seconds >= 30:
            level = "Average"
        else:
            level = "Below Average"
        return {"hold_time": hold_time_seconds, "level": level, "average": round(avg, 1), "total_tests": len(self._breath_holds)}

    def estimate_lung_capacity(self, height_cm: float, age: int, gender: str = "male") -> dict:
        if gender == "male":
            predicted = (0.052 * height_cm) - (0.022 * age) - 4.6
        else:
            predicted = (0.041 * height_cm) - (0.018 * age) - 3.6
        predicted = max(2.0, min(8.0, predicted))
        self._lung_capacity_estimates.append({"predicted_liters": round(predicted, 1), "timestamp": time.time()})
        return {"predicted_liters": round(predicted, 1), "normal_range": "3.5-6.0L", "percentile": "50th" if 4.0 <= predicted <= 5.5 else "above" if predicted > 5.5 else "below"}

    def get_copd_program(self) -> dict:
        return {
            "program_name": "COPD Management Program",
            "duration_weeks": 8,
            "weekly_plan": [
                {"week": 1, "focus": "Breathing Basics", "exercises": ["Diaphragmatic breathing", "Pursed lip breathing"], "goal": "Master foundational techniques"},
                {"week": 2, "focus": "Endurance Building", "exercises": ["Walking with pursed lip breathing", "Sit-to-stand"], "goal": "Build exercise tolerance"},
                {"week": 3, "focus": "Upper Body Strength", "exercises": ["Arm raises while breathing", "Resistance band exercises"], "goal": "Improve arm endurance for daily tasks"},
                {"week": 4, "focus": "Breathing Control", "exercises": ["Paced breathing during activity", "Recovery breathing"], "goal": "Control breath during exertion"},
                {"week": 5, "focus": "Stress Management", "exercises": ["4-7-8 breathing", "Progressive muscle relaxation"], "goal": "Manage anxiety and breathlessness"},
                {"week": 6, "focus": "Advanced Exercises", "exercises": ["Stair climbing with breathing", "Walking intervals"], "goal": "Increase functional capacity"},
                {"week": 7, "focus": "Self-Management", "exercises": ["Action plan practice", "Emergency breathing techniques"], "goal": "Manage exacerbations independently"},
                {"week": 8, "focus": "Maintenance", "exercises": ["Personalized routine", "Long-term plan"], "goal": "Establish lifelong habits"},
            ],
            "daily_minimum": "2 breathing sessions (morning and evening) + 20 minutes walking",
            "monitoring": "Track peak flow, SpO2, and symptom diary daily",
        }

    def get_asthma_program(self) -> dict:
        return {
            "program_name": "Asthma Management Program",
            "daily_exercises": ["Buteyko breathing: 15 minutes", "Relaxed breathing: 10 minutes", "Pursed lip breathing during activity"],
            "trigger_avoidance": ["Dust mites", "Pollen", "Cold air", "Exercise (use pre-exercise inhaler)", "Smoke"],
            "action_plan_levels": {"green": "Well controlled — continue medication", "yellow": "Worsening — increase medication, call doctor", "red": "Emergency — use rescue inhaler, call 911"},
        }

    def get_breathing_rate_data(self, days: int = 7) -> list[dict]:
        cutoff = time.time() - days * 86400
        return [b for b in self._breathing_rates if b["timestamp"] > cutoff]

    def get_session_history(self, user_id: str = "default", limit: int = 10) -> list[dict]:
        user_sessions = [s for s in self._sessions if s.get("user_id") == user_id]
        return [{"exercise": s["exercise_name"], "duration": s.get("duration_seconds", 0), "breaths": s.get("breaths_completed", 0), "date": time.strftime("%Y-%m-%d", time.localtime(s["started_at"]))} for s in user_sessions[-limit:]]


respiratory_training_service = RespiratoryTrainingService()

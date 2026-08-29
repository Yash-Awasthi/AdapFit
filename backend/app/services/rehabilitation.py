"""
Physical Therapy & Rehabilitation — Exercise prescription, progress tracking, recovery

Features:
- Injury-specific exercise programs
- PT exercise library with instructions
- Progress tracking (ROM, strength, pain levels)
- Milestone tracking
- Therapist notes and communication
- Recovery timeline estimation
- Pre/post surgery programs
- Chronic pain management exercises
"""
import time
import random
from typing import Optional
from dataclasses import dataclass, field


INJURY_PROGRAMS = {
    "knee_acl": {"name": "ACL Recovery", "duration_weeks": 12, "phases": ["Acute (0-2 weeks)", "Strengthening (2-6 weeks)", "Functional (6-10 weeks)", "Return to Sport (10-12 weeks)"], "exercises": ["Quad sets", "Straight leg raises", "Heel slides", "Wall squats", "Step-ups", "Leg press", "Hamstring curls", "Balance board"]},
    "shoulder_impingement": {"name": "Shoulder Rehabilitation", "duration_weeks": 8, "phases": ["Pain Relief (0-2 weeks)", "Mobility (2-4 weeks)", "Strengthening (4-6 weeks)", "Functional (6-8 weeks)"], "exercises": ["Pendulum swings", "Wall slides", "External rotation", "Internal rotation", "Scapular squeezes", "Shoulder shrugs", "Resistance band pulls", "Overhead press"]},
    "lower_back_pain": {"name": "Lower Back Recovery", "duration_weeks": 6, "phases": ["Acute Care (0-1 weeks)", "Mobility (1-3 weeks)", "Core Strengthening (3-5 weeks)", "Prevention (5-6 weeks)"], "exercises": ["Cat-cow", "Bird dog", "Dead bug", "Partial crunches", "Pelvic tilt", "Knee-to-chest", "Child's pose", "Bridge"]},
    "ankle_sprain": {"name": "Ankle Sprain Recovery", "duration_weeks": 6, "phases": ["Protection (0-1 weeks)", "Mobility (1-3 weeks)", "Strength (3-5 weeks)", "Proprioception (5-6 weeks)"], "exercises": ["Alphabet ankle", "Towel stretch", "Calf raises", "Balance on one foot", "Resistance band inversion", "Eversion", "Heel walks", "Toe walks"]},
    "tennis_elbow": {"name": "Tennis Elbow Recovery", "duration_weeks": 8, "phases": ["Rest (0-2 weeks)", "Stretching (2-4 weeks)", "Eccentric Loading (4-6 weeks)", "Strengthening (6-8 weeks)"], "exercises": ["Wrist extension stretch", "Towel wringing", "Eccentric wrist extension", "Grip strengthening", "Forearm massage", "Nerve gliding", "Ice massage", "Progressive loading"]},
    "post_surgery_knee": {"name": "Post-Knee Surgery", "duration_weeks": 16, "phases": ["Week 1-2: Flexion", "Week 3-6: Strengthening", "Week 7-10: Functional", "Week 11-16: Return to Activity"], "exercises": ["Ankle pumps", "Quad sets", "SLR", "Heel slides", "Standing march", "Step-ups", "Leg press", "Stationary bike"]},
}

PT_EXERCISE_LIBRARY = [
    {"id": "pt_001", "name": "Quad Set", "body_part": "knee", "difficulty": "beginner", "equipment": "none", "reps": "10", "hold": "5s", "instructions": "Sit with leg straight. Tighten thigh muscle, pressing back of knee into floor. Hold 5 seconds.", "tips": "Place small towel roll under knee for feedback"},
    {"id": "pt_002", "name": "Straight Leg Raise", "body_part": "knee", "difficulty": "beginner", "equipment": "none", "reps": "10", "hold": "5s", "instructions": "Lie on back, one knee bent. Lift straight leg to height of opposite knee. Hold 5 seconds.", "tips": "Keep core engaged. Don't lock knee."},
    {"id": "pt_003", "name": "Heel Slides", "body_part": "knee", "difficulty": "beginner", "equipment": "none", "reps": "15", "hold": "0s", "instructions": "Lie on back. Slide heel toward buttocks, bending knee. Slide back to start.", "tips": "Use a plastic bag under heel to reduce friction."},
    {"id": "pt_004", "name": "Wall Squat", "body_part": "knee", "difficulty": "intermediate", "equipment": "wall", "reps": "10", "hold": "10s", "instructions": "Lean against wall. Slide down until knees are at 45 degrees. Hold 10 seconds.", "tips": "Don't go past 90 degrees initially."},
    {"id": "pt_005", "name": "Bird Dog", "body_part": "back", "difficulty": "beginner", "equipment": "none", "reps": "10", "hold": "5s", "instructions": "On hands and knees. Extend opposite arm and leg simultaneously. Hold 5 seconds.", "tips": "Keep hips level. Don't arch back."},
    {"id": "pt_006", "name": "Dead Bug", "body_part": "core", "difficulty": "beginner", "equipment": "none", "reps": "10", "hold": "3s", "instructions": "Lie on back, arms up, knees bent 90°. Lower opposite arm and leg simultaneously.", "tips": "Press lower back into floor throughout."},
    {"id": "pt_007", "name": "Pendulum Swing", "body_part": "shoulder", "difficulty": "beginner", "equipment": "none", "reps": "30s", "hold": "0s", "instructions": "Lean forward, let arm hang. Gently swing arm in circles and front-to-back.", "tips": "Use body momentum, not arm muscles."},
    {"id": "pt_008", "name": "Scapular Squeeze", "body_part": "shoulder", "difficulty": "beginner", "equipment": "none", "reps": "15", "hold": "5s", "instructions": "Sit or stand. Squeeze shoulder blades together. Hold 5 seconds.", "tips": "Think 'proud chest' posture."},
    {"id": "pt_009", "name": "Wrist Extension", "body_part": "elbow", "difficulty": "beginner", "equipment": "none", "reps": "15", "hold": "3s", "instructions": "Forearm on table, hand hanging off edge. Extend wrist up. Hold 3 seconds.", "tips": "Start with no weight. Add light weight when pain-free."},
    {"id": "pt_010", "name": "Alphabet Ankle", "body_part": "ankle", "difficulty": "beginner", "equipment": "none", "reps": "1", "hold": "0s", "instructions": "Sit with leg extended. Trace entire alphabet with big toe.", "tips": "Move through full range of motion."},
]


class RehabilitationService:
    """Physical therapy and rehabilitation management."""

    def __init__(self):
        self._programs: dict[str, dict] = {}
        self._exercise_log: list[dict] = []
        self._progress: list[dict] = []
        self._milestones: list[dict] = []
        self._pain_log: list[dict] = []

    def get_injury_programs(self) -> list[dict]:
        return [{"id": k, **v, "total_exercises": len(v["exercises"])} for k, v in INJURY_PROGRAMS.items()]

    def get_program(self, injury_type: str) -> Optional[dict]:
        return INJURY_PROGRAMS.get(injury_type)

    def get_exercise_library(self, body_part: str = "", difficulty: str = "") -> list[dict]:
        exercises = list(PT_EXERCISE_LIBRARY)
        if body_part:
            exercises = [e for e in exercises if e["body_part"] == body_part]
        if difficulty:
            exercises = [e for e in exercises if e["difficulty"] == difficulty]
        return exercises

    def start_program(self, injury_type: str, user_id: str = "default") -> dict:
        program = INJURY_PROGRAMS.get(injury_type)
        if not program:
            return {"error": "Program not found"}
        prog_id = f"prog_{int(time.time())}"
        entry = {"program_id": prog_id, "injury_type": injury_type, "name": program["name"], "duration_weeks": program["duration_weeks"], "started_at": time.time(), "current_phase": 0, "user_id": user_id, "exercises_completed": 0, "total_exercises": len(program["exercises"])}
        self._programs[prog_id] = entry
        return {"program": entry, "first_exercises": program["exercises"][:3]}

    def log_exercise(self, program_id: str, exercise_name: str, reps_done: int = 0, pain_level: int = 0, notes: str = "") -> dict:
        prog = self._programs.get(program_id)
        if not prog:
            return {"error": "Program not found"}
        log = {"exercise": exercise_name, "reps": reps_done, "pain": pain_level, "notes": notes, "timestamp": time.time()}
        self._exercise_log.append(log)
        prog["exercises_completed"] = prog.get("exercises_completed", 0) + 1
        self._pain_log.append({"level": pain_level, "timestamp": time.time()})
        return {"logged": True, "pain_level": pain_level, "message": f"Exercise logged. Pain: {pain_level}/10" + (". Consider reducing intensity if pain increases." if pain_level >= 7 else "")}

    def log_progress(self, program_id: str, pain_level: int = 0, rom_degrees: int = 0, strength_score: int = 0, notes: str = "") -> dict:
        entry = {"program_id": program_id, "pain": pain_level, "rom": rom_points, "strength": strength_score, "notes": notes, "timestamp": time.time()}
        self._progress.append(entry)
        return {"logged": True}

    def get_progress_chart(self, program_id: str) -> list[dict]:
        return [{"pain": p["pain"], "rom": p.get("rom", 0), "strength": p.get("strength", 0), "date": time.strftime("%Y-%m-%d", time.localtime(p["timestamp"]))} for p in self._progress if p["program_id"] == program_id]

    def get_milestones(self, injury_type: str) -> list[dict]:
        program = INJURY_PROGRAMS.get(injury_type, {})
        return [{"phase": i + 1, "name": phase, "target_week": i * (program.get("duration_weeks", 6) // max(1, len(program.get("phases", []))))} for i, phase in enumerate(program.get("phases", []))]

    def get_pain_trend(self, days: int = 14) -> list[dict]:
        cutoff = time.time() - days * 86400
        return [{"level": p["level"], "date": time.strftime("%Y-%m-%d", time.localtime(p["timestamp"]))} for p in self._pain_log if p["timestamp"] > cutoff]

    def get_recovery_estimate(self, injury_type: str) -> dict:
        program = INJURY_PROGRAMS.get(injury_type, {})
        avg_pain = sum(p["level"] for p in self._pain_log[-10:]) / max(1, len(self._pain_log[-10:]))
        if avg_pain <= 3:
            progress = "ahead"
            estimate = "on track"
        elif avg_pain <= 5:
            progress = "on_track"
            estimate = "on track"
        else:
            progress = "behind"
            estimate = "may take longer"
        return {"injury": program.get("name", "Unknown"), "duration_weeks": program.get("duration_weeks", 0), "current_progress": progress, "estimate": estimate, "avg_pain": round(avg_pain, 1), "recommendation": "Follow your PT's guidance and don't rush recovery."}


rehabilitation_service = RehabilitationService()

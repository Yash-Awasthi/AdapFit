"""
Digital Therapeutics (DTx) — FDA-grade intervention tracking
Prescription digital therapeutics, evidence-based interventions, clinical outcomes.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid


class DigitalTherapeuticsService:
    DTX_PROGRAMS = {
        "cognitive_behavioral": {
            "name": "Cognitive Behavioral Therapy (CBT)",
            "condition": "insomnia",
            "fda_cleared": True,
            "evidence_level": "strong",
            "duration_weeks": 6,
            "sessions_per_week": 3,
            "module_count": 24,
            "modules": ["sleep_hygiene", "cognitive_restructuring", "stimulus_control", "sleep_restriction", "relaxation_training", "sleep_maintenance"],
        },
        "diabetes_cbt": {
            "name": "Diabetes CBT Program",
            "condition": "type2_diabetes",
            "fda_cleared": True,
            "evidence_level": "strong",
            "duration_weeks": 12,
            "sessions_per_week": 2,
            "module_count": 24,
            "modules": ["goal_setting", "blood_sugar_monitoring", "nutrition_planning", "medication_adherence", "coping_strategies", "health_literacy"],
        },
        "substance_abuse": {
            "name": "ReSET Substance Abuse Program",
            "condition": "substance_use",
            "fda_cleared": True,
            "evidence_level": "strong",
            "duration_weeks": 12,
            "sessions_per_week": 5,
            "module_count": 52,
            "modules": ["contingency_management", "community_reinforcement", "skills_training", "relapse_prevention", "social_support"],
        },
        "pain_management": {
            "name": "Chronic Pain Digital Program",
            "condition": "chronic_pain",
            "fda_cleared": True,
            "evidence_level": "moderate",
            "duration_weeks": 8,
            "sessions_per_week": 3,
            "module_count": 24,
            "modules": ["pain_education", "cognitive_restructuring", "behavioral_activation", "mindfulness", "activity_pacing", "sleep_hygiene"],
        },
        "depression_program": {
            "name": "Digital Depression Intervention",
            "condition": "depression",
            "fda_cleared": True,
            "evidence_level": "strong",
            "duration_weeks": 9,
            "sessions_per_week": 3,
            "module_count": 27,
            "modules": ["psychoeducation", "behavioral_activation", "cognitive_restructuring", "problem_solving", "social_skills", "relapse_prevention"],
        },
        "anxiety_program": {
            "name": "Digital Anxiety Management",
            "condition": "anxiety",
            "fda_cleared": True,
            "evidence_level": "moderate",
            "duration_weeks": 8,
            "sessions_per_week": 3,
            "module_count": 24,
            "modules": ["psychoeducation", "relaxation_techniques", "cognitive_restructuring", "exposure_therapy", "mindfulness", "relapse_prevention"],
        },
    }

    OUTCOME_METRICS = {
        "phq9": {"name": "PHQ-9 Depression Score", "min": 0, "max": 27, "clinical_threshold": 10, "response_threshold": 50, "remission_threshold": 5},
        "gad7": {"name": "GAD-7 Anxiety Score", "min": 0, "max": 21, "clinical_threshold": 10, "response_threshold": 50, "remission_threshold": 4},
        "isi": {"name": "Insomnia Severity Index", "min": 0, "max": 28, "clinical_threshold": 10, "response_threshold": 50, "remission_threshold": 7},
        "pain_nrs": {"name": "Pain NRS Score", "min": 0, "max": 10, "clinical_threshold": 4, "response_threshold": 30, "remission_threshold": 3},
        "hba1c": {"name": "HbA1c Level", "min": 4.0, "max": 15.0, "clinical_threshold": 7.0, "response_threshold": 0.5, "remission_threshold": 6.5},
        "adas_cog": {"name": "ADAS-Cog Cognitive Score", "min": 0, "max": 70, "clinical_threshold": 26, "response_threshold": 4, "remission_threshold": 20},
    }

    def __init__(self):
        self.enrollments: Dict[str, dict] = {}
        self.sessions: Dict[str, List[dict]] = {}
        self.outcomes: Dict[str, List[dict]] = {}
        self.adherence_logs: Dict[str, List[dict]] = {}

    def enroll_patient(self, user_id: str, program_key: str, prescriber: str = "system", notes: str = "") -> dict:
        program = self.DTX_PROGRAMS.get(program_key)
        if not program:
            return {"error": f"Unknown program: {program_key}"}
        
        enrollment_id = str(uuid.uuid4())
        start_date = datetime.now()
        end_date = start_date + timedelta(weeks=program["duration_weeks"])
        
        enrollment = {
            "id": enrollment_id,
            "user_id": user_id,
            "program": program_key,
            "program_name": program["name"],
            "condition": program["condition"],
            "prescriber": prescriber,
            "notes": notes,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_sessions": program["sessions_per_week"] * program["duration_weeks"],
            "completed_sessions": 0,
            "current_module": 0,
            "status": "active",
            "enrolled_at": datetime.now().isoformat(),
        }
        self.enrollments[enrollment_id] = enrollment
        self.sessions[enrollment_id] = []
        self.outcomes[enrollment_id] = []
        return enrollment

    def log_session(self, enrollment_id: str, module_name: str, duration_min: int, completion: float, mood_before: int, mood_after: int, notes: str = "") -> dict:
        enrollment = self.enrollments.get(enrollment_id)
        if not enrollment:
            return {"error": "Enrollment not found"}
        
        session = {
            "id": str(uuid.uuid4()),
            "enrollment_id": enrollment_id,
            "module": module_name,
            "duration_min": duration_min,
            "completion": min(max(completion, 0), 100),
            "mood_before": mood_before,
            "mood_after": mood_after,
            "mood_change": mood_after - mood_before,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
        }
        self.sessions.setdefault(enrollment_id, []).append(session)
        enrollment["completed_sessions"] += 1
        
        adherence_rate = enrollment["completed_sessions"] / max(enrollment["total_sessions"], 1) * 100
        self.adherence_logs.setdefault(enrollment_id, []).append({
            "adherence_rate": round(adherence_rate, 1),
            "timestamp": datetime.now().isoformat(),
        })
        
        return {**session, "adherence_rate": round(adherence_rate, 1)}

    def record_outcome(self, enrollment_id: str, metric_key: str, score: float, notes: str = "") -> dict:
        metric = self.OUTCOME_METRICS.get(metric_key)
        if not metric:
            return {"error": f"Unknown metric: {metric_key}"}
        
        enrollment = self.enrollments.get(enrollment_id)
        if not enrollment:
            return {"error": "Enrollment not found"}
        
        prev_outcomes = [o for o in self.outcomes.get(enrollment_id, []) if o["metric"] == metric_key]
        prev_score = prev_outcomes[-1]["score"] if prev_outcomes else None
        
        response = None
        if prev_score is not None:
            change = prev_score - score
            if metric_key in ("phq9", "gad7", "isi", "pain_nrs"):
                response = "improved" if change > 0 else "worsened" if change < 0 else "stable"
            else:
                response = "improved" if change < 0 else "worsened" if change > 0 else "stable"
        
        outcome = {
            "id": str(uuid.uuid4()),
            "enrollment_id": enrollment_id,
            "metric": metric_key,
            "metric_name": metric["name"],
            "score": score,
            "baseline_score": prev_outcomes[0]["score"] if prev_outcomes else score,
            "change_from_baseline": (prev_outcomes[0]["score"] - score) if prev_outcomes else 0,
            "clinical_threshold": metric["clinical_threshold"],
            "in_clinical_range": score <= metric["clinical_threshold"],
            "response": response,
            "notes": notes,
            "recorded_at": datetime.now().isoformat(),
        }
        self.outcomes.setdefault(enrollment_id, []).append(outcome)
        return outcome

    def get_enrollment_progress(self, enrollment_id: str) -> dict:
        enrollment = self.enrollments.get(enrollment_id)
        if not enrollment:
            return {"error": "Enrollment not found"}
        
        program = self.DTX_PROGRAMS.get(enrollment["program"], {})
        sessions = self.sessions.get(enrollment_id, [])
        outcomes = self.outcomes.get(enrollment_id, [])
        
        total_duration = sum(s["duration_min"] for s in sessions)
        avg_completion = sum(s["completion"] for s in sessions) / max(len(sessions), 1)
        avg_mood_change = sum(s["mood_change"] for s in sessions) / max(len(sessions), 0)
        
        latest_outcomes = {}
        for o in outcomes:
            latest_outcomes[o["metric"]] = o
        
        return {
            "enrollment": enrollment,
            "program": program,
            "progress": {
                "sessions_completed": enrollment["completed_sessions"],
                "total_sessions": enrollment["total_sessions"],
                "completion_percent": round(enrollment["completed_sessions"] / max(enrollment["total_sessions"], 1) * 100, 1),
                "total_duration_min": total_duration,
                "avg_session_completion": round(avg_completion, 1),
                "avg_mood_change": round(avg_mood_change, 1),
            },
            "latest_outcomes": list(latest_outcomes.values()),
        }

    def get_programs(self) -> List[dict]:
        return [{"key": k, **v} for k, v in self.DTX_PROGRAMS.items()]

    def get_user_enrollments(self, user_id: str) -> List[dict]:
        return [e for e in self.enrollments.values() if e["user_id"] == user_id]


dtx_service = DigitalTherapeuticsService()

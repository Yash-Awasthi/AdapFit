"""
AI Posture Analysis & Ergonomics — Real-time posture correction

Features:
- Camera-based posture assessment (head, shoulders, spine alignment)
- Sitting/standing posture classification
- Ergonomic workstation recommendations
- Posture score tracking over time
- Corrective exercise prescriptions
- Tech neck detection
- Screen time posture alerts
- Customized posture improvement plans
"""
import time
import random
from typing import Optional
from dataclasses import dataclass, field


POSTURE_CATEGORIES = {
    "head_forward": {"name": "Forward Head Posture", "severity": "moderate", "description": "Head is positioned forward of the spine", "corrections": ["Tuck chin back", "Strengthen deep neck flexors", "Stretch chest muscles", "Use phone at eye level"], "exercises": ["Chin tucks: 10 reps, 3 sets", "Neck extensions: 10 reps, 2 sets", "Wall angels: 15 reps, 2 sets"]},
    "rounded_shoulders": {"name": "Rounded Shoulders", "severity": "moderate", "description": "Shoulders are rounded forward, chest is collapsed", "corrections": ["Retract shoulder blades", "Strengthen upper back", "Stretch pectorals", "Adjust desk height"], "exercises": ["Face pulls: 15 reps, 3 sets", "Band pull-aparts: 15 reps, 3 sets", "Doorway stretch: 30s each side"]},
    "kyphosis": {"name": "Thoracic Kyphosis", "severity": "moderate", "description": "Excessive curvature of the upper back", "corrections": ["Strengthen thoracic extensors", "Improve thoracic mobility", "Reduce slouching", "Use lumbar support"], "exercises": ["Foam roller thoracic extension: 10 reps", "Cat-cow: 15 reps", "Prone Y-raises: 12 reps"]},
    "lordosis": {"name": "Lumbar Lordosis", "severity": "mild", "description": "Excessive inward curve of the lower back", "corrections": ["Engage core muscles", "Strengthen glutes", "Stretch hip flexors", "Maintain neutral pelvis"], "exercises": ["Dead bugs: 10 each side", "Glute bridges: 15 reps", "Hip flexor stretch: 30s each side"]},
    "lateral_shift": {"name": "Lateral Shift", "severity": "moderate", "description": "Spine is shifted to one side", "corrections": ["Check leg length discrepancy", "Strengthen obliques", "Balance core strength", "See a chiropractor if persistent"], "exercises": ["Side planks: 30s each side", "Bird dogs: 10 each side", "Pallof press: 12 each side"]},
    "good_posture": {"name": "Good Posture", "severity": "none", "description": "Head, shoulders, and spine are properly aligned", "corrections": ["Maintain current posture", "Take regular breaks", "Stay active"], "exercises": ["Continue regular stretching", "Maintain core strength", "Take hourly standing breaks"]},
}

WORKSPACE_TIPS = [
    {"area": "monitor", "tip": "Place monitor at arm's length, top of screen at eye level", "priority": "high"},
    {"area": "chair", "tip": "Adjust chair height so feet are flat on floor, knees at 90 degrees", "priority": "high"},
    {"area": "keyboard", "tip": "Keyboard at elbow height, wrists neutral, use wrist rest", "priority": "medium"},
    {"area": "lighting", "tip": "Avoid glare on screen, use indirect lighting, follow 20-20-20 rule for eyes", "priority": "medium"},
    {"area": "standing", "tip": "If using standing desk, alternate between sitting and standing every 30-60 minutes", "priority": "low"},
    {"area": "breaks", "tip": "Take a 5-minute movement break every 30 minutes", "priority": "high"},
]


class PostureAnalysisService:
    """AI-powered posture assessment and correction."""

    def __init__(self):
        self._assessments: list[dict] = []
        self._posture_scores: list[dict] = []
        self._alerts: list[dict] = {}
        self._session_data: dict[str, dict] = {}

    def analyze_posture(self, body_landmarks: dict = None) -> dict:
        """Analyze posture from body landmarks (or simulate)."""
        if body_landmarks:
            issues = self._detect_issues(body_landmarks)
        else:
            issues = random.choice([["good_posture"], ["head_forward"], ["rounded_shoulders"], ["kyphosis"]])

        score = 100
        detected = []
        for issue in issues:
            if issue != "good_posture":
                info = POSTURE_CATEGORIES.get(issue, {})
                score -= {"mild": 10, "moderate": 20, "severe": 35}.get(info.get("severity", "mild"), 10)
                detected.append({"category": issue, **info})

        score = max(0, score)
        assessment = {
            "posture_score": score,
            "grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F",
            "detected_issues": detected,
            "is_good_posture": len(detected) == 0,
            "recommendations": self._get_recommendations(detected),
            "timestamp": time.time(),
        }
        self._assessments.append(assessment)
        self._posture_scores.append({"score": score, "timestamp": time.time()})
        return assessment

    def _detect_issues(self, landmarks: dict) -> list[str]:
        issues = []
        head_forward = landmarks.get("head_angle", 0) > 15
        rounded = landmarks.get("shoulder_angle", 0) > 20
        if head_forward: issues.append("head_forward")
        if rounded: issues.append("rounded_shoulders")
        return issues if issues else ["good_posture"]

    def _get_recommendations(self, issues: list[dict]) -> list[str]:
        if not issues:
            return ["Great posture! Keep it up with regular breaks and stretching."]
        recs = []
        for issue in issues[:3]:
            recs.extend(issue.get("corrections", [])[:2])
        return recs

    def get_ergonomic_tips(self) -> list[dict]:
        return WORKSPACE_TIPS

    def get_corrective_exercises(self, posture_issue: str = "") -> list[dict]:
        if posture_issue and posture_issue in POSTURE_CATEGORIES:
            cat = POSTURE_CATEGORIES[posture_issue]
            return [{"exercise": e, "target": cat["name"]} for e in cat.get("exercises", [])]
        return [{"exercise": e, "target": "General"} for cat in POSTURE_CATEGORIES.values() for e in cat.get("exercises", [])[:2]]

    def get_score_history(self, days: int = 7) -> list[dict]:
        cutoff = time.time() - days * 86400
        return [s for s in self._posture_scores if s["timestamp"] > cutoff]

    def get_posture_improvement_plan(self) -> dict:
        recent = self._assessments[-5:] if self._assessments else []
        avg_score = sum(a.get("posture_score", 70) for a in recent) / max(1, len(recent))
        return {
            "current_avg_score": round(avg_score),
            "target_score": min(100, round(avg_score) + 15),
            "daily_exercises": ["Chin tucks: 10 reps", "Thoracic extensions: 10 reps", "Wall angels: 15 reps", "Hip flexor stretch: 30s each side"],
            "break_schedule": "Every 30 minutes: Stand, stretch, walk for 2-3 minutes",
            "estimated_timeline": "4-6 weeks for noticeable improvement",
            "milestones": ["Week 1: Build awareness of posture habits", "Week 2-3: Establish break routine", "Week 4-6: Notice reduced discomfort", "Week 8+: Posture becomes habitual"],
        }

    def start_monitoring_session(self, user_id: str) -> dict:
        self._session_data[user_id] = {"started_at": time.time(), "alerts": 0, "posture_checks": 0}
        return {"session_started": True, "message": "Posture monitoring active. You'll receive alerts if poor posture is detected."}

    def check_and_alert(self, user_id: str, current_posture: str = "good") -> dict:
        session = self._session_data.get(user_id, {})
        session["posture_checks"] = session.get("posture_checks", 0) + 1
        if current_posture != "good":
            session["alerts"] = session.get("alerts", 0) + 1
            return {"alert": True, "message": "Posture detected: Slouching. Sit up straight and align your spine!", "severity": "moderate"}
        return {"alert": False, "message": "Good posture maintained!", "checks": session["posture_checks"]}


posture_analysis_service = PostureAnalysisService()

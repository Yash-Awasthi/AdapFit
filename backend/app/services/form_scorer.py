"""Form Scorer — real-time exercise form analysis and scoring.

Uses MediaPipe landmarks to calculate joint angles and score exercise form.
Provides actionable feedback during and after each set.

References:
- FormAI (HuggingFace): real-time form analysis pipeline
- GC_Fit: angle-based rep detection with form feedback
- AI Fitness Trainer (LearnOpenCV): squat analysis with landmark angles
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from app.services.pose_estimation import (
    calculate_angle, Landmark, FormGrade, EXERCISE_ANGLES,
    JointAngle, FormAssessment, score_form
)


@dataclass
class FormFeedback:
    """Real-time form feedback for a single rep."""
    rep_number: int
    exercise_id: str
    grade: FormGrade
    joint_angles: dict[str, float]
    deviations: list[str]
    corrections: list[str]
    tempo_compliance: bool = True
    depth_compliance: bool = True


@dataclass
class SetFormReport:
    """Aggregated form report for a completed set."""
    exercise_id: str
    set_number: int
    total_reps: int
    avg_grade: FormGrade
    grade_distribution: dict[str, int] = field(default_factory=dict)
    best_rep: int = 0
    worst_rep: int = 0
    common_issues: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    tempo_consistency: float = 0.0
    depth_consistency: float = 0.0


# Exercise-specific form rules
FORM_RULES = {
    "bench-press": {
        "elbow_target": (80, 100),
        "wrist_target": (75, 105),  # wrist should be roughly aligned with forearm
        "bar_path": "vertical",
        "common_faults": [
            {"condition": "elbow_flare", "threshold": 110, "message": "Elbows flaring — tuck to ~45°"},
            {"condition": "uneven_bar", "threshold": 5, "message": "Bar path uneven — keep symmetric"},
            {"condition": "insufficient_depth", "threshold": 95, "message": "Bar not reaching chest"},
        ],
    },
    "barbell-back-squat": {
        "knee_target": (70, 100),
        "hip_target": (65, 100),
        "back_angle_target": (155, 180),
        "common_faults": [
            {"condition": "knee_cave", "threshold": 5, "message": "Knees caving in — push knees out"},
            {"condition": "insufficient_depth", "threshold": 100, "message": "Squat deeper — thighs parallel"},
            {"condition": "forward_lean", "threshold": 145, "message": "Excessive forward lean — chest up"},
        ],
    },
    "deadlift": {
        "hip_target": (55, 80),
        "knee_target": (80, 120),
        "back_angle_target": (155, 180),
        "common_faults": [
            {"condition": "rounded_back", "threshold": 150, "message": "Lower back rounding — brace core"},
            {"condition": "stiff_leg", "threshold": 130, "message": "Legs too straight — bend knees more"},
        ],
    },
    "barbell-row": {
        "elbow_target": (70, 100),
        "back_angle_target": (140, 170),
        "common_faults": [
            {"condition": "excessive_momentum", "threshold": 20, "message": "Too much body english — stay strict"},
            {"condition": "insufficient_pull", "threshold": 85, "message": "Pull higher — bar to lower chest"},
        ],
    },
    "pull-up": {
        "elbow_target": (60, 90),
        "common_faults": [
            {"condition": "half_rep", "threshold": 100, "message": "Full range of motion — chin over bar"},
            {"condition": "kipping", "threshold": 30, "message": "Reduce kipping — focus on strict form"},
        ],
    },
    "overhead-press": {
        "elbow_target": (170, 180),
        "shoulder_target": (160, 180),
        "common_faults": [
            {"condition": "incomplete_lockout", "threshold": 170, "message": "Lock out fully overhead"},
            {"condition": "excessive_lean", "threshold": 10, "message": "Reduce back lean — brace core"},
        ],
    },
    "bicep-curl": {
        "elbow_target": (45, 55),
        "common_faults": [
            {"condition": "swinging", "threshold": 15, "message": "Reduce body swing — keep elbows pinned"},
            {"condition": "incomplete_rom", "threshold": 90, "message": "Full extension at bottom"},
        ],
    },
    "push-up": {
        "elbow_target": (80, 100),
        "hip_angle_target": (170, 180),
        "common_faults": [
            {"condition": "sagging_hips", "threshold": 160, "message": "Hips sagging — engage core"},
            {"condition": "piking", "threshold": 160, "message": "Butt too high — straight body line"},
            {"condition": "incomplete_depth", "threshold": 90, "message": "Lower chest closer to floor"},
        ],
    },
}


class FormScorer:
    """Scores exercise form from landmark data with real-time feedback."""

    def __init__(self):
        self.rep_form_history: list[FormFeedback] = []

    def score_rep(
        self,
        exercise_id: str,
        rep_number: int,
        landmarks: dict[str, Landmark],
        tempo_ms: Optional[float] = None,
    ) -> FormFeedback:
        """Score a single rep and return feedback."""
        deviations = []
        corrections = []
        joint_angles = {}

        # Calculate relevant joint angles
        if exercise_id in ("bench-press", "barbell-row", "push-up"):
            elbow_angle = calculate_angle(
                landmarks["right_shoulder"], landmarks["right_elbow"], landmarks["right_wrist"]
            )
            joint_angles["elbow"] = elbow_angle

        if exercise_id in ("barbell-back-squat", "lunge"):
            knee_angle = calculate_angle(
                landmarks["right_hip"], landmarks["right_knee"], landmarks["right_ankle"]
            )
            joint_angles["knee"] = knee_angle

        if exercise_id == "deadlift":
            hip_angle = calculate_angle(
                landmarks["right_shoulder"], landmarks["right_hip"], landmarks["right_knee"]
            )
            joint_angles["hip"] = hip_angle

        # Apply form rules
        rules = FORM_RULES.get(exercise_id, {})
        for fault in rules.get("common_faults", []):
            condition = fault["condition"]
            threshold = fault["threshold"]

            if condition == "elbow_flare" and "elbow" in joint_angles:
                if joint_angles["elbow"] > threshold:
                    deviations.append("elbow_flare")
                    corrections.append(fault["message"])

            elif condition == "insufficient_depth" and "knee" in joint_angles:
                if joint_angles["knee"] > threshold:
                    deviations.append("insufficient_depth")
                    corrections.append(fault["message"])

            elif condition == "rounded_back" and "hip" in joint_angles:
                if joint_angles["hip"] < threshold:
                    deviations.append("rounded_back")
                    corrections.append(fault["message"])

            elif condition == "knee_cave":
                if "knee" in joint_angles:
                    deviations.append("knee_cave")
                    corrections.append(fault["message"])

        # Tempo compliance
        tempo_ok = True
        if tempo_ms is not None:
            if tempo_ms < 500:  # Too fast
                tempo_ok = False
                deviations.append("too_fast")
                corrections.append("Slow down — control the eccentric phase")

        # Depth compliance
        depth_ok = True
        if exercise_id == "barbell-back-squat" and "knee" in joint_angles:
            if joint_angles["knee"] > 100:
                depth_ok = False

        # Determine grade
        n_deviations = len(deviations)
        if n_deviations == 0:
            grade = FormGrade.A
        elif n_deviations == 1 and not any(d in deviations for d in ("rounded_back", "knee_cave")):
            grade = FormGrade.B
        elif n_deviations <= 2:
            grade = FormGrade.C
        elif n_deviations <= 3:
            grade = FormGrade.D
        else:
            grade = FormGrade.F

        feedback = FormFeedback(
            rep_number=rep_number,
            exercise_id=exercise_id,
            grade=grade,
            joint_angles=joint_angles,
            deviations=deviations,
            corrections=corrections,
            tempo_compliance=tempo_ok,
            depth_compliance=depth_ok,
        )

        self.rep_form_history.append(feedback)
        return feedback

    def get_set_report(self, exercise_id: str, set_number: int, total_reps: int) -> SetFormReport:
        """Generate a report for a completed set."""
        set_reps = [f for f in self.rep_form_history if f.exercise_id == exercise_id]
        set_reps = set_reps[-total_reps:]

        if not set_reps:
            return SetFormReport(
                exercise_id=exercise_id, set_number=set_number,
                total_reps=0, avg_grade=FormGrade.A,
            )

        grade_map = {"A": 0, "B": 1, "C": 2, "D": 3, "F": 4}
        reverse_map = {v: k for k, v in grade_map.items()}

        grades_numeric = [grade_map[f.grade.value] for f in set_reps]
        avg_numeric = sum(grades_numeric) / len(grades_numeric)
        avg_grade = FormGrade(reverse_map[min(4, round(avg_numeric))])

        dist = {}
        for f in set_reps:
            dist[f.grade.value] = dist.get(f.grade.value, 0) + 1

        best_idx = grades_numeric.index(min(grades_numeric))
        worst_idx = grades_numeric.index(max(grades_numeric))

        all_issues = []
        for f in set_reps:
            all_issues.extend(f.corrections)
        issue_freq = {}
        for issue in all_issues:
            issue_freq[issue] = issue_freq.get(issue, 0) + 1
        common = sorted(issue_freq.items(), key=lambda x: x[1], reverse=True)[:3]

        tempo_count = sum(1 for f in set_reps if f.tempo_compliance)
        depth_count = sum(1 for f in set_reps if f.depth_compliance)

        return SetFormReport(
            exercise_id=exercise_id,
            set_number=set_number,
            total_reps=total_reps,
            avg_grade=avg_grade,
            grade_distribution=dist,
            best_rep=set_reps[best_idx].rep_number,
            worst_rep=set_reps[worst_idx].rep_number,
            common_issues=[issue for issue, _ in common],
            tempo_consistency=round(tempo_count / len(set_reps) * 100, 1),
            depth_consistency=round(depth_count / len(set_reps) * 100, 1),
        )

    def get_workout_form_summary(self) -> dict:
        """Get overall form summary for the workout."""
        if not self.rep_form_history:
            return {"total_reps": 0, "avg_grade": "A", "exercises": []}

        grade_map = {"A": 0, "B": 1, "C": 2, "D": 3, "F": 4}
        all_grades = [grade_map[f.grade.value] for f in self.rep_form_history]
        avg = sum(all_grades) / len(all_grades)
        reverse_map = {v: k for k, v in grade_map.items()}

        by_exercise = {}
        for f in self.rep_form_history:
            if f.exercise_id not in by_exercise:
                by_exercise[f.exercise_id] = []
            by_exercise[f.exercise_id].append(f)

        exercises = []
        for ex_id, reps in by_exercise.items():
            ex_grades = [grade_map[r.grade.value] for r in reps]
            exercises.append({
                "exercise_id": ex_id,
                "total_reps": len(reps),
                "avg_grade": reverse_map[min(4, round(sum(ex_grades) / len(ex_grades)))],
                "form_score_pct": round((1 - sum(ex_grades) / len(ex_grades) / 4) * 100, 1),
            })

        return {
            "total_reps": len(self.rep_form_history),
            "avg_grade": reverse_map[min(4, round(avg))],
            "form_score_pct": round((1 - avg / 4) * 100, 1),
            "exercises": exercises,
            "best_exercise": max(exercises, key=lambda e: e["form_score_pct"])["exercise_id"] if exercises else None,
        }


# Singleton
form_scorer = FormScorer()

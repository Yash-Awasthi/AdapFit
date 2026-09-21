"""AI Workout Coach Service - Form correction, personalized plans, video demos.

Based on 2025 AI fitness app research:
- AI-generated personalized workout plans
- Real-time form correction via camera
- Exercise video demonstrations
- Adaptive difficulty based on progress
- Muscle group targeting
- Recovery-aware programming
"""

import time
from typing import Dict, List, Any


class AIWorkoutCoachService:
    """AI-powered workout coaching with form correction."""

    def __init__(self):
        self.profiles: Dict[str, Dict] = {}
        self.workout_logs: Dict[str, List] = {}
        self._init_exercise_videos()

    def _init_exercise_videos(self):
        self.exercise_demos = {
            "squat": {
                "name": "Barbell Squat",
                "muscle_groups": ["quadriceps", "glutes", "hamstrings", "core"],
                "difficulty": "intermediate",
                "equipment": "barbell",
                "video_url": "/assets/exercises/squat.mp4",
                "key_cues": ["Chest up", "Knees track toes", "Depth below parallel", "Core braced"],
                "common_mistakes": ["Knees caving in", "Heels lifting", "Rounding back", "Forward lean"],
                "form_checkpoints": ["hip_hinge", "knee_alignment", "depth", "back_position"],
            },
            "deadlift": {
                "name": "Conventional Deadlift",
                "muscle_groups": ["hamstrings", "glutes", "back", "core"],
                "difficulty": "intermediate",
                "equipment": "barbell",
                "video_url": "/assets/exercises/deadlift.mp4",
                "key_cues": ["Neutral spine", "Drive through heels", "Bar close to body", "Lock hips at top"],
                "common_mistakes": ["Rounding lower back", "Bar drifting forward", "Hyperextending at top"],
                "form_checkpoints": ["spine_neutral", "bar_path", "hip_drive"],
            },
            "bench_press": {
                "name": "Bench Press",
                "muscle_groups": ["chest", "shoulders", "triceps"],
                "difficulty": "beginner",
                "equipment": "barbell",
                "video_url": "/assets/exercises/bench.mp4",
                "key_cues": ["Retract shoulder blades", " arch back slightly", "Touch mid-chest", "Drive up and slightly back"],
                "common_mistakes": ["Flared elbows", "Bouncing off chest", "Uneven press"],
                "form_checkpoints": ["elbow_angle", "bar_path", "shoulder_position"],
            },
            "pull_up": {
                "name": "Pull-Up",
                "muscle_groups": ["lats", "biceps", "back"],
                "difficulty": "intermediate",
                "equipment": "pull_up_bar",
                "video_url": "/assets/exercises/pullup.mp4",
                "key_cues": ["Dead hang start", "Pull to chin over bar", "Control the descent", "Full range of motion"],
                "common_mistakes": ["Half reps", "Kipping", "Not full extension"],
                "form_checkpoints": ["range_of_motion", "control", "grip"],
            },
            "plank": {
                "name": "Plank Hold",
                "muscle_groups": ["core", "shoulders"],
                "difficulty": "beginner",
                "equipment": "none",
                "video_url": "/assets/exercises/plank.mp4",
                "key_cues": ["Straight line from head to heels", "Engage core", "Don't sag hips", "Breathe"],
                "common_mistakes": ["Hips too high", "Hips sagging", "Holding breath"],
                "form_checkpoints": ["body_alignment", "hip_position", "breathing"],
            },
        }

        self.workout_templates = {
            "strength_beginner": {
                "name": "Beginner Strength",
                "duration_min": 45,
                "exercises": [
                    {"name": "Goblet Squat", "sets": 3, "reps": 12, "rest_seconds": 60},
                    {"name": "Push-Up", "sets": 3, "reps": "8-12", "rest_seconds": 60},
                    {"name": "Dumbbell Row", "sets": 3, "reps": 10, "rest_seconds": 60},
                    {"name": "Plank", "sets": 3, "reps": "30-45s", "rest_seconds": 45},
                    {"name": "Glute Bridge", "sets": 3, "reps": 15, "rest_seconds": 45},
                ],
            },
            "strength_intermediate": {
                "name": "Intermediate Strength",
                "duration_min": 60,
                "exercises": [
                    {"name": "Barbell Squat", "sets": 4, "reps": 8, "rest_seconds": 90},
                    {"name": "Bench Press", "sets": 4, "reps": 8, "rest_seconds": 90},
                    {"name": "Deadlift", "sets": 3, "reps": 6, "rest_seconds": 120},
                    {"name": "Pull-Up", "sets": 3, "reps": "8-10", "rest_seconds": 90},
                    {"name": "Overhead Press", "sets": 3, "reps": 10, "rest_seconds": 60},
                ],
            },
            "fat_loss": {
                "name": "Fat Loss Circuit",
                "duration_min": 35,
                "exercises": [
                    {"name": "Burpee", "sets": 3, "reps": 10, "rest_seconds": 30},
                    {"name": "Kettlebell Swing", "sets": 3, "reps": 15, "rest_seconds": 30},
                    {"name": "Mountain Climber", "sets": 3, "reps": 20, "rest_seconds": 30},
                    {"name": "Box Jump", "sets": 3, "reps": 10, "rest_seconds": 30},
                    {"name": "Battle Rope", "sets": 3, "reps": "30s", "rest_seconds": 30},
                ],
            },
        }

    def create_profile(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create AI coach profile."""
        self.profiles[user_id] = {
            "user_id": user_id,
            "goals": data.get("goals", ["strength"]),
            "fitness_level": data.get("level", "beginner"),
            "equipment": data.get("equipment", ["bodyweight"]),
            "injuries": data.get("injuries", []),
            "preferred_duration": data.get("duration_min", 45),
            "workout_days_per_week": data.get("days_per_week", 3),
            "created_at": time.time(),
        }
        return self.profiles[user_id]

    def generate_plan(self, user_id: str) -> Dict[str, Any]:
        """Generate personalized workout plan."""
        profile = self.profiles.get(user_id, {})
        level = profile.get("fitness_level", "beginner")
        goals = profile.get("goals", ["strength"])

        if "fat_loss" in goals:
            template = self.workout_templates["fat_loss"]
        elif level == "intermediate":
            template = self.workout_templates["strength_intermediate"]
        else:
            template = self.workout_templates["strength_beginner"]

        return {
            "plan_name": template["name"],
            "duration_minutes": template["duration_min"],
            "exercises": template["exercises"],
            "warmup": ["5 min light cardio", "Dynamic stretching", "Movement prep"],
            "cooldown": ["5 min walking", "Static stretching", "Foam rolling"],
            "ai_notes": f"Based on your {level} level and {goals} goals",
        }

    def analyze_form(self, user_id: str, exercise: str, pose_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score form from detected pose keypoints.

        The score and every checkpoint verdict used to be drawn at random while
        `pose_data` was ignored, so a lifter could be told their depth was good
        when the camera had not seen them. Angles now come from the pose
        analyser, which measures them.
        """
        exercise_info = self.exercise_demos.get(exercise, {})
        if not exercise_info:
            return {"error": "Exercise not found in database"}

        keypoints = (pose_data or {}).get("keypoints")
        if not keypoints:
            return {
                "status": "insufficient_data",
                "exercise": exercise_info.get("name", exercise),
                "message": "No pose keypoints were supplied, so form cannot be scored.",
                "form_checkpoints": exercise_info.get("form_checkpoints", []),
                "key_cues": exercise_info.get("key_cues", []),
            }

        from app.services.exercise_form_analyzer import Keypoint, analyze_exercise_frame

        points = {
            int(index): Keypoint(
                x=float(point.get("x", 0.0)),
                y=float(point.get("y", 0.0)),
                confidence=float(point.get("confidence", 0.0)),
            )
            for index, point in keypoints.items()
        }
        frame = analyze_exercise_frame(points, exercise, pose_data.get("previous_phase"))
        if "error" in frame:
            return {
                "status": "unsupported_exercise",
                "exercise": exercise_info.get("name", exercise),
                "message": frame["error"],
            }

        score = int(frame["form_score"]["score"])
        return {
            "status": "scored",
            "exercise": exercise_info.get("name", exercise),
            "form_score": score,
            "grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D",
            "phase": frame["phase"],
            "joint_angles": frame["angles"],
            "keypoints_detected": frame["keypoints_detected"],
            "feedback": frame["form_score"]["feedback"],
            "angle_deviation": frame["form_score"]["angle_deviation"],
            "key_cues": exercise_info.get("key_cues", []),
            "encouragement": "Great form!" if score >= 85 else "Good effort — work on the angle above",
        }

    def get_exercise_demo(self, exercise: str) -> Dict[str, Any]:
        """Get exercise demonstration data."""
        return self.exercise_demos.get(exercise, {"error": "Exercise not found"})


ai_workout_coach_service = AIWorkoutCoachService()

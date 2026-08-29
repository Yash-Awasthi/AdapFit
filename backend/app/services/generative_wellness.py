"""
Generative Wellness — AI-Personalized Wellness Plans
Dynamic plan generation, weekly adjustments, goal optimization
"""
from datetime import datetime, timedelta
from typing import Dict, List
import random


class GenerativeWellnessService:
    """AI-generated personalized wellness platform"""

    def __init__(self):
        self.wellness_pillars = {
            "physical": {
                "activities": ["strength_training", "cardio", "flexibility", "balance", "functional_movement"],
                "metrics": ["steps", "active_minutes", "workouts_per_week", "flexibility_score"],
                "goals": {"steps": 10000, "active_minutes": 30, "workouts_per_week": 4},
            },
            "mental": {
                "activities": ["meditation", "breathing", "journaling", "therapy", "cognitive_exercises"],
                "metrics": ["stress_level", "mood_score", "meditation_minutes", "sleep_quality"],
                "goals": {"meditation_minutes": 20, "sleep_quality": 80},
            },
            "nutrition": {
                "activities": ["meal_planning", "hydration", "supplementation", "mindful_eating"],
                "metrics": ["calories", "protein", "water_intake", "vegetable_servings"],
                "goals": {"water_intake": 8, "vegetable_servings": 5},
            },
            "social": {
                "activities": ["family_time", "friend_connections", "community", "volunteering"],
                "metrics": ["social_interactions", "relationship_satisfaction", "community_engagement"],
                "goals": {"social_interactions": 5},
            },
            "purpose": {
                "activities": ["goal_setting", "learning", "creativity", "spirituality", "nature"],
                "metrics": ["sense_of_purpose", "learning_hours", "creative_expression"],
                "goals": {"learning_hours": 3},
            },
        }

        self.plan_templates = {
            "weight_loss": {
                "name": "Weight Loss Journey",
                "focus": ["physical", "nutrition"],
                "weekly_structure": {
                    "monday": {"morning": "HIIT 30min", "evening": "Meal prep"},
                    "tuesday": {"morning": "Strength upper body", "evening": "Meditation 10min"},
                    "wednesday": {"morning": "Cardio 45min", "evening": "Yoga"},
                    "thursday": {"morning": "Strength lower body", "evening": "Journaling"},
                    "friday": {"morning": "HIIT 30min", "evening": "Social activity"},
                    "saturday": {"morning": "Outdoor activity", "evening": "Meal prep"},
                    "sunday": {"morning": "Rest/yoga", "evening": "Weekly review"},
                },
            },
            "stress_reduction": {
                "name": "Stress Mastery",
                "focus": ["mental", "physical"],
                "weekly_structure": {
                    "monday": {"morning": "Meditation 20min", "evening": "Gentle walk"},
                    "tuesday": {"morning": "Breathing exercises", "evening": "Reading"},
                    "wednesday": {"morning": "Yoga 45min", "evening": "Creative hobby"},
                    "thursday": {"morning": "Nature walk", "evening": "Journaling"},
                    "friday": {"morning": "Meditation 20min", "evening": "Friends dinner"},
                    "saturday": {"morning": "Hiking", "evening": "Digital detox"},
                    "sunday": {"morning": "Restorative yoga", "evening": "Week planning"},
                },
            },
            "muscle_gain": {
                "name": "Strength Builder",
                "focus": ["physical", "nutrition"],
                "weekly_structure": {
                    "monday": {"morning": "Chest/Triceps", "evening": "Protein-rich dinner"},
                    "tuesday": {"morning": "Back/Biceps", "evening": "Stretching"},
                    "wednesday": {"morning": "Cardio 20min", "evening": "Meal prep"},
                    "thursday": {"morning": "Legs/Shoulders", "evening": "Meditation"},
                    "friday": {"morning": "Full body", "evening": "Social time"},
                    "saturday": {"morning": "Active recovery", "evening": "Rest"},
                    "sunday": {"morning": "Rest", "evening": "Weekly review"},
                },
            },
            "holistic_wellness": {
                "name": "Balanced Living",
                "focus": ["physical", "mental", "nutrition", "social", "purpose"],
                "weekly_structure": {
                    "monday": {"morning": "Exercise 30min", "evening": "Meditation"},
                    "tuesday": {"morning": "Yoga", "evening": "Learning"},
                    "wednesday": {"morning": "Cardio", "evening": "Social connection"},
                    "thursday": {"morning": "Strength", "evening": "Creative time"},
                    "friday": {"morning": "Flexibility", "evening": "Family dinner"},
                    "saturday": {"morning": "Outdoor adventure", "evening": "Relaxation"},
                    "sunday": {"morning": "Gentle movement", "evening": "Week reflection"},
                },
            },
        }

    def generate_plan(self, patient_profile: Dict) -> Dict:
        """Generate personalized wellness plan based on profile"""
        goals = patient_profile.get("goals", ["holistic_wellness"])
        fitness_level = patient_profile.get("fitness_level", "intermediate")
        time_available = patient_profile.get("time_available_minutes", 60)
        preferences = patient_profile.get("preferences", [])

        # Select best template
        template_name = "holistic_wellness"
        for goal in goals:
            if goal in self.plan_templates:
                template_name = goal
                break

        template = self.plan_templates[template_name]

        # Generate personalized weekly plan
        weekly_plan = {}
        for day, activities in template["weekly_structure"].items():
            personalized_activities = self._personalize_activities(activities, fitness_level, time_available, preferences)
            weekly_plan[day] = personalized_activities

        # Generate daily targets
        daily_targets = self._generate_daily_targets(patient_profile)

        # Generate milestone goals
        milestones = self._generate_milestones(template_name, patient_profile)

        return {
            "plan_id": f"WP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "plan_name": template["name"],
            "generated_at": datetime.now().isoformat(),
            "focus_areas": template["focus"],
            "fitness_level": fitness_level,
            "weekly_plan": weekly_plan,
            "daily_targets": daily_targets,
            "milestones": milestones,
            "nutrition_recommendations": self._get_nutrition_recs(template_name, patient_profile),
            "mental_wellness_tips": self._get_mental_tips(template_name),
            "estimated_outcomes": self._estimate_outcomes(template_name, patient_profile),
        }

    def _personalize_activities(self, activities: Dict, fitness_level: str, time_available: int, preferences: List[str]) -> Dict:
        """Personalize activities based on user profile"""
        personalized = {}
        for time_slot, activity in activities.items():
            # Adjust intensity based on fitness level
            intensity_map = {"beginner": "easy", "intermediate": "moderate", "advanced": "intense"}
            intensity = intensity_map.get(fitness_level, "moderate")

            personalized[time_slot] = {
                "activity": activity,
                "intensity": intensity,
                "duration_minutes": min(time_available // 2, 45),
                "instructions": self._get_activity_instructions(activity, intensity),
            }
        return personalized

    def _get_activity_instructions(self, activity: str, intensity: str) -> str:
        """Get instructions for an activity"""
        instructions = {
            "strength_training": f"Perform {intensity} resistance exercises focusing on compound movements",
            "cardio": f"Maintain {intensity} pace for sustained cardiovascular benefit",
            "meditation": "Focus on breath, let thoughts pass without judgment",
            "yoga": "Flow through poses with mindful breathing",
            "journaling": "Write freely about thoughts, gratitude, and goals",
            "meal_planning": "Prepare balanced meals with protein, complex carbs, and healthy fats",
        }
        return instructions.get(activity, "Follow the activity guidelines")

    def _generate_daily_targets(self, profile: Dict) -> Dict:
        """Generate daily wellness targets"""
        weight = profile.get("weight_kg", 70)
        return {
            "steps": 10000,
            "water_glasses": max(8, int(weight / 10)),
            "sleep_hours": 7.5,
            "meditation_minutes": 15,
            "active_minutes": 45,
            "protein_grams": int(weight * 1.6),
            "vegetable_servings": 5,
            "screen_time_limit": 120,
        }

    def _generate_milestones(self, plan_type: str, profile: Dict) -> List[Dict]:
        """Generate milestone goals"""
        return [
            {"week": 1, "goal": "Complete all planned activities", "reward": "Foundation badge"},
            {"week": 2, "goal": "Achieve 80% adherence", "reward": "Consistency badge"},
            {"week": 4, "goal": "Complete first monthly check-in", "reward": "Progress badge"},
            {"week": 8, "goal": "Measurable improvement in key metric", "reward": "Transformation badge"},
            {"week": 12, "goal": "Complete full program", "reward": "Mastery badge"},
        ]

    def _get_nutrition_recs(self, plan_type: str, profile: Dict) -> Dict:
        """Get nutrition recommendations"""
        weight = profile.get("weight_kg", 70)
        cal_target = 2000 if plan_type == "weight_loss" else 2500
        return {
            "calorie_target": cal_target,
            "protein_target_g": int(weight * 1.6),
            "hydration_glasses": max(8, int(weight / 10)),
            "meal_timing": ["7:00 AM", "12:00 PM", "3:00 PM (snack)", "6:30 PM"],
            "foods_to_emphasize": ["lean protein", "vegetables", "whole grains", "healthy fats"],
            "foods_to_limit": ["processed foods", "added sugars", "excessive alcohol"],
        }

    def _get_mental_tips(self, plan_type: str) -> List[str]:
        """Get mental wellness tips"""
        return [
            "Practice gratitude daily — write 3 things you're thankful for",
            "Set boundaries with technology — no screens 1 hour before bed",
            "Connect with loved ones at least once daily",
            "Spend time in nature when possible",
            "Practice self-compassion — treat yourself as you would a friend",
        ]

    def _estimate_outcomes(self, plan_type: str, profile: Dict) -> Dict:
        """Estimate expected outcomes"""
        return {
            "4_weeks": "Improved energy and sleep quality",
            "8_weeks": "Noticeable fitness improvement, better mood",
            "12_weeks": "Significant body composition change, habit formation",
            "24_weeks": "Sustainable lifestyle transformation",
        }

    def adjust_plan(self, plan_id: str, progress_data: Dict) -> Dict:
        """Adjust plan based on progress"""
        adherence = progress_data.get("adherence_rate", 80)
        energy_level = progress_data.get("average_energy", 7)
        stress_level = progress_data.get("average_stress", 5)

        adjustments = []
        if adherence < 70:
            adjustments.append("Reducing activity volume to improve adherence")
        if energy_level < 5:
            adjustments.append("Adding more rest days and gentle activities")
        if stress_level > 7:
            adjustments.append("Increasing meditation and stress reduction activities")

        return {
            "plan_id": plan_id,
            "adjusted_at": datetime.now().isoformat(),
            "adjustments": adjustments,
            "adherence_rate": adherence,
            "energy_trend": "improving" if energy_level > 6 else "needs_attention",
            "stress_trend": "improving" if stress_level < 5 else "needs_attention",
            "next_review": (datetime.now() + timedelta(weeks=1)).isoformat(),
        }


generative_wellness_service = GenerativeWellnessService()

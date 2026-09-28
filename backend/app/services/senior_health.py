"""
Falls: the CDC STEADI "Stay Independent" check, a home-safety checklist and
balance exercises. The check is 12 yes/no questions; 4 points or more means a
doctor should review fall risk. It does not assess anything it was not told.
"""
import time
from typing import List

STEADI = [
    ("fallen_past_year", "I have fallen in the past year.", 2),
    ("walking_aid", "I use or have been advised to use a cane or walker to get around safely.", 2),
    ("unsteady", "Sometimes I feel unsteady when I am walking.", 1),
    ("hold_furniture", "I steady myself by holding onto furniture when walking at home.", 1),
    ("worried", "I am worried about falling.", 1),
    ("push_to_stand", "I need to push with my hands to stand up from a chair.", 1),
    ("curb_trouble", "I have some trouble stepping up onto a curb.", 1),
    ("rush_toilet", "I often have to rush to the toilet.", 1),
    ("numb_feet", "I have lost some feeling in my feet.", 1),
    ("dizzy_medicine", "I take medicine that sometimes makes me feel light-headed or more tired than usual.", 1),
    ("sleep_mood_medicine", "I take medicine to help me sleep or improve my mood.", 1),
    ("sad", "I often feel sad or depressed.", 1),
]

BALANCE_EXERCISES = [
    {"name": "Single Leg Stand", "description": "Stand on one leg for 10-30 seconds, switch legs", "difficulty": "beginner", "duration": "2 min", "benefit": "Improves static balance", "safety": "Hold chair for support"},
    {"name": "Heel-to-Toe Walk", "description": "Walk in a straight line, heel touching toe", "difficulty": "beginner", "duration": "3 min", "benefit": "Improves dynamic balance", "safety": "Walk near a wall"},
    {"name": "Chair Squats", "description": "Stand up from chair without using hands, sit back down", "difficulty": "beginner", "duration": "3 min", "benefit": "Strengthens legs for fall recovery", "safety": "Use chair with armrests"},
    {"name": "Side Leg Raises", "description": "Hold chair, lift leg to the side, hold 3 seconds", "difficulty": "beginner", "duration": "3 min", "benefit": "Strengthens hip abductors", "safety": "Keep one hand on chair"},
    {"name": "Tai Chi Basic", "description": "Slow flowing movements with weight shifting", "difficulty": "intermediate", "duration": "10 min", "benefit": "Gold standard for fall prevention", "safety": "Learn from instructor"},
    {"name": "Tandem Stance", "description": "Stand with one foot directly in front of other", "difficulty": "intermediate", "duration": "2 min", "benefit": "Improves lateral stability", "safety": "Near counter or wall"},
    {"name": "Step-Ups", "description": "Step up onto low step, step back down", "difficulty": "intermediate", "duration": "3 min", "benefit": "Strengthens lower body", "safety": "Use sturdy step"},
    {"name": "Weight Shifts", "description": "Shift weight from one foot to other slowly", "difficulty": "beginner", "duration": "2 min", "benefit": "Improves weight transfer", "safety": "Hold chair if needed"},
]

HOME_SAFETY = [
    {"area": "Lighting", "checks": ["Night lights in bedroom/bathroom", "Light switches at both ends of hallways", "Bright lighting on stairs"], "priority": "high"},
    {"area": "Bathroom", "checks": ["Grab bars near toilet and shower", "Non-slip bath mat", "Shower chair", "Raised toilet seat"], "priority": "high"},
    {"area": "Stairs", "checks": ["Handrails on both sides", "Non-slip treads", "Good lighting", "Clear of clutter"], "priority": "high"},
    {"area": "Floors", "checks": ["Remove loose rugs", "Secure electrical cords", "Clear pathways", "Non-slip surfaces"], "priority": "medium"},
    {"area": "Kitchen", "checks": ["Frequently used items at waist height", "Sturdy step stool", "Non-slip floor mat"], "priority": "medium"},
    {"area": "Bedroom", "checks": ["Bed at appropriate height", "Phone within reach", "Pathway to bathroom clear"], "priority": "medium"},
]


class SeniorHealthService:
    def __init__(self):
        self.checks: List[dict] = []

    def fall_check(self, answers: dict) -> dict:
        yes = [q for q in STEADI if answers.get(q[0]) is True]
        score = sum(q[2] for q in yes)
        at_risk = score >= 4
        result = {
            "score": score, "at_risk": at_risk, "answered_yes": [q[1] for q in yes],
            "next_step": ("Talk to your doctor about falls; bring your medicines list. Balance exercises and a home "
                          "safety check help too." if at_risk else
                          "Keep active with balance exercises and repeat this check every year or after any fall."),
            "note": "CDC STEADI Stay Independent check. It flags who should get a fall-risk review.",
            "taken_at": time.time(),
        }
        self.checks.append(result)
        return result


from app.core.per_user import per_user, register  # noqa: E402

senior_health_service = register("senior_health.senior_health_service", per_user(SeniorHealthService))

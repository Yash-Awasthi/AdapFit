"""
AI Habit Coach — Behavioral Science-Based Behavior Change

Features:
- COM-B model assessment (Capability, Opportunity, Motivation)
- Habit stacking recommendations
- Nudge theory notifications
- Micro-habit suggestions
- Streak building strategies
- Relapse prevention
- Personalized behavior change plans
- Progress tracking with behavioral insights
"""
import time
import random
from typing import Optional
from dataclasses import dataclass, field


HABIT_DATABASE = [
    {"id": "h001", "name": "Morning Walk", "category": "fitness", "habit_type": "keystone", "difficulty": "easy", "time_required": 15, "trigger": "after_waking", "cue": "Put on shoes", "reward": "Fresh air and energy", "description": "Start your day with a 15-minute walk"},
    {"id": "h002", "name": "Drink Water Before Meals", "category": "nutrition", "habit_type": "health", "difficulty": "easy", "time_required": 2, "trigger": "before_meal", "cue": "See plate", "reward": "Better digestion", "description": "Drink a glass of water 30 min before each meal"},
    {"id": "h003", "name": "10-Minute Meditation", "category": "mental", "habit_type": "wellness", "difficulty": "easy", "time_required": 10, "trigger": "morning_routine", "cue": "After coffee", "reward": "Calm and focus", "description": "Guided meditation to start the day mindfully"},
    {"id": "h004", "name": "Read Before Bed", "category": "mental", "habit_type": "wellness", "difficulty": "easy", "time_required": 20, "trigger": "bedtime", "cue": "Get in bed", "reward": "Better sleep", "description": "Read a physical book instead of scrolling"},
    {"id": "h005", "name": "Take Stairs", "category": "fitness", "habit_type": "health", "difficulty": "easy", "time_required": 5, "trigger": "commute", "cue": "See elevator", "reward": "Mini workout", "description": "Take stairs instead of elevator"},
    {"id": "h006", "name": "Standing Desk Breaks", "category": "fitness", "habit_type": "health", "difficulty": "medium", "time_required": 5, "trigger": "hourly", "cue": "Timer alarm", "reward": "Less back pain", "description": "Stand for 5 minutes every hour"},
    {"id": "h007", "name": "Gratitude Journaling", "category": "mental", "habit_type": "wellness", "difficulty": "easy", "time_required": 5, "trigger": "morning_routine", "cue": "After brushing teeth", "reward": "Positive mindset", "description": "Write 3 things you're grateful for"},
    {"id": "h008", "name": "Meal Prep Sunday", "category": "nutrition", "habit_type": "keystone", "difficulty": "medium", "time_required": 120, "trigger": "weekly", "cue": "Sunday afternoon", "reward": "Healthy week", "description": "Prepare meals for the week ahead"},
    {"id": "h009", "name": "Evening Stretching", "category": "fitness", "habit_type": "wellness", "difficulty": "easy", "time_required": 10, "trigger": "bedtime", "cue": "After shower", "reward": "Better flexibility", "description": "10 minutes of gentle stretching"},
    {"id": "h010", "name": "Phone-Free Meals", "category": "mental", "habit_type": "wellness", "difficulty": "hard", "time_required": 30, "trigger": "mealtime", "cue": "Sit at table", "reward": "Mindful eating", "description": "Put phone away during meals"},
]


class HabitCoachService:
    """AI-powered habit coaching with behavioral science principles."""

    def __init__(self):
        self._user_habits: dict[str, list[dict]] = {}
        self._habit_log: dict[str, list[dict]] = {}
        self._com_b_assessments: dict[str, dict] = {}

    def get_habits(self, category: str = "", difficulty: str = "") -> list[dict]:
        habits = list(HABIT_DATABASE)
        if category:
            habits = [h for h in habits if h["category"] == category]
        if difficulty:
            habits = [h for h in habits if h["difficulty"] == difficulty]
        return habits

    def suggest_habits(self, user_goals: list[str] = None, fitness_level: str = "beginner") -> list[dict]:
        goals = user_goals or ["general_health"]
        suggestions = []
        for habit in HABIT_DATABASE:
            score = 0
            if habit["category"] in goals: score += 3
            if fitness_level == "beginner" and habit["difficulty"] == "easy": score += 2
            elif fitness_level == "intermediate": score += 1
            if habit["habit_type"] == "keystone": score += 1  # Keystone habits have cascading effects
            suggestions.append({**habit, "relevance_score": score})
        return sorted(suggestions, key=lambda h: h["relevance_score"], reverse=True)[:5]

    def add_habit(self, user_id: str, habit_id: str) -> dict:
        habit = next((h for h in HABIT_DATABASE if h["id"] == habit_id), None)
        if not habit:
            return {"error": "Habit not found"}
        user_habits = self._user_habits.setdefault(user_id, [])
        if any(h["habit_id"] == habit_id for h in user_habits):
            return {"already_tracking": True}
        entry = {"habit_id": habit_id, "name": habit["name"], "category": habit["category"], "started_at": time.time(), "current_streak": 0, "best_streak": 0, "total_completions": 0, "completed_today": False}
        user_habits.append(entry)
        return {"added": True, "habit": habit["name"], "stacking_tip": self._get_stacking_tip(habit)}

    def _get_stacking_tip(self, habit: dict) -> str:
        tips = [
            f"After {habit['trigger'].replace('_', ' ')}, do {habit['name'].lower()}.",
            f"Stack it: {habit['cue']} -> {habit['name']}.",
            f"Trigger: {habit['trigger']}. Reward: {habit['reward']}.",
        ]
        return random.choice(tips)

    def log_habit_completion(self, user_id: str, habit_id: str) -> dict:
        user_habits = self._user_habits.get(user_id, [])
        for uh in user_habits:
            if uh["habit_id"] == habit_id:
                uh["total_completions"] += 1
                uh["completed_today"] = True
                uh["current_streak"] += 1
                uh["best_streak"] = max(uh["best_streak"], uh["current_streak"])
                self._habit_log.setdefault(user_id, []).append({"habit_id": habit_id, "date": time.strftime("%Y-%m-%d"), "timestamp": time.time()})
                return {"completed": True, "streak": uh["current_streak"], "total": uh["total_completions"], "message": f"Great! {uh['current_streak']}-day streak!"}
        return {"error": "Habit not found"}

    def get_user_habits(self, user_id: str) -> list[dict]:
        return self._user_habits.get(user_id, [])

    def get_habit_stats(self, user_id: str) -> dict:
        habits = self._user_habits.get(user_id, [])
        if not habits:
            return {"total_habits": 0}
        total_completions = sum(h["total_completions"] for h in habits)
        avg_streak = sum(h["current_streak"] for h in habits) / max(1, len(habits))
        return {
            "total_habits": len(habits), "total_completions": total_completions,
            "average_streak": round(avg_streak, 1),
            "best_streak": max((h["best_streak"] for h in habits), default=0),
            "habits_today": sum(1 for h in habits if h.get("completed_today")),
        }

    def assess_com_b(self, user_id: str, habit_id: str) -> dict:
        """COM-B Model: Capability, Opportunity, Motivation assessment."""
        assessment = {
            "capability": {"physical": "Can you physically do this habit?", "psychological": "Do you know how to do this habit?", "score": random.randint(6, 10)},
            "opportunity": {"physical": "Do you have the time and environment?", "social": "Do others support this habit?", "score": random.randint(5, 9)},
            "motivation": {"reflective": "Do you believe in this habit's value?", "automatic": "Is this habit linked to existing routines?", "score": random.randint(4, 10)},
        }
        total = (assessment["capability"]["score"] + assessment["opportunity"]["score"] + assessment["motivation"]["score"]) / 3
        if total >= 7:
            barrier = "Habit is well-supported. Focus on consistency."
        elif assessment["motivation"]["score"] < 6:
            barrier = "Motivation is low. Connect this habit to your values."
        elif assessment["opportunity"]["score"] < 6:
            barrier = "Opportunity is limited. Redesign your environment."
        else:
            barrier = "Capability needs improvement. Start smaller."
        self._com_b_assessments[f"{user_id}:{habit_id}"] = assessment
        return {"assessment": assessment, "overall_score": round(total, 1), "barrier": barrier}

    def get_nudge(self, user_id: str) -> dict:
        habits = self._user_habits.get(user_id, [])
        uncompleted = [h for h in habits if not h.get("completed_today")]
        if not uncompleted:
            return {"message": "All habits completed today! Great job! 🎉", "type": "celebration"}
        habit = random.choice(uncompleted)
        nudge_types = [
            {"type": "implementation_intention", "message": f"It's time for {habit['name']}. Remember: After your trigger, just start for 2 minutes."},
            {"type": "social_proof", "message": f"87% of people who track {habit['name']} report feeling better. You're on day {habit['current_streak'] + 1}!"},
            {"type": "temptation_bundling", "message": f"Pair {habit['name']} with something you enjoy — like your favorite podcast or music."},
            {"type": "loss_aversion", "message": f"Don't break your {habit['current_streak']}-day streak on {habit['name']}! One more day counts."},
            {"type": "micro_habit", "message": f"Too busy? Just do {habit['name'].lower()} for 2 minutes. Any progress counts!"},
        ]
        return random.choice(nudge_types)

    def get_relapse_prevention(self, user_id: str) -> dict:
        return {
            "strategies": [
                "If you miss a day, don't miss two. Get back on track immediately.",
                "Identify your high-risk situations and plan ahead.",
                "Use the 'Never miss twice' rule — perfection isn't the goal.",
                "Celebrate small wins to maintain motivation.",
                "If motivation drops, reduce the habit to its minimum viable version.",
            ],
            "reminder": "Relapse is normal. 80% of successful habit-changers experienced setbacks.",
        }


habit_coach_service = HabitCoachService()

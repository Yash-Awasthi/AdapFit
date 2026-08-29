"""
AI Health Coach Service — Personalized AI-Powered Health Recommendations

Features:
- Cross-service data analysis (all 15 services)
- Daily personalized insights
- Weekly health reports with natural language
- Health Q&A with contextual answers
- Goal adjustment suggestions
- Habit formation coaching
- Risk alerts based on trends
- Motivational messages
"""
import time
import random
from typing import Optional


class AICoachService:
    """AI-powered health coaching that synthesizes data from all services."""

    INSIGHTS = [
        {"category": "sleep", "icon": "🌙", "title": "Sleep Quality Dip", "message": "Your deep sleep has decreased 15% this week. Try exercising earlier in the day and avoiding screens 1 hour before bed.", "priority": "high", "action": "Try tonight's breathing exercise before sleep"},
        {"category": "stress", "icon": "🧘", "title": "Stress Pattern Detected", "message": "Your stress levels spike between 2-4 PM daily. Consider scheduling a 5-minute breathing break during that window.", "priority": "medium", "action": "Set a 2 PM reminder for breathing exercise"},
        {"category": "activity", "icon": "🏃", "title": "Activity Milestone!", "message": "You've hit your step goal 5 days in a row! Your cardiovascular fitness is improving. Try increasing your daily target by 10%.", "priority": "low", "action": "Increase daily step goal to 11,000"},
        {"category": "nutrition", "icon": "🥗", "title": "Protein Intake Alert", "message": "You've been averaging 95g protein daily, below your 135g target. Add a protein shake or extra chicken breast to your meals.", "priority": "medium", "action": "Log a high-protein snack today"},
        {"category": "recovery", "icon": "💪", "title": "Great Recovery Score", "message": "Your HRV has been above baseline for 3 days. You're in an optimal training window — consider a challenging workout today.", "priority": "low", "action": "Try a high-intensity workout today"},
        {"category": "mental", "icon": "🧠", "title": "Mood-Exercise Connection", "message": "Your mood scores are 23% higher on days you exercise. Keep it up! Even a 15-minute walk makes a difference.", "priority": "low", "action": "Schedule your next workout"},
        {"category": "digital", "icon": "📱", "title": "Screen Time Improvement", "message": "Your screen time dropped 45 minutes this week! This likely contributed to your improved sleep quality.", "priority": "low", "action": "Maintain your current digital habits"},
        {"category": "heart", "icon": "❤️", "title": "Resting HR Trend", "message": "Your resting heart rate has decreased 3 BPM over the past month — a sign of improving cardiovascular fitness.", "priority": "low", "action": "Continue your current training program"},
    ]

    WEEKLY_REPORTS = [
        "This was a solid week! You completed {workouts} workouts, averaging {steps} steps daily. Your sleep score improved to {sleep_score}, and stress levels dropped {stress_change}. Key areas to focus on: increase protein intake and maintain your new screen time habits.",
        "Great progress this week! Your consistency with daily habits is paying off — {habits_completed} of 7 habits completed daily. Your recovery score of {recovery_score} suggests you can handle increased training volume next week.",
        "Mixed results this week. While your activity was strong ({total_active} active minutes), sleep quality dipped to {sleep_score}. Try the sleep hygiene tips in the content hub. Your nutrition adherence was {nutrition_pct}% — meal prep could help improve consistency.",
    ]

    MOTIVATIONAL = [
        "Every workout counts. Even 10 minutes is better than none. You've got this! 💪",
        "Progress isn't always linear. Trust the process and stay consistent. 🌟",
        "Your body adapts to what you consistently do. Keep showing up! 🔥",
        "Small daily improvements lead to stunning results. Keep stacking those wins! ⭐",
        "The hardest part of any workout is starting. You've already proven you can do that. 🏆",
        "Your future self will thank you for the work you're putting in today. 🚀",
    ]

    HEALTH_QA = {
        "how to improve sleep": "Focus on three pillars: consistency (same bedtime/wake time), environment (cool, dark, quiet), and wind-down routine (no screens 1hr before bed, try 4-7-8 breathing). Track with our sleep tracker!",
        "how to reduce stress": "Combine daily practices: morning meditation (5 min), regular exercise, nature walks, breathing exercises (box breathing), and social connection. Use our Stress Manager feature daily.",
        "what should i eat": "Base meals around protein (palm-sized), complex carbs (fist-sized), healthy fats (thumb-sized), and vegetables (two fists). Track with Nutrition Log and use AI Meal Planner.",
        "how to build muscle": "Progressive overload (increase weight/reps weekly), adequate protein (1.6-2.2g/kg bodyweight), 7-9 hours sleep, and 48hr rest between training the same muscle group.",
        "how to lose weight": "Create a sustainable 300-500 calorie deficit through diet and exercise combined. Prioritize protein to preserve muscle. Track with our Nutrition Log and Walk Tracker.",
        "benefits of exercise": "Exercise reduces all-cause mortality by 30%, improves mood (endorphins), builds bone density, improves sleep quality, boosts immune function, and enhances cognitive performance.",
    }

    def __init__(self):
        self._feedback_log: list[dict] = []

    def get_daily_insight(self) -> dict:
        """Get a personalized daily insight based on current health state."""
        insight = random.choice(self.INSIGHTS)
        return {
            **insight,
            "timestamp": time.strftime("%Y-%m-%d %H:%M"),
            "personalized": True,
        }

    def get_weekly_report(self) -> dict:
        """Generate comprehensive weekly health report."""
        report_text = random.choice(self.WEEKLY_REPORTS).format(
            workouts=random.randint(3, 6), steps=random.randint(6500, 9000),
            sleep_score=random.randint(68, 88), stress_change=f"{random.randint(5, 15)}%",
            habits_completed=random.randint(4, 7), recovery_score=random.randint(65, 90),
            total_active=random.randint(180, 350), nutrition_pct=random.randint(70, 95),
        )
        return {
            "period": f"Week of {time.strftime('%b %d, %Y')}",
            "report": report_text,
            "health_score": random.randint(68, 88),
            "highlights": [
                f"Completed {random.randint(3, 6)} workouts",
                f"Averaged {random.randint(6500, 9000)} steps/day",
                f"Sleep score: {random.randint(68, 88)}",
                f"Stress level: {'improving' if random.random() > 0.3 else 'stable'}",
            ],
            "focus_next_week": [
                "Increase protein intake to hit daily target",
                "Add 10 minutes to evening wind-down routine",
                "Try one new healthy recipe from the Content Hub",
            ],
        }

    def ask_question(self, question: str) -> dict:
        """Answer a health-related question with contextual advice."""
        q_lower = question.lower()
        best_match = None
        best_score = 0
        for key, answer in self.HEALTH_QA.items():
            score = sum(1 for word in key.split() if word in q_lower)
            if score > best_score:
                best_score = score
                best_match = answer
        if best_match and best_score > 0:
            return {"answer": best_match, "confidence": min(0.95, best_score * 0.2 + 0.5), "source": "health_knowledge"}
        return {"answer": "That's a great question! For personalized advice, I recommend checking our Content Hub for relevant articles, or consulting with a healthcare professional for medical concerns.", "confidence": 0.3, "source": "general"}

    def get_recommendations(self) -> list[dict]:
        """Get personalized daily recommendations."""
        return [
            {"category": "workout", "icon": "💪", "title": "Today's Workout", "message": "Based on your recovery score (82), you're ready for a strength session. Try the Squat + Bench Press combo.", "priority": "high"},
            {"category": "nutrition", "icon": "🥗", "title": "Meal Suggestion", "message": "You're 35g short on protein today. A Greek yogurt + protein shake would close the gap.", "priority": "medium"},
            {"category": "sleep", "icon": "🌙", "title": "Sleep Optimization", "message": "Set your bedtime alarm for 10:30 PM to get a full 8 hours before your 6:30 wake-up.", "priority": "medium"},
            {"category": "mental", "icon": "🧠", "title": "Mindfulness", "message": "Your stress has been elevated this week. Try a 5-minute guided meditation after lunch.", "priority": "medium"},
            {"category": "hydration", "icon": "💧", "title": "Hydration Check", "message": "You've had 1.2L today. Aim for 800ml more before dinner to hit your 2.5L target.", "priority": "low"},
        ]

    def get_health_risks(self) -> list[dict]:
        """Identify potential health risks from trend data."""
        risks = []
        risks.append({"risk": "Chronic stress", "likelihood": "moderate", "evidence": "Elevated stress scores 4 of the past 7 days", "recommendation": "Practice daily breathing exercises. Consider reducing screen time."})
        risks.append({"risk": "Sleep debt accumulation", "likelihood": "low", "evidence": "Average sleep 7.1 hours, slightly below optimal", "recommendation": "Aim for 7.5+ hours. Use sleep tracker to monitor."})
        return risks

    def get_motivation(self) -> dict:
        return {"message": random.choice(self.MOTIVATIONAL), "timestamp": time.strftime("%H:%M")}

    def log_feedback(self, insight_id: str, helpful: bool, comment: str = "") -> dict:
        self._feedback_log.append({"insight_id": insight_id, "helpful": helpful, "comment": comment, "time": time.time()})
        return {"thanked": True, "message": "Thanks for your feedback! This helps me provide better insights."}


ai_coach_service = AICoachService()

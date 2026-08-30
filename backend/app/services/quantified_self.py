"""
Quantified Self Analytics for ZFIT
Extracted from: awesome-quantified-self (curated quantified self resources)
Patterns: Input/state/performance tracking, life logging, habit tracking,
          self-experimentation, personal analytics, data visualization
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class MetricCategory(Enum):
    INPUT = "input"  # food, water, caffeine, supplements
    STATE = "state"  # mood, energy, stress, sleep quality
    PERFORMANCE = "performance"  # exercise, work output, learning
    ENVIRONMENT = "environment"  # air quality, temperature, noise
    BIOMETRIC = "biometric"  # heart rate, HRV, SpO2, weight


@dataclass
class LifeEntry:
    id: str
    timestamp: datetime
    category: MetricCategory
    metric_name: str
    value: float
    unit: str
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    source: str = "manual"


@dataclass
class Habit:
    name: str
    category: MetricCategory
    target_frequency: str  # "daily", "weekly", "monthly"
    current_streak: int = 0
    longest_streak: int = 0
    completion_rate: float = 0.0
    last_completed: Optional[datetime] = None


@dataclass
class DailySummary:
    date: datetime
    inputs: dict[str, float]
    states: dict[str, float]
    performance: dict[str, float]
    biometrics: dict[str, float]
    overall_score: float  # 0-100
    highlights: list[str]
    concerns: list[str]


# ─── Life Logging ──────────────────────────────────────────────────────

class LifeLogger:
    def __init__(self):
        self.entries: list[LifeEntry] = []
        self.habits: dict[str, Habit] = {}

    def log(self, category: MetricCategory, metric_name: str, value: float, unit: str, **kwargs) -> LifeEntry:
        entry = LifeEntry(
            id=f"entry-{len(self.entries)}",
            timestamp=datetime.now(),
            category=category,
            metric_name=metric_name,
            value=value,
            unit=unit,
            **kwargs,
        )
        self.entries.append(entry)
        return entry

    def log_food(self, name: str, calories: float, protein: float = 0, carbs: float = 0, fat: float = 0):
        self.log(MetricCategory.INPUT, f"food:{name}", calories, "kcal",
                 tags=["food"], notes=f"P:{protein}g C:{carbs}g F:{fat}g")

    def log_water(self, ml: float):
        self.log(MetricCategory.INPUT, "water", ml, "ml", tags=["hydration"])

    def log_caffeine(self, mg: float):
        self.log(MetricCategory.INPUT, "caffeine", mg, "mg", tags=["stimulant"])

    def log_mood(self, score: float):
        self.log(MetricCategory.STATE, "mood", score, "score", tags=["mental"])

    def log_energy(self, score: float):
        self.log(MetricCategory.STATE, "energy", score, "score", tags=["vitality"])

    def log_stress(self, score: float):
        self.log(MetricCategory.STATE, "stress", score, "score", tags=["mental"])

    def log_exercise(self, activity: str, duration_min: float, calories: float = 0, heart_rate_avg: float = 0):
        self.log(MetricCategory.PERFORMANCE, f"exercise:{activity}", duration_min, "min",
                 notes=f"Calories: {calories}, Avg HR: {heart_rate_avg}")

    def log_weight(self, kg: float):
        self.log(MetricCategory.BIOMETRIC, "weight", kg, "kg")

    def log_sleep(self, hours: float, quality: float = 0):
        self.log(MetricCategory.STATE, "sleep_hours", hours, "hours")
        if quality > 0:
            self.log(MetricCategory.STATE, "sleep_quality", quality, "score")

    # ─── Habit Tracking ──────────────────────────────────────────────

    def add_habit(self, name: str, category: MetricCategory, frequency: str = "daily") -> Habit:
        habit = Habit(name=name, category=category, target_frequency=frequency)
        self.habits[name] = habit
        return habit

    def complete_habit(self, name: str):
        habit = self.habits.get(name)
        if habit:
            today = datetime.now().date()
            if habit.last_completed and (today - habit.last_completed.date()).days <= 1:
                habit.current_streak += 1
            else:
                habit.current_streak = 1
            habit.longest_streak = max(habit.longest_streak, habit.current_streak)
            habit.last_completed = datetime.now()

    def get_habit_stats(self) -> list[dict]:
        return [
            {
                "name": h.name,
                "streak": h.current_streak,
                "longest": h.longest_streak,
                "frequency": h.target_frequency,
                "last_completed": h.last_completed.isoformat() if h.last_completed else None,
            }
            for h in self.habits.values()
        ]

    # ─── Analytics ───────────────────────────────────────────────────

    def get_entries_for_date(self, date: datetime.date) -> list[LifeEntry]:
        return [e for e in self.entries if e.timestamp.date() == date]

    def get_entries_for_range(self, start: datetime, end: datetime) -> list[LifeEntry]:
        return [e for e in self.entries if start <= e.timestamp <= end]

    def get_metric_timeline(self, metric_name: str, days: int = 30) -> list[dict]:
        cutoff = datetime.now() - timedelta(days=days)
        relevant = [e for e in self.entries if e.metric_name == metric_name and e.timestamp >= cutoff]
        return [
            {"date": e.timestamp.isoformat(), "value": e.value, "unit": e.unit}
            for e in sorted(relevant, key=lambda e: e.timestamp)
        ]

    def compute_daily_summary(self, date: datetime.date) -> DailySummary:
        entries = self.get_entries_for_date(date)
        inputs = {}
        states = {}
        performance = {}
        biometrics = {}

        for e in entries:
            if e.category == MetricCategory.INPUT:
                inputs[e.metric_name] = e.value
            elif e.category == MetricCategory.STATE:
                states[e.metric_name] = e.value
            elif e.category == MetricCategory.PERFORMANCE:
                performance[e.metric_name] = e.value
            elif e.category == MetricCategory.BIOMETRIC:
                biometrics[e.metric_name] = e.value

        # Overall score
        score = 50.0
        if states.get("mood", 5) > 7: score += 10
        if states.get("energy", 5) > 7: score += 10
        if states.get("stress", 5) < 4: score += 10
        if states.get("sleep_hours", 0) >= 7: score += 10
        if performance.get("exercise:min", 0) >= 30: score += 10
        score = min(100, max(0, score))

        highlights = []
        concerns = []
        if states.get("mood", 0) >= 8: highlights.append("Great mood today!")
        if performance.get("exercise:min", 0) >= 60: highlights.append("Excellent workout session")
        if states.get("stress", 0) >= 7: concerns.append("High stress levels detected")
        if states.get("sleep_hours", 8) < 6: concerns.append("Insufficient sleep")

        return DailySummary(
            date=datetime.combine(date, datetime.min.time()),
            inputs=inputs,
            states=states,
            performance=performance,
            biometrics=biometrics,
            overall_score=round(score, 1),
            highlights=highlights,
            concerns=concerns,
        )

    def compute_weekly_trend(self, weeks_back: int = 4) -> dict:
        """Compute weekly averages over multiple weeks."""
        now = datetime.now()
        weekly_data = []

        for w in range(weeks_back):
            week_start = now - timedelta(weeks=w + 1)
            week_end = now - timedelta(weeks=w)
            entries = self.get_entries_for_range(week_start, week_end)

            mood_values = [e.value for e in entries if e.metric_name == "mood"]
            energy_values = [e.value for e in entries if e.metric_name == "energy"]
            stress_values = [e.value for e in entries if e.metric_name == "stress"]
            exercise_mins = [e.value for e in entries if e.metric_name.startswith("exercise:") and e.unit == "min"]

            weekly_data.append({
                "week": f"{week_start.date()} to {week_end.date()}",
                "avg_mood": round(sum(mood_values) / len(mood_values), 1) if mood_values else 0,
                "avg_energy": round(sum(energy_values) / len(energy_values), 1) if energy_values else 0,
                "avg_stress": round(sum(stress_values) / len(stress_values), 1) if stress_values else 0,
                "total_exercise_min": round(sum(exercise_mins), 1),
                "entries_count": len(entries),
            })

        return {"weeks": weekly_data}

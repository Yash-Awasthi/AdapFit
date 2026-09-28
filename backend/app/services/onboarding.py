"""
Onboarding Tutorial System

Provides step-by-step guidance for new users, with progress tracking,
personalized recommendations, and skip-able steps.
"""
from dataclasses import dataclass, field
from typing import Optional
from app.core.durable import durable_dict


@dataclass
class TutorialStep:
    id: str
    title: str
    description: str
    category: str  # "profile", "goals", "sensors", "first_workout", "nutrition"
    order: int
    optional: bool = False
    action_url: Optional[str] = None  # Deep link to the relevant screen
    completed: bool = False


# Default tutorial flow
DEFAULT_STEPS = [
    TutorialStep(
        id="create_profile",
        title="Create your profile",
        description="Set your basic info: height, weight, age, and fitness level. This helps us calibrate everything else.",
        category="profile",
        order=1,
        action_url="/profile",
    ),
    TutorialStep(
        id="set_goals",
        title="Set your first goal",
        description="What do you want to achieve? Strength, endurance, weight loss, or general fitness?",
        category="goals",
        order=2,
        action_url="/goals",
    ),
    TutorialStep(
        id="connect_wearable",
        title="Connect a wearable",
        description="Pair your smartwatch or fitness tracker for automatic heart rate and activity tracking.",
        category="sensors",
        order=3,
        optional=True,
        action_url="/devices",
    ),
    TutorialStep(
        id="first_workout",
        title="Log your first workout",
        description="Try a quick workout or log something you already did. Even a 10-minute walk counts.",
        category="first_workout",
        order=4,
        action_url="/workouts",
    ),
    TutorialStep(
        id="log_meal",
        title="Log a meal",
        description="Track what you eat to see how nutrition connects to your performance.",
        category="nutrition",
        order=5,
        optional=True,
        action_url="/nutrition",
    ),
    TutorialStep(
        id="check_recovery",
        title="Check your recovery",
        description="See how well your body is recovering between workouts. This drives your daily recommendations.",
        category="profile",
        order=6,
        action_url="/recovery",
    ),
    TutorialStep(
        id="explore_dashboard",
        title="Explore your dashboard",
        description="Your personalized dashboard shows trends, insights, and what to do next.",
        category="profile",
        order=7,
        action_url="/dashboard",
    ),
]


@dataclass
class OnboardingState:
    user_id: str
    steps: list[TutorialStep] = field(default_factory=lambda: list(DEFAULT_STEPS))
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    @property
    def progress_pct(self) -> float:
        required = [s for s in self.steps if not s.optional]
        if not required:
            return 100.0
        done = sum(1 for s in required if s.completed)
        return round(done / len(required) * 100, 1)

    @property
    def current_step(self) -> Optional[TutorialStep]:
        for s in sorted(self.steps, key=lambda x: x.order):
            if not s.completed:
                return s
        return None

    @property
    def is_complete(self) -> bool:
        return all(s.completed for s in self.steps if not s.optional)

    def mark_complete(self, step_id: str) -> bool:
        for s in self.steps:
            if s.id == step_id:
                s.completed = True
                return True
        return False

    def skip_step(self, step_id: str) -> bool:
        for s in self.steps:
            if s.id == step_id and s.optional:
                s.completed = True
                return True
        return False

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "progress_pct": self.progress_pct,
            "is_complete": self.is_complete,
            "current_step": {
                "id": self.current_step.id,
                "title": self.current_step.title,
                "description": self.current_step.description,
                "action_url": self.current_step.action_url,
            } if self.current_step else None,
            "steps": [
                {
                    "id": s.id,
                    "title": s.title,
                    "description": s.description,
                    "category": s.category,
                    "order": s.order,
                    "optional": s.optional,
                    "completed": s.completed,
                    "action_url": s.action_url,
                }
                for s in sorted(self.steps, key=lambda x: x.order)
            ],
        }


# In-memory store (replace with DB in production)
_onboarding = durable_dict("app.services.onboarding._onboarding")


def get_onboarding(user_id: str) -> OnboardingState:
    if user_id not in _onboarding:
        _onboarding[user_id] = OnboardingState(user_id=user_id)
    return _onboarding[user_id]

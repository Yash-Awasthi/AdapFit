from typing import List, Optional, Dict, Any, Generic, TypeVar
from enum import Enum
from pydantic import BaseModel, Field

from app.core.health_validation import PHYSIOLOGICAL_RANGES

T = TypeVar('T')

class FitnessLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class PrimaryGoal(str, Enum):
    HYPERTROPHY = "hypertrophy"
    STRENGTH = "strength"
    ENDURANCE = "endurance"
    FAT_LOSS = "fat_loss"
    GENERAL_FITNESS = "general_fitness"

class ReadinessState(str, Enum):
    OPTIMAL = "OPTIMAL"
    MODERATE = "MODERATE"
    REDUCED = "REDUCED"
    DEPLETED = "DEPLETED"

class ACWRStatus(str, Enum):
    UNDER_TRAINING = "UNDER_TRAINING"
    SWEET_SPOT = "SWEET_SPOT"
    CAUTION = "CAUTION"
    DANGER_ZONE = "DANGER_ZONE"

# --- User & Baseline ---
class UserProfileCreate(BaseModel):
    email: str = Field(..., examples=["athlete@example.com"])
    name: Optional[str] = Field(None, examples=["Alex Johnson"])
    fitness_level: FitnessLevel = Field(FitnessLevel.INTERMEDIATE, examples=["intermediate"])
    primary_goal: PrimaryGoal = Field(PrimaryGoal.HYPERTROPHY, examples=["hypertrophy"])
    preferred_days_per_week: int = Field(4, ge=1, le=7, examples=[4])
    equipment_access: List[str] = Field(["bodyweight", "dumbbells", "barbell"], examples=[["bodyweight", "dumbbells", "barbell"]])
    health_connect_enabled: bool = Field(False, examples=[True])
    age: Optional[int] = Field(None, ge=13, le=100, examples=[28])
    gender: Optional[str] = Field(None, examples=["female"])
    height_cm: Optional[float] = Field(None, ge=100, le=250, examples=[175])
    work_start: Optional[str] = Field(None, examples=["09:00"])
    work_end: Optional[str] = Field(None, examples=["17:00"])

    model_config = {"json_schema_extra": {"examples": [{"email": "athlete@example.com", "name": "Alex Johnson", "fitness_level": "intermediate", "primary_goal": "hypertrophy"}]}}

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    fitness_level: Optional[FitnessLevel] = None
    primary_goal: Optional[PrimaryGoal] = None
    preferred_days_per_week: Optional[int] = Field(None, ge=1, le=7)
    equipment_access: Optional[List[str]] = None
    health_connect_enabled: Optional[bool] = None
    age: Optional[int] = Field(None, ge=13, le=100)
    gender: Optional[str] = None
    height_cm: Optional[float] = Field(None, ge=100, le=250)
    work_start: Optional[str] = None
    work_end: Optional[str] = None

class UserProfileResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    fitness_level: str
    primary_goal: str
    preferred_days_per_week: int
    equipment_access: List[str]
    created_at: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    work_start: Optional[str] = None
    work_end: Optional[str] = None

class UserBaseline(BaseModel):
    user_id: str
    hrv_mean_rmssd: float = 50.0
    hrv_std_rmssd: float = 10.0
    rhr_baseline: float = 65.0
    sleep_target_hours: float = 8.0
    chronic_load_28d: float = 500.0

# --- Telemetry & Ingestion ---
class WearableBiometrics(BaseModel):
    sleep_duration_hours: Optional[float] = Field(None, ge=PHYSIOLOGICAL_RANGES["sleep_duration_hours"][0], le=PHYSIOLOGICAL_RANGES["sleep_duration_hours"][1])
    sleep_efficiency_pct: Optional[float] = Field(None, ge=PHYSIOLOGICAL_RANGES["sleep_efficiency_pct"][0], le=PHYSIOLOGICAL_RANGES["sleep_efficiency_pct"][1])
    hrv_rmssd: Optional[float] = Field(None, ge=PHYSIOLOGICAL_RANGES["hrv_rmssd"][0], le=PHYSIOLOGICAL_RANGES["hrv_rmssd"][1])
    resting_heart_rate: Optional[int] = Field(None, ge=PHYSIOLOGICAL_RANGES["resting_heart_rate"][0], le=PHYSIOLOGICAL_RANGES["resting_heart_rate"][1])
    steps: Optional[int] = Field(None, ge=PHYSIOLOGICAL_RANGES["steps"][0], le=PHYSIOLOGICAL_RANGES["steps"][1])
    active_calories: Optional[float] = Field(None, ge=PHYSIOLOGICAL_RANGES["active_calories"][0], le=PHYSIOLOGICAL_RANGES["active_calories"][1])

class SubjectiveCheckin(BaseModel):
    soreness: int = Field(ge=1, le=10, description="1 (extremely sore) to 10 (fresh)")
    fatigue: int = Field(ge=1, le=10, description="1 (exhausted) to 10 (energized)")
    stress: int = Field(ge=1, le=10, description="1 (relaxed) to 10 (extreme stress)")
    sore_muscle_groups: List[str] = []
    pain_flagged: bool = False
    illness_flagged: bool = False

class RecoveryCalculationRequest(BaseModel):
    user_id: str = Field(..., examples=["user-123"])
    log_date: str = Field(..., examples=["2026-01-15"])
    wearable_data: Optional[WearableBiometrics] = Field(None, examples=[{"hrv_rmssd": 48, "sleep_duration_hours": 7.5, "sleep_efficiency_pct": 88}])
    subjective_checkin: Optional[SubjectiveCheckin] = Field(None, examples=[{"soreness": 7, "fatigue": 8, "stress": 3}])
    current_acute_load: Optional[float] = Field(None, examples=[520])
    current_chronic_load: Optional[float] = Field(None, examples=[500])

    model_config = {"json_schema_extra": {"examples": [{"user_id": "user-123", "log_date": "2026-01-15", "wearable_data": {"hrv_rmssd": 48, "sleep_duration_hours": 7.5}, "subjective_checkin": {"soreness": 7, "fatigue": 8, "stress": 3}, "current_acute_load": 520, "current_chronic_load": 500}]}}

class RecoveryMetricsBreakdown(BaseModel):
    hrv_z_score: Optional[float] = None
    sleep_score: float
    subjective_score: float
    acwr: Optional[float] = None
    acwr_status: ACWRStatus

class RecoveryCalculationResponse(BaseModel):
    recovery_score: int = Field(ge=0, le=100)
    readiness_state: ReadinessState
    metrics_breakdown: RecoveryMetricsBreakdown
    recommendation_directive: str
    ml_insights: Optional[Dict[str, Any]] = None
    agent_recommendations: Optional[Dict[str, Any]] = None
    injury_risk: Optional[Dict[str, Any]] = None

# --- Exercise & Workout ---
class ExerciseItem(BaseModel):
    id: str
    name: str
    category: str
    primary_muscles: List[str]
    secondary_muscles: List[str] = []
    equipment: str
    mechanic: Optional[str] = "compound"
    instructions: List[str] = []
    gif_url: Optional[str] = None
    axial_loading_rating: int = 1

class PrescribedExercise(BaseModel):
    exercise_id: str
    name: str
    target_muscle: str
    sets: int
    target_reps: str
    target_rpe: float
    rest_seconds: int
    gif_url: Optional[str] = None
    notes: Optional[str] = None

class WarmupCooldownItem(BaseModel):
    name: str
    duration_sec: Optional[int] = None
    reps: Optional[str] = None
    sets: Optional[int] = None

class WorkoutGenerateRequest(BaseModel):
    user_id: str
    target_date: str
    target_duration_minutes: int = 45
    override_focus_muscle: Optional[str] = None

class WorkoutGenerateResponse(BaseModel):
    workout_id: str
    title: str
    readiness_state: ReadinessState
    adaptation_rationale: str
    target_duration_minutes: int
    warmup: List[WarmupCooldownItem]
    exercises: List[PrescribedExercise]
    cooldown: List[WarmupCooldownItem]
    ml_insights: Optional[Dict[str, Any]] = None
    agent_memory_insights: Optional[Dict[str, Any]] = None

# --- Workout Logging & Feedback ---
class CompletedSet(BaseModel):
    set_number: int
    weight_kg: float
    reps_completed: int
    rpe: float

class CompletedExerciseLog(BaseModel):
    exercise_id: str
    name: str
    sets: List[CompletedSet]

class WorkoutCompleteRequest(BaseModel):
    user_id: str
    actual_duration_minutes: int
    session_rpe: int = Field(ge=1, le=10)
    logged_exercises: List[CompletedExerciseLog]
    user_feedback_notes: Optional[str] = None

class WorkoutCompleteResponse(BaseModel):
    log_id: str
    session_load: float
    acute_load_7d: float
    chronic_load_28d: float
    acwr: float
    acwr_status: ACWRStatus
    deload_recommended: bool
    message: str
    nlp_sentiment: Optional[Dict[str, Any]] = None
    injury_risk: Optional[Dict[str, Any]] = None

# --- Semantic Search ---
class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filter_equipment: Optional[List[str]] = None
    filter_muscles: Optional[List[str]] = None
    exclude_muscles: Optional[List[str]] = None

class ExerciseSubstitutionRequest(BaseModel):
    exercise_id: str
    top_k: int = 3
    exclude_muscles: Optional[List[str]] = None

# --- NLP ---
class NLPFeedbackRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    exercise_id: Optional[str] = None

class GoalParsingRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)

class SentimentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)

# --- Pagination ---
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int

# --- Errors ---
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    suggestion: Optional[str] = None

# --- Agent ---
class AgentInsightsResponse(BaseModel):
    personalization: Dict[str, Any]
    strategy_shift: Dict[str, Any]
    weekly_summary: Optional[str] = None

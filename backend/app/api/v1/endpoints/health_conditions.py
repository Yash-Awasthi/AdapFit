"""Health Conditions & Medication Tracker — enterprise-grade health profile.

Tracks: chronic conditions, medications, allergies, disabilities, physiotherapy plans,
fever/illness episodes, surgical history, and their impact on workout recommendations.

Every workout recommendation checks this profile before suggesting exercises.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()

# In-memory storage
_profiles: dict[str, dict] = {}  # user_id -> health profile
_medications: dict[str, list[dict]] = {}
_conditions: dict[str, list[dict]] = {}
_physio_plans: dict[str, list[dict]] = {}
_episodes: dict[str, list[dict]] = {}  # fever, illness episodes


# === ENUMS & CONSTANTS ===

CHRONIC_CONDITIONS = [
    "diabetes_type1", "diabetes_type2", "hypertension", "hypotension",
    "heart_disease", "heart_failure", "arrhythmia",
    "asthma", "copd", "pulmonary_fibrosis",
    "thyroid_hyper", "thyroid_hypo",  # hyperthyroidism, hypothyroidism
    "liver_disease", "liver_fatty", "liver_cirrhosis",
    "kidney_disease", "kidney_stones",
    "arthritis_rheumatoid", "arthritis_osteo", "ankylosing_spondylitis",
    "hernia_inguinal", "hernia_umbilical", "hernia_disc",
    "osteoporosis", "osteopenia",
    "fibromyalgia", "chronic_fatigue",
    "crohns", "ulcerative_colitis", "ibs",
    "pcos", "endometriosis",
    "epilepsy", "migraine_chronic",
    "sleep_apnea", "insomnia_chronic",
    "depression", "anxiety_disorder", "ptsd",
    "scoliosis", "kyphosis", "lordosis",
    "rotator_cuff_injury", "tennis_elbow", "plantar_fasciitis",
    "acl_reconstruction", "meniscus_tear", "disc_herniation_l4l5",
    "blood_clot_history", "dvt",
]

DISABILITY_TYPES = [
    "mobility_limited", "wheelchair_user", "amputee_upper", "amputee_lower",
    "visual_impairment", "blind", "hearing_impaired", "deaf",
    "cerebral_palsy", "spinal_cord_injury", "multiple_sclerosis",
    "muscular_dystrophy", "parkinsons", "stroke_aftermath",
    "chronic_pain", "joint_replacement_hip", "joint_replacement_knee",
]

MEDICATION_CATEGORIES = [
    "blood_pressure", "diabetes", "thyroid", "cholesterol",
    "anticoagulant", "painkiller", "anti_inflammatory",
    "antidepressant", "anxiety", "sleep_aid",
    "asthma_inhaler", "corticosteroid",
    "antibiotic", "antifungal",
    "supplement_vitamin", "supplement_mineral", "supplement_protein",
    "hormone", "contraceptive",
    "liver_support", "kidney_support",
    "muscle_relaxant", "nerve_pain",
]

FEVER_SEVERITY = ["mild_37_5", "moderate_38_39", "high_39_40", "severe_40plus"]


# === MODELS ===

class ConditionLog(BaseModel):
    condition_id: str = Field(..., description="Condition from CHRONIC_CONDITIONS or custom")
    diagnosed_date: Optional[str] = None
    severity: int = Field(ge=1, le=10, default=5)
    is_active: bool = True
    notes: str = Field(max_length=500, default="")
    doctor_name: Optional[str] = None
    next_checkup: Optional[str] = None


class MedicationLog(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    dosage: str = Field(min_length=1, max_length=50)
    frequency: str = Field(description="e.g., daily, twice_daily, as_needed, weekly")
    category: str = Field(default="other")
    time_of_day: list[str] = Field(default_factory=lambda: ["morning"])
    with_food: bool = False
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    side_effects: list[str] = Field(default_factory=list)
    interacts_with_exercise: bool = False
    exercise_notes: str = Field(max_length=300, default="")
    notes: str = Field(max_length=300, default="")


class PhysioPlan(BaseModel):
    condition_id: str
    exercise_name: str
    description: str
    sets: int = 3
    reps: str = "10"
    hold_seconds: Optional[int] = None
    frequency: str = "daily"
    contraindications: list[str] = Field(default_factory=list)
    pain_allowed: str = Field(default="mild", description="none, mild, moderate")


class EpisodeLog(BaseModel):
    episode_type: str  # fever, illness, flare_up, injury
    severity: int = Field(ge=1, le=10)
    start_date: str
    end_date: Optional[str] = None
    symptoms: list[str] = Field(default_factory=list)
    temperature_c: Optional[float] = None
    notes: str = Field(max_length=500, default="")


class AllergyLog(BaseModel):
    allergen: str
    severity: str = Field(default="mild", description="mild, moderate, severe, anaphylaxis")
    reaction: str = Field(max_length=200, default="")


# === EXERCISE RESTRICTIONS PER CONDITION ===

CONDITION_EXERCISE_RULES = {
    "hypertension": {
        "avoid": ["heavy_deadlift", "valsalva_maneuver", "overhead_heavy"],
        "modify": {"max_heart_rate_pct": 80, "no_isometric_holds": True},
        "recommend": ["walking", "swimming", "cycling", "yoga"],
    },
    "heart_disease": {
        "avoid": ["max_effort", "hiit", "heavy_compounds"],
        "modify": {"max_heart_rate_pct": 70, "required_warmup_minutes": 15},
        "recommend": ["walking", "light_cycling", "tai_chi", "gentle_yoga"],
    },
    "asthma": {
        "avoid": ["cold_air_outdoor", "high_intensity_sprints"],
        "modify": {"carry_inhaler": True, "extended_warmup": True},
        "recommend": ["swimming", "walking", "cycling", "yoga"],
    },
    "thyroid_hypo": {
        "avoid": ["extreme_endurance", "very_low_calorie_training"],
        "modify": {"monitor_energy_closely": True},
        "recommend": ["moderate_strength", "walking", "yoga"],
    },
    "thyroid_hyper": {
        "avoid": ["heavy_stimulants", "max_cardio"],
        "modify": {"monitor_heart_rate": True, "reduce_intensity": True},
        "recommend": ["gentle_strength", "walking", "meditation"],
    },
    "liver_disease": {
        "avoid": ["alcohol_based_supplements", "high_dose_acetaminophen", "heavy_oral_steroids"],
        "modify": {"consult_doctor_before_new_exercises": True},
        "recommend": ["walking", "light_yoga", "gentle_swimming"],
    },
    "hernia_disc": {
        "avoid": ["heavy_deadlift", "heavy_squat", "sit_ups", "toe_touches"],
        "modify": {"neutral_spine_only": True, "no_spinal_flexion_under_load": True},
        "recommend": ["bird_dog", "plank", "swimming", "walking", "mcgill_back_protocol"],
    },
    "arthritis_osteo": {
        "avoid": ["high_impact_running", "jumping", "deep_squats"],
        "modify": {"warm_water_exercises": True, "reduced_range_if_painful": True},
        "recommend": ["swimming", "water_aerobics", "gentle_yoga", "tai_chi"],
    },
    "diabetes_type2": {
        "avoid": ["fasting_workouts", "late_night_high_intensity"],
        "modify": {"monitor_blood_sugar": True, "carry_fast_carbs": True},
        "recommend": ["walking", "cycling", "resistance_training", "yoga"],
    },
    "fibromyalgia": {
        "avoid": ["high_intensity", "heavy_weights", "prolonged_cardio"],
        "modify": {"start_very_low", "increase_very_gradually", "prioritize_sleep"},
        "recommend": ["water_exercises", "gentle_yoga", "walking", "stretching"],
    },
    "sleep_apnea": {
        "avoid": ["supine_exercises_if_uncomfortable", "sedatives_before_sleep"],
        "modify": {"priority_sleep_hygiene": True},
        "recommend": ["aerobic_exercise", "position_training", "yoga"],
    },
    "pregnancy": {
        "avoid": ["contact_sports", "hot_yoga", "supine_after_20wks", "heavy_deadlift"],
        "modify": {"reduce_intensity": True, "monitor_temperature": True},
        "recommend": ["walking", "swimming", "prenatal_yoga", "light_weights"],
    },
    "parkinsons": {
        "avoid": ["balance_risky_exercises"],
        "modify": {"focus_balance_training": True, "cueing_for_gait": True},
        "recommend": ["tai_chi", "dance_therapy", "cycling", "walking", "balance_drills"],
    },
}

MEDICATION_EXERCISE_INTERACTIONS = {
    "beta_blocker": {"effect": "lower_max_hr", "adjustment": "use_perceived_exertion_not_hr"},
    "statin": {"effect": "muscle_pain_risk", "adjustment": "monitor_for_muscle_soreness"},
    "corticosteroid": {"effect": "weaken_tendons", "adjustment": "avoid_heavy_eccentrics"},
    "anticoagulant": {"effect": "bleeding_risk", "adjustment": "avoid_contact_high_fall_risk"},
    "antidepressant_ssri": {"effect": "fatigue_dizziness", "adjustment": "slower_progression"},
    "insulin": {"effect": "hypoglycemia_risk", "adjustment": "carry_glucose_be_ready"},
    "diuretic": {"effect": "dehydration_risk", "adjustment": "extra_hydration_monitor_electrolytes"},
    "muscle_relaxant": {"effect": "drowsiness_impaired_coordination", "adjustment": "no_heavy_machinery_or_barbell_overhead"},
    "painkiller_opioid": {"effect": "impaired_pain_perception", "adjustment": "very_reduced_load_do_not_push_through"},
    "thyroid_medication": {"effect": "heart_rate_changes", "adjustment": "monitor_rhr_titrate_exercise_gradually"},
}


# === ENDPOINTS ===

@router.post("/conditions")
async def log_condition(req: ConditionLog, user_id: str = Query("default")):
    record = {**req.model_dump(), "id": str(uuid.uuid4())[:12], "logged_at": datetime.now(timezone.utc).isoformat()}
    _conditions.setdefault(user_id, []).append(record)
    return {"logged": True, "record": record}


@router.get("/conditions")
async def get_conditions(user_id: str = Query("default")):
    return {"conditions": _conditions.get(user_id, [])}


@router.post("/medications")
async def log_medication(req: MedicationLog, user_id: str = Query("default")):
    record = {**req.model_dump(), "id": str(uuid.uuid4())[:12], "logged_at": datetime.now(timezone.utc).isoformat()}
    _medications.setdefault(user_id, []).append(record)

    # Check exercise interactions
    warnings = []
    for cat in MEDICATION_EXERCISE_INTERACTIONS:
        if cat in req.name.lower() or cat in req.category.lower():
            interaction = MEDICATION_EXERCISE_INTERACTIONS[cat]
            warnings.append({
                "medication": req.name,
                "effect": interaction["effect"],
                "adjustment": interaction["adjustment"],
            })

    return {"logged": True, "record": record, "exercise_warnings": warnings}


@router.get("/medications")
async def get_medications(user_id: str = Query("default")):
    return {"medications": _medications.get(user_id, [])}


@router.get("/medications/schedule")
async def get_medication_schedule(user_id: str = Query("default")):
    meds = _medications.get(user_id, [])
    schedule = {"morning": [], "afternoon": [], "evening": [], "night": []}
    for med in meds:
        for time_slot in med.get("time_of_day", []):
            if time_slot in schedule:
                schedule[time_slot].append({
                    "name": med["name"],
                    "dosage": med["dosage"],
                    "with_food": med.get("with_food", False),
                })
    return {"schedule": schedule, "total_medications": len(meds)}


@router.post("/episodes")
async def log_episode(req: EpisodeLog, user_id: str = Query("default")):
    record = {**req.model_dump(), "id": str(uuid.uuid4())[:12], "logged_at": datetime.now(timezone.utc).isoformat()}
    _episodes.setdefault(user_id, []).append(record)
    return {"logged": True, "record": record}


@router.get("/episodes")
async def get_episodes(user_id: str = Query("default"), days: int = Query(30, ge=1, le=365)):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    episodes = [e for e in _episodes.get(user_id, []) if e.get("start_date", "") >= cutoff[:10]]
    return {"episodes": episodes, "total": len(episodes)}


@router.get("/exercise-restrictions")
async def get_exercise_restrictions(user_id: str = Query("default")):
    conditions = _conditions.get(user_id, [])
    meds = _medications.get(user_id, [])

    restrictions = {"avoid": [], "modify": {}, "recommend": [], "warnings": []}

    for cond in conditions:
        cid = cond.get("condition_id", "")
        rules = CONDITION_EXERCISE_RULES.get(cid, {})
        if rules:
            restrictions["avoid"].extend(rules.get("avoid", []))
            restrictions["modify"].update(rules.get("modify", {}))
            restrictions["recommend"].extend(rules.get("recommend", []))
            restrictions["warnings"].append(f"Condition: {cid} — {cond.get('notes', 'No additional notes')}")

    for med in meds:
        for cat, interaction in MEDICATION_EXERCISE_INTERACTIONS.items():
            if cat in med.get("name", "").lower():
                restrictions["warnings"].append(
                    f"Medication: {med['name']} — {interaction['effect']}. "
                    f"Adjustment: {interaction['adjustment']}"
                )

    # Deduplicate
    restrictions["avoid"] = list(set(restrictions["avoid"]))
    restrictions["recommend"] = list(set(restrictions["recommend"]))

    return restrictions


@router.post("/physio")
async def log_physio_plan(req: PhysioPlan, user_id: str = Query("default")):
    record = {**req.model_dump(), "id": str(uuid.uuid4())[:12]}
    _physio_plans.setdefault(user_id, []).append(record)
    return {"logged": True, "record": record}


@router.get("/physio")
async def get_physio_plans(user_id: str = Query("default")):
    return {"plans": _physio_plans.get(user_id, [])}


@router.get("/profile-summary")
async def get_health_profile_summary(user_id: str = Query("default")):
    conditions = _conditions.get(user_id, [])
    meds = _medications.get(user_id, [])
    episodes = _episodes.get(user_id, [])
    physio = _physio_plans.get(user_id, [])

    active_conditions = [c for c in conditions if c.get("is_active", True)]
    active_meds = [m for m in meds if not m.get("end_date")]

    risk_level = "low"
    if len(active_conditions) >= 3:
        risk_level = "high"
    elif len(active_conditions) >= 1:
        risk_level = "moderate"

    recent_episodes = [e for e in episodes if e.get("start_date", "") >= (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()[:10]]

    return {
        "active_conditions": len(active_conditions),
        "active_medications": len(active_meds),
        "recent_episodes": len(recent_episodes),
        "physio_exercises": len(physio),
        "risk_level": risk_level,
        "conditions": [c["condition_id"] for c in active_conditions],
        "medications": [m["name"] for m in active_meds],
        "needs_doctor_clearance": risk_level == "high",
    }

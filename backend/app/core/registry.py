"""
Endpoint Auto-Discovery Registry

Scans app/api/v1/endpoints/ and auto-discovers routers.
Each endpoint module should export a `router` attribute.
Prefix and tags are looked up from ROUTE_MAP below.
"""
import importlib
import logging
import pkgutil
from pathlib import Path
from fastapi import FastAPI
from starlette.routing import compile_path

logger = logging.getLogger("adapfit.registry")


# Module name → (prefix, tags) mapping
# Modules not in this map get auto-generated prefix/tags from filename
ROUTE_MAP = {
    "decision": ("/decision", ["Daily Decision"]),
    "users": ("/users", ["Users"]),
    "recovery": ("/recovery-logs", ["Recovery Logs"]),
    "workouts": ("/workouts", ["Workouts"]),
    "exercises": ("/exercises", ["Exercises"]),
    "trends": ("/trends", ["Trends, ML & Agent"]),
    "chat": ("/chat", ["AI Coach"]),
    "mental_health": ("/mental-health", ["Mental Health"]),
    "achievements": ("/achievements", ["Achievements"]),
    "nutrition": ("/nutrition", ["Nutrition"]),
    "periodization": ("/periodization", ["Periodization"]),
    "sleep": ("/sleep", ["Sleep"]),
    "body_composition": ("/body", ["Body Composition"]),
    "progress_photos": ("/progress-photos", ["Progress Photos"]),
    "simulator": ("/simulator", ["Simulator"]),
    "tasks": ("/tasks", ["Background Tasks"]),
    "wearos": ("/wearable", ["Wearable Sync"]),
    "fitness_assessment": ("/fitness", ["Fitness Assessment"]),
    "music": ("/music", ["Workout Music"]),
    "notifications": ("/notifications", ["Notifications"]),
    "export": ("/export", ["Data Export"]),
    "community": ("/community", ["Community"]),
    "goals": ("/goals", ["Goals"]),
    "fitness_challenges": ("/challenges", ["Fitness Challenges"]),
    "hydration": ("/hydration", ["Hydration"]),
    "warmup_cooldown": ("/routine", ["Warmup/Cooldown"]),
    "nl_workout": ("/nl-workout", ["NL Workout Logging"]),
    "memory": ("/memory", ["Conversational Memory"]),
    "voice": ("/voice", ["Voice Workout Logging"]),
    "learning": ("/learning", ["Continuous Learning"]),
    "injury_risk": ("/injury-risk", ["Injury Risk Prediction"]),
    "meal_plan": ("/meal-plan", ["AI Meal Planning"]),
    "auto_scale": ("/workouts", ["Auto-Scaling"]),
    "ws_chat": ("/chat", ["WebSocket Chat"]),
    "metrics": ("/metrics", ["Observability"]),
    "auth": ("/auth", ["Authentication"]),
    "music_playlists": ("/music-playlists", ["Music Playlists"]),
    "challenges_ws": ("/challenges", ["Challenge WebSocket"]),
    "workout_stats": ("/workout-stats", ["Workout Stats"]),
    "hrv": ("/hrv", ["HRV"]),
    "training_api": ("/training", ["Training Analytics"]),
    "cycle_tracking": ("/cycle", ["Cycle Tracking"]),
    "form_check": ("/form-check", ["Form Check"]),
    "gps_tracking": ("/gps", ["GPS Tracking"]),
    "sensor_hub": ("/sensors", ["Sensor Hub"]),
    "health_conditions": ("/health", ["Health Conditions"]),
    "diet_logging": ("/diet", ["Diet Logging"]),
    "meditation_api": ("/meditation", ["Meditation"]),
    "voice_engine_api": ("/voice-engine", ["Voice Engine"]),
    "adaptive_workouts_api": ("/workouts/adaptive", ["Adaptive Workouts"]),
    "i18n_api": ("/i18n", ["Internationalization"]),
    "healthkit_api": ("/healthkit", ["HealthKit Bridge"]),
    "camera_vitals": ("/camera", ["Camera Vitals"]),
    "stress_management": ("/stress", ["Stress Management"]),
    "digital_wellbeing_api": ("/wellbeing", ["Digital Wellbeing"]),
    "location_tracking": ("/location", ["Location Tracking"]),
    "content_hub": ("/content", ["Content Hub"]),
    "wearable_api": ("/wearable", ["Wearable Import"]),
    "blood_pressure_api": ("/blood-pressure", ["Blood Pressure"]),
    "ws_camera": ("/camera-ws", ["Camera WebSocket"]),
    "medication_api": ("/medication", ["Medication Reminders"]),
    "emergency_api": ("/emergency", ["Emergency SOS"]),
    "workout_api": ("/workout-engine", ["Workout Engine"]),
    "ai_coach_api": ("/ai-coach", ["AI Health Coach"]),
    "wearable_realtime_api": ("/wearable-rt", ["Wearable Real-Time"]),
    "admin_api": ("/admin", ["Admin Dashboard"]),
    "telemedicine_api": ("/telemedicine", ["Telemedicine"]),
    "vital_signs_api": ("/vitals", ["Vital Signs"]),
    "calendar_api": ("/health-calendar", ["Health Calendar"]),
    "health_risk_api": ("/health-risk", ["Health Risk"]),
    "recipe_api": ("/recipes", ["AI Recipes"]),
    "habit_coach_api": ("/habits", ["AI Habit Coach"]),
    "symptom_checker_api": ("/symptoms", ["Symptom Checker"]),
    "posture_api": ("/posture", ["Posture Analysis"]),
    "circadian_api": ("/circadian", ["Circadian Rhythm"]),
    "respiratory_api": ("/respiratory", ["Respiratory Training"]),
    "skin_health_api": ("/skin", ["Skin Health"]),
    "diabetes_api": ("/diabetes", ["Diabetes Management"]),
    "rehab_api": ("/rehab", ["Physical Therapy"]),
    "voice_biomarker_api": ("/voice-biomarker", ["Voice Biomarker"]),
    "longevity_api": ("/longevity", ["Longevity"]),
    "ambient_health_api": ("/ambient", ["Ambient Health"]),
    "genomics_api": ("/genomics", ["Genomics"]),
    "fertility_api": ("/fertility", ["Fertility Tracking"]),
    "wound_care_api": ("/wound-care", ["Wound Care"]),
    "travel_health_api": ("/travel-health", ["Travel Health"]),
    "allergy_api": ("/allergies", ["Allergy Tracking"]),
    "cognitive_api": ("/cognitive", ["Cognitive Training"]),
    "pregnancy_api": ("/pregnancy", ["Pregnancy Tracking"]),
    "chronic_pain_api": ("/chronic-pain", ["Chronic Pain"]),
    "senior_health_api": ("/senior-health", ["Senior Health"]),
    "digital_detox_api": ("/digital-detox", ["Digital Detox"]),
    "sleep_audio_api": ("/sleep-audio", ["Sleep Audio"]),
    "environmental_api": ("/environmental", ["Environmental Health"]),
    "ergonomics_api": ("/ergonomics", ["Workplace Ergonomics"]),
    "cardiac_rehab_api": ("/cardiac-rehab", ["Cardiac Rehab"]),
    "screening_api": ("/screening", ["Preventive Screening"]),
    "drug_interactions_api": ("/drug-interactions", ["Drug Interactions"]),
    "hospital_finder_api": ("/hospitals", ["Hospital Finder"]),
    "peer_support_api": ("/peer-support", ["Peer Support"]),
    "stroke_rehab_api": ("/stroke-rehab", ["Stroke Rehab"]),
    "first_aid_api": ("/first-aid", ["First Aid"]),
    "medical_imaging_api": ("/medical-imaging", ["Medical Imaging"]),
    "remote_monitoring_api": ("/remote-monitoring", ["Remote Monitoring"]),
    "misinformation_api": ("/misinformation", ["Misinformation Detection"]),
    "substance_use_api": ("/substance-use", ["Substance Use"]),
    "vision_health_api": ("/vision", ["Vision Health"]),
    "chronic_disease_api": ("/chronic-disease", ["Chronic Disease"]),
    "notepad_api": ("/notepad", ["Health Notepad"]),
    "rate_limiter_api": ("/rate-limit", ["Rate Limiting"]),
    "biomarkers_api": ("/biomarkers", ["Biomarker Tracking"]),
    "biometrics_api": ("/biometrics", ["ECG & HRV Signal Processing"]),
    "rppg_api": ("/rppg", ["Remote Photoplethysmography"]),
    "sensor_api": ("/ble-sensors", ["BLE Sensor Integration"]),
    "moderation_api": ("/moderation", ["Moderation"]),
    "accessibility_api": ("/accessibility", ["Accessibility"]),
    "security_api": ("/security", ["Security"]),
    "health_passport_api": ("/passport", ["Health Passport"]),
    "health_savings_api": ("/health-savings", ["Health Savings"]),
    "precision_nutrition_api": ("/precision-nutrition", ["Precision Nutrition"]),
    "health_equity_api": ("/health-equity", ["Health Equity"]),
    "hospital_at_home_api": ("/hospital-at-home", ["Hospital at Home"]),
    "realtime_api": ("/realtime", ["Real-Time Monitoring"]),
    "encryption_api": ("/encryption", ["E2E Encryption"]),
    "government_schemes_api": ("/government-schemes", ["Government Schemes"]),
    "health_data_api": ("/health-data", ["Health Data"]),
    "family_network_api": ("/family-network", ["Family Network"]),
    "privacy_dashboard_api": ("/privacy", ["Privacy Dashboard"]),
}

# Prefixes to skip (these have special handling or are registered manually)
SKIP_PREFIXES = {"/metrics"}  # metrics is registered manually at root level in main.py


def _prefix_is_baked(router, prefix: str) -> bool:
    """True when every route path already carries `prefix`.

    A router declared as `APIRouter()` with the segment written into each path
    looks identical to a router with no prefix and relative paths. The two need
    opposite handling: the first must not have the generated prefix appended.
    """
    routes = [r for r in router.routes if getattr(r, "path", None)]
    if not routes:
        return False
    return all(r.path == prefix or r.path.startswith(prefix + "/") for r in routes)


def _strip_baked_prefix(router, baked_prefix: str) -> None:
    """Remove a router's own APIRouter(prefix=...) from each route's path.

    add_api_route bakes the router's prefix into route.path at decoration time,
    before register_endpoints ever sees the router. When the declared prefix
    (ROUTE_MAP) disagrees with that baked-in one, the baked one has to be
    stripped and the match regex recompiled, or it would still show up in the
    final path alongside the declared prefix.
    """
    for route in router.routes:
        path = getattr(route, "path", None)
        if path is None or not path.startswith(baked_prefix):
            continue
        route.path = path[len(baked_prefix):] or "/"
        route.path_regex, route.path_format, route.param_convertors = compile_path(route.path)


def register_endpoints(app: FastAPI, package_path: str = "app.api.v1.endpoints"):
    """Auto-discover and register all endpoint routers."""
    try:
        package = importlib.import_module(package_path)
    except ImportError:
        return {"registered": 0, "skipped": 0, "errors": 0}

    package_dir = Path(package.__file__).parent
    registered = 0
    skipped = 0
    errors = 0
    failures: list[tuple[str, str]] = []

    for _, module_name, is_pkg in pkgutil.iter_modules([str(package_dir)]):
        if is_pkg or module_name.startswith("_"):
            skipped += 1
            continue

        try:
            module = importlib.import_module(f"{package_path}.{module_name}")
            router = getattr(module, "router", None)

            if router is None:
                skipped += 1
                continue

            # Look up prefix and tags
            if module_name in ROUTE_MAP:
                prefix, tags = ROUTE_MAP[module_name]
            else:
                # Auto-generate from filename
                prefix = "/" + module_name.replace("_api", "").replace("_", "-")
                tags = [prefix.strip("/").replace("-", " ").title()]

            # Skip manually-registered prefixes
            if prefix in SKIP_PREFIXES:
                skipped += 1
                continue

            # Most modules declare their own APIRouter(prefix=...), which is
            # already baked into every route path — adding it again here would
            # double it. If a module's own prefix disagrees with the one
            # declared above, the declared one wins and the baked-in one is
            # stripped instead of being appended a second time.
            router_prefix = getattr(router, "prefix", "") or ""
            if router_prefix and router_prefix != prefix:
                _strip_baked_prefix(router, router_prefix)
                router_prefix = ""

            # A router with no declared prefix may still have the segment baked
            # into its paths; appending the generated prefix would double it.
            if not router_prefix and _prefix_is_baked(router, prefix):
                full_prefix = settings.API_V1_STR
            else:
                full_prefix = settings.API_V1_STR if router_prefix else f"{settings.API_V1_STR}{prefix}"

            app.include_router(router, prefix=full_prefix, tags=tags)
            registered += 1
        except Exception as e:
            # A module that cannot import used to disappear without a trace,
            # taking its endpoints with it and leaving the API looking healthy.
            errors += 1
            failures.append((module_name, f"{type(e).__name__}: {e}"))
            logger.error("Endpoint module %s failed to register: %s", module_name, e, exc_info=True)

    return {"registered": registered, "skipped": skipped, "errors": errors, "failures": failures}


# Lazy import for settings
from app.core.config import settings

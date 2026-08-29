"""
Endpoint Auto-Discovery Registry

Scans app/api/v1/endpoints/ and auto-discovers routers.
Each endpoint module should export a `router` attribute.
Prefix and tags are looked up from ROUTE_MAP below.
"""
import importlib
import pkgutil
from pathlib import Path
from fastapi import FastAPI


# Module name → (prefix, tags) mapping
# Modules not in this map get auto-generated prefix/tags from filename
ROUTE_MAP = {
    "users": ("/users", ["Users"]),
    "recovery": ("/recovery-logs", ["Recovery Logs"]),
    "workouts": ("/workouts", ["Workouts"]),
    "exercises": ("/exercises", ["Exercises"]),
    "trends": ("/trends", ["Trends, ML & Agent"]),
    "chat": ("/chat", ["AI Coach"]),
    "mental_health": ("/mental-health", ["Mental Health"]),
    "achievements": ("/achievements", ["Achievements"]),
    "social": ("/social", ["Social"]),
    "nutrition": ("/nutrition", ["Nutrition"]),
    "periodization": ("/periodization", ["Periodization"]),
    "sleep": ("/sleep", ["Sleep"]),
    "body_composition": ("/body", ["Body Composition"]),
    "progress_photos": ("/progress-photos", ["Progress Photos"]),
    "simulator": ("/simulator", ["Simulator"]),
    "tasks": ("/tasks", ["Background Tasks"]),
    "wearos": ("/wearable", ["Wearable Sync"]),
    "streaks": ("/streaks", ["Streaks"]),
    "fitness_assessment": ("/fitness", ["Fitness Assessment"]),
    "music": ("/music", ["Workout Music"]),
    "notifications": ("/notifications", ["Notifications"]),
    "export": ("/export", ["Data Export"]),
    "workout_analytics": ("/analytics", ["Workout Analytics"]),
    "workout_templates": ("/templates", ["Workout Templates"]),
    "community": ("/community", ["Community"]),
    "goals": ("/goals", ["Goals"]),
    "fitness_challenges": ("/challenges", ["Fitness Challenges"]),
    "workout_import_export": ("/plan", ["Workout Import/Export"]),
    "recommendations": ("/recommend", ["Smart Recommendations"]),
    "body_dashboard": ("/dashboard", ["Body Dashboard"]),
    "workout_timer": ("/timer", ["Workout Timer"]),
    "training_calendar": ("/calendar", ["Training Calendar"]),
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
    "sleep_analysis": ("/sleep-analysis", ["Sleep Analysis"]),
    "music_playlists": ("/music-playlists", ["Music Playlists"]),
    "challenges_ws": ("/challenges", ["Challenge WebSocket"]),
    "quick_workout": ("/quick-workout", ["Quick Workouts"]),
    "exercise_subs": ("/exercise-subs", ["Exercise Substitutions"]),
    "breathing": ("/breathing", ["Breathing Exercises"]),
    "workout_stats": ("/workout-stats", ["Workout Stats"]),
    "achievements_v2": ("/achievements-v2", ["Achievements V2"]),
    "qr_share": ("/qr-share", ["QR Share"]),
    "exercise_library": ("/exercise-library", ["Exercise Library"]),
    "activity_feed": ("/activity-feed", ["Activity Feed"]),
    "photo_compare": ("/photo-compare", ["Photo Comparison"]),
    "hrv_trends": ("/hrv-trends", ["HRV Trends"]),
    "workout_compare": ("/workout-compare", ["Workout Comparison"]),
    "body_trends": ("/body-trends", ["Body Trends"]),
    "personal_bests": ("/personal-bests", ["Personal Bests"]),
    "daily_checkin": ("/daily-checkin", ["Daily Check-in"]),
    "cycle_tracking": ("/cycle", ["Cycle Tracking"]),
    "form_check": ("/form-check", ["Form Check"]),
    "gps_tracking": ("/gps", ["GPS Tracking"]),
    "sensor_hub": ("/sensors", ["Sensor Hub"]),
    "workout_rooms": ("/rooms", ["Workout Rooms"]),
    "health_conditions": ("/health", ["Health Conditions"]),
    "diet_logging": ("/diet", ["Diet Logging"]),
    "schedule": ("/schedule", ["Schedule"]),
    "meditation_api": ("/meditation", ["Meditation"]),
    "voice_engine_api": ("/voice-engine", ["Voice Engine"]),
    "camera_vitals": ("/camera", ["Camera Vitals"]),
    "stress_management": ("/stress", ["Stress Management"]),
    "digital_wellbeing_api": ("/wellbeing", ["Digital Wellbeing"]),
    "location_tracking": ("/location", ["Location Tracking"]),
    "content_hub": ("/content", ["Content Hub"]),
    "personalization_api": ("/personalize", ["Personalization"]),
    "sleep_tracking_api": ("/sleep-tracking", ["Sleep Tracking"]),
    "nutrition_api": ("/nutrition-logging", ["Nutrition Logging"]),
    "health_goals_api": ("/health-goals", ["Health Goals"]),
    "health_summary": ("/summary", ["Health Summary"]),
    "ws_camera": ("/camera-ws", ["Camera WebSocket"]),
    "health_analytics_api": ("/health-analytics", ["Health Analytics"]),
    "medication_api": ("/medication", ["Medication Reminders"]),
    "emergency_api": ("/emergency", ["Emergency SOS"]),
    "data_export_api": ("/data-export", ["Data Export"]),
    "mental_health_api": ("/clinical", ["Clinical Assessments"]),
    "community_api": ("/community-challenges", ["Community Challenges"]),
    "workout_api": ("/workout-engine", ["Workout Engine"]),
    "device_sync_api": ("/device-sync", ["Device Sync"]),
    "ai_coach_api": ("/ai-coach", ["AI Health Coach"]),
    "body_health_api": ("/body-health", ["Body Health"]),
    "wearable_realtime_api": ("/wearable-rt", ["Wearable Real-Time"]),
    "health_rewards_api": ("/rewards", ["Health Rewards"]),
    "notifications_api": ("/push-notifications", ["Push Notifications"]),
    "auth_api": ("/auth-v2", ["User Authentication"]),
    "admin_api": ("/admin", ["Admin Dashboard"]),
    "telemedicine_api": ("/telemedicine", ["Telemedicine"]),
    "forums_api": ("/forums", ["Community Forums"]),
    "analytics_dashboard_api": ("/analytics-dashboard", ["Analytics Dashboard"]),
    "vital_signs_api": ("/vitals", ["Vital Signs"]),
    "gamification_api": ("/gamification", ["Gamification"]),
    "family_api": ("/family", ["Family"]),
    "calendar_api": ("/health-calendar", ["Health Calendar"]),
    "health_risk_api": ("/risk", ["Health Risk"]),
    "voice_api": ("/voice-assistant", ["Voice Assistant"]),
    "recipe_api": ("/recipes", ["AI Recipes"]),
    "social_api": ("/social-share", ["Social Sharing"]),
    "habit_coach_api": ("/habits", ["AI Habit Coach"]),
    "symptom_checker_api": ("/symptoms", ["Symptom Checker"]),
    "corporate_api": ("/corporate", ["Corporate Health"]),
    "posture_api": ("/posture", ["Posture Analysis"]),
    "circadian_api": ("/circadian", ["Circadian Rhythm"]),
    "respiratory_api": ("/respiratory", ["Respiratory Training"]),
    "skin_health_api": ("/skin", ["Skin Health"]),
    "diabetes_api": ("/diabetes", ["Diabetes Management"]),
    "meditation_api_v2": ("/meditation-v2", ["Mindfulness"]),
    "rehab_api": ("/rehab", ["Physical Therapy"]),
    "voice_biomarker_api": ("/voice-biomarker", ["Voice Biomarker"]),
    "longevity_api": ("/longevity", ["Longevity"]),
    "ambient_health_api": ("/ambient", ["Ambient Health"]),
    "genomics_api": ("/genomics", ["Genomics"]),
    "fertility_api": ("/fertility", ["Fertility Tracking"]),
    "wound_care_api": ("/wound-care", ["Wound Care"]),
    "travel_health_api": ("/travel-health", ["Travel Health"]),
    "allergy_api": ("/allergies", ["Allergy Tracking"]),
    "recovery_api": ("/recovery-v1", ["Recovery"]),
    "cognitive_api": ("/cognitive", ["Cognitive Training"]),
    "pregnancy_api": ("/pregnancy", ["Pregnancy Tracking"]),
    "chronic_pain_api": ("/chronic-pain", ["Chronic Pain"]),
    "senior_health_api": ("/senior-health", ["Senior Health"]),
    "digital_detox_api": ("/digital-detox", ["Digital Detox"]),
    "sleep_audio_api": ("/sleep-audio", ["Sleep Audio"]),
    "medical_id_api": ("/medical-id", ["Medical ID"]),
    "environmental_api": ("/environmental", ["Environmental Health"]),
    "ergonomics_api": ("/ergonomics", ["Workplace Ergonomics"]),
    "digital_twin_api": ("/digital-twin", ["Digital Twin"]),
    "voice_diary_api": ("/voice-diary", ["Voice Diary"]),
    "cardiac_rehab_api": ("/cardiac-rehab", ["Cardiac Rehab"]),
    "screening_api": ("/screening", ["Preventive Screening"]),
    "ai_coach_v2_api": ("/ai-coach-v2", ["AI Coach V2"]),
    "ar_fitness_api": ("/ar-fitness", ["AR Fitness"]),
    "blockchain_records_api": ("/health-records", ["Blockchain Records"]),
    "microbiome_api": ("/microbiome", ["Microbiome"]),
    "ecg_api": ("/ecg", ["ECG Interpretation"]),
    "drug_interactions_api": ("/drug-interactions", ["Drug Interactions"]),
    "clinical_trials_api": ("/clinical-trials", ["Clinical Trials"]),
    "insurance_api": ("/insurance", ["Insurance"]),
    "hospital_finder_api": ("/hospitals", ["Hospital Finder"]),
    "health_education_api": ("/health-education", ["Health Education"]),
    "peer_support_api": ("/peer-support", ["Peer Support"]),
    "ai_companion_api": ("/ai-companion", ["AI Companion"]),
    "meal_delivery_api": ("/meal-delivery", ["Meal Delivery"]),
    "gym_integration_api": ("/gym", ["Gym Integration"]),
    "health_coaching_api": ("/health-coaching", ["Health Coaching"]),
    "stroke_rehab_api": ("/stroke-rehab", ["Stroke Rehab"]),
    "nutrigenomics_api": ("/nutrigenomics", ["Nutrigenomics"]),
    "first_aid_api": ("/first-aid", ["First Aid"]),
    "food_scanner_api": ("/food-scanner", ["Food Scanner"]),
    "medical_imaging_api": ("/medical-imaging", ["Medical Imaging"]),
    "personalized_medicine_api": ("/personalized-medicine", ["Personalized Medicine"]),
    "remote_monitoring_api": ("/remote-monitoring", ["Remote Monitoring"]),
    "sdoh_api": ("/sdoh", ["Social Determinants"]),
    "generative_wellness_api": ("/wellness-ai", ["AI Wellness"]),
    "misinformation_api": ("/misinformation", ["Misinformation Detection"]),
    "workplace_safety_api": ("/workplace-safety", ["Workplace Safety"]),
    "substance_use_api": ("/substance-use", ["Substance Use"]),
    "vision_health_api": ("/vision", ["Vision Health"]),
    "predictive_health_api": ("/predictive-health", ["Predictive Health"]),
    "chronic_disease_api": ("/chronic-disease", ["Chronic Disease"]),
    "health_aggregator_api": ("/health-score", ["Health Score"]),
    "health_gateway_api": ("/gateway", ["API Gateway"]),
    "ai_assistant_api": ("/ai-assistant", ["AI Assistant"]),
    "notepad_api": ("/notepad", ["Health Notepad"]),
    "biometric_unlock_api": ("/data-sharing", ["Data Sharing"]),
    "wellness_hub_api": ("/wellness-hub", ["Wellness Hub"]),
    "health_trends_api": ("/health-trends", ["Health Trends"]),
    "rate_limiter_api": ("/rate-limit", ["Rate Limiting"]),
    "export_v2_api": ("/export-v2", ["Export V2"]),
    "integrations_api": ("/integrations", ["Integrations"]),
    "recommendations_v2_api": ("/recommendations-v2", ["Recommendations V2"]),
    "community_v2_api": ("/community-v2", ["Community V2"]),
    "moderation_api": ("/moderation", ["Moderation"]),
    "accessibility_api": ("/accessibility", ["Accessibility"]),
    "security_api": ("/security", ["Security"]),
    "digital_therapeutics_api": ("/dtx", ["Digital Therapeutics"]),
    "health_passport_api": ("/passport", ["Health Passport"]),
    "health_savings_api": ("/health-savings", ["Health Savings"]),
    "precision_nutrition_api": ("/precision-nutrition", ["Precision Nutrition"]),
    "health_equity_api": ("/health-equity", ["Health Equity"]),
    "hospital_at_home_api": ("/hospital-at-home", ["Hospital at Home"]),
    "ai_insights_api": ("/ai-insights", ["AI Insights"]),
    "realtime_api": ("/realtime", ["Real-Time Monitoring"]),
    "encryption_api": ("/encryption", ["E2E Encryption"]),
    "health_recommendations_api": ("/health-recommendations", ["Health Recommendations"]),
    "health_action_api": ("/health-action", ["Health Action"]),
    "government_schemes_api": ("/government-schemes", ["Government Schemes"]),
    "health_data_api": ("/health-data", ["Health Data"]),
    "family_network_api": ("/family-network", ["Family Network"]),
    "health_news_api": ("/health-news", ["Health News"]),
    "healthcare_providers_api": ("/providers", ["Healthcare Providers"]),
    "recovery_v2_api": ("/recovery-v2", ["Recovery V2"]),
    "privacy_dashboard_api": ("/privacy", ["Privacy Dashboard"]),
}

# Prefixes to skip (these have special handling or are registered manually)
SKIP_PREFIXES = {"/metrics"}  # metrics uses a different prefix pattern


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
                # Apply API_V1_STR prefix
                full_prefix = f"{settings.API_V1_STR}{prefix}"
            else:
                # Auto-generate from filename
                prefix = module_name.replace("_api", "").replace("_", "-")
                full_prefix = f"{settings.API_V1_STR}/{prefix}"
                tags = [prefix.replace("-", " ").title()]

            # Skip manually-registered prefixes
            if prefix in SKIP_PREFIXES:
                skipped += 1
                continue

            app.include_router(router, prefix=full_prefix, tags=tags)
            registered += 1
        except Exception as e:
            errors += 1

    return {"registered": registered, "skipped": skipped, "errors": errors}


# Lazy import for settings
from app.core.config import settings

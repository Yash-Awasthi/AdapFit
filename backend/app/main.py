import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pathlib import Path
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.api.v1.endpoints import recovery, workouts, exercises, trends, users, chat, mental_health, achievements, social, nutrition, periodization, sleep, body_composition, progress_photos, simulator, tasks, wearos, streaks, fitness_assessment, music, notifications, export, workout_analytics, workout_templates, community, goals, fitness_challenges, workout_import_export, recommendations, body_dashboard, workout_timer, training_calendar, hydration, warmup_cooldown, nl_workout, memory, voice, learning, injury_risk, meal_plan, auto_scale, ws_chat
from app.core.logging_config import setup_logging, get_logger
from app.core.error_handlers import ErrorHandlingMiddleware
from app.core.metrics import MetricsMiddleware
from app.api.v1.endpoints import metrics as metrics_endpoint
from app.api.v1.endpoints import auth as auth_endpoint
from app.api.v1.endpoints import sleep_analysis
from app.api.v1.endpoints import music_playlists
from app.api.v1.endpoints import challenges_ws
from app.api.v1.endpoints import quick_workout
from app.api.v1.endpoints import exercise_subs
from app.api.v1.endpoints import breathing
from app.api.v1.endpoints import workout_stats
from app.api.v1.endpoints import achievements_v2
from app.api.v1.endpoints import qr_share
from app.api.v1.endpoints import exercise_library
from app.api.v1.endpoints import activity_feed
from app.api.v1.endpoints import photo_compare
from app.api.v1.endpoints import hrv_trends
from app.api.v1.endpoints import workout_compare
from app.api.v1.endpoints import body_trends
from app.api.v1.endpoints import personal_bests
from app.api.v1.endpoints import daily_checkin
from app.api.v1.endpoints import cycle_tracking
from app.api.v1.endpoints import form_check
from app.api.v1.endpoints import gps_tracking
from app.api.v1.endpoints import sensor_hub
from app.api.v1.endpoints import workout_rooms
from app.api.v1.endpoints import health_conditions
from app.api.v1.endpoints import diet_logging
from app.api.v1.endpoints import schedule
from app.api.v1.endpoints import meditation_api
from app.api.v1.endpoints import voice_engine_api

setup_logging()
logger = get_logger("adapfit.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AdapFit starting up...")
    try:
        from app.services.exercise_service import exercise_service
        from app.services.vector_store import vector_store
        vector_store.initialize([ex.model_dump() for ex in exercise_service.get_all()])
        logger.info("Vector store initialized")
    except Exception as e:
        logger.warning(f"Vector store init failed: {e}")
    yield
    logger.info("AdapFit shutting down")


# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
## AdapFit: AI-Powered Adaptive Fitness & Recovery Engine

AdapFit listens to your body's biometrics — HRV, sleep, subjective wellness, and training load — then generates personalized workouts that adapt in real-time.

### Features
- **Recovery Engine**: HRV Z-Score, Hooper-Mackinnon matrix, ACWR workload ratio
- **AI Workout Generation**: Gemini 2.0 Flash + rule-based fallback
- **ML Analytics**: PyTorch neural networks, XGBoost, anomaly detection
- **NLP Pipeline**: Sentiment analysis, goal parsing, pain detection
- **AI Coach**: Context-aware fitness chat
- **Mental Health**: Mood tracking, breathing exercises
- **Achievements**: Gamification with badges and streaks

### Quick Start
```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# Mobile
cd mobile && npm install && npx expo start
```

### API Key
Optional — set `GEMINI_API_KEY` for AI features. Works without it via rule-based fallbacks.
""",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - restrict to known origins in production
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8081",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8081",
]
app.add_middleware(MetricsMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID + API version middleware for tracing
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-API-Version"] = settings.VERSION
    return response

# Static dashboard
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# API Routers
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(recovery.router, prefix=f"{settings.API_V1_STR}/recovery-logs", tags=["Recovery Logs"])
app.include_router(workouts.router, prefix=f"{settings.API_V1_STR}/workouts", tags=["Workouts"])
app.include_router(exercises.router, prefix=f"{settings.API_V1_STR}/exercises", tags=["Exercises"])
app.include_router(trends.router, prefix=f"{settings.API_V1_STR}/trends", tags=["Trends, ML & Agent"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["AI Coach"])
app.include_router(mental_health.router, prefix=f"{settings.API_V1_STR}/mental-health", tags=["Mental Health"])
app.include_router(achievements.router, prefix=f"{settings.API_V1_STR}/achievements", tags=["Achievements"])
app.include_router(social.router, prefix=f"{settings.API_V1_STR}/social", tags=["Social"])
app.include_router(nutrition.router, prefix=f"{settings.API_V1_STR}/nutrition", tags=["Nutrition"])
app.include_router(periodization.router, prefix=f"{settings.API_V1_STR}/periodization", tags=["Periodization"])
app.include_router(sleep.router, prefix=f"{settings.API_V1_STR}/sleep", tags=["Sleep"])
app.include_router(body_composition.router, prefix=f"{settings.API_V1_STR}/body", tags=["Body Composition"])
app.include_router(progress_photos.router, prefix=f"{settings.API_V1_STR}/progress-photos", tags=["Progress Photos"])
app.include_router(simulator.router, prefix=f"{settings.API_V1_STR}/simulator", tags=["Simulator"])
app.include_router(tasks.router, prefix=f"{settings.API_V1_STR}/tasks", tags=["Background Tasks"])
app.include_router(wearos.router, prefix=f"{settings.API_V1_STR}/wearable", tags=["Wearable Sync"])
app.include_router(streaks.router, prefix=f"{settings.API_V1_STR}/streaks", tags=["Streaks"])
app.include_router(fitness_assessment.router, prefix=f"{settings.API_V1_STR}/fitness", tags=["Fitness Assessment"])
app.include_router(music.router, prefix=f"{settings.API_V1_STR}/music", tags=["Workout Music"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["Notifications"])
app.include_router(export.router, prefix=f"{settings.API_V1_STR}/export", tags=["Data Export"])
app.include_router(workout_analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["Workout Analytics"])
app.include_router(workout_templates.router, prefix=f"{settings.API_V1_STR}/templates", tags=["Workout Templates"])
app.include_router(community.router, prefix=f"{settings.API_V1_STR}/community", tags=["Community"])
app.include_router(goals.router, prefix=f"{settings.API_V1_STR}/goals", tags=["Goals"])
app.include_router(fitness_challenges.router, prefix=f"{settings.API_V1_STR}/challenges", tags=["Fitness Challenges"])
app.include_router(workout_import_export.router, prefix=f"{settings.API_V1_STR}/plan", tags=["Workout Import/Export"])
app.include_router(recommendations.router, prefix=f"{settings.API_V1_STR}/recommend", tags=["Smart Recommendations"])
app.include_router(body_dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["Body Dashboard"])
app.include_router(workout_timer.router, prefix=f"{settings.API_V1_STR}/timer", tags=["Workout Timer"])
app.include_router(training_calendar.router, prefix=f"{settings.API_V1_STR}/calendar", tags=["Training Calendar"])
app.include_router(hydration.router, prefix=f"{settings.API_V1_STR}/hydration", tags=["Hydration"])
app.include_router(warmup_cooldown.router, prefix=f"{settings.API_V1_STR}/routine", tags=["Warmup/Cooldown"])
app.include_router(nl_workout.router, prefix=f"{settings.API_V1_STR}/nl-workout", tags=["NL Workout Logging"])
app.include_router(memory.router, prefix=f"{settings.API_V1_STR}/memory", tags=["Conversational Memory"])
app.include_router(voice.router, prefix=f"{settings.API_V1_STR}/voice", tags=["Voice Workout Logging"])
app.include_router(learning.router, prefix=f"{settings.API_V1_STR}/learning", tags=["Continuous Learning"])
app.include_router(injury_risk.router, prefix=f"{settings.API_V1_STR}/injury-risk", tags=["Injury Risk Prediction"])
app.include_router(meal_plan.router, prefix=f"{settings.API_V1_STR}/meal-plan", tags=["AI Meal Planning"])
app.include_router(auto_scale.router, prefix=f"{settings.API_V1_STR}/workouts", tags=["Auto-Scaling"])
app.include_router(ws_chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["WebSocket Chat"])
app.include_router(metrics_endpoint.router, prefix="/metrics", tags=["Observability"])
app.include_router(auth_endpoint.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(sleep_analysis.router, prefix=f"{settings.API_V1_STR}/sleep-analysis", tags=["Sleep Analysis"])
app.include_router(music_playlists.router, prefix=f"{settings.API_V1_STR}/music-playlists", tags=["Music Playlists"])
app.include_router(challenges_ws.router, prefix=f"{settings.API_V1_STR}/challenges", tags=["Challenge WebSocket"])
app.include_router(quick_workout.router, prefix=f"{settings.API_V1_STR}/quick-workout", tags=["Quick Workouts"])
app.include_router(exercise_subs.router, prefix=f"{settings.API_V1_STR}/exercise-subs", tags=["Exercise Substitutions"])
app.include_router(breathing.router, prefix=f"{settings.API_V1_STR}/breathing", tags=["Breathing Exercises"])
app.include_router(workout_stats.router, prefix=f"{settings.API_V1_STR}/workout-stats", tags=["Workout Stats"])
app.include_router(achievements_v2.router, prefix=f"{settings.API_V1_STR}/achievements-v2", tags=["Achievements V2"])
app.include_router(qr_share.router, prefix=f"{settings.API_V1_STR}/qr-share", tags=["QR Share"])
app.include_router(exercise_library.router, prefix=f"{settings.API_V1_STR}/exercise-library", tags=["Exercise Library"])
app.include_router(activity_feed.router, prefix=f"{settings.API_V1_STR}/activity-feed", tags=["Activity Feed"])
app.include_router(photo_compare.router, prefix=f"{settings.API_V1_STR}/photo-compare", tags=["Photo Comparison"])
app.include_router(hrv_trends.router, prefix=f"{settings.API_V1_STR}/hrv-trends", tags=["HRV Trends"])
app.include_router(workout_compare.router, prefix=f"{settings.API_V1_STR}/workout-compare", tags=["Workout Comparison"])
app.include_router(body_trends.router, prefix=f"{settings.API_V1_STR}/body-trends", tags=["Body Trends"])
app.include_router(personal_bests.router, prefix=f"{settings.API_V1_STR}/personal-bests", tags=["Personal Bests"])
app.include_router(daily_checkin.router, prefix=f"{settings.API_V1_STR}/daily-checkin", tags=["Daily Check-in"])
app.include_router(cycle_tracking.router, prefix=f"{settings.API_V1_STR}/cycle", tags=["Cycle Tracking"])
app.include_router(form_check.router, prefix=f"{settings.API_V1_STR}/form-check", tags=["Form Check"])
app.include_router(gps_tracking.router, prefix=f"{settings.API_V1_STR}/gps", tags=["GPS Tracking"])
app.include_router(sensor_hub.router, prefix=f"{settings.API_V1_STR}/sensors", tags=["Sensor Hub"])
app.include_router(workout_rooms.router, prefix=f"{settings.API_V1_STR}/rooms", tags=["Workout Rooms"])
app.include_router(health_conditions.router, prefix=f"{settings.API_V1_STR}/health", tags=["Health Conditions"])
app.include_router(diet_logging.router, prefix=f"{settings.API_V1_STR}/diet", tags=["Diet Logging"])
app.include_router(schedule.router, prefix=f"{settings.API_V1_STR}/schedule", tags=["Schedule"])
app.include_router(meditation_api.router, prefix=f"{settings.API_V1_STR}/meditation", tags=["Meditation"])
app.include_router(voice_engine_api.router, prefix=f"{settings.API_V1_STR}/voice-engine", tags=["Voice Engine"])


@app.get("/")
async def root():
    return {"app": settings.PROJECT_NAME, "version": settings.VERSION, "status": "healthy", "docs": "/docs"}


@app.get("/health")
@limiter.limit("30/minute")
async def health(request: Request):
    from app.core.storage import storage
    stats = await storage.get_stats()
    services = {}
    # Check each service
    for name, getter in [
        ("ml_engine", lambda: __import__("app.services.ml_engine", fromlist=["ml_engine"]).ml_engine.get_status()),
        ("nlp_pipeline", lambda: __import__("app.services.nlp_pipeline", fromlist=["nlp_pipeline"]).nlp_pipeline.get_status()),
        ("spark", lambda: __import__("app.services.spark_processor", fromlist=["spark_analytics"]).spark_analytics.get_status()),
        ("vector_store", lambda: __import__("app.services.vector_store", fromlist=["vector_store"]).vector_store.get_status()),
    ]:
        try:
            services[name] = getter()
        except Exception:
            services[name] = {"status": "unavailable"}
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "api_version": settings.VERSION,
        "storage": stats,
        "services": services,
    }


@app.get("/dashboard")
async def dashboard():
    """Serve the interactive dashboard."""
    from fastapi.responses import FileResponse
    return FileResponse(str(Path(__file__).parent / "static" / "index.html"))


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """Real-time WebSocket for push notifications."""
    from app.services.websocket_manager import ws_manager
    await ws_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)

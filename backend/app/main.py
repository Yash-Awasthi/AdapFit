"""
AdapFit — AI-Powered Adaptive Fitness & Recovery Engine

Entry point. Endpoint routers are auto-discovered by app/core/registry.py.
Add a new endpoint: drop a file in app/api/v1/endpoints/, export `router`.
"""
import sys
from pathlib import Path as _Path
# Ensure the ZFIT project root is on sys.path so that `src.*` modules
# (achievements, anomaly, biometrics, etc.) are importable from services.
_zfit_root = str(_Path(__file__).resolve().parent.parent.parent)
if _zfit_root not in sys.path:
    sys.path.insert(0, _zfit_root)

import uuid
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
from slowapi.errors import RateLimitExceeded
from app.core.limiter import make_limiter

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.core.error_handlers import ErrorHandlingMiddleware
from app.core.metrics import MetricsMiddleware
from app.core.validation import ValidationMiddleware
from app.core.compression import CompressionMiddleware
from app.middleware.security import SecurityHeadersMiddleware, InputSanitizationMiddleware, RequestLoggingMiddleware
from app.middleware.auth import AuthMiddleware

setup_logging()
logger = get_logger("adapfit.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AdapFit starting up...")
    # ── Startup config validation ─────────────────────────────────────────
    # Fails fast in production if critical settings (JWT, DB, LLM keys) are
    # missing or insecure. In dev, logs warnings but continues.
    try:
        from app.core.startup_checks import run_startup_checks
        run_startup_checks()
    except SystemExit:
        raise  # production fail-fast
    except Exception as e:
        logger.warning(f"Startup checks failed to run: {e}")
    # ── Load accounts ─────────────────────────────────────────────────────
    # A failure here means nobody can log in, so it stops startup rather than
    # leaving the API up and answering every login with "invalid credentials".
    from app.core.auth import user_manager
    await user_manager.load()
    logger.info("Accounts loaded: %d", len(user_manager._users))
    # ── Restore feature data ──────────────────────────────────────────────
    # Same rule as accounts: serving requests on empty state would save it over the real data.
    from app.core import durable
    logger.info("Feature state restored: %s", await durable.load_all())
    # ── Initialize services ───────────────────────────────────────────────
    try:
        from app.services.exercise_service import exercise_service
        from app.services.vector_store import vector_store
        vector_store.initialize([ex.model_dump() for ex in exercise_service.get_all()])
        logger.info("Vector store initialized")
    except Exception as e:
        logger.warning(f"Vector store init failed: {e}")
    yield
    await durable.flush()
    logger.info("AdapFit shutting down")


# Rate limiter
limiter = make_limiter()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AdapFit: AI-Powered Adaptive Fitness & Recovery Engine",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)
app.state.limiter = limiter
if settings.RATE_LIMITING_ENABLED:
    from slowapi import _rate_limit_exceeded_handler
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
import os as _os
_is_prod = _os.getenv("ENVIRONMENT", "development") == "production"
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8081",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8081",
]
if _is_prod:
    ALLOWED_ORIGINS += [
        origin.strip()
        for origin in _os.getenv("ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]

# Middleware stack
app.add_middleware(ValidationMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(CompressionMiddleware)
# Imported at module scope on purpose: a failure here must stop startup, not
# leave the app serving without authentication or security headers.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(InputSanitizationMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
    response = await call_next(request)
    from app.core import durable
    await durable.flush()
    response.headers["X-Request-ID"] = request_id
    response.headers["X-API-Version"] = settings.VERSION
    return response


# Prometheus metrics at root level
from app.api.v1.endpoints.metrics import router as metrics_router
app.include_router(metrics_router, prefix="/metrics", tags=["Observability"])


# Static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

web_dir = Path(__file__).parent.parent.parent / "web"
if web_dir.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/admin", StaticFiles(directory=str(web_dir), html=True), name="admin")


# ─── Auto-discover and register all endpoint routers ───
from app.core.registry import register_endpoints
_registration = register_endpoints(app)
logger.info(
    "Registered %d endpoint modules (%d skipped, %d failed)",
    _registration["registered"], _registration["skipped"], _registration["errors"],
)
if _registration["errors"]:
    # Serving a partial API is worse than not starting: the missing routes
    # return 404 and look like a client bug rather than a broken deploy.
    _broken = ", ".join(f"{name} ({reason})" for name, reason in _registration["failures"])
    if settings.ENVIRONMENT.lower() == "production":
        raise RuntimeError(f"Endpoint modules failed to register: {_broken}")
    logger.error("Endpoint modules failed to register: %s", _broken)

# Added after registration so the middleware can read the finished route table
# and learn which paths carry a {user_id} segment.
from app.middleware.identity import IdentityMiddleware
app.add_middleware(IdentityMiddleware, fastapi_app=app)


# ─── Root endpoints ───

@app.get("/")
async def root():
    return {"app": settings.PROJECT_NAME, "version": settings.VERSION, "status": "healthy", "docs": "/docs"}


@app.get("/health")
@limiter.limit("30/minute")
async def health(request: Request):
    from app.core.storage import storage
    stats = await storage.get_stats()
    services = {}
    for name, getter in [
        ("ml_engine", lambda: __import__("app.services.ml_engine", fromlist=["ml_engine"]).ml_engine.get_status()),
        ("nlp_pipeline", lambda: __import__("app.services.nlp_pipeline", fromlist=["nlp_pipeline"]).nlp_pipeline.get_status()),
        ("vector_store", lambda: __import__("app.services.vector_store", fromlist=["vector_store"]).vector_store.get_status()),
    ]:
        try:
            services[name] = getter()
        except Exception:
            services[name] = {"status": "unavailable"}
    return {"status": "healthy", "version": settings.VERSION, "storage": stats, "services": services}


@app.get("/ready")
async def ready():
    checks = {}
    try:
        from app.core.storage import storage
        await storage.get_stats()
        checks["storage"] = "ok"
    except Exception:
        checks["storage"] = "error"
    try:
        from app.services.vector_store import vector_store
        vs_status = vector_store.get_status()
        checks["vector_store"] = "ok" if vs_status.get("initialized", False) else "not_initialized"
    except Exception:
        checks["vector_store"] = "error"
    is_ready = all(v in ("ok", "not_initialized") for v in checks.values())
    return {"status": "ready" if is_ready else "not_ready", "checks": checks}


@app.post("/seed-demo")
async def seed_demo():
    # Demo data must never reach a real account.
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=404, detail="Not found")
    from app.core.seed_demo import seed_all
    from app.core.storage import storage
    results = seed_all("demo_user", storage)
    return {"status": "seeded", "data": results}


@app.get("/dashboard")
async def dashboard():
    from fastapi.responses import FileResponse
    return FileResponse(str(Path(__file__).parent / "static" / "index.html"))


# ─── WebSocket endpoints ───

@app.websocket("/ws/bpm/{user_id}")
async def bpm_websocket(websocket: WebSocket, user_id: str):
    from app.services.camera_vitals import camera_vitals_service
    from app.core.dependencies import authenticate_websocket
    import json
    user = await authenticate_websocket(websocket, expected_user_id=user_id)
    if user is None:
        return
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "start":
                result = camera_vitals_service.start_measurement()
                await websocket.send_json({"type": "status", **result})
            elif msg.get("type") == "frame":
                result = camera_vitals_service.process_frame(msg)
                await websocket.send_json({"type": "update", **result})
            elif msg.get("type") == "stop":
                reading = camera_vitals_service.get_bpm_reading()
                await websocket.send_json({"type": "result", "bpm": reading.bpm, "hrv": reading.hrv_estimate})
                break
    except WebSocketDisconnect:
        pass


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    from app.services.websocket_manager import ws_manager
    from app.core.dependencies import authenticate_websocket
    user = await authenticate_websocket(websocket, expected_user_id=user_id)
    if user is None:
        return
    await ws_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)

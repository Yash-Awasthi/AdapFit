"""
AdapFit — AI-Powered Adaptive Fitness & Recovery Engine

Entry point. Endpoint routers are auto-discovered by app/core/registry.py.
Add a new endpoint: drop a file in app/api/v1/endpoints/, export `router`.
"""
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.core.error_handlers import ErrorHandlingMiddleware
from app.core.metrics import MetricsMiddleware
from app.core.validation import ValidationMiddleware
from app.core.compression import CompressionMiddleware

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
    description="AdapFit: AI-Powered Adaptive Fitness & Recovery Engine",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)
app.state.limiter = limiter
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
try:
    from app.middleware.security import SecurityHeadersMiddleware, InputSanitizationMiddleware, RequestLoggingMiddleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(InputSanitizationMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
except ImportError:
    pass
try:
    from app.middleware.auth import AuthMiddleware
    app.add_middleware(AuthMiddleware)
except ImportError:
    pass
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
    response.headers["X-Request-ID"] = request_id
    response.headers["X-API-Version"] = settings.VERSION
    return response


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
register_endpoints(app)


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
        checks["vector_store"] = "ok" if vector_store._initialized else "not_initialized"
    except Exception:
        checks["vector_store"] = "error"
    is_ready = all(v in ("ok", "not_initialized") for v in checks.values())
    return {"status": "ready" if is_ready else "not_ready", "checks": checks}


@app.post("/seed-demo")
async def seed_demo():
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
    import json
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
    await ws_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)

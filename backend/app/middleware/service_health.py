"""
Service Health Middleware — monitors all intelligence services.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import time


class ServiceHealthMiddleware(BaseHTTPMiddleware):
    """Middleware that tracks service health and adds health headers."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self._service_start_times: dict[str, float] = {}
        self._service_counts: dict[str, int] = {}

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        # Add performance headers
        response.headers["X-Response-Time"] = f"{duration:.3f}s"

        # Track which endpoint was called
        path = request.url.path
        for prefix in ["/api/v1/pose", "/api/v1/biomarkers", "/api/v1/biometrics",
                       "/api/v1/anomaly", "/api/v1/planner", "/api/v1/tracker",
                       "/api/v1/chat", "/api/v1/rppg", "/api/v1/sensors",
                       "/api/v1/sleep", "/api/v1/breathing",
                       "/api/v1/injury-risk", "/api/v1/medication-tracker",
                       "/api/v1/achievements"]:
            if path.startswith(prefix):
                service_name = prefix.split("/")[-1]
                self._service_counts[service_name] = self._service_counts.get(service_name, 0) + 1
                response.headers["X-Service"] = service_name
                break

        return response

    def get_stats(self) -> dict[str, Any]:
        return {"service_calls": dict(self._service_counts)}

"""TRACK: Prometheus-compatible /metrics endpoint."""

import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from app.core.config import settings
from app.core.metrics import metrics


def _scraper(authorization: str = Header("")) -> None:
    """Request counts and error rates help an attacker; only the configured scraper reads them in production."""
    if settings.METRICS_TOKEN:
        if not hmac.compare_digest(authorization.encode(), f"Bearer {settings.METRICS_TOKEN}".encode()):
            raise HTTPException(status_code=401, detail="Metrics token required")
    elif settings.ENVIRONMENT.lower() == "production":
        raise HTTPException(status_code=404, detail="Not found")


router = APIRouter(dependencies=[Depends(_scraper)])


@router.get("")
async def metrics_endpoint():
    """Return Prometheus-compatible metrics."""
    body = metrics.render()
    return Response(
        content=body,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@router.get("/summary")
async def metrics_summary():
    """Human-readable metrics summary."""
    return {
        "http_requests": metrics.http_requests_total._value,
        "active_users": metrics.active_users._value,
        "workouts_generated": metrics.workouts_generated_total._value,
        "recovery_scores": metrics.recovery_scores_computed._value,
        "llm_calls": metrics.ai_llm_calls_total._value,
        "errors": metrics.error_rate._value,
    }

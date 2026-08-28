"""TRACK: Prometheus-compatible /metrics endpoint."""

from fastapi import APIRouter, Response
from app.core.metrics import metrics

router = APIRouter()


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

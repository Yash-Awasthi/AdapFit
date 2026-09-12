"""
Health Anomaly Detection API — detects anomalies in wearable health data.
"""
from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.core.dependencies import require_user
from app.services.websocket_manager import ws_manager

router = APIRouter()

VALID_METRICS = frozenset({
    "heart_rate", "hrv", "spo2", "sleep_quality", "temperature",
    "blood_pressure_systolic", "blood_pressure_diastolic",
    "respiratory_rate", "stress_level", "activity_level",
})


class AnomalyDetectRequest(BaseModel):
    metric: str
    current_value: float
    timestamp: str | None = None

    def model_post_init(self, __context: object) -> None:
        if self.metric not in VALID_METRICS:
            raise ValueError(f"Invalid metric '{self.metric}'. Valid: {sorted(VALID_METRICS)}")


class BatchAnomalyRequest(BaseModel):
    metric: str
    values: list[list] = Field(min_length=1, max_length=10000)

    def model_post_init(self, __context: object) -> None:
        if self.metric not in VALID_METRICS:
            raise ValueError(f"Invalid metric '{self.metric}'. Valid: {sorted(VALID_METRICS)}")


class EmergencyCheckRequest(BaseModel):
    metrics: dict[str, float] = Field(min_length=1, max_length=20)


@lru_cache(maxsize=1)
def _get_detector():
    from src.anomaly.detector import HealthAnomalyDetector
    return HealthAnomalyDetector()


@router.post("/detect", summary="Detect if a single metric value is anomalous")
async def detect_anomaly(req: AnomalyDetectRequest, user: dict = Depends(require_user)) -> dict[str, Any]:
    from src.anomaly.detector import MetricType
    detector = _get_detector()
    ts = datetime.fromisoformat(req.timestamp) if req.timestamp else datetime.utcnow()
    try:
        metric = MetricType(req.metric)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Unknown metric type: {req.metric}")
    try:
        anomaly = detector.detect(metric, req.current_value, ts)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if anomaly:
        # Push real-time alert to the user's connected WebSocket clients so
        # the mobile app shows an instant notification without polling.
        try:
            await ws_manager.push_alert(
                user_id=user["id"],
                alert_type="health_anomaly",
                message=f"{anomaly.message}",
                severity="warning" if anomaly.severity.value != "critical" else "critical",
            )
        except Exception:
            pass  # WebSocket push must never break anomaly detection.
        return {"is_anomaly": True, "severity": anomaly.severity.value, "message": anomaly.message,
                "expected_range": list(anomaly.expected_range)}
    return {"is_anomaly": False, "value": req.current_value, "metric": req.metric}


@router.post("/detect-batch", summary="Detect anomalies in a time series")
async def detect_batch_anomalies(req: BatchAnomalyRequest, user: dict = Depends(require_user)) -> dict[str, Any]:
    from src.anomaly.detector import MetricType
    detector = _get_detector()
    try:
        metric = MetricType(req.metric)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Unknown metric type: {req.metric}")
    try:
        values = [(datetime.fromisoformat(str(v[0])), float(v[1])) for v in req.values]
    except (ValueError, IndexError) as exc:
        raise HTTPException(status_code=422, detail=f"Invalid timestamp/value pairs: {exc}") from exc
    anomalies = detector.detect_batch(metric, values)
    # Push a real-time alert for each detected anomaly so the user's mobile app
    # gets instant notifications. Fire-and-forget — never breaks the response.
    for a in anomalies:
        try:
            await ws_manager.push_alert(
                user_id=user["id"],
                alert_type="health_anomaly",
                message=a.message,
                severity="warning" if a.severity.value != "critical" else "critical",
            )
        except Exception:
            pass
    return {
        "total_points": len(req.values), "anomalies_found": len(anomalies),
        "anomalies": [{"timestamp": a.timestamp.isoformat(), "value": a.value,
                        "severity": a.severity.value, "message": a.message} for a in anomalies],
    }


@router.post("/emergency-check", summary="Check for emergency-level health anomalies")
async def check_emergencies(req: EmergencyCheckRequest, user: dict = Depends(require_user)) -> dict[str, Any]:
    from src.anomaly.detector import MetricType
    detector = _get_detector()
    metrics = {}
    for k, v in req.metrics.items():
        try:
            metrics[MetricType(k)] = v
        except ValueError:
            continue
    if not metrics:
        raise HTTPException(status_code=422, detail="No valid metric types provided")
    emergencies = detector.detect_health_emergencies(metrics)
    # Push a critical real-time alert for each emergency so the user's mobile
    # app shows an immediate notification. Fire-and-forget.
    for e in emergencies:
        try:
            await ws_manager.push_alert(
                user_id=user["id"],
                alert_type="health_emergency",
                message=e.message,
                severity="critical",
            )
        except Exception:
            pass
    return {
        "emergencies": len(emergencies),
        "alerts": [{"metric": e.metric.value, "severity": e.severity.value, "message": e.message} for e in emergencies],
    }

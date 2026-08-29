"""
Health Data API — Normalized Health Records with Source Attribution

Every record carries source, timestamp, confidence, and provenance metadata.
Supports all measurement types with proper validation and filtering.
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional
from app.core.health_data import health_data_store, MEASUREMENT_TYPES
from app.core.health_validation import PHYSIOLOGICAL_RANGES, validate, compute_confidence
from app.core.dependencies import require_user

router = APIRouter()


class AddRecordRequest(BaseModel):
    measurement_type: str = Field(min_length=1, max_length=50)
    value: float
    source: str = Field(default="manual", description="manual, device, sensor, import, calculated, clinical")
    device: str = ""
    confidence: str = Field(default="medium", description="high, medium, low, estimated — ignored for types with a known physiological range, where confidence is computed instead")
    timestamp: Optional[float] = None
    privacy_level: str = Field(default="private", description="private, family, medical")
    metadata: Optional[dict] = None


class BatchAddRequest(BaseModel):
    records: list[AddRecordRequest] = Field(max_length=100)


def _add_validated_record(user_id: str, rec: AddRecordRequest) -> dict:
    """Store one record, computing confidence instead of trusting the client's claim
    whenever the measurement type has a known plausible physiological range.
    """
    value = rec.value
    confidence = rec.confidence
    if rec.measurement_type in PHYSIOLOGICAL_RANGES:
        ok, normalized, reason = validate(rec.measurement_type, value)
        if not ok:
            return {"error": reason, "type": rec.measurement_type, "value": value}
        value = normalized
        confidence = compute_confidence(rec.measurement_type, value, source=rec.source).value
    return health_data_store.add_record(
        user_id=user_id,
        measurement_type=rec.measurement_type,
        value=value,
        source=rec.source,
        device=rec.device,
        confidence=confidence,
        timestamp=rec.timestamp,
        privacy_level=rec.privacy_level,
        metadata=rec.metadata,
    )


@router.post("/record")
async def add_health_record(request: AddRecordRequest, user: dict = Depends(require_user)):
    """Add a normalized health data record with source attribution."""
    return _add_validated_record(user["id"], request)


@router.post("/batch")
async def add_batch_records(request: BatchAddRequest, user: dict = Depends(require_user)):
    """Add multiple health records in a single request."""
    results = [_add_validated_record(user["id"], rec) for rec in request.records]
    return {"added": len(results), "results": results}


@router.get("/records")
async def get_health_records(
    user: dict = Depends(require_user),
    measurement_type: Optional[str] = None,
    source: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get health records with optional filtering by type, source, and date range."""
    records = health_data_store.get_records(
        user["id"],
        measurement_type=measurement_type,
        days=days,
        limit=limit,
    )
    if source:
        records = [r for r in records if r.get("source") == source]
    return {"records": records, "count": len(records), "user_id": user["id"]}


@router.get("/latest/{measurement_type}")
async def get_latest_record(measurement_type: str, user: dict = Depends(require_user)):
    """Get the most recent record of a specific measurement type."""
    record = health_data_store.get_latest(user["id"], measurement_type)
    if not record:
        return {"error": f"No records found for {measurement_type}"}
    return record


@router.get("/summary")
async def get_health_summary(user: dict = Depends(require_user), days: int = Query(7, ge=1, le=365)):
    """Get a summary of all health data for the specified period."""
    return health_data_store.get_summary(user["id"], days)


@router.get("/measurement-types")
async def get_measurement_types():
    """List all supported measurement types with their units and ranges."""
    types = []
    for mt, info in MEASUREMENT_TYPES.items():
        types.append({
            "type": mt,
            "unit": info["unit"],
            "category": info["category"],
            "typical_range": PHYSIOLOGICAL_RANGES.get(mt),
        })
    return {"measurement_types": types, "count": len(types)}


@router.get("/categories")
async def get_data_categories():
    """List all health data categories."""
    categories = {}
    for mt, info in MEASUREMENT_TYPES.items():
        cat = info["category"]
        if cat not in categories:
            categories[cat] = {"id": cat, "name": cat.replace("_", " ").title(), "types": []}
        categories[cat]["types"].append(mt)
    return {"categories": list(categories.values())}

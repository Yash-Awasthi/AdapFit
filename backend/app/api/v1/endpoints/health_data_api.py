"""
Health Data API — Normalized Health Records with Source Attribution

Every record carries source, timestamp, confidence, and provenance metadata.
Supports all measurement types with proper validation and filtering.
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional
from app.core.health_data import health_data_store, MEASUREMENT_TYPES
from app.core.dependencies import require_user

router = APIRouter()


class AddRecordRequest(BaseModel):
    measurement_type: str = Field(min_length=1, max_length=50)
    value: float
    source: str = Field(default="manual", description="manual, device, sensor, import, calculated, clinical")
    device: str = ""
    confidence: str = Field(default="medium", description="high, medium, low, estimated")
    timestamp: Optional[float] = None
    privacy_level: str = Field(default="private", description="private, family, medical")
    metadata: Optional[dict] = None


class BatchAddRequest(BaseModel):
    records: list[AddRecordRequest] = Field(max_length=100)


@router.post("/record")
async def add_health_record(request: AddRecordRequest, user: dict = Depends(require_user)):
    """Add a normalized health data record with source attribution."""
    return health_data_store.add_record(
        user_id=user["id"],
        measurement_type=request.measurement_type,
        value=request.value,
        source=request.source,
        device=request.device,
        confidence=request.confidence,
        timestamp=request.timestamp,
        privacy_level=request.privacy_level,
        metadata=request.metadata,
    )


@router.post("/batch")
async def add_batch_records(request: BatchAddRequest, user: dict = Depends(require_user)):
    """Add multiple health records in a single request."""
    results = []
    for rec in request.records:
        result = health_data_store.add_record(
            user_id=user["id"],
            measurement_type=rec.measurement_type,
            value=rec.value,
            source=rec.source,
            device=rec.device,
            confidence=rec.confidence,
            timestamp=rec.timestamp,
            privacy_level=rec.privacy_level,
            metadata=rec.metadata,
        )
        results.append(result)
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
        source=source,
        days=days,
        limit=limit,
    )
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
            "typical_range": info["typical_range"],
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

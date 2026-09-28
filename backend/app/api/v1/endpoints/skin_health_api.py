"""Skin Health & Mole Tracking API"""
from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel, Field
from typing import Optional
from app.services.skin_health import skin_health_service

router = APIRouter()


class SkinTypeRequest(BaseModel):
    skin_color: int = 3
    sun_reaction: int = 3
    tanning_ability: int = 3


class MoleRequest(BaseModel):
    name: str
    body_location: str
    size_mm: float
    color: str = "brown"
    notes: str = ""


class UVRequest(BaseModel):
    uv_index: int = 5
    duration_minutes: int = 30
    protection_used: str = "none"


@router.post("/skin-type")
async def assess_skin_type(request: SkinTypeRequest):
    return skin_health_service.assess_skin_type(request.model_dump())


@router.post("/mole")
async def add_mole(request: MoleRequest):
    return skin_health_service.add_mole(request.name, request.body_location, request.size_mm, request.color, request.notes)


@router.get("/moles")
async def get_moles():
    return {"moles": skin_health_service.get_all_moles()}


@router.get("/mole/{mole_id}")
async def get_mole(mole_id: str):
    mole = skin_health_service.get_mole(mole_id)
    if not mole:
        return {"error": "Mole not found"}
    return {"mole": mole}


class MoleMeasurement(BaseModel):
    """A fresh measurement of a mole already being tracked."""
    size_mm: float = Field(gt=0, le=100)
    color: str = ""
    notes: str = ""


@router.post("/mole/{mole_id}/measure")
async def measure_mole(mole_id: str, measurement: MoleMeasurement):
    """Record a new measurement and report what changed since the last one."""
    return skin_health_service.record_measurement(
        mole_id, measurement.size_mm, measurement.color, measurement.notes
    )


@router.post("/mole/{mole_id}/photo")
async def measure_mole_photo(mole_id: str, file: UploadFile = File(...),
                             reference_mm: Optional[float] = Form(None, gt=5, le=40)):
    """Measure the mole in a photo and compare with its last check. The photo is not kept."""
    from app.services import lesion_measure
    measured = lesion_measure.measure(await file.read(lesion_measure.MAX_UPLOAD_BYTES + 1), reference_mm)
    if measured["status"] != "measured":
        return measured
    f = measured["features"]
    result = skin_health_service.record_measurement(
        mole_id, f["diameter_mm"], features={k: f[k] for k in ("asymmetry_score", "border_irregularity", "color_variation")})
    return {**result, "measurement": measured}


@router.get("/mole/{mole_id}/history")
async def get_mole_history(mole_id: str):
    return {"history": skin_health_service.get_mole_history(mole_id)}


@router.post("/uv")
async def log_uv(request: UVRequest):
    return skin_health_service.log_uv_exposure(request.uv_index, request.duration_minutes, request.protection_used)


@router.get("/uv-history")
async def get_uv_history(days: int = 7):
    return {"history": skin_health_service.get_uv_history(days)}


@router.get("/cancer-risk")
async def get_cancer_risk():
    return skin_health_service.get_skin_cancer_risk()


@router.get("/dermatology-report")
async def get_report():
    return skin_health_service.get_dermatology_report()

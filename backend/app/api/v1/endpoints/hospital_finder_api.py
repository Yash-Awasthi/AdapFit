"""Nearby hospitals, clinics and pharmacies from OpenStreetMap."""
from typing import Literal

from fastapi import APIRouter, Query

from app.services import hospital_finder

router = APIRouter()


@router.get("/nearby")
async def find_nearby(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    kind: Literal["all", "hospital", "clinic", "pharmacy"] = "all",
    radius_km: float = Query(5.0, ge=0.5, le=25),
):
    return await hospital_finder.find_nearby(lat, lon, kind, radius_km)

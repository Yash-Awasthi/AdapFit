"""Lab results: values from your reports, compared with the report's own range, over time."""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.lab_results import CATALOG, lab_results

router = APIRouter()


class ReadingRequest(BaseModel):
    test: str = Field(min_length=2, max_length=40, pattern=r"^[a-z0-9_]+$")
    value: float = Field(ge=0, le=100000)
    taken_on: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    ref_low: Optional[float] = Field(None, ge=0)
    ref_high: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=20)
    lab: str = Field("", max_length=80)


@router.get("/tests")
async def tests_catalog():
    return [{"id": k, "label": v[0], "unit": v[1]} for k, v in CATALOG.items()]


@router.post("/readings", status_code=201)
async def add_reading(req: ReadingRequest):
    return lab_results.add(**req.model_dump())


@router.get("/summary")
async def summary():
    return {"tests": lab_results.summary(), "note": "Ranges come from your report where you entered them. Only a doctor can interpret results."}


@router.delete("/readings/{reading_id}")
async def delete_reading(reading_id: str):
    if not lab_results.delete(reading_id):
        raise HTTPException(status_code=404, detail="Reading not found")
    return {"deleted": True}

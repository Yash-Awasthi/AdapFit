"""Medication Reminder API"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from app.services.medication_reminder import medication_reminder_service

router = APIRouter()

class MedAddRequest(BaseModel):
    name: str
    dosage: str
    frequency: str = "once_daily"
    times: list[str] = ["08:00"]
    category: str = "supplement"
    notes: str = ""

class DoseLogRequest(BaseModel):
    medication_id: str
    status: str = "taken"

class MedicalInfoRequest(BaseModel):
    blood_type: str = "unknown"
    allergies: list[str] = []
    conditions: list[str] = []
    medications: list[str] = []
    emergency_note: str = ""

@router.post("/add")
async def add_medication(request: MedAddRequest):
    return medication_reminder_service.add_medication(
        request.name, request.dosage, request.frequency,
        request.times, request.category, request.notes,
    )

@router.post("/dose")
async def log_dose(request: DoseLogRequest):
    return medication_reminder_service.log_dose(request.medication_id, request.status)

@router.get("/today")
async def get_today_schedule():
    return medication_reminder_service.get_today_schedule()

@router.get("/adherence")
async def get_adherence(days: int = 30):
    return medication_reminder_service.get_adherence_score(days)

@router.get("/list")
async def list_medications():
    return {"medications": medication_reminder_service.get_all_medications()}

@router.get("/refills")
async def get_refill_alerts():
    return {"alerts": medication_reminder_service.get_refill_alerts()}


@router.get("/drug-info")
async def drug_info(name: str = Query(min_length=2, max_length=60, pattern=r"^[A-Za-z0-9 \-]+$")):
    """Label summary and recalls from the US FDA's open data, for a brand or generic name."""
    import asyncio

    from app.services import openfda_client as fda

    labels, recalls = await asyncio.gather(
        asyncio.to_thread(fda.search_drug_label, name),
        asyncio.to_thread(fda.search_drug_recalls, fda.us_name(name), 5),
    )
    return {
        "query": name,
        "searched_as": fda.us_name(name),
        "matches": [
            {"brand_name": l.brand_name, "generic_name": l.generic_name, "manufacturer": l.manufacturer,
             "route": l.route, "purpose": [p[:400] for p in l.purpose][:2], "warnings": [w[:600] for w in l.warnings][:3]}
            for l in labels
        ],
        "recalls": [{"reason": r.reason, "classification": r.classification, "date": r.date,
                     "product": r.product_description[:200]} for r in recalls],
        "source": "US FDA (openFDA). Indian brands may differ; your pharmacist can confirm.",
        "note": "General label information. Ask your doctor or pharmacist before changing how you take any medicine.",
    }

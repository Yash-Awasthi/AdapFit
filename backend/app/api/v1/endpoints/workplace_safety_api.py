"""
Workplace Safety & OSHA Compliance API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/workplace-safety", tags=["Workplace Safety"])


class IncidentReportRequest(BaseModel):
    user_id: str
    incident_type: str
    description: str
    location: str
    injury_severity: str
    body_part: Optional[str] = None
    witnesses: List[str] = []


class ErgonomicAssessmentRequest(BaseModel):
    user_id: str
    work_type: str
    hours_per_day: float
    desk_height: Optional[float] = None
    chair_type: Optional[str] = None
    screen_distance: Optional[float] = None


class HazardReportRequest(BaseModel):
    user_id: str
    hazard_type: str
    description: str
    location: str
    severity: str


@router.post("/incident/report")
async def report_incident(req: IncidentReportRequest):
    from app.services.workplace_safety import workplace_safety_service
    return workplace_safety_service.report_incident(req.user_id, req.incident_type, req.description, req.location, req.injury_severity, req.body_part, req.witnesses)


@router.post("/ergonomic/assess")
async def assess_ergonomics(req: ErgonomicAssessmentRequest):
    from app.services.workplace_safety import workplace_safety_service
    return workplace_safety_service.assess_ergonomics(req.user_id, req.work_type, req.hours_per_day, req.desk_height, req.chair_type, req.screen_distance)


@router.post("/hazard/report")
async def report_hazard(req: HazardReportRequest):
    from app.services.workplace_safety import workplace_safety_service
    return workplace_safety_service.report_hazard(req.user_id, req.hazard_type, req.description, req.location, req.severity)


@router.get("/compliance/{user_id}")
async def get_compliance(user_id: str):
    from app.services.workplace_safety import workplace_safety_service
    return workplace_safety_service.get_compliance_status(user_id)


@router.get("/training/{user_id}")
async def get_training(user_id: str):
    from app.services.workplace_safety import workplace_safety_service
    return workplace_safety_service.get_required_training(user_id)


@router.get("/checklist/{industry}")
async def get_safety_checklist(industry: str):
    from app.services.workplace_safety import workplace_safety_service
    return workplace_safety_service.get_safety_checklist(industry)


@router.get("/incidents/{user_id}")
async def get_incidents(user_id: str):
    from app.services.workplace_safety import workplace_safety_service
    return workplace_safety_service.get_incident_history(user_id)

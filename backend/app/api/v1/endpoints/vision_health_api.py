"""
Vision Health & Eye Care API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/vision", tags=["Vision Health"])


class PrescriptionRequest(BaseModel):
    user_id: str
    right_eye: dict
    left_eye: dict
    pupillary_distance: float
    doctor: str
    date_issued: str
    expiry: str


class EyeExamRequest(BaseModel):
    user_id: str
    exam_type: str
    date: str
    visual_acuity_right: str
    visual_acuity_left: str
    intraocular_pressure: Optional[float] = None
    notes: str = ""


class ScreenTimeRequest(BaseModel):
    user_id: str
    hours: float
    breaks_taken: int
    strain_level: int


class StrainLogRequest(BaseModel):
    user_id: str
    symptoms: List[str]
    severity: int
    duration_hours: float


class ExerciseLogRequest(BaseModel):
    user_id: str
    exercise_id: str
    completed: bool


@router.post("/prescription/add")
async def add_prescription(req: PrescriptionRequest):
    from app.services.vision_health import vision_health_service
    return vision_health_service.add_prescription(req.user_id, req.right_eye, req.left_eye, req.pupillary_distance, req.doctor, req.date_issued, req.expiry)


@router.post("/exam/log")
async def log_eye_exam(req: EyeExamRequest):
    from app.services.vision_health import vision_health_service
    return vision_health_service.log_eye_exam(req.user_id, req.exam_type, req.date, req.visual_acuity_right, req.visual_acuity_left, req.intraocular_pressure, req.notes)


@router.post("/screen-time/log")
async def log_screen_time(req: ScreenTimeRequest):
    from app.services.vision_health import vision_health_service
    return vision_health_service.log_screen_time(req.user_id, req.hours, req.breaks_taken, req.strain_level)


@router.post("/strain/log")
async def log_strain(req: StrainLogRequest):
    from app.services.vision_health import vision_health_service
    return vision_health_service.log_strain(req.user_id, req.symptoms, req.severity, req.duration_hours)


@router.get("/exercises/{strain_level}")
async def get_exercises(strain_level: int):
    from app.services.vision_health import vision_health_service
    return vision_health_service.get_exercise_plan(strain_level)


@router.get("/exercises/all")
async def get_all_exercises():
    from app.services.vision_health import vision_health_service
    return vision_health_service.VISION_EXERCISES


@router.post("/exercise/log")
async def log_exercise(req: ExerciseLogRequest):
    from app.services.vision_health import vision_health_service
    return vision_health_service.log_exercise(req.user_id, req.exercise_id, req.completed)


@router.get("/health-score/{user_id}")
async def get_vision_health_score(user_id: str):
    from app.services.vision_health import vision_health_service
    return vision_health_service.get_vision_health_score(user_id)


@router.get("/prescription/alerts/{user_id}")
async def get_expiry_alerts(user_id: str):
    from app.services.vision_health import vision_health_service
    return vision_health_service.get_prescription_expiry_alert(user_id)

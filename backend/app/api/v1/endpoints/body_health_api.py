"""Body Composition, Hydration & Blood Pressure API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.body_composition import body_composition_service
from app.services.hydration_tracker import hydration_service
from app.services.blood_pressure import blood_pressure_service

router = APIRouter()

class BMIRequest(BaseModel):
    weight_kg: float; height_cm: float

class BodyFatRequest(BaseModel):
    gender: str; waist_cm: float; neck_cm: float; height_cm: float; hip_cm: float = 0

class IdealWeightRequest(BaseModel):
    gender: str; height_cm: float; frame: str = "medium"

class HydrationLogRequest(BaseModel):
    amount_ml: float = 250; drink_type: str = "water"; note: str = ""

class HydrationGoalRequest(BaseModel):
    weight_kg: float; activity_level: str = "moderate"

class BPLogRequest(BaseModel):
    systolic: int; diastolic: int; pulse: Optional[int] = None; context: str = "resting"; notes: str = ""

# Body Composition
@router.post("/bmi")
async def calculate_bmi(request: BMIRequest):
    return body_composition_service.calculate_bmi(request.weight_kg, request.height_cm)

@router.post("/body-fat")
async def estimate_body_fat(request: BodyFatRequest):
    return body_composition_service.estimate_body_fat(request.gender, request.waist_cm, request.neck_cm, request.height_cm, request.hip_cm)

@router.post("/ideal-weight")
async def get_ideal_weight(request: IdealWeightRequest):
    return body_composition_service.ideal_weight(request.gender, request.height_cm, request.frame)

@router.get("/body-trends")
async def get_body_trends():
    return body_composition_service.get_trends()

# Hydration
@router.post("/hydration/goal")
async def set_hydration_goal(request: HydrationGoalRequest):
    return hydration_service.set_goal(request.weight_kg, request.activity_level)

@router.post("/hydration/log")
async def log_hydration(request: HydrationLogRequest):
    return hydration_service.log_intake(request.amount_ml, request.drink_type, request.note)

@router.get("/hydration/today")
async def get_hydration_today():
    return hydration_service.get_today_summary()

@router.get("/hydration/streak")
async def get_hydration_streak():
    return hydration_service.get_streak()

@router.get("/hydration/recommendations")
async def get_hydration_recommendations():
    return {"recommendations": hydration_service.get_recommendations()}

# Blood Pressure
@router.post("/bp/log")
async def log_bp(request: BPLogRequest):
    return blood_pressure_service.log_reading(request.systolic, request.diastolic, request.pulse, request.context, request.notes)

@router.get("/bp/today")
async def get_bp_today():
    return {"readings": blood_pressure_service.get_today_readings()}

@router.get("/bp/trend")
async def get_bp_trend(days: int = 30):
    return blood_pressure_service.get_trend(days)

@router.get("/bp/report")
async def get_bp_doctor_report():
    return blood_pressure_service.get_doctor_report()

"""Activity recognition — workout detection, step counting, calorie burn, intensity."""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from app.services.activity_recognition import (
    SensorReading, UserProfile,
    detect_activity, count_steps, estimate_distance,
    calculate_calories, classify_intensity,
)

router = APIRouter()


class SensorInput(BaseModel):
    timestamp: float
    accel_x: float
    accel_y: float
    accel_z: float
    gyro_x: float = 0
    gyro_y: float = 0
    gyro_z: float = 0


class ActivityDetectInput(BaseModel):
    readings: list[SensorInput]
    window_seconds: float = 5.0


class StepsInput(BaseModel):
    readings: list[SensorInput]
    sensitivity: float = 1.2


class DistanceInput(BaseModel):
    steps: int = Field(..., ge=0)
    height_cm: float = Field(..., ge=100, le=250)
    sex: str = Field(..., pattern="^(male|female)$")


class CalorieInput(BaseModel):
    activity: str
    duration_minutes: float = Field(..., gt=0)
    weight_kg: float = Field(..., ge=20, le=300)
    height_cm: float = Field(..., ge=100, le=250)
    age: int = Field(..., ge=10, le=120)
    sex: str = Field(..., pattern="^(male|female)$")
    heart_rate: Optional[int] = None


@router.post("/detect")
async def detect_workout(req: ActivityDetectInput):
    """Detect current activity from accelerometer/gyroscope data."""
    readings = [SensorReading(**r.model_dump()) for r in req.readings]
    return detect_activity(readings, req.window_seconds)


@router.post("/steps")
async def get_steps(req: StepsInput):
    """Count steps from accelerometer data."""
    readings = [SensorReading(**r.model_dump()) for r in req.readings]
    return count_steps(readings, req.sensitivity)


@router.post("/distance")
async def get_distance(req: DistanceInput):
    """Estimate distance from step count."""
    return estimate_distance(req.steps, req.height_cm, req.sex)


@router.post("/calories")
async def get_calories(req: CalorieInput):
    """Calculate calorie burn for an activity."""
    user = UserProfile(
        weight_kg=req.weight_kg, height_cm=req.height_cm,
        age=req.age, sex=req.sex,
    )
    return calculate_calories(req.activity, req.duration_minutes, user, req.heart_rate)


@router.post("/intensity")
async def get_intensity(heart_rate: int, age: int):
    """Classify exercise intensity from heart rate."""
    return classify_intensity(heart_rate, age)

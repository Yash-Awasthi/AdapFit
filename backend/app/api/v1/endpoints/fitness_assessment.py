"""Fitness assessment: 1RM estimation, fitness tests, bodyweight standards."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from app.services.fitness_assessment import (
    estimate_1rm, assess_strength, assess_fitness_test,
    available_tests, OneRepMaxEstimate, FitnessTest,
)

router = APIRouter()


class OneRMRequest(BaseModel):
    exercise: str = Field(min_length=1, examples=["bench press"])
    weight_kg: float = Field(ge=1, le=500, examples=[80])
    reps: int = Field(ge=1, le=100, examples=[5])
    bodyweight_kg: Optional[float] = Field(None, ge=20, le=300, examples=[80])


class FitnessTestRequest(BaseModel):
    test_id: str = Field(examples=["pushups_1min"])
    result: float = Field(ge=0, examples=[35])


class FitnessAssessment(BaseModel):
    one_rm: Optional[OneRepMaxEstimate] = None
    fitness_tests: List[FitnessTest] = []
    overall_score: float  # 0-100
    recommendations: List[str]


@router.post("/one-rm", response_model=OneRepMaxEstimate)
async def calculate_one_rm(request: OneRMRequest):
    """Estimate 1RM from a set of weight x reps."""
    if request.bodyweight_kg:
        return assess_strength(request.exercise, request.weight_kg, request.reps, request.bodyweight_kg)
    return estimate_1rm(request.weight_kg, request.reps, request.exercise)


@router.post("/test", response_model=FitnessTest)
async def run_fitness_test(request: FitnessTestRequest):
    """Assess a fitness test result."""
    return assess_fitness_test(request.test_id, request.result)


@router.get("/tests", response_model=list)
async def list_tests():
    """List available fitness tests."""
    return available_tests()


@router.get("/summary", response_model=FitnessAssessment)
async def get_assessment_summary(user_id: str = Query("default")):
    """Get a fitness assessment summary (placeholder — would aggregate from user data)."""
    return FitnessAssessment(
        overall_score=65,
        recommendations=[
            "Add push-up test to track upper body endurance",
            "Log a plank test to track core strength",
            "Try a squat test to benchmark lower body",
        ],
    )

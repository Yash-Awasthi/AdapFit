"""Fitness assessment: 1RM estimation, fitness tests, bodyweight standards."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from app.services.fitness_assessment import (
    estimate_1rm, assess_lift_strength, assess_fitness_test,
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


@router.post("/one-rm", response_model=OneRepMaxEstimate)
async def calculate_one_rm(request: OneRMRequest):
    """Estimate 1RM from a set of weight x reps."""
    if request.bodyweight_kg:
        return assess_lift_strength(request.exercise, request.weight_kg, request.reps, request.bodyweight_kg)
    return estimate_1rm(request.weight_kg, request.reps, request.exercise)


@router.post("/test", response_model=FitnessTest)
async def run_fitness_test(request: FitnessTestRequest):
    """Assess a fitness test result."""
    try:
        return assess_fitness_test(request.test_id, request.result)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown fitness test: {request.test_id}")


@router.get("/tests", response_model=list)
async def list_tests():
    """List available fitness tests."""
    return available_tests()

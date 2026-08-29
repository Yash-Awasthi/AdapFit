"""Diabetes Management API — Glucose tracking, insulin, carb counting"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.diabetes_manager import diabetes_manager_service

router = APIRouter()


class GlucoseRequest(BaseModel):
    value_mgdl: int
    context: str = "fasting"
    notes: str = ""


class InsulinRequest(BaseModel):
    insulin_type: str
    units: float
    site: str = "abdomen"
    notes: str = ""


class CarbRequest(BaseModel):
    food_name: str
    carbs: float
    meal_type: str = "snack"


@router.post("/glucose")
async def log_glucose(request: GlucoseRequest):
    return diabetes_manager_service.log_glucose(request.value_mgdl, request.context, request.notes)


@router.get("/glucose/readings")
async def get_readings(hours: int = 24):
    return {"readings": diabetes_manager_service.get_glucose_readings(hours)}


@router.get("/glucose/summary")
async def get_summary():
    return diabetes_manager_service.get_glucose_summary()


@router.get("/glucose/patterns")
async def get_patterns():
    return {"patterns": diabetes_manager_service.get_patterns()}


@router.post("/insulin")
async def log_insulin(request: InsulinRequest):
    return diabetes_manager_service.log_insulin(request.insulin_type, request.units, request.site, request.notes)


@router.get("/insulin/history")
async def get_insulin_history(days: int = 7):
    return {"history": diabetes_manager_service.get_insulin_history(days)}


@router.get("/insulin/types")
async def get_insulin_types():
    return {"types": diabetes_manager_service.get_insulin_types()}


@router.post("/carbs")
async def log_carbs(request: CarbRequest):
    return diabetes_manager_service.log_carbs(request.food_name, request.carbs, request.meal_type)


@router.get("/carbs/search")
async def search_carbs(q: str = ""):
    return {"results": diabetes_manager_service.search_food_carbs(q)}


@router.get("/carbs/summary")
async def get_carb_summary():
    return diabetes_manager_service.get_carb_summary()


@router.get("/carbs/database")
async def get_carb_database():
    return {"foods": diabetes_manager_service.get_carb_database()}

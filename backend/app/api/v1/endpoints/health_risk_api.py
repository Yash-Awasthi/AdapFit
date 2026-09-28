"""
Indian Diabetes Risk Score (IDRS; Mohan et al., J Assoc Physicians India 2005).

A validated four-question screen for Indian adults. It says whether a blood
test is worth doing; it does not say whether someone has diabetes.
"""
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class IDRSRequest(BaseModel):
    age: int = Field(ge=18, le=110)
    sex: Literal["male", "female"]
    waist_cm: float = Field(ge=40, le=200, description="Measured at the navel")
    activity: Literal["vigorous", "moderate", "mild", "sedentary"]
    parents_with_diabetes: int = Field(ge=0, le=2)


def idrs(req: IDRSRequest) -> dict:
    age = 0 if req.age < 35 else 20 if req.age < 50 else 30
    lo, hi = (80, 90) if req.sex == "female" else (90, 100)
    waist = 0 if req.waist_cm < lo else 10 if req.waist_cm < hi else 20
    activity = {"vigorous": 0, "moderate": 10, "mild": 20, "sedentary": 30}[req.activity]
    family = {0: 0, 1: 10, 2: 20}[req.parents_with_diabetes]
    score = age + waist + activity + family
    band = "high" if score >= 60 else "moderate" if score >= 30 else "low"
    steps = {
        "high": "Get an HbA1c or fasting blood sugar test in the next few weeks; free at government health centres.",
        "moderate": "Get a blood sugar test at your next check-up, and aim for 150 minutes of activity a week.",
        "low": "Keep active and check again in a few years or if your weight or waist goes up.",
    }[band]
    return {"score": score, "band": band, "next_step": steps,
            "parts": {"age": age, "waist": waist, "activity": activity, "family_history": family},
            "note": "A screening score (IDRS). Only a blood test can show diabetes."}


@router.post("/idrs")
async def indian_diabetes_risk_score(req: IDRSRequest):
    return idrs(req)

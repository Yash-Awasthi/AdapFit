"""Mental Health API — Assessments, Mood Journaling, CBT"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.mental_health import mental_health_service

router = APIRouter()

class MoodLogRequest(BaseModel):
    mood: int
    emoji: str = "😐"
    energy: int = 3
    anxiety: int = 3
    tags: list[str] = []
    notes: str = ""
    journal: str = ""

class PHQ9Request(BaseModel):
    answers: list[int]

class GAD7Request(BaseModel):
    answers: list[int]

class ThoughtRecordRequest(BaseModel):
    situation: str
    automatic_thought: str
    emotion: str
    emotion_intensity: int
    evidence_for: str
    evidence_against: str
    balanced_thought: str
    new_intensity: int

@router.get("/phq9")
async def get_phq9():
    return mental_health_service.get_phq9_assessment()

@router.post("/phq9/score")
async def score_phq9(request: PHQ9Request):
    return mental_health_service.score_phq9(request.answers)

@router.get("/gad7")
async def get_gad7():
    return mental_health_service.get_gad7_assessment()

@router.post("/gad7/score")
async def score_gad7(request: GAD7Request):
    return mental_health_service.score_gad7(request.answers)

@router.post("/mood")
async def log_mood(request: MoodLogRequest):
    return mental_health_service.log_mood(request.mood, request.emoji, request.energy, request.anxiety, request.tags, request.notes, request.journal)

@router.get("/mood/trend")
async def get_mood_trend(days: int = 7):
    return mental_health_service.get_mood_trend(days)

@router.get("/journal")
async def get_journal(limit: int = 20):
    return {"entries": mental_health_service.get_journal_entries(limit)}

@router.post("/thought-record")
async def create_thought_record(request: ThoughtRecordRequest):
    return mental_health_service.create_thought_record(
        request.situation, request.automatic_thought, request.emotion,
        request.emotion_intensity, request.evidence_for, request.evidence_against,
        request.balanced_thought, request.new_intensity,
    )

@router.get("/crisis")
async def get_crisis_resources():
    return {"resources": mental_health_service.get_crisis_resources()}

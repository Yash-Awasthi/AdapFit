"""Data Export API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.data_export import data_export_service, ExportConfig

router = APIRouter()

class ExportRequest(BaseModel):
    format: str = "json"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    include: Optional[list[str]] = None

@router.post("/export")
async def export_data(request: ExportRequest = ExportRequest()):
    config = ExportConfig(format=request.format, start_date=request.start_date, end_date=request.end_date, include=request.include)
    return data_export_service.export_data(config)

@router.get("/preview")
async def get_export_preview():
    return data_export_service.get_export_preview()

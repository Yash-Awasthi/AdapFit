"""
Health Data Export V2 API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/export-v2", tags=["Health Data Export V2"])


class CreateExportRequest(BaseModel):
    user_id: str
    format: str
    categories: Optional[List[str]] = None
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    anonymize: bool = False


@router.post("/create")
async def create_export(req: CreateExportRequest):
    from app.services.health_export_v2 import health_export_v2
    return health_export_v2.create_export(req.user_id, req.format, req.categories, req.date_range_start, req.date_range_end, req.anonymize)


@router.get("/history/{user_id}")
async def get_history(user_id: str, limit: int = 20):
    from app.services.health_export_v2 import health_export_v2
    return health_export_v2.get_export_history(user_id, limit)


@router.get("/status/{export_id}")
async def get_status(export_id: str):
    from app.services.health_export_v2 import health_export_v2
    return health_export_v2.get_export_status(export_id)


@router.get("/formats")
async def get_formats():
    from app.services.health_export_v2 import health_export_v2
    return health_export_v2.EXPORT_FORMATS


@router.get("/categories")
async def get_categories():
    from app.services.health_export_v2 import health_export_v2
    return health_export_v2.DATA_CATEGORIES

"""Genomics: raw DNA file upload, panel report and medicine check."""
from typing import List

from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel, Field

from app.services.genomics_insights import MAX_UPLOAD_BYTES, genomics_insights_service

router = APIRouter(prefix="/genomics", tags=["Genomics & Pharmacogenomics"])


class DrugCheckRequest(BaseModel):
    medications: List[str] = Field(max_length=50)


class ApoeRequest(BaseModel):
    show: bool


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    return genomics_insights_service.upload(await file.read(MAX_UPLOAD_BYTES + 1))


@router.get("/report")
async def report():
    return genomics_insights_service.report()


@router.post("/apoe")
async def show_apoe(request: ApoeRequest):
    return genomics_insights_service.set_show_apoe(request.show)


@router.post("/drug-check")
async def drug_check(request: DrugCheckRequest):
    return genomics_insights_service.check_drugs(request.medications)


@router.delete("/report")
async def delete_report():
    genomics_insights_service.forget()
    return {"deleted": True}

"""
Health Passport API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/passport", tags=["Health Passport"])


class CreatePassportRequest(BaseModel):
    user_id: str
    full_name: str
    dob: str
    nationality: str
    passport_number: str = ""


class AddVaccinationRequest(BaseModel):
    user_id: str
    vaccine_key: str
    dose_number: int
    date_administered: str
    lot_number: str = ""
    provider: str = ""
    location: str = ""


class AddLabResultRequest(BaseModel):
    user_id: str
    test_name: str
    result: str
    reference_range: str
    date: str
    provider: str = ""


class CertificateRequest(BaseModel):
    user_id: str
    purpose: str
    validity_days: int = 365


@router.post("/create")
async def create_passport(req: CreatePassportRequest):
    from app.services.health_passport import health_passport
    return health_passport.create_passport(req.user_id, req.full_name, req.dob, req.nationality, req.passport_number)


@router.post("/vaccination/add")
async def add_vaccination(req: AddVaccinationRequest):
    from app.services.health_passport import health_passport
    return health_passport.add_vaccination(req.user_id, req.vaccine_key, req.dose_number, req.date_administered, req.lot_number, req.provider, req.location)


@router.get("/vaccinations/{user_id}")
async def get_vaccination_status(user_id: str):
    from app.services.health_passport import health_passport
    return health_passport.get_vaccination_status(user_id)


@router.get("/travel/{user_id}/{region}")
async def check_travel(user_id: str, region: str):
    from app.services.health_passport import health_passport
    return health_passport.check_travel_requirements(user_id, region)


@router.post("/lab/add")
async def add_lab_result(req: AddLabResultRequest):
    from app.services.health_passport import health_passport
    return health_passport.add_lab_result(req.user_id, req.test_name, req.result, req.reference_range, req.date, req.provider)


@router.post("/certificate/generate")
async def generate_certificate(req: CertificateRequest):
    from app.services.health_passport import health_passport
    return health_passport.generate_certificate(req.user_id, req.purpose, req.validity_days)


@router.get("/passport/{user_id}")
async def get_passport(user_id: str):
    from app.services.health_passport import health_passport
    return health_passport.get_passport(user_id)


@router.get("/regions")
async def get_regions():
    from app.services.health_passport import health_passport
    return health_passport.get_regions()


@router.get("/vaccines")
async def get_vaccines():
    from app.services.health_passport import health_passport
    return health_passport.VACCINE_DATABASE

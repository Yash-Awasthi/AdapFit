import logging
logger = logging.getLogger(__name__)

"""Medical domain — groups medication, drug interactions, chronic disease, conditions endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/medical-domain", tags=["Medical Domain"])

try:
    from app.api.v1.endpoints import medication_api
    router.include_router(medication_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import medication_tracker_api
    router.include_router(medication_tracker_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import drug_interactions_api
    router.include_router(drug_interactions_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import chronic_disease_api
    router.include_router(chronic_disease_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import chronic_pain_api
    router.include_router(chronic_pain_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import diabetes_api
    router.include_router(diabetes_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import health_conditions
    router.include_router(health_conditions.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import allergy_api
    router.include_router(allergy_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import symptom_checker_api
    router.include_router(symptom_checker_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import clinical_trials_api
    router.include_router(clinical_trials_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import medical_id_api
    router.include_router(medical_id_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import medical_imaging_api
    router.include_router(medical_imaging_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import personalized_medicine_api
    router.include_router(personalized_medicine_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import wound_care_api
    router.include_router(wound_care_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import screening_api
    router.include_router(screening_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import hospital_finder_api
    router.include_router(hospital_finder_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import hospital_at_home_api
    router.include_router(hospital_at_home_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import telemedicine_api
    router.include_router(telemedicine_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import healthcare_providers_api
    router.include_router(healthcare_providers_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import insurance_api
    router.include_router(insurance_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

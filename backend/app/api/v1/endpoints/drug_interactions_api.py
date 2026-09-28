"""Drug Interaction Checker API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List
from app.services.drug_interactions import drug_interaction_service

router = APIRouter(prefix="/drug-interactions", tags=["Drug Interaction Checker"])

class InteractionCheckRequest(BaseModel):
    medications: List[str] = Field(max_length=30)

NEXT_STEP = {
    "contraindicated": "Contact your doctor or pharmacist today, before your next dose.",
    "major": "Contact your doctor or pharmacist today, before your next dose.",
    "moderate": "Mention this to your doctor or pharmacist at your next visit or refill.",
    "minor": "Worth mentioning at your next visit.",
}
DO_NOT_CHANGE = "Do not stop or change any medicine on your own."


@router.post("/check")
async def check_interactions(req: InteractionCheckRequest):
    result = drug_interaction_service.check_interactions(req.medications)
    # The source's "action" is written for prescribers; users get a next step instead.
    for item in result.get("interactions", []):
        item["for_your_doctor"] = item.pop("action", "")
        item["next_step"] = f"{NEXT_STEP.get(item.get('severity'), NEXT_STEP['moderate'])} {DO_NOT_CHANGE}"
    return {"success": True, "data": result}


@router.post("/food-interactions")
async def check_food_interactions(req: InteractionCheckRequest):
    """Check for food-drug interactions among medications."""
    result = drug_interaction_service.check_food_interactions(req.medications)
    return {"success": True, "data": result}

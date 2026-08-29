"""Onboarding tutorial — step-by-step guide for new users."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.onboarding import get_onboarding

router = APIRouter()


class StepAction(BaseModel):
    step_id: str


@router.get("/{user_id}")
async def get_tutorial(user_id: str):
    """Get onboarding tutorial state and progress."""
    state = get_onboarding(user_id)
    return state.to_dict()


@router.post("/{user_id}/complete")
async def complete_step(user_id: str, body: StepAction):
    """Mark a tutorial step as completed."""
    state = get_onboarding(user_id)
    if state.mark_complete(body.step_id):
        return {"status": "completed", "step_id": body.step_id, **state.to_dict()}
    return {"error": "Step not found"}


@router.post("/{user_id}/skip")
async def skip_step(user_id: str, body: StepAction):
    """Skip an optional tutorial step."""
    state = get_onboarding(user_id)
    if state.skip_step(body.step_id):
        return {"status": "skipped", "step_id": body.step_id, **state.to_dict()}
    return {"error": "Step not found or not skippable"}


@router.post("/{user_id}/dismiss")
async def dismiss_tutorial(user_id: str):
    """Dismiss the entire tutorial (mark all steps complete)."""
    state = get_onboarding(user_id)
    for s in state.steps:
        s.completed = True
    return {"status": "dismissed", **state.to_dict()}

"""
Health Action Engine API — "Help Me" Natural Language Router

Routes natural language requests to the appropriate health module.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.services.health_action_engine import health_action_engine
from app.core.dependencies import require_user

router = APIRouter()


class ActionRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500, description="Natural language health request")


@router.post("/route")
async def route_action(request: ActionRequest, user: dict = Depends(require_user)):
    """
    Route a natural language request to the appropriate health module.
    
    Examples:
    - "I feel exhausted" → Recovery module
    - "I want a doctor" → Telemedicine
    - "Show my sleep trend" → Sleep analysis
    - "Help me calm down" → Breathing exercises
    - "What government schemes apply?" → Government health schemes
    """
    route = health_action_engine.route(request.text)
    suggestions = health_action_engine.get_suggestions(route.intent)
    
    return {
        "text": request.text,
        "intent": route.intent,
        "module": route.module,
        "screen": route.screen,
        "api_endpoint": route.api_endpoint,
        "message": route.message,
        "confidence": route.confidence,
        "suggestions": suggestions,
        "user_id": user["id"],
    }


@router.post("/route-anonymous")
async def route_action_anonymous(request: ActionRequest):
    """
    Route without authentication — for onboarding or pre-login use.
    No user-specific data is returned.
    """
    route = health_action_engine.route(request.text)
    suggestions = health_action_engine.get_suggestions(route.intent)
    
    return {
        "text": request.text,
        "intent": route.intent,
        "module": route.module,
        "screen": route.screen,
        "message": route.message,
        "confidence": route.confidence,
        "suggestions": suggestions,
    }


@router.get("/intents")
async def list_intents():
    """List all supported intents and their trigger phrases."""
    intents = []
    for intent, config in health_action_engine.INTENT_PATTERNS.items():
        intents.append({
            "intent": intent,
            "module": config["module"],
            "screen": config["screen"],
            "keywords": config["keywords"][:5],  # First 5 keywords as examples
            "description": config["message"],
        })
    return {"intents": intents, "count": len(intents)}

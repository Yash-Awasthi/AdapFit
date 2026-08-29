"""
Health Notepad API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/notepad", tags=["Health Notepad"])


class AddNoteRequest(BaseModel):
    user_id: str
    title: str
    content: str
    category: str = "general"
    tags: List[str] = []
    mood: Optional[int] = None


@router.post("/add")
async def add_note(req: AddNoteRequest):
    from app.services.health_notepad import health_notepad
    return health_notepad.add_note(req.user_id, req.title, req.content, req.category, req.tags, req.mood)


@router.get("/notes/{user_id}")
async def get_notes(user_id: str, category: Optional[str] = None, search: Optional[str] = None, limit: int = 50):
    from app.services.health_notepad import health_notepad
    return health_notepad.get_notes(user_id, category, search, limit)


@router.post("/pin/{user_id}/{note_id}")
async def pin_note(user_id: str, note_id: str):
    from app.services.health_notepad import health_notepad
    return health_notepad.pin_note(user_id, note_id)


@router.delete("/note/{user_id}/{note_id}")
async def delete_note(user_id: str, note_id: str):
    from app.services.health_notepad import health_notepad
    return health_notepad.delete_note(user_id, note_id)


@router.get("/summary/{user_id}")
async def get_summary(user_id: str):
    from app.services.health_notepad import health_notepad
    return health_notepad.get_notes_summary(user_id)


@router.get("/categories")
async def get_categories():
    from app.services.health_notepad import health_notepad
    return health_notepad.CATEGORIES

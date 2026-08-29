"""
Health Notepad — Quick notes, observations, and health journal
"""
from datetime import datetime
from typing import Dict, List, Optional
import uuid


class HealthNotepad:
    CATEGORIES = ["symptom", "medication", "exercise", "nutrition", "mood", "sleep", "appointment", "question", "general"]
    MOOD_EMOJIS = {"1": "😢", "2": "😟", "3": "😐", "4": "🙂", "5": "😊", "6": "😄", "7": "😁", "8": "🤩", "9": "🥳", "10": "🌟"}

    def __init__(self):
        self.notes: Dict[str, List[dict]] = {}

    def add_note(self, user_id: str, title: str, content: str, category: str = "general", tags: List[str] = None, mood: Optional[int] = None) -> dict:
        note = {
            "id": str(uuid.uuid4()),
            "title": title,
            "content": content,
            "category": category,
            "tags": tags or [],
            "mood": mood,
            "mood_emoji": self.MOOD_EMOJIS.get(str(mood), ""),
            "pinned": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        self.notes.setdefault(user_id, []).append(note)
        return note

    def get_notes(self, user_id: str, category: Optional[str] = None, search: Optional[str] = None, limit: int = 50) -> List[dict]:
        notes = self.notes.get(user_id, [])
        if category:
            notes = [n for n in notes if n["category"] == category]
        if search:
            search_lower = search.lower()
            notes = [n for n in notes if search_lower in n["title"].lower() or search_lower in n["content"].lower()]
        pinned = [n for n in notes if n["pinned"]]
        unpinned = [n for n in notes if not n["pinned"]]
        return (pinned + unpinned)[-limit:]

    def pin_note(self, user_id: str, note_id: str) -> dict:
        for note in self.notes.get(user_id, []):
            if note["id"] == note_id:
                note["pinned"] = not note["pinned"]
                return note
        return {"error": "Note not found"}

    def delete_note(self, user_id: str, note_id: str) -> dict:
        notes = self.notes.get(user_id, [])
        self.notes[user_id] = [n for n in notes if n["id"] != note_id]
        return {"deleted": note_id}

    def get_notes_summary(self, user_id: str) -> dict:
        notes = self.notes.get(user_id, [])
        categories = {}
        for n in notes:
            cat = n["category"]
            categories[cat] = categories.get(cat, 0) + 1
        return {"total_notes": len(notes), "categories": categories, "pinned_count": sum(1 for n in notes if n["pinned"])}


health_notepad = HealthNotepad()

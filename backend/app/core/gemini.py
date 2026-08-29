"""Shared request shaping for the Google Generative Language API."""
from typing import Any, Dict, Optional, Tuple

BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# gemini-2.0-flash was retired and now answers 404 with a pointer to this model.
DEFAULT_MODEL = "gemini-3.6-flash"


def gemini_endpoint(key: str, model: str = DEFAULT_MODEL) -> Tuple[str, Dict[str, str]]:
    """
    Build the generateContent URL and headers for a credential.

    API keys — both the "AIza..." and "AQ..." forms — go in the key query
    parameter. Only a real OAuth access token ("ya29...") authenticates as a
    bearer header, and sending an API key that way returns 401.
    """
    url = f"{BASE}/{model or DEFAULT_MODEL}:generateContent"
    if key.startswith("ya29."):
        return url, {"Authorization": f"Bearer {key}"}
    return f"{url}?key={key}", {}


def extract_text(data: Any) -> Optional[str]:
    """
    Pull the answer text out of a generateContent response.

    Reasoning models put a thought part ahead of the answer and omit `text`
    on it entirely, so indexing parts[0]["text"] raises on exactly the
    responses that did succeed. Joining every non-thought part is stable
    across both model families.
    """
    try:
        parts = data["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError):
        return None

    chunks = [
        part["text"]
        for part in parts
        if isinstance(part, dict) and not part.get("thought") and part.get("text")
    ]
    text = "".join(chunks).strip()
    return text or None

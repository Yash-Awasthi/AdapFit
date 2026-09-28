"""Check a forward: parses model JSON, drops untrusted sources, falls back to 'unverified'."""
from fastapi.testclient import TestClient

from app.api.v1.endpoints import chat
from app.main import app

c = TestClient(app)


def test_no_model_means_unverified(monkeypatch):
    async def none(*a, **k):
        return None
    monkeypatch.setattr(chat, "_call_gemini", none)
    monkeypatch.setattr(chat, "_call_groq", none)
    r = c.post("/api/v1/misinformation/check", json={"text": "Drinking hot water every hour kills all viruses."}).json()
    assert r["verdict"] == "unverified" and "PIB Fact Check" in r["sources"]


def test_model_reply_is_parsed_and_sources_filtered(monkeypatch):
    async def fake(*a, **k):
        return '{"verdict": "false", "explanation": "No.", "what_to_do": "Ignore it.", "sources": ["WHO", "Dr Random Blog"]}'
    monkeypatch.setattr(chat, "_call_gemini", fake)
    r = c.post("/api/v1/misinformation/check", json={"text": "Vaccines cause infertility in young women."}).json()
    assert r["verdict"] == "false" and r["sources"] == ["WHO"]


def test_an_emergency_in_the_text_gets_the_safety_reply():
    r = c.post("/api/v1/misinformation/check", json={"text": "I have crushing chest pain, will garlic help?"}).json()
    assert r["safety"]["category"] == "medical_emergency"

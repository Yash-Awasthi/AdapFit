"""TRACK 6: WebSocket streaming chat for real-time AI coaching responses."""

import json
import asyncio
import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.config import settings
from app.services.rag_knowledge import rag_retriever
from app.services.chat_actions import maybe_execute_action

router = APIRouter()


async def _stream_gemini(prompt: str, history: list[dict], system: str = "") -> str:
    """Call Gemini with a system instruction and user history, return full response."""
    contents = []
    if system:
        contents.append({"role": "user", "parts": [{"text": system}]})
        contents.append({"role": "model", "parts": [{"text": "Understood."}]})
    for msg in history[-10:]:
        role = "user" if msg.get("role") == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={settings.GOOGLE_AI_API_KEY}",
            json={"contents": contents, "generationConfig": {"maxOutputTokens": 1024}},
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    return ""


async def _stream_groq(prompt: str, history: list[dict]) -> str:
    """Call Groq Llama-3.3-70B as fallback."""
    messages = [{"role": "system", "content": "You are AdapFit, an expert AI fitness coach. Be concise, evidence-based, and motivating."}]
    for msg in history[-8:]:
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            json={"model": "llama-3.3-70b-versatile", "messages": messages, "max_tokens": 1024},
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    return ""


def _rule_fallback(message: str) -> str:
    """Offline fallback when no LLM key is configured — grounded in the RAG knowledge base."""
    entries = rag_retriever.retrieve(message, top_k=2)
    if entries:
        parts = [f"{e['content']} (source: {e['source']})" for e in entries]
        return " ".join(parts)

    msg = message.lower()
    if any(w in msg for w in ["tired", "fatigue", "exhausted"]):
        return "Your body is telling you to rest. Focus on sleep, hydration, and light mobility today. Training when exhausted increases injury risk."
    if any(w in msg for w in ["sore", "pain", "hurt"]):
        return "Listen to your body. If it's muscle soreness, light movement helps. If it's sharp or joint pain, rest and consider seeing a professional."
    if any(w in msg for w in ["rest", "day off", "skip"]):
        return "Rest days are where adaptation happens. Take it guilt-free — your muscles grow during recovery, not during training."
    if any(w in msg for w in ["motivation", "lazy", "don't want"]):
        return "Motivation follows action, not the other way around. Start with just 5 minutes. If you still want to stop after that, listen to your body."
    return "I'm here to help with your training, recovery, and nutrition. What do you need today?"


@router.websocket("/ws/{user_id}")
async def chat_websocket(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for streaming AI coach responses token-by-token."""
    await websocket.accept()
    history: list[dict] = []

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            message = data.get("message", "")
            if not message:
                continue

            history.append({"role": "user", "content": message})

            # Send typing indicator
            await websocket.send_json({"type": "status", "status": "thinking"})

            action_result = await maybe_execute_action(message, user_id)
            if action_result:
                response = action_result["reply"]
                history.append({"role": "assistant", "content": response})
                chunk_size = 20
                for i in range(0, len(response), chunk_size):
                    await websocket.send_json({"type": "chunk", "content": response[i : i + chunk_size]})
                    await asyncio.sleep(0.02)
                await websocket.send_json({
                    "type": "done", "model": "action", "full_response": response,
                    "action": action_result["data"],
                })
                continue

            knowledge_context = rag_retriever.build_context_string(message, max_tokens=600)
            grounded_prompt = f"{knowledge_context}\n\nUser's message: {message}" if knowledge_context else message

            # Try Gemini first, then Groq, then rules
            response = ""
            model_used = ""
            if settings.GOOGLE_AI_API_KEY:
                try:
                    response = await _stream_gemini(grounded_prompt, history)
                    model_used = "gemini-2.0-flash"
                except Exception:
                    pass

            if not response and settings.GROQ_API_KEY:
                try:
                    response = await _stream_groq(grounded_prompt, history)
                    model_used = "llama-3.3-70b"
                except Exception:
                    pass

            if not response:
                response = _rule_fallback(message)
                model_used = "rule-based"

            history.append({"role": "assistant", "content": response})

            # Stream response in chunks (simulate token streaming for UX)
            chunk_size = 20
            for i in range(0, len(response), chunk_size):
                chunk = response[i : i + chunk_size]
                await websocket.send_json({"type": "chunk", "content": chunk})
                await asyncio.sleep(0.02)  # 20ms between chunks for smooth streaming

            # Send completion signal
            await websocket.send_json({
                "type": "done",
                "model": model_used,
                "full_response": response,
            })

    except WebSocketDisconnect:
        # Store conversation summary for memory
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass

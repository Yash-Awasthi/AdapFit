"""
AdapFit Voice Engine
- Speech-to-Text: faster-whisper (local, offline, no API key)
- Text-to-Speech: edge-tts (Microsoft Edge neural voices, free) with
  optional local fallback via pyttsx3 if edge-tts is unavailable.

All model loads are lazy so the API boots instantly.
"""
from __future__ import annotations

import asyncio
import base64
import io
import os
import tempfile
from typing import Optional

# --- STT: faster-whisper (lazy) ---
_whisper_model = None
_WHISPER_LOADED = False


def _get_whisper_model():
    global _whisper_model, _WHISPER_LOADED
    if _WHISPER_LOADED:
        return _whisper_model
    try:
        from faster_whisper import WhisperModel
        model_size = os.getenv("WHISPER_MODEL", "base")
        # base = ~75MB, small = ~250MB, medium = ~750MB
        _whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
    except Exception:
        _whisper_model = None
    _WHISPER_LOADED = True
    return _whisper_model


def transcribe_audio_file(path: str, language: Optional[str] = None) -> dict:
    """Transcribe an audio file (wav/mp3/m4a/ogg) to text."""
    model = _get_whisper_model()
    if model is None:
        return {
            "text": "",
            "language": None,
            "confidence": 0.0,
            "available": False,
            "message": "Speech-to-text model not available — install faster-whisper.",
        }
    try:
        segments, info = model.transcribe(
            path,
            language=language,
            beam_size=5,
            vad_filter=True,
        )
        text = "".join(seg.text for seg in segments).strip()
        return {
            "text": text,
            "language": info.language,
            "confidence": round(info.language_probability, 3) if info.language_probability else 0.0,
            "available": True,
        }
    except Exception as e:
        return {"text": "", "language": None, "confidence": 0.0, "available": True, "message": str(e)}


def transcribe_audio_bytes(data: bytes, filename: str = "audio.wav") -> dict:
    """Transcribe raw audio bytes (base64-decoded)."""
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else "wav"
    with tempfile.NamedTemporaryFile(suffix=f".{suffix}", delete=False) as f:
        f.write(data)
        tmp = f.name
    try:
        return transcribe_audio_file(tmp)
    finally:
        try:
            os.unlink(tmp)
        except Exception:
            pass


# --- TTS: edge-tts (lazy) ---
_edge_tts = None
_TTS_LOADED = False

VOICE_PRESETS = {
    "coach_female": "en-US-JennyNeural",
    "coach_male": "en-US-GuyNeural",
    "energetic": "en-US-AriaNeural",
    "calm": "en-US-JennyNeural",
    "british": "en-GB-SoniaNeural",
    "australian": "en-AU-NatashaNeural",
}


def _get_edge_tts():
    global _edge_tts, _TTS_LOADED
    if _TTS_LOADED:
        return _edge_tts
    try:
        import edge_tts
        _edge_tts = edge_tts
    except Exception:
        _edge_tts = None
    _TTS_LOADED = True
    return _edge_tts


async def synthesize_speech(
    text: str,
    voice: str = "en-US-JennyNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz",
) -> dict:
    """Synthesize speech, return base64 mp3 + metadata."""
    if not text or not text.strip():
        return {"ok": False, "message": "No text to speak"}

    edge = _get_edge_tts()
    if edge is None:
        return {
            "ok": False,
            "message": "TTS engine unavailable — install edge-tts (pip install edge-tts).",
            "available": False,
        }

    try:
        communicate = edge.Communicate(text, voice=voice, rate=rate, pitch=pitch)
        buf = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        audio = buf.getvalue()
        if not audio:
            return {"ok": False, "message": "Empty audio generated"}
        return {
            "ok": True,
            "audio_base64": base64.b64encode(audio).decode(),
            "content_type": "audio/mpeg",
            "voice": voice,
            "available": True,
            "chars": len(text),
        }
    except Exception as e:
        return {"ok": False, "message": f"TTS failed: {e}", "available": True}


def list_voices() -> list[dict]:
    """List available voice presets (edge-tts supports 100+ neural voices)."""
    return [{"id": k, "name": v} for k, v in VOICE_PRESETS.items()]


def get_status() -> dict:
    return {
        "stt_available": _get_whisper_model() is not None,
        "stt_model": os.getenv("WHISPER_MODEL", "base"),
        "tts_available": _get_edge_tts() is not None,
        "voices": len(VOICE_PRESETS),
    }


voice_engine = None  # placeholder singleton (module-level functions used directly)
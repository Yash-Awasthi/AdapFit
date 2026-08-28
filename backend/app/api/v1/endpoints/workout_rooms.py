"""Social Workout Rooms — multiplayer workout sessions via WebSocket.

Users can create or join workout rooms to train together virtually.
Features:
- Live participant count and status
- Shared workout timer
- Real-time exercise progress sharing
- Voice chat text cues
- Leaderboard within the room
"""

from __future__ import annotations
import asyncio
import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()

# Room state
_rooms: dict[str, dict] = {}
# user_id -> websocket
_user_connections: dict[str, WebSocket] = {}


class RoomCreateRequest(BaseModel):
    room_name: str = Field(min_length=1, max_length=50)
    workout_type: str = Field(default="strength")
    max_participants: int = Field(default=6, ge=2, le=12)
    is_public: bool = True


def _create_room(room_id: str, host_user_id: str, name: str, workout_type: str, max_participants: int, is_public: bool) -> dict:
    return {
        "room_id": room_id,
        "name": name,
        "host": host_user_id,
        "workout_type": workout_type,
        "max_participants": max_participants,
        "is_public": is_public,
        "participants": {host_user_id: {"user_id": host_user_id, "status": "ready", "exercises_done": 0, "current_exercise": ""}},
        "timer": {"running": False, "elapsed_seconds": 0, "interval_seconds": 60},
        "messages": [],
        "started_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/create")
async def create_room(req: RoomCreateRequest, user_id: str = Query("default")):
    """Create a new workout room."""
    room_id = str(uuid.uuid4())[:8]
    room = _create_room(room_id, user_id, req.room_name, req.workout_type, req.max_participants, req.is_public)
    _rooms[room_id] = room
    return {"room_id": room_id, "name": room["name"], "max_participants": room["max_participants"]}


@router.get("")
async def list_rooms(user_id: str = Query("default")):
    """List public workout rooms."""
    public = [r for r in _rooms.values() if r["is_public"]]
    return {
        "rooms": [
            {
                "room_id": r["room_id"],
                "name": r["name"],
                "host": r["host"],
                "workout_type": r["workout_type"],
                "participant_count": len(r["participants"]),
                "max_participants": r["max_participants"],
                "is_active": r["started_at"] is not None,
            }
            for r in public
        ],
        "total": len(public),
    }


@router.post("/{room_id}/join")
async def join_room(room_id: str, user_id: str = Query("default")):
    """Join a workout room."""
    room = _rooms.get(room_id)
    if not room:
        return {"error": "Room not found"}

    if len(room["participants"]) >= room["max_participants"]:
        return {"error": "Room is full"}

    if user_id in room["participants"]:
        return {"error": "Already in room"}

    room["participants"][user_id] = {
        "user_id": user_id,
        "status": "ready",
        "exercises_done": 0,
        "current_exercise": "",
    }

    return {"joined": True, "participant_count": len(room["participants"])}


@router.post("/{room_id}/leave")
async def leave_room(room_id: str, user_id: str = Query("default")):
    """Leave a workout room."""
    room = _rooms.get(room_id)
    if not room or user_id not in room["participants"]:
        return {"error": "Not in room"}

    del room["participants"][user_id]

    # Transfer host if needed
    if user_id == room["host"] and room["participants"]:
        room["host"] = next(iter(room["participants"]))

    # Delete room if empty
    if not room["participants"]:
        del _rooms[room_id]
        return {"left": True, "room_deleted": True}

    return {"left": True, "participant_count": len(room["participants"])}


@router.get("/{room_id}")
async def get_room(room_id: str, user_id: str = Query("default")):
    """Get room details."""
    room = _rooms.get(room_id)
    if not room:
        return {"error": "Room not found"}

    return {
        "room_id": room["room_id"],
        "name": room["name"],
        "host": room["host"],
        "workout_type": room["workout_type"],
        "participants": list(room["participants"].values()),
        "timer": room["timer"],
        "messages": room["messages"][-20:],
        "started_at": room["started_at"],
    }


@router.websocket("/ws/{room_id}")
async def room_websocket(websocket: WebSocket, room_id: str, user_id: str = Query("default")):
    """Real-time WebSocket for workout room.

    Messages:
    - {"type": "exercise_update", "exercise": "...", "reps": 10, "weight": 80}
    - {"type": "timer_start", "seconds": 60}
    - {"type": "timer_stop"}
    - {"type": "chat_message", "text": "Nice set!"}
    - {"type": "workout_complete", "exercises_done": 8}
    """
    await websocket.accept()
    _user_connections[user_id] = websocket

    # Add to room if not already
    room = _rooms.get(room_id)
    if room and user_id not in room["participants"]:
        room["participants"][user_id] = {
            "user_id": user_id, "status": "ready",
            "exercises_done": 0, "current_exercise": "",
        }

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            room = _rooms.get(room_id)
            if not room:
                break

            msg_type = msg.get("type", "")

            if msg_type == "exercise_update":
                participant = room["participants"].get(user_id, {})
                participant["current_exercise"] = msg.get("exercise", "")
                participant["last_reps"] = msg.get("reps", 0)
                participant["last_weight"] = msg.get("weight", 0)
                participant["last_update"] = datetime.now(timezone.utc).isoformat()
                room["participants"][user_id] = participant

                # Broadcast to all
                await _broadcast_room(room_id, {
                    "type": "exercise_update",
                    "user_id": user_id,
                    "exercise": msg.get("exercise"),
                    "reps": msg.get("reps"),
                    "weight": msg.get("weight"),
                })

            elif msg_type == "timer_start":
                room["timer"]["running"] = True
                room["timer"]["interval_seconds"] = msg.get("seconds", 60)
                room["timer"]["elapsed_seconds"] = 0
                room["started_at"] = datetime.now(timezone.utc).isoformat()
                await _broadcast_room(room_id, {"type": "timer_started", "seconds": msg.get("seconds", 60)})

            elif msg_type == "timer_stop":
                room["timer"]["running"] = False
                await _broadcast_room(room_id, {"type": "timer_stopped"})

            elif msg_type == "chat_message":
                chat = {"user_id": user_id, "text": msg.get("text", ""), "time": datetime.now(timezone.utc).isoformat()}
                room["messages"].append(chat)
                await _broadcast_room(room_id, {"type": "chat_message", **chat})

            elif msg_type == "workout_complete":
                participant = room["participants"].get(user_id, {})
                participant["status"] = "completed"
                participant["exercises_done"] = msg.get("exercises_done", 0)
                await _broadcast_room(room_id, {
                    "type": "workout_complete", "user_id": user_id,
                    "exercises_done": msg.get("exercises_done", 0),
                })

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    finally:
        _user_connections.pop(user_id, None)


async def _broadcast_room(room_id: str, data: dict):
    """Broadcast message to all participants in a room."""
    room = _rooms.get(room_id)
    if not room:
        return
    for uid in room["participants"]:
        ws = _user_connections.get(uid)
        if ws:
            try:
                await ws.send_json(data)
            except Exception:
                pass


@router.get("/{room_id}/leaderboard")
async def get_room_leaderboard(room_id: str):
    """Get real-time leaderboard within a room."""
    room = _rooms.get(room_id)
    if not room:
        return {"error": "Room not found"}

    participants = sorted(
        room["participants"].values(),
        key=lambda p: p.get("exercises_done", 0),
        reverse=True,
    )

    for i, p in enumerate(participants):
        p["rank"] = i + 1

    return {"leaderboard": participants, "total_participants": len(participants)}

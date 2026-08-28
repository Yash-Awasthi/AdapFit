"""WebSocket endpoint for real-time challenge leaderboard updates.

When a user joins, logs progress, or completes a milestone,
all connected clients in that challenge see the update instantly.
"""

from __future__ import annotations
import json
import asyncio
from collections import defaultdict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# challenge_id -> set of connected websockets
_connections: dict[str, set[WebSocket]] = defaultdict(set)
# challenge_id -> current leaderboard snapshot
_leaderboards: dict[str, list[dict]] = {}


async def broadcast_to_challenge(challenge_id: str, message: dict):
    """Send a message to all clients connected to a challenge."""
    dead = set()
    for ws in _connections.get(challenge_id, set()):
        try:
            await ws.send_json(message)
        except Exception:
            dead.add(ws)
    _connections[challenge_id] -= dead


def update_leaderboard_snapshot(challenge_id: str, entries: list[dict]):
    """Update the cached leaderboard for a challenge."""
    _leaderboards[challenge_id] = entries


@router.websocket("/ws/challenges/{challenge_id}")
async def challenge_websocket(websocket: WebSocket, challenge_id: str):
    """WebSocket for real-time challenge leaderboard."""
    await websocket.accept()
    _connections[challenge_id].add(websocket)

    # Send current leaderboard snapshot on connect
    snapshot = _leaderboards.get(challenge_id, [])
    await websocket.send_json({
        "type": "snapshot",
        "challenge_id": challenge_id,
        "leaderboard": snapshot,
        "connected_users": len(_connections[challenge_id]),
    })

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type", "")

            if msg_type == "progress_update":
                # Broadcast progress to all connected clients
                await broadcast_to_challenge(challenge_id, {
                    "type": "progress_update",
                    "user_id": data.get("user_id"),
                    "user_name": data.get("user_name", "Anonymous"),
                    "progress": data.get("progress", 0),
                    "value": data.get("value", 0),
                    "notes": data.get("notes", ""),
                })

            elif msg_type == "milestone":
                # Broadcast milestone achievement
                await broadcast_to_challenge(challenge_id, {
                    "type": "milestone",
                    "user_id": data.get("user_id"),
                    "user_name": data.get("user_name", "Anonymous"),
                    "milestone_pct": data.get("milestone_pct", 0),
                    "badge": data.get("badge", ""),
                })

            elif msg_type == "chat":
                # Simple in-challenge chat
                await broadcast_to_challenge(challenge_id, {
                    "type": "chat",
                    "user_id": data.get("user_id"),
                    "user_name": data.get("user_name", "Anonymous"),
                    "message": data.get("message", ""),
                })

    except WebSocketDisconnect:
        _connections[challenge_id].discard(websocket)
        if not _connections[challenge_id]:
            _connections.pop(challenge_id, None)
        # Notify remaining users
        await broadcast_to_challenge(challenge_id, {
            "type": "user_left",
            "connected_users": len(_connections.get(challenge_id, set())),
        })

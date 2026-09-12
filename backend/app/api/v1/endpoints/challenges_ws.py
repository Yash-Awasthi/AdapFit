"""WebSocket endpoint for real-time challenge leaderboard updates.

When a user joins, logs progress, or completes a milestone,
all connected clients in that challenge see the update instantly.
"""
from __future__ import annotations
import json
import time
from collections import defaultdict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.dependencies import authenticate_websocket

router = APIRouter()

# Module-level state is intentional — WebSocket connections are inherently
# cross-request. Move to a Redis adapter if scaling beyond one process.
_connections: dict[str, set[WebSocket]] = defaultdict(set)
_leaderboards: dict[str, list[dict]] = {}

# Rate limiting: per-connection message timestamps
_rate_limits: dict[WebSocket, list[float]] = defaultdict(list)
MAX_MESSAGES_PER_MINUTE = 30


def _is_rate_limited(ws: WebSocket) -> bool:
    """Check if a WebSocket connection is sending too many messages."""
    now = time.time()
    timestamps = _rate_limits[ws]
    # Remove timestamps older than 60 seconds
    _rate_limits[ws] = [t for t in timestamps if now - t < 60]
    if len(_rate_limits[ws]) >= MAX_MESSAGES_PER_MINUTE:
        return True
    _rate_limits[ws].append(now)
    return False


async def _authenticate_ws(websocket: WebSocket) -> str | None:
    """Validate the handshake token. Returns the caller's user_id, or None.

    Closes the socket itself when the token is missing or invalid, so callers
    only have to check for None.
    """
    user = await authenticate_websocket(websocket)
    return user["id"] if user else None


async def broadcast_to_challenge(challenge_id: str, message: dict):
    """Send a message to all clients connected to a challenge."""
    dead = set()
    for ws in _connections.get(challenge_id, set()):
        try:
            await ws.send_json(message)
        except Exception:
            dead.add(ws)
    _connections[challenge_id] -= dead


@router.websocket("/ws/challenges/{challenge_id}")
async def challenge_websocket(websocket: WebSocket, challenge_id: str, token: str = Query(default="")):
    """WebSocket for real-time challenge leaderboard."""
    # Authenticate before accepting; the helper closes the socket when it refuses.
    user_id = await _authenticate_ws(websocket)
    if not user_id:
        return

    await websocket.accept()
    _connections[challenge_id].add(websocket)

    # Send current leaderboard snapshot on connect
    snapshot = _leaderboards.get(challenge_id, [])
    await websocket.send_json({
        "type": "snapshot",
        "challenge_id": challenge_id,
        "leaderboard": snapshot,
        "connected_users": len(_connections[challenge_id]),
        "user_id": user_id,
    })

    # Notify others
    await broadcast_to_challenge(challenge_id, {
        "type": "user_joined",
        "user_id": user_id,
        "connected_users": len(_connections[challenge_id]),
    })

    try:
        while True:
            raw = await websocket.receive_text()

            # Rate limiting
            if _is_rate_limited(websocket):
                await websocket.send_json({"type": "error", "message": "Rate limit exceeded. Slow down."})
                continue

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type", "")

            if msg_type == "progress_update":
                await broadcast_to_challenge(challenge_id, {
                    "type": "progress_update",
                    "user_id": user_id,
                    "progress": data.get("progress", 0),
                    "value": data.get("value", 0),
                    "notes": data.get("notes", ""),
                })

            elif msg_type == "milestone":
                await broadcast_to_challenge(challenge_id, {
                    "type": "milestone",
                    "user_id": user_id,
                    "milestone_pct": data.get("milestone_pct", 0),
                    "badge": data.get("badge", ""),
                })

            elif msg_type == "chat":
                await broadcast_to_challenge(challenge_id, {
                    "type": "chat",
                    "user_id": user_id,
                    "message": data.get("message", "")[:500],
                })

    except WebSocketDisconnect:
        _connections[challenge_id].discard(websocket)
        _rate_limits.pop(websocket, None)
        if not _connections[challenge_id]:
            _connections.pop(challenge_id, None)
        await broadcast_to_challenge(challenge_id, {
            "type": "user_left",
            "user_id": user_id,
            "connected_users": len(_connections.get(challenge_id, set())),
        })

"""
AdapFit WebSocket Manager
Accepts connections and sends messages to connected users.
"""
import json
from typing import Dict, Set
from datetime import datetime, timezone


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set] = {}

    async def connect(self, websocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        await websocket.send_text(json.dumps({
            "type": "connected",
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }))

    def disconnect(self, websocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_to_user(self, user_id: str, message: dict):
        if user_id not in self.active_connections:
            return
        disconnected = set()
        for ws in self.active_connections[user_id]:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                disconnected.add(ws)
        for ws in disconnected:
            self.active_connections[user_id].discard(ws)

    async def push_alert(self, user_id: str, alert_type: str, message: str, severity: str = "info"):
        """Push an alert notification to a connected user."""
        await self.send_to_user(user_id, {
            "type": "alert",
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def push_recovery_update(self, user_id: str, recovery_score: int, state: str):
        """Push a recovery score update."""
        await self.send_to_user(user_id, {
            "type": "recovery_update",
            "recovery_score": recovery_score,
            "readiness_state": state,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def push_social_update(self, event_type: str, data: dict):
        """Broadcast a social event to ALL connected users."""
        message = {
            "type": "social_update",
            "event": event_type,
            **data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        disconnected = set()
        for user_id, connections in self.active_connections.items():
            for ws in connections:
                try:
                    await ws.send_text(json.dumps(message))
                except Exception:
                    disconnected.add((user_id, ws))
        for user_id, ws in disconnected:
            self.active_connections.get(user_id, set()).discard(ws)

    async def broadcast(self, message: dict):
        """Send a message to every connected user."""
        disconnected = set()
        for user_id, connections in self.active_connections.items():
            for ws in connections:
                try:
                    await ws.send_text(json.dumps(message))
                except Exception:
                    disconnected.add((user_id, ws))
        for user_id, ws in disconnected:
            self.active_connections.get(user_id, set()).discard(ws)

    def get_status(self) -> dict:
        return {
            "active_users": len(self.active_connections),
            "total_connections": sum(len(c) for c in self.active_connections.values()),
        }


ws_manager = WebSocketManager()

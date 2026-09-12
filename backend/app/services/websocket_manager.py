"""
AdapFit WebSocket Manager
Accepts connections and sends messages to connected users.
"""
import json
from typing import Dict, Set
from datetime import datetime, timezone


class WebSocketManager:
    # Maximum simultaneous connections per user (DoS / leak guard).
    MAX_CONNECTIONS_PER_USER = 5

    def __init__(self):
        self.active_connections: Dict[str, Set] = {}
        # Track last activity per websocket so a periodic sweep can detect
        # silently-dropped TCP connections (proxy timeout, mobile sleep, etc.).
        self._last_seen: Dict[int, float] = {}
        import time
        self._time = time  # injectable for tests

    async def connect(self, websocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        # Enforce per-user connection cap — drop the oldest if at the limit.
        if len(self.active_connections[user_id]) >= self.MAX_CONNECTIONS_PER_USER:
            oldest = next(iter(self.active_connections[user_id]))
            self.active_connections[user_id].discard(oldest)
            try:
                await oldest.close(code=1013, reason="max connections")
            except Exception:
                pass
        self.active_connections[user_id].add(websocket)
        self._last_seen[id(websocket)] = self._time.time()
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
        self._last_seen.pop(id(websocket), None)

    async def send_to_user(self, user_id: str, message: dict):
        if user_id not in self.active_connections:
            return
        text = json.dumps(message)
        disconnected = set()
        for ws in self.active_connections[user_id]:
            try:
                await ws.send_text(text)
                self._last_seen[id(ws)] = self._time.time()
            except Exception:
                disconnected.add(ws)
        for ws in disconnected:
            self.active_connections[user_id].discard(ws)
            self._last_seen.pop(id(ws), None)

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

    async def push_health_update(self, user_id: str, measurement_type: str, value: float,
                                  source: str = "", confidence: float = 1.0,
                                  metadata: dict | None = None):
        """Push a live health-data record to the user's connected clients.

        Called by the health-data ingestion endpoint whenever a new record is
        added, so the mobile app's charts update in real time without polling.
        """
        await self.send_to_user(user_id, {
            "type": "health_update",
            "measurement_type": measurement_type,
            "value": value,
            "source": source,
            "confidence": confidence,
            "metadata": metadata or {},
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

    async def sweep_stale(self, max_idle_seconds: float = 120):
        """Close connections that have been idle beyond ``max_idle_seconds``.

        Silently-dropped TCP sessions (proxy timeout, mobile backgrounding,
        WiFi loss) never deliver a close frame, so they linger in
        active_connections forever. A periodic sweep keeps the connection map
        honest. Returns the count of swept connections.
        """
        import asyncio
        now = self._time.time()
        swept = 0
        for user_id, conns in list(self.active_connections.items()):
            for ws in list(conns):
                ws_id = id(ws)
                last = self._last_seen.get(ws_id, now)
                if now - last > max_idle_seconds:
                    conns.discard(ws)
                    self._last_seen.pop(ws_id, None)
                    swept += 1
                    try:
                        await ws.close(code=1001, reason="idle timeout")
                    except Exception:
                        pass
            if not conns:
                self.active_connections.pop(user_id, None)
        return swept

    def get_status(self) -> dict:
        return {
            "active_users": len(self.active_connections),
            "total_connections": sum(len(c) for c in self.active_connections.values()),
        }


ws_manager = WebSocketManager()

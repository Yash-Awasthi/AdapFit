"""Event Bus — lightweight pub/sub for decoupled event-driven architecture.

Events flow: workout.completed, recovery.logged, achievement.unlocked,
user.goal_updated, challenge.progress, meal.logged, etc.

Consumers register handlers; producers fire events. No coupling.
"""

from __future__ import annotations
import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine
import uuid

logger = logging.getLogger("adapfit.events")


@dataclass
class Event:
    event_type: str
    payload: dict[str, Any]
    user_id: str = ""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = "system"


EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """In-process async event bus with topic-based routing."""

    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._history: list[Event] = []
        self._max_history = 500

    def subscribe(self, event_type: str, handler: EventHandler):
        """Register a handler for an event type. Use '*' for all events."""
        self._handlers[event_type].append(handler)
        logger.debug(f"Subscribed to {event_type}: {handler.__name__}")

    def unsubscribe(self, event_type: str, handler: EventHandler):
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    async def emit(self, event_type: str, payload: dict, user_id: str = "", source: str = "system"):
        """Fire an event asynchronously."""
        event = Event(
            event_type=event_type,
            payload=payload,
            user_id=user_id,
            source=source,
        )
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        handlers = self._handlers.get(event_type, []) + self._handlers.get("*", [])
        if not handlers:
            logger.debug(f"No handlers for {event_type}")
            return

        results = await asyncio.gather(
            *(self._safe_call(h, event) for h in handlers),
            return_exceptions=True,
        )
        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            logger.exception(f"Event {event_type} had {len(errors)} handler errors")

    def emit_sync(self, event_type: str, payload: dict, user_id: str = "", source: str = "system"):
        """Fire an event synchronously (queues for async processing)."""
        event = Event(
            event_type=event_type,
            payload=payload,
            user_id=user_id,
            source=source,
        )
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        # Sync handlers run immediately
        for handler in self._handlers.get(event_type, []):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(self._safe_call(handler, event))
                else:
                    loop.run_until_complete(self._safe_call(handler, event))
            except RuntimeError:
                pass

    @staticmethod
    async def _safe_call(handler: EventHandler, event: Event):
        try:
            await handler(event)
        except Exception as e:
            logger.exception(f"Handler {handler.__name__} failed for {event.event_type}")

    def get_history(self, event_type: str = "", limit: int = 50) -> list[dict]:
        events = self._history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return [
            {
                "event_id": e.event_id,
                "event_type": e.event_type,
                "user_id": e.user_id,
                "payload": e.payload,
                "timestamp": e.timestamp,
                "source": e.source,
            }
            for e in events[-limit:]
        ]

    def get_subscriptions(self) -> dict[str, int]:
        return {k: len(v) for k, v in self._handlers.items()}


# Global event bus instance
event_bus = EventBus()


# Built-in event types
class EventTypes:
    WORKOUT_COMPLETED = "workout.completed"
    WORKOUT_STARTED = "workout.started"
    RECOVERY_LOGGED = "recovery.logged"
    ACHIEVEMENT_UNLOCKED = "achievement.unlocked"
    GOAL_MILESTONE = "goal.milestone"
    GOAL_ACHIEVED = "goal.achieved"
    CHALLENGE_JOINED = "challenge.joined"
    CHALLENGE_PROGRESS = "challenge.progress"
    CHALLENGE_COMPLETED = "challenge.completed"
    MEAL_LOGGED = "meal.logged"
    SLEEP_LOGGED = "sleep.logged"
    PR_LOGGED = "pr.logged"
    STREAK_UPDATED = "streak.updated"
    HYDRATION_LOGGED = "hydration.logged"
    DAILY_CHECKIN = "daily.checkin"
    INJURY_RISK_ALERT = "injury.risk_alert"
    ACWR_ALERT = "acwr.alert"
    VOICE_INPUT = "voice.input"
    FEED_POST = "feed.post"
    WORKOUT_SHARED = "workout.shared"

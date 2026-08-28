"""Request Deduplication — idempotency keys for POST endpoints.

Prevents duplicate processing when:
- Network retries cause duplicate requests
- User double-taps submit button
- Mobile app resends after timeout

Uses idempotency key header or auto-generated key from request hash.
"""

from __future__ import annotations
import hashlib
import json
import time
import threading
from typing import Optional
from dataclasses import dataclass


@dataclass
class IdempotencyRecord:
    key: str
    status: str  # "processing", "completed", "failed"
    response: Optional[dict] = None
    created_at: float = 0
    expires_at: float = 0


class DeduplicationStore:
    """In-memory idempotency store with TTL cleanup."""

    def __init__(self, ttl_seconds: float = 86400, max_entries: int = 10000):
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._store: dict[str, IdempotencyRecord] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[IdempotencyRecord]:
        with self._lock:
            record = self._store.get(key)
            if record and record.expires_at > time.time():
                return record
            elif record:
                del self._store[key]
            return None

    def set_processing(self, key: str) -> bool:
        """Mark key as processing. Returns False if already exists."""
        with self._lock:
            if key in self._store and self._store[key].expires_at > time.time():
                return False

            self._cleanup_if_needed()
            self._store[key] = IdempotencyRecord(
                key=key,
                status="processing",
                created_at=time.time(),
                expires_at=time.time() + self.ttl_seconds,
            )
            return True

    def set_completed(self, key: str, response: dict):
        with self._lock:
            if key in self._store:
                self._store[key].status = "completed"
                self._store[key].response = response

    def set_failed(self, key: str, error: str):
        with self._lock:
            if key in self._store:
                self._store[key].status = "failed"
                self._store[key].response = {"error": error}

    def _cleanup_if_needed(self):
        if len(self._store) >= self.max_entries:
            now = time.time()
            expired = [k for k, v in self._store.items() if v.expires_at <= now]
            for k in expired[:len(expired) // 2]:
                del self._store[k]


# Global store
_dedup_store = DeduplicationStore()


def generate_idempotency_key(method: str, path: str, body: Optional[dict] = None, user_id: str = "") -> str:
    """Generate an idempotency key from request details."""
    content = f"{method}:{path}:{json.dumps(body or {}, sort_keys=True)}:{user_id}"
    return hashlib.sha256(content.encode()).hexdigest()[:32]


def check_duplicate(idempotency_key: str) -> Optional[dict]:
    """Check if request is a duplicate. Returns cached response or None."""
    record = _dedup_store.get(idempotency_key)
    if record:
        if record.status == "completed":
            return record.response
        elif record.status == "processing":
            return {"error": "Request already being processed", "idempotency_key": idempotency_key}
    return None


def mark_processing(idempotency_key: str) -> bool:
    """Mark request as processing. Returns True if first attempt."""
    return _dedup_store.set_processing(idempotency_key)


def mark_completed(idempotency_key: str, response: dict):
    """Mark request as completed with response."""
    _dedup_store.set_completed(idempotency_key, response)


def mark_failed(idempotency_key: str, error: str):
    """Mark request as failed."""
    _dedup_store.set_failed(idempotency_key, error)


def get_dedup_stats() -> dict:
    return {
        "total_entries": len(_dedup_store._store),
        "max_entries": _dedup_store.max_entries,
        "ttl_seconds": _dedup_store.ttl_seconds,
    }

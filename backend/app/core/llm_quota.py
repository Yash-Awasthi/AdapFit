"""
Daily cap on language model calls per account, so free use stays affordable.

Every call site asks `ai_call_allowed()`, which is the AI consent check plus
one unit of today's quota; over the cap the caller takes its rule-based
fallback. Counts reset at UTC midnight.
"""
import os
from datetime import datetime, timezone
from typing import Optional

from app.core.durable import durable_dict
from app.core.privacy import _is_account, allowed, current_user_id

DAILY_CALLS = int(os.getenv("LLM_DAILY_CALLS", "60"))
_used = durable_dict("app.core.llm_quota.used")  # user id -> [day, calls]


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def remaining(uid: Optional[str] = None) -> int:
    uid = uid or current_user_id()
    day, calls = _used.get(uid) or [_today(), 0]
    return DAILY_CALLS - (calls if day == _today() else 0)


def ai_call_allowed(uid: Optional[str] = None) -> bool:
    """AI consent granted and a call left today; counts the call."""
    uid = uid or current_user_id()
    if not allowed("ai", uid):
        return False
    if not _is_account(uid):
        return True
    left = remaining(uid)
    if left <= 0:
        return False
    _used[uid] = [_today(), DAILY_CALLS - left + 1]
    return True

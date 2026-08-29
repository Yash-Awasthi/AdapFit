"""
Canonical user identifiers.

Every user_id column is `uuid`, but the seeded development identity and several
older call sites pass the literal string "default". Postgres rejects that with
`invalid input syntax for type uuid`, and the failure previously surfaced as a
lost write rather than an error, so the mapping happens once here instead of at
each call site.
"""
import uuid
from typing import Optional

# Derived rather than random so the same identity is produced on every machine
# and across restarts without needing to be stored anywhere.
DEV_USER_UUID = str(uuid.uuid5(uuid.NAMESPACE_DNS, "adapfit.dev.default"))

_ALIASES = {"default", "dev", "demo", "me", ""}


def normalize_user_id(user_id: Optional[str]) -> str:
    """
    Return a value usable as a `uuid` column.

    Known aliases map onto the seeded development user. Anything already a
    valid UUID passes through untouched. Anything else is folded into a stable
    UUID derived from the string, so an unexpected identifier degrades to a
    consistent row rather than a database error.
    """
    if user_id is None or str(user_id).strip().lower() in _ALIASES:
        return DEV_USER_UUID
    candidate = str(user_id).strip()
    try:
        return str(uuid.UUID(candidate))
    except ValueError:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"adapfit.user.{candidate}"))

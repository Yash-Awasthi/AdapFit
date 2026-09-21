"""
Per-user service state.

Most feature services are module-level singletons holding plain dicts —
`medication_reminder_service.get_today_schedule()` reads one list that every
account on the server shares. That is invisible with one user and wrong with
two.

`per_user(ServiceClass)` replaces the singleton with a proxy that keeps one
instance per caller and forwards every attribute to the right one, so a service
becomes per-user by changing the line that constructs it rather than every
endpoint that calls it.

Reference services — the exercise catalogue, the drug database, the vector
store — must stay shared; state there is the same for everyone and duplicating
it per user wastes memory and loses whatever was loaded at startup.
"""
from collections import OrderedDict
from contextvars import ContextVar
from threading import Lock
from typing import Any, Callable, Dict, Optional, TypeVar

# Set per request by IdentityMiddleware. None outside a request — a startup
# hook, a background job, a test — which is what SHARED covers.
CURRENT_USER: ContextVar[Optional[str]] = ContextVar("adapfit_current_user", default=None)

SHARED = "__shared__"

# Instances are cheap dict-holders, but an unbounded map keyed by user id is a
# memory leak on a busy server. The least recently used instance is dropped
# past this, which loses in-memory state for a user who has been idle longest.
# ponytail: acceptable while these services are memory-backed. Services whose
# state must survive eviction belong in storage, not here.
MAX_INSTANCES = 512

T = TypeVar("T")


def current_user_id() -> str:
    """The caller this request belongs to, or SHARED outside a request."""
    return CURRENT_USER.get() or SHARED


class PerUserProxy:
    """One service instance per user, addressed through a single name."""

    def __init__(self, factory: Callable[[], Any], max_instances: int = MAX_INSTANCES):
        object.__setattr__(self, "_factory", factory)
        object.__setattr__(self, "_instances", OrderedDict())
        object.__setattr__(self, "_lock", Lock())
        object.__setattr__(self, "_max_instances", max_instances)

    def instance_for(self, user_id: str) -> Any:
        instances: "OrderedDict[str, Any]" = object.__getattribute__(self, "_instances")
        lock: Lock = object.__getattribute__(self, "_lock")
        with lock:
            if user_id in instances:
                instances.move_to_end(user_id)
                return instances[user_id]
            instance = object.__getattribute__(self, "_factory")()
            instances[user_id] = instance
            while len(instances) > object.__getattribute__(self, "_max_instances"):
                instances.popitem(last=False)
            return instance

    @property
    def current(self) -> Any:
        return self.instance_for(current_user_id())

    def reset(self, user_id: Optional[str] = None) -> None:
        """Drop one user's state, or everyone's. Used by tests and by account deletion."""
        instances = object.__getattribute__(self, "_instances")
        lock = object.__getattribute__(self, "_lock")
        with lock:
            if user_id is None:
                instances.clear()
            else:
                instances.pop(user_id, None)

    def tracked_users(self) -> int:
        return len(object.__getattribute__(self, "_instances"))

    # Attribute access is the whole point: callers keep writing
    # `service.method(...)` and reach their own instance.
    def __getattr__(self, name: str) -> Any:
        return getattr(self.current, name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(self.current, name, value)

    def __repr__(self) -> str:
        factory = object.__getattribute__(self, "_factory")
        return f"<per-user {getattr(factory, '__name__', factory)} users={self.tracked_users()}>"


def per_user(factory: Callable[[], T], max_instances: int = MAX_INSTANCES) -> T:
    """
    A service whose state is private to each caller.

        medication_reminder_service = per_user(MedicationReminderService)

    Typed as the service itself so call sites and type checkers are unchanged.
    """
    return PerUserProxy(factory, max_instances)  # type: ignore[return-value]


_registry: Dict[str, PerUserProxy] = {}


def register(name: str, proxy: PerUserProxy) -> PerUserProxy:
    """Record a proxy so a deleted account's state can be dropped everywhere."""
    _registry[name] = proxy
    return proxy


def forget_user(user_id: str) -> int:
    """Drop every service's state for one user. Returns how many were cleared."""
    for proxy in _registry.values():
        proxy.reset(user_id)
    return len(_registry)

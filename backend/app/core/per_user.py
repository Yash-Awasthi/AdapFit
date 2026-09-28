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

# No eviction: instances are the live copy of state persisted by app.core.durable,
# and a dropped instance would be recreated empty and saved over the stored one.
MAX_INSTANCES = None

T = TypeVar("T")


def current_user_id() -> str:
    """The caller this request belongs to, or SHARED outside a request."""
    return CURRENT_USER.get() or SHARED


class PerUserProxy:
    """One service instance per user, addressed through a single name."""

    def __init__(self, factory: Callable[[], Any], max_instances: Optional[int] = MAX_INSTANCES):
        object.__setattr__(self, "_ns", None)
        object.__setattr__(self, "_factory", factory)
        object.__setattr__(self, "_instances", OrderedDict())
        object.__setattr__(self, "_lock", Lock())
        object.__setattr__(self, "_max_instances", max_instances)

    def instance_for(self, user_id: str) -> Any:
        instances: "OrderedDict[str, Any]" = object.__getattribute__(self, "_instances")
        lock: Lock = object.__getattribute__(self, "_lock")
        ns = object.__getattribute__(self, "_ns")
        if ns:
            from app.core import durable
            durable.touch(ns, user_id)
        with lock:
            if user_id in instances:
                instances.move_to_end(user_id)
                return instances[user_id]
            instance = object.__getattribute__(self, "_factory")()
            instances[user_id] = instance
            cap = object.__getattribute__(self, "_max_instances")
            while cap and len(instances) > cap:
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


def per_user(factory: Callable[[], T], max_instances: Optional[int] = MAX_INSTANCES) -> T:
    """
    A service whose state is private to each caller.

        medication_reminder_service = per_user(MedicationReminderService)

    Typed as the service itself so call sites and type checkers are unchanged.
    """
    return PerUserProxy(factory, max_instances)  # type: ignore[return-value]


_registry: Dict[str, PerUserProxy] = {}


def register(name: str, proxy: PerUserProxy) -> PerUserProxy:
    """Record a proxy so its state persists and a deleted account's state can be dropped everywhere."""
    from app.core import durable

    _registry[name] = proxy
    object.__setattr__(proxy, "_ns", name)
    durable.track_per_user(name, proxy)
    return proxy


def forget_user(user_id: str) -> int:
    """Drop every service's state for one user. Returns how many were cleared."""
    for proxy in _registry.values():
        proxy.reset(user_id)
    return len(_registry)


def _plain(value: Any) -> Any:
    import dataclasses
    from datetime import date, datetime
    from enum import Enum

    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {k: _plain(v) for k, v in dataclasses.asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_plain(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def export_user(user_id: str) -> Dict[str, Any]:
    """Everything each per-user service holds for one user, as plain JSON-able data."""
    out: Dict[str, Any] = {}
    for name, proxy in _registry.items():
        instances = object.__getattribute__(proxy, "_instances")
        instance = instances.get(user_id)
        if instance is None:
            continue
        state = {k: _plain(v) for k, v in vars(instance).items() if v not in (None, [], {}, "", set())}
        if state:
            out[name] = state
    return out

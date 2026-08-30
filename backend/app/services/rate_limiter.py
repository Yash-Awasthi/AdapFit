"""Rate Limiter Service.

Extracted from tapiriik (inspiration).
Token bucket rate limiting with sliding window, burst support,
and per-service limits.

All pure functions — no DB, no async.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_second: float = 10.0
    requests_per_minute: float = 100.0
    requests_per_hour: float = 1000.0
    burst_size: int = 20
    burst_window_seconds: float = 1.0


@dataclass
class RateLimitState:
    """Current state of rate limiter."""
    tokens: float
    last_refill: float
    request_count_minute: int = 0
    request_count_hour: int = 0
    minute_window_start: float = 0.0
    hour_window_start: float = 0.0


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    remaining_tokens: float
    retry_after: Optional[float] = None
    limit: int = 0
    remaining: int = 0
    reset_at: Optional[float] = None


# --- Token Bucket ---

def create_rate_limiter(config: RateLimitConfig = RateLimitConfig()) -> RateLimitState:
    """Create a new rate limiter state.

    Args:
        config: Rate limit configuration

    Returns:
        Initial rate limiter state
    """
    return RateLimitState(
        tokens=float(config.burst_size),
        last_refill=time.time(),
    )


def refill_tokens(
    state: RateLimitState,
    config: RateLimitConfig,
    now: Optional[float] = None,
) -> RateLimitState:
    """Refill tokens based on elapsed time.

    Args:
        state: Current rate limiter state
        config: Rate limit configuration
        now: Current timestamp

    Returns:
        Updated state
    """
    if now is None:
        now = time.time()

    elapsed = now - state.last_refill
    new_tokens = elapsed * config.requests_per_second
    tokens = min(config.burst_size, state.tokens + new_tokens)

    return RateLimitState(
        tokens=tokens,
        last_refill=now,
        request_count_minute=state.request_count_minute,
        request_count_hour=state.request_count_hour,
        minute_window_start=state.minute_window_start,
        hour_window_start=state.hour_window_start,
    )


def check_rate_limit(
    state: RateLimitState,
    config: RateLimitConfig,
    now: Optional[float] = None,
) -> tuple[RateLimitResult, RateLimitState]:
    """Check if a request is allowed under rate limits.

    Args:
        state: Current rate limiter state
        config: Rate limit configuration
        now: Current timestamp

    Returns:
        Tuple of (result, updated_state)
    """
    if now is None:
        now = time.time()

    # Refill tokens first
    state = refill_tokens(state, config, now)

    # Check token bucket
    if state.tokens < 1:
        wait_time = (1 - state.tokens) / config.requests_per_second
        return RateLimitResult(
            allowed=False,
            remaining_tokens=state.tokens,
            retry_after=round(wait_time, 3),
            remaining=0,
        ), state

    # Check minute window
    if now - state.minute_window_start >= 60:
        state.request_count_minute = 0
        state.minute_window_start = now

    if state.request_count_minute >= config.requests_per_minute:
        reset_at = state.minute_window_start + 60
        return RateLimitResult(
            allowed=False,
            remaining_tokens=state.tokens,
            retry_after=round(reset_at - now, 3),
            remaining=0,
            reset_at=reset_at,
        ), state

    # Check hour window
    if now - state.hour_window_start >= 3600:
        state.request_count_hour = 0
        state.hour_window_start = now

    if state.request_count_hour >= config.requests_per_hour:
        reset_at = state.hour_window_start + 3600
        return RateLimitResult(
            allowed=False,
            remaining_tokens=state.tokens,
            retry_after=round(reset_at - now, 3),
            remaining=0,
            reset_at=reset_at,
        ), state

    # Allow request
    new_state = RateLimitState(
        tokens=state.tokens - 1,
        last_refill=now,
        request_count_minute=state.request_count_minute + 1,
        request_count_hour=state.request_count_hour + 1,
        minute_window_start=state.minute_window_start,
        hour_window_start=state.hour_window_start,
    )

    remaining = min(
        int(new_state.tokens),
        config.requests_per_minute - new_state.request_count_minute,
        config.requests_per_hour - new_state.request_count_hour,
    )

    return RateLimitResult(
        allowed=True,
        remaining_tokens=new_state.tokens,
        remaining=remaining,
        limit=config.requests_per_minute,
    ), new_state


# --- Sliding Window ---

def create_sliding_window(
    max_requests: int,
    window_seconds: float = 60.0,
) -> dict:
    """Create a sliding window rate limiter.

    Args:
        max_requests: Maximum requests in window
        window_seconds: Window duration in seconds

    Returns:
        Sliding window state
    """
    return {
        "max_requests": max_requests,
        "window_seconds": window_seconds,
        "timestamps": [],
    }


def check_sliding_window(
    window: dict,
    now: Optional[float] = None,
) -> tuple[bool, float]:
    """Check sliding window rate limit.

    Args:
        window: Sliding window state
        now: Current timestamp

    Returns:
        Tuple of (allowed, retry_after)
    """
    if now is None:
        now = time.time()

    cutoff = now - window["window_seconds"]
    window["timestamps"] = [t for t in window["timestamps"] if t > cutoff]

    if len(window["timestamps"]) >= window["max_requests"]:
        oldest = window["timestamps"][0]
        retry_after = oldest + window["window_seconds"] - now
        return False, max(0, retry_after)

    window["timestamps"].append(now)
    return True, 0.0


# --- Per-Service Limits ---

def create_service_rate_limiter(
    services: dict[str, RateLimitConfig],
) -> dict[str, RateLimitState]:
    """Create rate limiters for multiple services.

    Args:
        services: Dict of service_name -> config

    Returns:
        Dict of service_name -> state
    """
    return {name: create_rate_limiter(config) for name, config in services.items()}


def check_service_rate_limit(
    limiters: dict[str, RateLimitState],
    service_name: str,
    configs: dict[str, RateLimitConfig],
    now: Optional[float] = None,
) -> RateLimitResult:
    """Check rate limit for a specific service.

    Args:
        limiters: Service rate limiter states
        service_name: Service to check
        configs: Service configurations
        now: Current timestamp

    Returns:
        Rate limit result
    """
    if service_name not in configs:
        return RateLimitResult(
            allowed=True,
            remaining_tokens=999,
            remaining=999,
        )

    state = limiters.get(service_name, create_rate_limiter(configs[service_name]))
    config = configs[service_name]

    result, new_state = check_rate_limit(state, config, now)
    limiters[service_name] = new_state

    return result


# --- Refresh ---

def refresh_rate_limits(
    limiters: dict[str, RateLimitState],
    configs: dict[str, RateLimitConfig],
    now: Optional[float] = None,
) -> dict[str, RateLimitState]:
    """Refresh all rate limiters.

    Args:
        limiters: Current rate limiter states
        configs: Service configurations
        now: Current timestamp

    Returns:
        Updated rate limiter states
    """
    if now is None:
        now = time.time()

    refreshed = {}
    for name, config in configs.items():
        state = limiters.get(name, create_rate_limiter(config))
        refreshed[name] = refill_tokens(state, config, now)

    return refreshed

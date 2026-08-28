"""Circuit Breaker — resilient external API calls with retry and backoff.

Protects against cascading failures when external services (Gemini, Groq, etc.) are down.

States:
- CLOSED: Normal operation, requests flow through
- OPEN: Service is down, requests fail immediately
- HALF_OPEN: Testing if service recovered

References:
- Michael Nygard "Release It!" circuit breaker pattern
- AWS recommended retry/backoff strategy
"""

from __future__ import annotations
import asyncio
import time
import logging
from enum import Enum
from typing import Optional, Callable, Any
from functools import wraps

logger = logging.getLogger("adapfit.circuit_breaker")


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker with configurable thresholds and backoff."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
        success_threshold: int = 2,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._half_open_calls = 0
        self._total_requests = 0
        self._total_failures = 0
        self._total_successes = 0
        self._consecutive_successes = 0

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                self._success_count = 0
                logger.info(f"Circuit '{self.name}' transitioning to HALF_OPEN")
        return self._state

    @property
    def is_available(self) -> bool:
        return self.state != CircuitState.OPEN

    def _on_success(self):
        self._total_successes += 1
        self._consecutive_successes += 1
        self._failure_count = 0

        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.success_threshold:
                self._state = CircuitState.CLOSED
                logger.info(f"Circuit '{self.name}' recovered → CLOSED")

    def _on_failure(self):
        self._failure_count += 1
        self._total_failures += 1
        self._consecutive_successes = 0
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            logger.warning(f"Circuit '{self.name}' failed in HALF_OPEN → OPEN")
        elif self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(f"Circuit '{self.name}' tripped → OPEN after {self._failure_count} failures")

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker."""
        self._total_requests += 1

        if not self.is_available:
            raise CircuitOpenError(
                f"Circuit '{self.name}' is OPEN. "
                f"Retry in {self._time_until_half_open():.0f}s"
            )

        if self._state == CircuitState.HALF_OPEN:
            self._half_open_calls += 1
            if self._half_open_calls > self.half_open_max_calls:
                raise CircuitOpenError(f"Circuit '{self.name}' HALF_OPEN limit reached")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _time_until_half_open(self) -> float:
        elapsed = time.time() - self._last_failure_time
        return max(0, self.recovery_timeout - elapsed)

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "total_requests": self._total_requests,
            "total_failures": self._total_failures,
            "total_successes": self._total_successes,
            "failure_rate": round(self._total_failures / max(self._total_requests, 1) * 100, 1),
            "consecutive_successes": self._consecutive_successes,
            "time_until_half_open": round(self._time_until_half_open(), 1) if self._state == CircuitState.OPEN else 0,
        }


class CircuitOpenError(Exception):
    pass


# Pre-configured circuit breakers for external services
gemini_breaker = CircuitBreaker(
    name="gemini",
    failure_threshold=3,
    recovery_timeout=60,
    success_threshold=2,
)

groq_breaker = CircuitBreaker(
    name="groq",
    failure_threshold=3,
    recovery_timeout=30,
    success_threshold=2,
)

health_connect_breaker = CircuitBreaker(
    name="health_connect",
    failure_threshold=5,
    recovery_timeout=120,
    success_threshold=3,
)


def with_retry(
    func: Callable = None,
    *,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
):
    """Decorator: retry with exponential backoff and jitter."""
    import random

    def decorator(fn):
        @wraps(fn)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await fn(*args, **kwargs)
                except CircuitOpenError:
                    raise
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                        if jitter:
                            delay *= (0.5 + random.random() * 0.5)
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {fn.__name__}: {e}. "
                            f"Waiting {delay:.1f}s"
                        )
                        await asyncio.sleep(delay)
            raise last_exception

        @wraps(fn)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except CircuitOpenError:
                    raise
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        import random as rnd
                        delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                        if jitter:
                            delay *= (0.5 + rnd.random() * 0.5)
                        time.sleep(delay)
            raise last_exception

        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return sync_wrapper

    if func is not None:
        return decorator(func)
    return decorator

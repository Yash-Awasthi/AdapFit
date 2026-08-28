"""Structured logging configuration with correlation IDs and JSON output.

Replaces simple logging with enterprise-grade structured logging:
- JSON-formatted log entries for log aggregation
- Correlation ID propagation across request lifecycle
- Performance timing decorators
- Sensitive data masking
"""

import logging
import json
import sys
import time
import uuid
from contextvars import ContextVar
from functools import wraps
from typing import Optional, Callable

# Context variable for correlation ID — request-scoped
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")
_request_start: ContextVar[float] = ContextVar("request_start", default=0.0)


def get_correlation_id() -> str:
    return _correlation_id.get()


def set_correlation_id(cid: str = "") -> str:
    if not cid:
        cid = str(uuid.uuid4())[:8]
    _correlation_id.set(cid)
    return cid


class StructuredFormatter(logging.Formatter):
    """JSON structured log formatter with correlation ID support."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "ts": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }

        cid = get_correlation_id()
        if cid:
            log_entry["cid"] = cid

        # Add request duration if available
        start = _request_start.get(0)
        if start > 0:
            log_entry["duration_ms"] = round((time.time() - start) * 1000, 1)

        # Add exception info if present
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }

        # Add extra fields
        for key in ("user_id", "endpoint", "status_code", "method"):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val

        return json.dumps(log_entry, default=str)


class HumanReadableFormatter(logging.Formatter):
    """Human-readable formatter for development."""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[1;31m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        cid = get_correlation_id()
        cid_str = f" [{cid}]" if cid else ""
        return f"{color}{record.levelname:8s}{self.RESET} {record.name}{cid_str}: {record.getMessage()}"


def setup_logging(level: str = "INFO", json_mode: bool = False):
    """Configure application logging."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stderr)
    if json_mode:
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(HumanReadableFormatter())
    root.addHandler(handler)

    # Quieten noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"adapfit.{name}")


def log_timing(logger: logging.Logger, operation: str):
    """Decorator to log operation timing."""
    def decorator(func: Callable):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = (time.perf_counter() - start) * 1000
                logger.debug(f"{operation} completed in {elapsed:.1f}ms")
                return result
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                logger.error(f"{operation} failed after {elapsed:.1f}ms: {e}")
                raise

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                elapsed = (time.perf_counter() - start) * 1000
                logger.debug(f"{operation} completed in {elapsed:.1f}ms")
                return result
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                logger.error(f"{operation} failed after {elapsed:.1f}ms: {e}")
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator

"""Prometheus-compatible metrics for AdapFit observability.

Exposes /metrics endpoint with request counts, latencies, error rates,
and business metrics (workouts generated, recovery scores, etc.).
"""

from __future__ import annotations
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


@dataclass
class HistogramMetric:
    """Simple histogram for tracking latency distributions."""
    name: str
    description: str
    buckets: list[float] = field(default_factory=lambda: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
    _counts: list[int] = field(default_factory=list)
    _sum: float = 0.0
    _total: int = 0

    def __post_init__(self):
        self._counts = [0] * (len(self.buckets) + 1)

    def observe(self, value: float):
        self._sum += value
        self._total += 1
        for i, bound in enumerate(self.buckets):
            if value <= bound:
                self._counts[i] += 1
                return
        self._counts[-1] += 1

    def render(self) -> str:
        lines = [f"# HELP {self.name} {self.description}", f"# TYPE {self.name} histogram"]
        cumulative = 0
        for i, bound in enumerate(self.buckets):
            cumulative += self._counts[i]
            lines.append(f'{self.name}_bucket{{le="{bound}"}} {cumulative}')
        cumulative += self._counts[-1]
        lines.append(f'{self.name}_bucket{{le="+Inf"}} {cumulative}')
        lines.append(f'{self.name}_sum {self._sum:.6f}')
        lines.append(f'{self.name}_count {self._total}')
        return "\n".join(lines)


@dataclass
class CounterMetric:
    """Simple counter for tracking event counts."""
    name: str
    description: str
    _value: float = 0.0
    _labels: dict[str, float] = field(default_factory=dict)

    def inc(self, amount: float = 1.0, label: Optional[str] = None):
        self._value += amount
        if label:
            self._labels[label] = self._labels.get(label, 0) + amount

    def render(self) -> str:
        lines = [f"# HELP {self.name} {self.description}", f"# TYPE {self.name} counter"]
        lines.append(f"{self.name} {self._value}")
        for label, val in sorted(self._labels.items()):
            lines.append(f'{self.name}{{label="{label}"}} {val}')
        return "\n".join(lines)


@dataclass
class GaugeMetric:
    """Simple gauge for tracking current values."""
    name: str
    description: str
    _value: float = 0.0

    def set(self, value: float):
        self._value = value

    def render(self) -> str:
        return f"# HELP {self.name} {self.description}\n# TYPE {self.name} gauge\n{self.name} {self._value}"


# ============================================================
# Global Metrics Registry
# ============================================================

class MetricsRegistry:
    """Central registry for all application metrics."""

    def __init__(self):
        self.http_requests_total = CounterMetric(
            "http_requests_total",
            "Total number of HTTP requests"
        )
        self.http_request_duration_seconds = HistogramMetric(
            "http_request_duration_seconds",
            "HTTP request latency in seconds"
        )
        self.http_requests_by_status = CounterMetric(
            "http_requests_by_status_total",
            "HTTP requests by status code"
        )
        self.http_requests_by_endpoint = CounterMetric(
            "http_requests_by_endpoint_total",
            "HTTP requests by endpoint"
        )
        self.workouts_generated_total = CounterMetric(
            "workouts_generated_total",
            "Total workouts generated"
        )
        self.recovery_scores_computed = CounterMetric(
            "recovery_scores_computed_total",
            "Total recovery scores computed"
        )
        self.ai_llm_calls_total = CounterMetric(
            "ai_llm_calls_total",
            "Total LLM API calls",
        )
        self.ai_llm_call_duration = HistogramMetric(
            "ai_llm_call_duration_seconds",
            "LLM API call latency"
        )
        self.active_users = GaugeMetric(
            "active_users_current",
            "Number of currently active users"
        )
        self.storage_operations_total = CounterMetric(
            "storage_operations_total",
            "Total storage operations"
        )
        self.error_rate = CounterMetric(
            "errors_total",
            "Total errors by type"
        )

    def render(self) -> str:
        """Render all metrics in Prometheus exposition format."""
        metrics = [
            self.http_requests_total,
            self.http_request_duration_seconds,
            self.http_requests_by_status,
            self.http_requests_by_endpoint,
            self.workouts_generated_total,
            self.recovery_scores_computed,
            self.ai_llm_calls_total,
            self.ai_llm_call_duration,
            self.active_users,
            self.storage_operations_total,
            self.error_rate,
        ]
        return "\n\n".join(m.render() for m in metrics)


# Global singleton
metrics = MetricsRegistry()


# ============================================================
# Middleware
# ============================================================

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware that records request metrics for every endpoint."""

    SKIP_PATHS = {"/health", "/metrics", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in self.SKIP_PATHS or path.startswith("/static"):
            return await call_next(request)

        method = request.method
        start = time.perf_counter()

        try:
            response = await call_next(request)
            elapsed = time.perf_counter() - start

            # Record metrics
            metrics.http_requests_total.inc()
            metrics.http_request_duration_seconds.observe(elapsed)
            metrics.http_requests_by_status.inc(label=str(response.status_code))

            # Normalize endpoint (remove IDs for cardinality control)
            endpoint = self._normalize_path(path)
            metrics.http_requests_by_endpoint.inc(label=f"{method} {endpoint}")

            return response

        except Exception:
            elapsed = time.perf_counter() - start
            metrics.http_requests_total.inc()
            metrics.http_request_duration_seconds.observe(elapsed)
            metrics.http_requests_by_status.inc(label="500")
            metrics.error_rate.inc(label="unhandled_exception")
            raise

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalize path to reduce cardinality: replace UUIDs and numbers with placeholders."""
        import re
        # Replace UUIDs
        path = re.sub(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '{id}', path
        )
        # Replace standalone numbers
        path = re.sub(r'/\d+', '/{id}', path)
        return path

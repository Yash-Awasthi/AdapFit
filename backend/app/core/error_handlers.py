"""Structured error handling middleware for AdapFit.

Provides consistent error responses across all endpoints.
"""

from __future__ import annotations
import traceback
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handler that returns structured JSON errors."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        try:
            response = await call_next(request)
            elapsed = (time.perf_counter() - start) * 1000

            # Add request ID and timing headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{elapsed:.1f}ms"

            return response

        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": {
                        "type": "http_error",
                        "status_code": exc.status_code,
                        "detail": str(exc.detail),
                        "request_id": request_id,
                    }
                },
                headers={"X-Request-ID": request_id},
            )

        except ValueError as exc:
            return JSONResponse(
                status_code=422,
                content={
                    "error": {
                        "type": "validation_error",
                        "status_code": 422,
                        "detail": str(exc),
                        "request_id": request_id,
                    }
                },
                headers={"X-Request-ID": request_id},
            )

        except Exception as exc:
            # Log the full traceback but don't expose internals
            tb = traceback.format_exc()
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "type": "internal_error",
                        "status_code": 500,
                        "detail": "An internal error occurred. Please try again.",
                        "request_id": request_id,
                    }
                },
                headers={"X-Request-ID": request_id},
            )

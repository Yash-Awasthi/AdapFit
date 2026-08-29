"""
Response Compression Middleware — Gzip compression for API responses

Reduces bandwidth usage and improves response times, especially for:
- Large JSON payloads (exercise library, health records)
- Health data exports
- API responses with repeated patterns
"""
import gzip
import io
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# Minimum response size to compress (bytes)
MIN_COMPRESS_SIZE = 500

# Content types eligible for compression
COMPRESSIBLE_TYPES = {
    "application/json",
    "text/html",
    "text/css",
    "text/plain",
    "text/xml",
    "application/javascript",
}


class CompressionMiddleware(BaseHTTPMiddleware):
    """Gzip compression for compressible API responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding:
            return response

        # Check content type
        content_type = response.headers.get("content-type", "")
        if not any(ct in content_type for ct in COMPRESSIBLE_TYPES):
            return response

        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            if isinstance(chunk, str):
                body += chunk.encode("utf-8")
            else:
                body += chunk

        # Only compress if large enough
        if len(body) < MIN_COMPRESS_SIZE:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=content_type,
            )

        # Compress
        compressed = gzip.compress(body, compresslevel=6)

        # Only use compressed if it's actually smaller
        if len(compressed) >= len(body):
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=content_type,
            )

        # Return compressed response
        headers = dict(response.headers)
        headers["content-encoding"] = "gzip"
        headers["content-length"] = str(len(compressed))
        headers["vary"] = "Accept-Encoding"

        # Remove content-type if not set
        return Response(
            content=compressed,
            status_code=response.status_code,
            headers=headers,
            media_type=content_type,
        )

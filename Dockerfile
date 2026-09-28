# AdapFit Backend — Multi-stage Docker Build

# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim as production

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code. `src/` is required: 29 imports across the endpoint
# layer read `src.*`, and main.py adds the project root to sys.path to reach
# them. Without it those endpoints fail to import inside the image.
COPY backend/ ./backend/
COPY web/ ./web/
COPY src/ ./src/

# Set environment variables
ENV PYTHONPATH=/app/backend
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000
# The container is reachable only through the platform proxy, so its X-Forwarded-For
# is the real client address; rate limits and the audit log key on it.
ENV FORWARDED_ALLOW_IPS="*"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# One worker: feature state is held in memory and written through (app/core/durable.py).
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# AdapFit backend. Build from the repository root: docker build -t adapfit .
FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /bin/uv

# MediaPipe's native library links EGL and GLES at import time, even on CPU.
# upgrade first so the base image's OS packages carry the latest security fixes.
RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends libegl1 libgles2 \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv PATH="/opt/venv/bin:$PATH"
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-cache

# main.py adds the repository root to sys.path for the `src.*` imports.
COPY src/ /app/src/
COPY backend/ /app/backend/
ADD https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task     ./app/data/pose_landmarker_full.task
RUN useradd -m -u 1000 app && chown -R app:app /app/backend/app/data
USER app

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PORT=8000
# Only the platform proxy reaches the container, so X-Forwarded-For is the client address.
ENV FORWARDED_ALLOW_IPS="*"
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://localhost:{os.environ[\"PORT\"]}/health')"

# One worker: feature state lives in process memory (app/core/durable.py).
CMD ["sh", "-c", "if [ -n \"$DATABASE_URL\" ]; then python -m scripts.apply_migrations && python -m scripts.migrate_feature_state_json || exit 1; fi; exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --proxy-headers"]

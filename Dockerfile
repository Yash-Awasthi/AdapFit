# AdapFit backend. Build from the repository root: docker build -t adapfit .
FROM python:3.12-slim

# opencv and mediapipe need these shared libraries at import time on a slim image.
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt .
# CPU wheels: the default torch wheel pulls several GB of CUDA libraries.
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# main.py adds the repository root to sys.path for the `src.*` imports.
COPY src/ ./src/
COPY backend/ ./backend/
ADD https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task     ./backend/app/data/pose_landmarker_full.task
RUN useradd -m -u 1000 app && chown -R app:app /app/backend/app/data
USER app
WORKDIR /app/backend

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PORT=8000
# Only the platform proxy reaches the container, so X-Forwarded-For is the client address.
ENV FORWARDED_ALLOW_IPS="*"
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://localhost:{os.environ[\"PORT\"]}/health')"

# One worker: feature state lives in process memory (app/core/durable.py).
CMD ["sh", "-c", "if [ -n \"$DATABASE_URL\" ]; then python -m scripts.apply_migrations || exit 1; fi; exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --proxy-headers"]

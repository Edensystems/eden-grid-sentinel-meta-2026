FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    EDEN_SERVICE=learn

# Only package metadata and source go into the image (no keys, .env or tooling)
COPY pyproject.toml .
COPY src/ ./src/
RUN pip install --no-cache-dir ".[pipeline]"

EXPOSE 8080

# One image for all stages: set EDEN_SERVICE=think|learn|act per Cloud Run service
CMD exec uvicorn "eden.services.${EDEN_SERVICE}:app" --host 0.0.0.0 --port "${PORT}"

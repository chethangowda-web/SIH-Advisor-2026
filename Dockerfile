# SIH Aurora — single-service image (backend API + static frontend)
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for ChromaDB / sentence-transformers native builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for better layer caching
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Bundle application code
COPY backend /app/backend
COPY frontend /app/frontend

WORKDIR /app/backend

EXPOSE 8000

# Start the API server directly. The app's RAG uses scikit-learn TF-IDF over the
# JSON dataset (no ChromaDB needed at boot), so we skip the heavy embedding
# pipeline for fast, reliable cold starts.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
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

# Build the vector DB on boot if missing, then start the API server.
# The /data volume persists the ChromaDB index across redeploys.
ENV CHROMA_DB_PATH_DEFAULT=./chroma_db
CMD ["sh", "-c", "DB=${CHROMA_DB_PATH:-${CHROMA_DB_PATH_DEFAULT}}; if [ ! -d \"$DB\" ] || [ -z \"$(ls -A \"$DB\" 2>/dev/null)\" ]; then python data_pipeline.py; fi && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
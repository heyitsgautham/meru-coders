# Backend image for Meru Coders, the Sanskrit meter identification API.
# Build from the repository root: docker build -f backend/Dockerfile .
FROM python:3.11-slim

WORKDIR /app

# Tesseract OCR with Sanskrit, Hindi and English data, libmagic for file type
# detection, and ffmpeg for converting browser voice recordings to WAV.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-san \
    tesseract-ocr-hin \
    tesseract-ocr-eng \
    libmagic1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt is exported from uv.lock, so versions match the lockfile.
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code, datasets and, when present at deploy time, backend/secrets/.
COPY backend/ /app/backend/

# Paths the app writes at runtime, owned by the non-root user:
#   backend/uploads/        photos, texts, results, TTS audio, community images
#   backend/data/chroma_db/ ChromaDB opens its SQLite store read-write
#   /home/app/.cache/       Hugging Face model downloads for the RAG embeddings
# settings.TMP_PATH lives under /tmp, which is already world-writable.
RUN useradd --create-home --uid 10001 app \
    && mkdir -p /app/backend/uploads/photos /app/backend/uploads/texts \
       /app/backend/uploads/results /app/backend/uploads/audio \
       /app/backend/uploads/community /app/backend/data/chroma_db \
       /home/app/.cache \
    && chown -R app:app /app/backend/uploads /app/backend/data/chroma_db /home/app/.cache

USER app

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# Cloud Run overrides PORT; run.py reads it.
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"5000\")}/health', timeout=4)"

CMD ["python", "backend/run.py"]
